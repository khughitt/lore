"""Resolution outcomes, real Git discovery, and the tasks response trust boundary."""
import json
import pytest
from lore import ProfileError, resolve
from conftest import git, init_repo


def test_registered_assignment_and_repository_override(profile_world):
    w=profile_world
    r=resolve(w.checkout,w.env)
    assert [p['name'] for p in r['profiles']]==['personal']
    assert r['keys']['design_docs']['value']=='records'
    assert r['layout']=={'kind':'detached','records':str(w.records/'demo')}
    (w.checkout/'AGENTS.md').write_text('Designs in docs/superpowers/specs/')
    assert resolve(w.checkout,w.env)['keys']['design_docs']['value']=='commit'
    git(w.checkout,w.env,'config','agent.profile','work')
    assert resolve(w.checkout,w.env)['keys']['gh_account']['value']=='work-test'


@pytest.mark.parametrize('damage', ['entry_error','profile','bad_status','warnings','bad_results'])
def test_override_does_not_hide_invalid_metadata(profile_world,damage):
    w=profile_world
    git(w.checkout,w.env,'config','agent.profile','personal')
    if damage=='entry_error': w.row['entry_error']='unreadable'
    elif damage=='profile': w.row['entry']['profile']='not-defined'
    elif damage=='bad_status': w.row['status']='ambiguous'
    elif damage=='warnings': w.data[f'resolve {w.checkout} --json']['warnings']=['unreadable entry']
    else: w.data[f'resolve {w.checkout} --json']['results']={}
    w.save()
    with pytest.raises(ProfileError): resolve(w.checkout,w.env)


def test_path_and_default_only_for_absent_assignment(profile_world):
    w=profile_world
    w.row['entry'].pop('profile');w.save()
    assert resolve(w.checkout,w.env)['profiles'][0]['name']=='external'
    with w.private.open('a') as f: f.write(f'\n[[family]]\npath="{w.checkout}"\nprofiles=["work"]\n')
    assert resolve(w.checkout,w.env)['profiles'][0]['name']=='work'
    git(w.checkout,w.env,'config','agent.profile','personal,science')
    assert [p['name'] for p in resolve(w.checkout,w.env)['profiles']]==['personal','science']
    git(w.checkout,w.env,'config','agent.profile','personal,personal')
    with pytest.raises(ProfileError):resolve(w.checkout,w.env)


def test_store_paths_use_canonical_root(profile_world):
    w=profile_world
    w.data[f'resolve {w.records} --json']={'results':[{'status':'unregistered','records_store':str(w.records)}],'warnings':[]};w.save()
    wt=w.records.parent/'records-wt'
    git(w.records,w.env,'worktree','add','-qb','fixture-store',str(wt))
    for path in (w.records,w.records/'lore',wt):
        r=resolve(path,w.env)
        assert r['kind']=='records-store' and r['project'] is None
        assert r['keys']['design_docs']=={'value':'not-applicable','source':'tasks records store'}
        assert r['records_store']==str(w.records)
    calls=[json.loads(line) for line in w.calls.read_text().splitlines()]
    assert not any(c[0]=='where' for c in calls)


def test_parent_store_marker_is_not_store(profile_world):
    w=profile_world;w.row['records_store']=str(w.records);w.save()
    assert resolve(w.checkout,w.env)['kind']=='checkout'


def test_in_tree_and_historical_worktree_keep_checkout(profile_world):
    w=profile_world;w.row['entry']['kind']='in-tree';w.save()
    wt=w.checkout.parent/'project-wt'
    git(w.checkout,w.env,'worktree','add','-qb','fixture-code',str(wt))
    (wt/'AGENTS.md').write_text('docs/superpowers/plans/')
    r=resolve(wt,w.env)
    assert r['kind']=='checkout' and r['worktree']
    assert r['keys']['design_docs']['value']=='commit'


def test_payload_home_and_private_listing(profile_world):
    w=profile_world
    git(w.checkout,w.env,'config','agent.profile','work')
    r=resolve(w.checkout,w.env,{'transcript_path':str(w.records.parent/'.codex-work/sessions/s.jsonl')})
    assert r['home']['name']=='work'


def test_linked_notes_and_private_retirement(profile_world):
    w=profile_world
    w.row['entry']['kind']='linked';w.row['entry']['profile']='work'
    (w.records/'demo').mkdir();(w.records/'demo/AGENTS.md').write_text('Overlay notes')
    w.data['resolve --all --json']['results'].append({'status':'resolved','prefix':'ret',
        'root':str(w.checkout.parent/'retired'),
        'entry':{'config':str(w.records/'ret/tasks/.config.toml'),'records':str(w.records/'ret'),
                 'checkout':str(w.checkout.parent/'retired'),'kind':'detached','profile':'work','retired':{'date':'2026-01-01','reason':'replacement'},'name':'Retired fixture','purpose':'retired'}})
    w.save()
    r=resolve(w.checkout,w.env)
    assert r['notes']==str(w.records/'demo/AGENTS.md')
    assert r['records']['linked'] is True
    assert any('`ret`' in line for line in r['private_projects'])


def test_audit_uses_supplied_git_environment(profile_world,monkeypatch):
    from lore._profiles import audit
    w=profile_world
    git(w.checkout,w.env,'config','ops.designDocs','commit')
    (w.checkout/'.git/info/exclude').write_text('docs/specs/\n')
    monkeypatch.setenv('GIT_DIR',str(w.records/'.git'))
    assert any(line.startswith('docs/specs/') for line in audit(w.checkout,w.env))


