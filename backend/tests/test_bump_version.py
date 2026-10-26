"""Release versioning policy (scripts/bump_version.py, DL-152)."""
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    'bump_version', Path(__file__).resolve().parents[2] / 'scripts' / 'bump_version.py')
bv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bv)


@pytest.mark.parametrize('level,expected', [('major', '3.0.0'), ('minor', '2.7.0'), ('patch', '2.6.1')])
def test_bump_levels(level, expected):
    assert bv.bump('2.6.0', level) == expected


def test_feat_makes_a_minor_release():
    assert bv.decide_level(['fix: typo', 'feat: spotify scene', 'chore: deps']) == 'minor'
    assert bv.decide_level(['feat(ui): watermark']) == 'minor'


def test_only_fixes_make_a_patch_release():
    assert bv.decide_level(['fix: crash', 'docs: readme', 'chore: bump', 'refactor: x', 'not conventional']) == 'patch'


def test_breaking_change_makes_a_major_release():
    assert bv.decide_level(['feat: new', 'refactor!: drop old config']) == 'major'
    assert bv.decide_level(['fix: x\n\nBREAKING CHANGE: ports moved']) == 'major'


def test_non_semver_version_is_rejected():
    with pytest.raises(ValueError):
        bv.bump('2.6', 'patch')
