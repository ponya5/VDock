"""DL-144: the GitHub CI / PR widgets work off the user's `gh` login.

REST is mocked at ``Plugin._api``; ``sr.run`` is mocked for `gh auth token`
and `git remote`. The point is the contract the deck relies on: a token is
found without any .env setup, the widget result carries tone + badge + the
URL a press should open, and the token never leaks into messages.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integrations import github_pack  # noqa: E402
from integrations.github_pack import Plugin  # noqa: E402
from services import secrets  # noqa: E402
from utils.subprocess_runner import CommandResult  # noqa: E402

GH_TOKEN = 'gho_secret_from_gh_login'


def _result(stdout='', ok=True):
    return CommandResult(
        ok=ok, exit_code=0 if ok else 1, stdout=stdout, stderr='', argv=[],
    )


@pytest.fixture(autouse=True)
def no_env_token(monkeypatch):
    monkeypatch.delenv('GITHUB_TOKEN', raising=False)
    secrets._runtime_secrets.clear()
    yield
    secrets._runtime_secrets.clear()


@pytest.fixture
def plugin(mocker):
    mocker.patch('integrations.github_pack.sr.find_binary', return_value='C:/gh.exe')

    def fake_run(argv, **kwargs):
        if argv[:3] == ['gh', 'auth', 'token']:
            return _result(GH_TOKEN + '\n')
        if argv[:2] == ['gh', 'auth']:
            return _result('logged in')
        if argv[:3] == ['git', 'remote', 'get-url']:
            return _result('https://github.com/me/app.git\n')
        return _result()

    run = mocker.patch('integrations.github_pack.sr.run', side_effect=fake_run)
    mocker.patch('integrations.github_pack.context.resolve_cwd', return_value='/repo')
    mocker.patch('integrations.github_pack.context.current_branch', return_value='main')
    p = Plugin()
    p.initialize()
    p._run = run
    return p


# ---------------------------------------------------------------------------
# token resolution
# ---------------------------------------------------------------------------

def test_token_comes_from_gh_login_when_env_is_empty(plugin):
    assert plugin._token() == GH_TOKEN
    assert plugin._api_reason() is None


def test_env_token_wins_over_gh(plugin, monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'ghp_env')

    assert plugin._token() == 'ghp_env'


def test_widgets_are_available_with_only_a_gh_login(plugin):
    specs = {s.id: s for s in plugin.get_action_specs()}

    assert specs['gh_widget_ci'].unavailable_reason is None
    assert specs['gh_widget_prs'].unavailable_reason is None


def test_no_gh_and_no_env_means_no_token(mocker):
    mocker.patch('integrations.github_pack.sr.find_binary', return_value=None)
    p = Plugin()
    p.initialize()

    assert p._token() is None
    assert 'gh auth login' in p._api_reason()


def test_gh_token_is_cached(plugin):
    plugin._token()
    plugin._token()

    token_calls = [c for c in plugin._run.call_args_list if c.args[0][:3] == ['gh', 'auth', 'token']]
    assert len(token_calls) == 1


def test_gh_token_is_redacted_from_text(plugin):
    plugin._token()

    assert GH_TOKEN not in secrets.redact(f'request failed for Bearer {GH_TOKEN}')


# ---------------------------------------------------------------------------
# CI widget
# ---------------------------------------------------------------------------

def _runs(status, conclusion=None):
    return {'workflow_runs': [{
        'status': status, 'conclusion': conclusion,
        'html_url': 'https://github.com/me/app/actions/runs/7',
    }]}


@pytest.mark.parametrize('status, conclusion, badge, tone', [
    ('completed', 'success', '✓', 'success'),
    ('completed', 'failure', '✕', 'critical'),
    ('completed', 'timed_out', '✕', 'critical'),
    ('in_progress', None, '…', 'running'),
    ('completed', 'cancelled', '–', 'normal'),
])
def test_ci_widget_maps_run_state_to_badge_and_tone(plugin, mocker, status, conclusion, badge, tone):
    mocker.patch.object(plugin, '_api', return_value=_runs(status, conclusion))

    result = plugin.execute_action('gh_widget_ci', {})

    assert result['success'] is True
    assert result['data']['badge'] == badge
    assert result['data']['status'] == tone
    assert result['data']['sublabel'] == 'main'
    assert result['data']['url'] == 'https://github.com/me/app/actions/runs/7'
    assert result['data']['repo'] == 'me/app'


def test_ci_widget_without_runs_links_to_the_actions_page(plugin, mocker):
    mocker.patch.object(plugin, '_api', return_value={'workflow_runs': []})

    result = plugin.execute_action('gh_widget_ci', {})

    assert result['data']['badge'] == '–'
    assert result['data']['url'] == 'https://github.com/me/app/actions'


def test_ci_widget_reports_a_missing_token_clearly(mocker):
    mocker.patch('integrations.github_pack.sr.find_binary', return_value=None)
    mocker.patch('integrations.github_pack.sr.run', return_value=_result('https://github.com/me/app.git'))
    mocker.patch('integrations.github_pack.context.resolve_cwd', return_value='/repo')
    mocker.patch('integrations.github_pack.context.current_branch', return_value='main')
    p = Plugin()
    p.initialize()

    result = p.execute_action('gh_widget_ci', {})

    assert result['success'] is False
    assert result['message'] == 'GitHub token missing'
    assert result['data']['badge'] == '!'


def test_ci_widget_never_leaks_the_token_in_errors(plugin, mocker):
    plugin._token()
    mocker.patch.object(plugin, '_api',
                        side_effect=RuntimeError(f'401 for header Bearer {GH_TOKEN}'))

    result = plugin.execute_action('gh_widget_ci', {})

    assert result['success'] is False
    assert GH_TOKEN not in str(result)


# ---------------------------------------------------------------------------
# PR widget
# ---------------------------------------------------------------------------

def test_pr_widget_counts_open_prs_and_links_to_them(plugin, mocker):
    mocker.patch.object(plugin, '_api', return_value=[{}, {}, {}])

    result = plugin.execute_action('gh_widget_prs', {})

    assert result['data']['badge'] == '3'
    assert result['data']['status'] == 'warning'
    assert result['data']['url'] == 'https://github.com/me/app/pulls'


def test_pr_widget_zero_is_calm(plugin, mocker):
    mocker.patch.object(plugin, '_api', return_value=[])

    result = plugin.execute_action('gh_widget_prs', {})

    assert result['data']['badge'] == '0'
    assert result['data']['status'] == 'normal'


def test_review_requested_filters_by_the_logged_in_user(plugin, mocker):
    def fake_api(path, params=None):
        if path == '/user':
            return {'login': 'daniel'}
        return [
            {'requested_reviewers': [{'login': 'daniel'}]},
            {'requested_reviewers': [{'login': 'someone-else'}]},
            {'requested_reviewers': []},
            {},
        ]

    mocker.patch.object(plugin, '_api', side_effect=fake_api)

    result = plugin.execute_action('gh_widget_prs', {'only_mine': True})

    assert result['data']['badge'] == '1'
    assert result['data']['sublabel'] == 'awaiting your review'
    assert result['data']['url'].endswith('/pulls/review-requested')


def test_api_uses_the_bearer_token(plugin, mocker):
    import requests
    get = mocker.patch.object(requests, 'get')
    get.return_value.json.return_value = []
    get.return_value.raise_for_status.return_value = None

    plugin._api('/repos/me/app/pulls')

    assert get.call_args.kwargs['headers']['Authorization'] == f'Bearer {GH_TOKEN}'


def test_github_api_constant_unchanged():
    assert github_pack.GITHUB_API == 'https://api.github.com'