def test_live_marker_and_missing_executable_are_explicit(tmp_path):
    from conftest import live_tasks_unavailable, require_tasks
    assert not live_tasks_unavailable({})
    assert live_tasks_unavailable({'LORE_TEST_LIVE_TASKS':'unavailable'})
    for bad in ('', 'yes', 'false'):
        with pytest.raises(ValueError):live_tasks_unavailable({'LORE_TEST_LIVE_TASKS':bad})
    with pytest.raises(RuntimeError,match='missing'):require_tasks({'PATH':str(tmp_path)})


def test_commit_profile_reports_hidden_design_docs(profile_world):
    w=profile_world
    git(w.checkout,w.env,'config','ops.designDocs','commit')
    (w.checkout/'.git/info/exclude').write_text('docs/specs/\n')
    assert any('hides 1 design-doc' in line for line in resolve(w.checkout,w.env)['warnings'])


def test_invalid_store_marker_fails(profile_world):
    w=profile_world;w.row['records_store']=42;w.save()
    with pytest.raises(ProfileError):resolve(w.checkout,w.env)


def test_live_recipe_refuses_missing_tasks(profile_world,tmp_path):
    import os,shutil,subprocess
    from pathlib import Path
    w=profile_world
    only=tmp_path/'runner-bin';only.mkdir()
    for name in ('python3','sh'):
        (only/name).symlink_to(shutil.which(name))
    env={'PATH':str(only),'HOME':w.env['HOME'], 'XDG_CONFIG_HOME':w.env['XDG_CONFIG_HOME'],
         'XDG_STATE_HOME':w.env['XDG_STATE_HOME'],'GIT_CONFIG_GLOBAL':w.env['GIT_CONFIG_GLOBAL'],
         'GIT_CONFIG_NOSYSTEM':'1','LORE_TEST_LIVE_TASKS':'unavailable'}
    result=subprocess.run([shutil.which('just'),'test-live'],cwd=Path(__file__).resolve().parents[1],
                          env=env,capture_output=True,text=True,timeout=15)
    assert result.returncode != 0
    assert 'installed tasks missing' in result.stdout+result.stderr


def test_private_listing_preserves_aliases_and_retired_successor(profile_world):
    w=profile_world
    w.row['entry'].update(profile='work',aliases=['alias'])
    w.data['resolve --all --json']['results'].append({'status':'resolved','prefix':'ret',
        'root':str(w.checkout.parent/'retired'),
        'entry':{'config':str(w.records/'ret/tasks/.config.toml'),'records':str(w.records/'ret'),
                 'checkout':str(w.checkout.parent/'retired'),'kind':'detached','profile':'work','name':'Old','purpose':'old',
                 'retired':{'date':'2026-01-01','successor':'demo','reason':'replacement'}}})
    w.save();git(w.checkout,w.env,'config','agent.profile','work')
    lines=resolve(w.checkout,w.env)['private_projects']
    assert '- `demo` — demo (alias) — A fixture' in lines
    assert 'Retired: `ret` (Old, 2026-01-01) → `demo`.' in lines


@pytest.mark.parametrize('override',[False,True])
@pytest.mark.parametrize('damage',['entry','kind','records','checkout','config','invalid_kind','relative_records','bad_checkout','blank_config'])
def test_required_resolved_metadata_cannot_change_policy(profile_world,override,damage):
    w=profile_world
    if override:git(w.checkout,w.env,'config','agent.profile','personal')
    if damage=='entry':w.row.pop('entry')
    elif damage in ('kind','records','checkout','config'):w.row['entry'].pop(damage)
    elif damage=='invalid_kind':w.row['entry']['kind']='other'
    elif damage=='relative_records':w.row['entry']['records']='relative'
    elif damage=='bad_checkout':w.row['entry']['checkout']=42
    else:w.row['entry']['config']=''
    w.save()
    with pytest.raises(ProfileError):resolve(w.checkout,w.env)


def test_unrelated_catalogue_warning_does_not_disable_session(profile_world):
    from lore._profiles import check
    w=profile_world;warning='other: /records/other: configuration unreadable'
    for key in ('resolve lore --json',f'resolve {w.checkout} --json','resolve --all --json'):
        w.data[key]['warnings']=[warning]
    w.save()
    assert resolve(w.checkout,w.env)['profiles'][0]['name']=='personal'
    with pytest.raises(ProfileError,match='other.*configuration unreadable'):check(w.env)
    git(w.checkout,w.env,'config','agent.profile','work')
    with pytest.raises(ProfileError,match='other'):resolve(w.checkout,w.env)


def test_relevant_warning_keeps_its_diagnostic(profile_world):
    w=profile_world
    w.data[f'resolve {w.checkout} --json']['warnings']=['demo: /records/demo: incomplete identity']
    w.save()
    with pytest.raises(ProfileError,match='demo.*incomplete identity'):resolve(w.checkout,w.env)


def test_legitimate_unregistered_checkout_can_use_default(profile_world):
    w=profile_world;w.data[f'resolve {w.checkout} --json']={'results':[{'status':'unregistered'}],'warnings':[]};w.save()
    assert resolve(w.checkout,w.env)['profiles'][0]['name']=='external'


@pytest.mark.parametrize('field',['kind','status'])
def test_container_in_scalar_metadata_is_profile_error(profile_world,field):
    w=profile_world
    if field=='kind':w.row['entry']['kind']=[]
    else:w.row['status']=[]
    w.save()
    with pytest.raises(ProfileError):resolve(w.checkout,w.env)
