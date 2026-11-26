"""The committed applicability file and the band worker context it is tried on."""
import json
import os
import pathlib
import re
import subprocess

import pytest

from lore.context import check, select_text
from lore.context._applicability import parse, required_by, state
from lore.context._corpus import load

from .conftest import ROOT

FIXTURE = ROOT / 'tests/context/fixtures/band-worker.json'


def band_worker():
    return json.loads(FIXTURE.read_text())


def titles():
    return {json.loads(p.read_text())['title']: 'rule:' + p.stem for p in (ROOT / 'instructions/rules').glob('*.json')}


def decisions(context, shadow=True):
    _, record = select_text(ROOT, context, shadow=shadow, view='working')
    return {r['id']: r for r in record['rules']}


def expect(rules, title, decision, reason):
    """The decision for a titled rule, or include/stale while its entry is stale after a rule-text edit."""
    corpus = load(ROOT, 'working')
    entries = parse(corpus.applicability)
    rule_id = titles()[title]
    sha = next(r.sha256 for r in corpus.rules if r.id == rule_id)
    if rule_id in entries and state(entries[rule_id], sha, required_by(entries).get(rule_id, ())) == 'stale':
        decision, reason = 'include', 'stale'
    assert (rules[rule_id]['decision'], rules[rule_id]['reason']) == (decision, reason), title


def test_applicability_file_has_no_problems():
    problems, warnings = check(ROOT, 'working')
    assert problems == []


def test_live_selection_for_band_worker_omits_only_rules_with_reviewed_entries():
    corpus = load(ROOT, 'working')
    entries = parse(corpus.applicability)
    incoming = required_by(entries)
    shas = {r.id: r.sha256 for r in corpus.rules}
    live = {i for i, r in decisions(band_worker(), shadow=False).items() if r['decision'] == 'omit'}
    shadow = {i for i, r in decisions(band_worker(), shadow=True).items() if r['decision'] == 'omit'}
    for rule in live:
        assert state(entries[rule], shas[rule], incoming.get(rule, ())) == 'reviewed', rule
    assert live <= shadow


def test_shadow_selection_for_band_worker_omits_withheld_duty_rules_and_keeps_unknown_ones():
    rules = decisions(band_worker())
    expect(rules, 'Question format', 'omit', 'test-false')
    expect(rules, 'Live desktop permission', 'include', 'unknown-fact')
    expect(rules, 'Shell syntax boundaries', 'include', 'unknown-fact')
    expect(rules, 'Record machine-readable outcomes', 'include', 'entry-holds')


def test_record_keeping_report_rules_stay_for_an_unread_actor_that_writes_task_records():
    unchanged = decisions(band_worker())
    writer = band_worker()
    writer['duties']['withheld'] = [w for w in writer['duties']['withheld'] if w['duty'] != 'task-records']
    writer['duties']['held'].append('task-records')
    changed = decisions(writer)
    for title in ('Report evidence and limits', 'Retain rulings and integration state'):
        expect(unchanged, title, 'omit', 'test-false')
        expect(changed, title, 'include', 'entry-holds')


def _registry_env():
    """PATH and the variables that locate the user's tasks registry, nothing else."""
    env = {}
    for key in ('PATH', 'HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_STATE_HOME'):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def band_root():
    try:
        result = subprocess.run(['tasks', 'resolve', 'band', '--json'], capture_output=True, text=True, timeout=30,
                                env=_registry_env())
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    root = json.loads(result.stdout)['results'][0].get('root')
    return pathlib.Path(root) if root and (pathlib.Path(root) / 'src/adapters/tasks/brief.ts').is_file() else None


def test_band_fixture_quotes_exist_in_band_brief():
    root = band_root()
    if root is None:
        pytest.skip('band checkout not resolvable on this host (tasks resolve band); quotes not checked')
    brief = (root / 'src/adapters/tasks/brief.ts').read_text()
    for withheld in band_worker()['duties']['withheld']:
        source = withheld['source']
        assert source.startswith('band src/adapters/tasks/brief.ts: '), source
        quote = re.search(r'"(.*)"$', source).group(1)
        for part in (p.strip() for p in quote.split('…')):
            if part:
                assert part in brief, (withheld['duty'], part)


def test_band_root_builds_its_environment_key_by_key(monkeypatch):
    seen = {}

    def fake(args, **kwargs):
        seen.update(kwargs)
        raise OSError('not run')

    monkeypatch.setenv('GIT_DIR', '/elsewhere/.git')
    monkeypatch.setattr(subprocess, 'run', fake)
    assert band_root() is None
    assert isinstance(seen.get('env'), dict) and 'GIT_DIR' not in seen['env'] and 'PATH' in seen['env']
