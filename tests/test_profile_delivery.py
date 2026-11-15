"""Fresh-process delivery tests; source location and payloads are real, accounts fake."""
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def delivery(profile_world):
    w=profile_world
    shutil.copytree(ROOT/'src',w.corpus/'src',ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('hooks/claude-profile','bin/lore'):
        target=w.corpus/name;target.parent.mkdir(exist_ok=True)
        if (ROOT/name).exists(): shutil.copy2(ROOT/name,target)
    # Store prose is corpus data, copied independently of production rendering logic.
    if (ROOT/'profiles/records-store.md').exists():
        shutil.copy2(ROOT/'profiles/records-store.md',w.corpus/'profiles/records-store.md')
    return w


def hook(w,payload=None,extra=None,root=None):
    root=root or w.corpus
    env=w.env | {'CLAUDE_ENV_FILE':str(w.records.parent/'export.sh')}
    env.update(extra or {})
    return subprocess.run([sys.executable,str(root/'hooks/claude-profile')],
        input=json.dumps({'cwd':str(w.checkout)}) if payload is None else payload,
        cwd=w.checkout,env=env,capture_output=True,text=True,timeout=10)


def cli(w,*args,root=None):
    return subprocess.run([sys.executable,str((root or w.corpus)/'bin/lore'),'profile',*args],
        cwd=w.checkout,env=w.env,capture_output=True,text=True,timeout=10)


def test_hook_renders_before_export(delivery):
    w=delivery;r=hook(w)
    assert r.returncode==0
    assert r.stdout.startswith('profile: personal')
    assert '# Profile: personal' in r.stdout
    assert (w.records.parent/'export.sh').read_text()=='export AGENT_PROFILE=personal\n'
    assert not list((w.corpus/'src').rglob('__pycache__'))


@pytest.mark.parametrize('payload',['bad-json','null','[]','{}'])
def test_payload_cwd_falls_back(delivery,payload):
    assert hook(delivery,payload).stdout.startswith('profile: personal')


@pytest.mark.parametrize('failure',['private','fragment','export'])
def test_failure_has_one_line_no_success_or_partial_export(delivery,failure):
    w=delivery
    if failure=='private':w.private.write_text('not [toml')
    elif failure=='fragment':(w.corpus/'profiles/personal.md').write_bytes(b'\xff')
    else:(w.records.parent/'export.sh').mkdir()
    r=hook(w)
    assert r.returncode==0
    assert r.stdout.startswith('profile: unresolved') and len(r.stdout.splitlines())==1
    assert '# Profile:' not in r.stdout
    if failure!='export': assert not (w.records.parent/'export.sh').exists()


def test_store_prose_replaces_external_placement(delivery):
    w=delivery
    w.data[f'resolve {w.records} --json']={'results':[{'status':'unregistered','records_store':str(w.records)}],'warnings':[]};w.save()
    text=hook(w,json.dumps({'cwd':str(w.records/'lore')})).stdout
    assert text.startswith('profile: records-store')
    assert 'tasks commit --project' in text
    assert 'no worktrees' in text.lower()
    assert 'attribution' in text and 'task-id' in text
    assert '# Profile: external' not in text
    assert (w.records.parent/'export.sh').read_text()=='export AGENT_PROFILE=external\n'


def test_cli_surfaces_and_nonzero_errors(delivery):
    w=delivery
    r=cli(w,'resolve',str(w.checkout),'--json')
    assert r.returncode==0,r.stderr
    result=json.loads(r.stdout)
    assert result['profiles'][0]['name']=='personal' and '_otherwise' not in result
    assert cli(w,'explain',str(w.checkout)).returncode==0
    assert cli(w,'session',str(w.checkout)).stdout.startswith('profile: personal')
    assert cli(w,'check').returncode==0
    assert cli(w,'audit',str(w.checkout)).returncode==0
    w.private.write_text('[bad');assert cli(w,'resolve',str(w.checkout),'--json').returncode!=0


def test_advice_without_path_install(delivery):
    w=delivery
    alternate=w.corpus.parent/"lore source's space"
    shutil.copytree(w.corpus,alternate)
    advice=shlex.quote(str(alternate/'bin/lore'))+' profile explain'
    assert advice in hook(w,root=alternate).stdout
    assert advice in cli(w,'session',str(w.checkout),root=alternate).stdout
    w.private.write_text('[bad')
    failure=hook(w,root=alternate).stdout
    recovery=shlex.quote(str(alternate/'bin/lore'))+' profile session'
    assert recovery in failure
    # Even failure before package import identifies the usable source-tree launcher.
    shutil.rmtree(alternate/'src/lore')
    assert recovery in hook(w,root=alternate).stdout


def test_payload_transcript_controls_hook_home(delivery):
    w=delivery
    payload={'cwd':str(w.checkout),'transcript_path':str(w.records.parent/'.codex-work/sessions/session.jsonl')}
    r=hook(w,json.dumps(payload))
    assert '; home: work;' in r.stdout
    assert 'expects home personal; running in work' in r.stdout


@pytest.mark.parametrize('body', ["raise RuntimeError('first\\nsecond')\n",
    "def resolve(*args): raise RuntimeError('first\\nsecond')\ndef session_text(r): return 'unused'\n"])
def test_unexpected_import_and_resolution_errors_are_one_line(delivery,body):
    w=delivery;(w.corpus/'src/lore/__init__.py').write_text(body)
    r=hook(w)
    assert r.returncode==0 and len(r.stdout.splitlines())==1
    assert 'first second' in r.stdout
    assert not (w.records.parent/'export.sh').exists()


def test_deleted_cwd_is_reported(delivery):
    w=delivery;deleted=w.records.parent/'deleted';deleted.mkdir()
    r=subprocess.run([sys.executable,'-c',
       "import os,runpy,sys;os.chdir(sys.argv[1]);os.rmdir(sys.argv[1]);runpy.run_path(sys.argv[2],run_name='__main__')",
       str(deleted),str(w.corpus/'hooks/claude-profile')],env=w.env,input='{}',capture_output=True,text=True,timeout=10)
    assert r.returncode==0 and r.stdout.startswith('profile: unresolved')
    assert len(r.stdout.splitlines())==1
