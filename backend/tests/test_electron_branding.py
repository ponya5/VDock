"""Dev-checkout Electron is renamed to VDock on macOS and left alone elsewhere."""
import plistlib
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))

import electron_branding  # noqa: E402


@pytest.fixture
def electron_dir(tmp_path):
    contents = electron_branding.electron_app_bundle(tmp_path) / 'Contents'
    contents.mkdir(parents=True)
    with (contents / 'Info.plist').open('wb') as plist_file:
        plistlib.dump({'CFBundleName': 'Electron', 'CFBundleDisplayName': 'Electron'}, plist_file)
    return tmp_path


def _bundle_name(electron_dir):
    plist_path = electron_branding.electron_app_bundle(electron_dir) / 'Contents' / 'Info.plist'
    with plist_path.open('rb') as plist_file:
        return plistlib.load(plist_file)['CFBundleName']


def test_macos_bundle_is_renamed_and_resigned_once(electron_dir):
    with mock.patch('electron_branding.platform.system', return_value='Darwin'), \
            mock.patch('electron_branding.resign_bundle') as resign:
        first_run = electron_branding.brand_electron_bundle(electron_dir)
        second_run = electron_branding.brand_electron_bundle(electron_dir)

    assert (first_run, second_run) == (True, False)
    assert _bundle_name(electron_dir) == 'VDock'
    resign.assert_called_once()


@pytest.mark.parametrize('system_name', ['Windows', 'Linux'])
def test_other_platforms_are_untouched(electron_dir, system_name):
    with mock.patch('electron_branding.platform.system', return_value=system_name):
        assert electron_branding.brand_electron_bundle(electron_dir) is None

    assert _bundle_name(electron_dir) == 'Electron'


def test_missing_bundle_is_a_no_op(tmp_path):
    with mock.patch('electron_branding.platform.system', return_value='Darwin'):
        assert electron_branding.brand_electron_bundle(tmp_path) is None
