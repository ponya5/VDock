"""DL-165: open_app resolves the real app, and says so when it is not installed (Windows + macOS paths)."""
from services import app_launcher as al


def test_missing_app_is_reported_not_silently_started(monkeypatch):
    monkeypatch.setattr(al, '_SYSTEM', 'Windows')
    monkeypatch.setattr(al, '_windows_resolvable', lambda name: False)
    monkeypatch.setattr('services.app_paths.override_for', lambda *n: None)
    r = al.launch('Cursor')
    assert not r.ok and r.not_installed and r.message == 'Cursor is not installed'
    assert 'Browse' in r.details


def test_claude_desktop_uses_the_store_app_not_the_cli(monkeypatch):
    calls = []
    monkeypatch.setattr(al, '_SYSTEM', 'Windows')
    monkeypatch.setattr('services.app_paths.override_for', lambda *n: None)
    monkeypatch.setattr(al, 'start_apps_id', lambda name: 'Claude_x!Claude')
    monkeypatch.setattr(al, '_spawn', lambda argv, shell=False: (calls.append(argv), al.AppLaunchResult(True, 'Opened'))[1])
    r = al.launch('Claude Desktop')
    assert r.ok and 'shell:AppsFolder' in calls[0] and 'Claude_x!Claude' in calls[0]


def test_claude_desktop_not_installed_has_a_download_link(monkeypatch):
    monkeypatch.setattr(al, '_SYSTEM', 'Windows')
    monkeypatch.setattr('services.app_paths.override_for', lambda *n: None)
    monkeypatch.setattr(al, 'start_apps_id', lambda name: None)
    r = al.launch('Claude Desktop')
    assert r.not_installed and r.download.startswith('https://claude.com')


def test_macos_checks_the_app_bundle_then_opens_it(monkeypatch):
    calls = []
    monkeypatch.setattr(al, '_SYSTEM', 'Darwin')
    monkeypatch.setattr('services.app_paths.override_for', lambda *n: None)
    monkeypatch.setattr(al, '_mac_app_exists', lambda bundle: bundle == 'Claude.app')
    monkeypatch.setattr(al, '_spawn', lambda argv, shell=False: (calls.append(argv), al.AppLaunchResult(True, 'Opened'))[1])
    assert al.launch('Claude Desktop').ok and calls[0] == ['open', '-a', 'Claude']
    monkeypatch.setattr(al, '_mac_app_exists', lambda bundle: False)
    assert al.launch('Claude Desktop').not_installed


def test_a_configured_location_wins(monkeypatch):
    monkeypatch.setattr('services.app_paths.override_for', lambda *n: '/opt/Apps/Cursor')
    monkeypatch.setattr('services.app_paths.launch_app', lambda p: p == '/opt/Apps/Cursor')
    assert al.launch('cursor').ok


def test_a_missing_explicit_path_is_not_installed(monkeypatch):
    monkeypatch.setattr('services.app_paths.override_for', lambda *n: None)
    r = al.launch('/Applications/Nope.app')
    assert r.not_installed and 'expected at' in r.details
