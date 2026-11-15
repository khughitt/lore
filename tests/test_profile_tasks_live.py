"""Integration with installed tasks, never a substitute for hosted fake-value coverage."""
import fcntl
import hashlib
import os
from pathlib import Path
import subprocess

import pytest
from conftest import git, live_tasks_unavailable, require_tasks
from lore import resolve

pytestmark = pytest.mark.skipif(live_tasks_unavailable(os.environ),
    reason='installed tasks unavailable on hosted CI; run just test-live locally')


def test_resolution_ignores_task_body_and_records_lock(profile_world):
    w=profile_world
    env={key:value for key,value in w.env.items() if key not in {'REPLIES','CALL_LOG'}}
    env['PATH']=os.environ['PATH']
    env.update(GIT_AUTHOR_NAME='Fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='Fixture',GIT_COMMITTER_EMAIL='fixture@example.invalid')
    executable=require_tasks(env)
    for prefix,checkout in [('lore',w.corpus),('demo',w.checkout)]:
        result=subprocess.run([executable,'-C',str(checkout),'init','--prefix',prefix,
                               '--records',str(w.records)],env=env,capture_output=True,text=True,timeout=10)
        assert result.returncode==0,result.stderr
        config=w.records/prefix/'tasks/.config.toml'
        config.write_text('profile = "personal"\n'+config.read_text())
    broken=w.records/'demo/tasks/demo-abcdef.md';broken.write_text('---\nnot valid yaml: [\n')
    common=Path(git(w.records,env,'rev-parse','--path-format=absolute','--git-common-dir'))
    digest=hashlib.sha256(os.fsencode(common)).hexdigest()[:16]
    lock=Path(env['XDG_STATE_HOME'])/'tasks/claims'/f'.commit-{digest}.lock'
    lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('w') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before={str(p.relative_to(w.records)):p.read_bytes() for p in w.records.rglob('*') if p.is_file()}
        result=resolve(w.checkout,env)
        assert result['profiles'][0]['name']=='personal'
        after={str(p.relative_to(w.records)):p.read_bytes() for p in w.records.rglob('*') if p.is_file()}
        assert after==before
