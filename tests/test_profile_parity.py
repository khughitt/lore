"""Acceptance comparator tests pin which differences may be normalized away."""
import copy
import importlib.util
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


def comparator():
    spec=importlib.util.spec_from_file_location('profile_parity',ROOT/'scripts/profile-parity.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def result(tmp_path):
    fragment=tmp_path/'personal.md';fragment.write_text('Profile prose\n')
    return {'checkout':'/fixture','path':'/fixture','worktree':False,'project':'demo',
        'profiles':[{'name':'personal','source':'old source'}], 'home':{'name':'personal','source':'old'},
        'keys':{'gh_account':{'value':'fake','source':'old'},'design_docs':{'value':'records','source':'old'}},
        'records':None,'layout':{'kind':'detached','records':'/records/demo'},'notes':None,
        'fragments':[str(fragment)],'private_projects':[],'warnings':[]}


def test_only_documented_differences_normalize(tmp_path):
    mod=comparator();old=result(tmp_path);new=copy.deepcopy(old)
    new.update(kind='checkout',records_store=None)
    new['profiles'][0]['source']='new source';new['home']['source']='new hint'
    new['keys']['gh_account']['source']='private definition'
    assert mod.compare_resolution(old,new)==[]
    for change in ('account','home','profile','warning','private','placement','kind'):
        bad=copy.deepcopy(new)
        if change=='account':bad['keys']['gh_account']['value']='wrong'
        elif change=='home':bad['home']['name']='work'
        elif change=='profile':bad['profiles'][0]['name']='external'
        elif change=='warning':bad['warnings']=['missing identity']
        elif change=='private':bad['private_projects']=['lost project']
        elif change=='placement':bad['layout']['records']='/wrong'
        else:bad['kind']='records-store'
        assert mod.compare_resolution(old,bad),change


def test_present_failure_is_not_unavailable(tmp_path):
    mod=comparator();path=tmp_path/'code';path.mkdir()
    rows=[{'status':'resolved','prefix':'demo','root':str(path)},
          {'status':'resolved','prefix':'gone','root':str(tmp_path/'missing')},
          {'status':'unregistered','prefix':'record-only'}]
    def broken(path):raise RuntimeError('broken resolver')
    report=mod.compare_all(rows,broken,broken)
    assert report['present']==['demo'] and report['matched']==[]
    assert report['unavailable']==['gone'] and 'demo' in report['differences']


def test_unused_definition_drift_fails():
    mod=comparator()
    old={'profile':{'unused':{'pr_draft':'required'}},'home':{},'family':[],'default':{}}
    new=copy.deepcopy(old);new['_sources']={};new['_paths']=[]
    assert mod.compare_definitions(old,new,{})==[]
    new['profile']['unused']['pr_draft']='by-permission'
    assert mod.compare_definitions(old,new,{})
