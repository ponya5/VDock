"""DL-145: context.focused_repo() keeps meaning something while the deck has focus."""
import pytest

from integrations import agent_state, context


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    context.reset_focus_memory()
    agent_state.reset()
    monkeypatch.setattr(context, 'current_editor', lambda: context.EditorContext())
    yield
    context.reset_focus_memory()
    agent_state.reset()


def _editor(cwd):
    return context.EditorContext(app_exe='cursor.exe', cwd=str(cwd))


def _note(monkeypatch, project_dir):
    monkeypatch.setattr(context, '_resolve_project_dir',
                        lambda name: str(project_dir))
    context.note_foreground('cursor.exe', 'a.py - proj - Cursor')


def test_configured_dir_wins(tmp_path, monkeypatch):
    other = tmp_path / 'other'
    other.mkdir()
    monkeypatch.setattr(context, 'current_editor', lambda: _editor(other))
    configured = tmp_path / 'cfg'
    configured.mkdir()
    assert context.focused_repo(str(configured)) == str(configured)


def test_missing_configured_dir_is_ignored(tmp_path, monkeypatch):
    other = tmp_path / 'other'
    other.mkdir()
    monkeypatch.setattr(context, 'current_editor', lambda: _editor(other))
    assert context.focused_repo(str(tmp_path / 'nope')) == str(other)


def test_focused_editor_beats_memory(tmp_path, monkeypatch):
    remembered, focused = tmp_path / 'a', tmp_path / 'b'
    remembered.mkdir()
    focused.mkdir()
    _note(monkeypatch, remembered)
    monkeypatch.setattr(context, 'current_editor', lambda: _editor(focused))
    assert context.focused_repo() == str(focused)


def test_memory_used_when_deck_has_focus(tmp_path, monkeypatch):
    project = tmp_path / 'proj'
    project.mkdir()
    _note(monkeypatch, project)
    assert context.focused_repo() == str(project)


def test_non_editor_foreground_is_not_remembered(tmp_path, monkeypatch):
    monkeypatch.setattr(context, '_resolve_project_dir',
                        lambda name: str(tmp_path))
    context.note_foreground('chrome.exe', 'a - b - Chrome')
    assert context._last_editor is None


def test_memory_expires(tmp_path, monkeypatch):
    project = tmp_path / 'proj'
    project.mkdir()
    _note(monkeypatch, project)
    real = context.time.time()
    monkeypatch.setattr(context.time, 'time',
                        lambda: real + context.LAST_EDITOR_TTL_SECONDS + 5)
    fallback = tmp_path / 'fallback'
    fallback.mkdir()
    monkeypatch.setattr(context, 'resolve_cwd', lambda c=None: str(fallback))
    assert context.focused_repo() == str(fallback)


def test_falls_back_to_newest_agent_session_cwd(tmp_path):
    old, new = tmp_path / 'old', tmp_path / 'new'
    old.mkdir()
    new.mkdir()
    agent_state.record('claude', 'ready', session_id='o', cwd=str(old))
    agent_state._sessions_by_source['claude']['o']['ts'] -= 100
    agent_state.record('cursor', 'working', session_id='n', cwd=str(new))
    assert context.focused_repo() == str(new)


def test_nonexistent_dirs_are_skipped(tmp_path, monkeypatch):
    agent_state.record('claude', 'ready', session_id='x',
                       cwd=str(tmp_path / 'gone'))
    sentinel = tmp_path / 'fb'
    sentinel.mkdir()
    monkeypatch.setattr(context, 'resolve_cwd', lambda c=None: str(sentinel))
    assert context.focused_repo() == str(sentinel)


def test_final_fallback_equals_resolve_cwd():
    assert context.focused_repo() == context.resolve_cwd(None)
