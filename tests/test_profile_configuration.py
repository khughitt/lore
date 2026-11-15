"""Configuration ownership tests catch accidental last-wins or public private values."""
import pytest
from lore._configuration import ProfileError, load, compose
from conftest import PUBLIC, PRIVATE


def test_split_configuration_composes(tmp_path):
    pub=tmp_path/'public'; priv=tmp_path/'private'
    pub.write_text(PUBLIC); priv.write_text(PRIVATE)
    config=load(pub, priv, {'HOME': str(tmp_path)})
    assert compose(['personal'],config)['gh_account']['value']=='personal-test'
    with pytest.raises(ProfileError, match='both|twice'):
        compose(['personal','external'],config)
    with pytest.raises(ProfileError, match='no selected|missing'):
        compose(['science'],config)


@pytest.mark.parametrize('public,private', [
    (PUBLIC+'\n[profile.bad]\ngh_account="leaked"\n', PRIVATE),
    (PUBLIC, PRIVATE+'\n[default]\nprofiles=["personal"]\n'),
    (PUBLIC, PRIVATE+'\n[profile.science]\nfragment="different"\n'),
    (PUBLIC, PRIVATE+'\n[[family]]\npath="relative"\nprofiles=["work"]\n'),
    (PUBLIC, PRIVATE+'\n[profile.bad]\nunknown=true\n'),
    (PUBLIC, PRIVATE+'\n[[family]]\npath="~/same"\nprofiles=["work"]\n[[family]]\npath="~/same"\nprofiles=["personal"]\n'),
    (PUBLIC, PRIVATE+'\n[profile.bad]\ngit_identity="bad"\n'),
    ('profile=[]', PRIVATE),
])
def test_invalid_configuration_is_not_a_default(tmp_path,public,private):
    pub=tmp_path/'public'; priv=tmp_path/'private'
    pub.write_text(public); priv.write_text(private)
    with pytest.raises(ProfileError): load(pub,priv,{'HOME':str(tmp_path)})


def test_missing_file_is_explicit(tmp_path):
    with pytest.raises(ProfileError): load(tmp_path/'absent',tmp_path/'also-absent',{})


def test_composition_reports_definition_file(tmp_path):
    pub=tmp_path/'public';priv=tmp_path/'private'
    pub.write_text(PUBLIC);priv.write_text(PRIVATE)
    config=load(pub,priv,{'HOME':str(tmp_path)})
    assert str(priv) in compose(['personal'],config)['git_identity']['source']


@pytest.mark.parametrize('section',['home.personal', 'default'])
def test_unknown_container_keys_fail(tmp_path,section):
    pub=tmp_path/'public';priv=tmp_path/'private'
    pub.write_text(PUBLIC.replace(f'[{section}]',f'[{section}]\nwrong=true'));priv.write_text(PRIVATE)
    with pytest.raises(ProfileError):load(pub,priv,{'HOME':str(tmp_path)})


def test_shipped_profiles_have_complete_corpus(profile_world,monkeypatch):
    from pathlib import Path
    from lore import _profiles
    monkeypatch.setattr(_profiles,'CORPUS',Path(__file__).resolve().parents[1])
    assert _profiles.check(profile_world.env)==[]
