"""GitHub integration pack: gh CLI actions plus live PR/CI widgets.

Two halves, deliberately:

* **gh CLI** for anything that *does* something -- open a PR, check out a
  branch, rerun a workflow. These reuse the user's existing ``gh auth login``,
  so VDock stores no credential of its own.
* **REST API** for the live widgets that put a count or a CI colour on a button
  face. Polling needs a token (GITHUB_TOKEN), but only the widgets need it; the
  CLI actions work without one.

Everything resolves "which repo" through ``integrations.context``, which infers
the project from the focused editor window, so one button works across repos.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from actions.catalog import ActionSpec, ConfigField, RUNS_BACKEND
from plugins.base_plugin import BasePlugin, PluginInfo
from services import secrets
from utils import subprocess_runner as sr

from . import context

logger = logging.getLogger('vdock')

GH_BINARY = 'gh'
GITHUB_API = 'https://api.github.com'

_CWD_FIELD = ConfigField(
    'cwd', 'Repository path', 'path',
    placeholder="Leave blank to use the focused editor's project",
    help='Blank means VDock infers the repository from the focused editor.',
)


class Plugin(BasePlugin):
    """GitHub actions."""

    def __init__(self) -> None:
        super().__init__()
        self.gh_path: Optional[str] = None
        self.gh_authenticated = False

    # --- lifecycle -----------------------------------------------------------

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            id='github',
            name='GitHub',
            version='1.0.0',
            author='VDock',
            description='Pull requests, issues, workflow runs and live status.',
            actions=[
                'gh_pr_list', 'gh_pr_create', 'gh_pr_checkout', 'gh_pr_view',
                'gh_pr_checks', 'gh_issue_list', 'gh_issue_create',
                'gh_run_list', 'gh_run_rerun', 'gh_status',
                'gh_widget_prs', 'gh_widget_ci', 'gh_widget_notifications',
            ],
        )

    def initialize(self) -> bool:
        self.gh_path = sr.find_binary(GH_BINARY)
        if not self.gh_path:
            logger.info('gh CLI not on PATH; GitHub CLI actions unavailable')
            return True

        # `gh auth status` exits non-zero when not logged in.
        try:
            result = sr.run([GH_BINARY, 'auth', 'status'], timeout=15)
            self.gh_authenticated = result.ok
        except Exception as e:  # pragma: no cover - environment dependent
            logger.debug('Could not check gh auth status: %s', e)
            self.gh_authenticated = False

        logger.info(
            'gh CLI found at %s (authenticated: %s)',
            self.gh_path, self.gh_authenticated
        )
        return True

    def cleanup(self) -> None:
        pass

    def is_available(self) -> tuple:
        if self.gh_path or secrets.is_configured(secrets.GITHUB_TOKEN):
            return True, ''
        return False, (
            'Neither the gh CLI nor GITHUB_TOKEN was found. Install gh from '
            'https://cli.github.com, or set GITHUB_TOKEN in backend/.env.'
        )

    # --- catalog -------------------------------------------------------------

    def _cli_reason(self) -> Optional[str]:
        if not self.gh_path:
            return ('gh CLI not found on PATH. Install it from '
                    'https://cli.github.com')
        if not self.gh_authenticated:
            return 'gh is installed but not logged in. Run: gh auth login'
        return None

    def _api_reason(self) -> Optional[str]:
        if secrets.is_configured(secrets.GITHUB_TOKEN):
            return None
        return secrets.GITHUB_TOKEN.reason()

    def get_action_specs(self) -> Sequence[ActionSpec]:
        cli = self._cli_reason()
        api = self._api_reason()

        def cli_action(
            action_id: str, label: str, icon: str, description: str,
            keywords: tuple, fields: tuple = (), long_running: bool = False,
            default_config: Optional[Dict[str, Any]] = None,
        ) -> ActionSpec:
            return ActionSpec(
                id=action_id, label=label, category='dev', icon=('fas', icon),
                action_type=action_id, runs_on=RUNS_BACKEND,
                long_running=long_running, description=description,
                keywords=keywords + ('github', 'gh'),
                default_config=default_config or {},
                config_fields=(_CWD_FIELD,) + fields,
                unavailable_reason=cli,
            )

        def widget(
            action_id: str, label: str, icon: str, description: str,
            keywords: tuple, fields: tuple = (),
        ) -> ActionSpec:
            # Widgets are dispatched (they fetch), but their result updates the
            # button face rather than opening anything.
            return ActionSpec(
                id=action_id, label=label, category='dev', icon=('fas', icon),
                action_type=action_id, runs_on=RUNS_BACKEND,
                description=description, keywords=keywords + ('github', 'badge'),
                default_config={'refresh_interval': 120},
                config_fields=(_CWD_FIELD,) + fields + (
                    ConfigField('refresh_interval', 'Refresh (seconds)',
                                'number', default=120),
                ),
                unavailable_reason=api,
            )

        return (
            cli_action(
                'gh_pr_list', 'List Pull Requests', 'code-pull-request',
                'Show open pull requests for this repository.',
                ('pr', 'pulls', 'list'),
                (ConfigField('limit', 'How many', 'number', default=10),),
            ),
            cli_action(
                'gh_pr_create', 'Create Pull Request', 'code-pull-request',
                'Open a pull request for the current branch, filling the title '
                'and body from your commits.',
                ('pr', 'create', 'open'),
                (
                    ConfigField('title', 'Title', 'text',
                                placeholder='Leave blank to use the commit'),
                    ConfigField('draft', 'Create as draft', 'boolean',
                                default=False),
                    ConfigField('web', 'Finish in the browser', 'boolean',
                                default=True,
                                help='Opens the PR form instead of submitting '
                                     'straight away.'),
                ),
                long_running=True,
            ),
            cli_action(
                'gh_pr_checkout', 'Check Out Pull Request', 'code-branch',
                'Check out a pull request branch locally.',
                ('pr', 'checkout', 'branch'),
                (ConfigField('pr', 'PR number', 'text', required=True,
                             placeholder='123'),),
                long_running=True,
            ),
            cli_action(
                'gh_pr_view', 'Open Pull Request', 'up-right-from-square',
                "Open this branch's pull request in the browser.",
                ('pr', 'view', 'browser'),
                (ConfigField('pr', 'PR number', 'text',
                             placeholder='Blank = current branch'),),
            ),
            cli_action(
                'gh_pr_checks', 'PR Checks', 'circle-check',
                'Show CI check results for the current pull request.',
                ('ci', 'checks', 'status', 'tests'),
                long_running=True,
            ),
            cli_action(
                'gh_issue_list', 'List Issues', 'circle-dot',
                'Show open issues for this repository.',
                ('issues', 'list', 'bugs'),
                (ConfigField('limit', 'How many', 'number', default=10),),
            ),
            cli_action(
                'gh_issue_create', 'Create Issue', 'circle-plus',
                'Open a new issue.',
                ('issues', 'create', 'bug'),
                (
                    ConfigField('title', 'Title', 'text', required=True),
                    ConfigField('body', 'Body', 'textarea'),
                    ConfigField('web', 'Finish in the browser', 'boolean',
                                default=True),
                ),
            ),
            cli_action(
                'gh_run_list', 'List Workflow Runs', 'play',
                'Show recent GitHub Actions runs.',
                ('actions', 'ci', 'workflow', 'runs'),
                (ConfigField('limit', 'How many', 'number', default=10),),
            ),
            cli_action(
                'gh_run_rerun', 'Rerun Failed Jobs', 'rotate-right',
                'Rerun the failed jobs of the latest workflow run.',
                ('actions', 'ci', 'retry', 'rerun'),
                long_running=True,
            ),
            cli_action(
                'gh_status', 'GitHub Status', 'bell',
                'Show your assigned issues, review requests and mentions.',
                ('status', 'review', 'mentions', 'notifications'),
                long_running=True,
            ),
            widget(
                'gh_widget_prs', 'Open PR Count', 'code-pull-request',
                'Live count of open pull requests on the button face.',
                ('pr', 'count', 'live'),
                (ConfigField('only_mine', 'Only review requests for me',
                             'boolean', default=False),),
            ),
            widget(
                'gh_widget_ci', 'CI Status', 'heart-pulse',
                "Live CI status for the current branch.",
                ('ci', 'build', 'status', 'live'),
            ),
            widget(
                'gh_widget_notifications', 'Unread Notifications', 'bell',
                'Live count of unread GitHub notifications.',
                ('notifications', 'inbox', 'count', 'live'),
            ),
        )

    def get_action_schema(self, action_id: str) -> Dict[str, Any]:
        for spec in self.get_action_specs():
            if spec.id == action_id:
                return {
                    'type': 'object',
                    'properties': {
                        f.name: {'type': 'string', 'title': f.label}
                        for f in spec.config_fields
                    },
                    'required': [f.name for f in spec.config_fields if f.required],
                }
        return {}

    # --- dispatch ------------------------------------------------------------

    def execute_action(self, action_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        handlers = {
            'gh_pr_list': self._pr_list,
            'gh_pr_create': self._pr_create,
            'gh_pr_checkout': self._pr_checkout,
            'gh_pr_view': self._pr_view,
            'gh_pr_checks': self._pr_checks,
            'gh_issue_list': self._issue_list,
            'gh_issue_create': self._issue_create,
            'gh_run_list': self._run_list,
            'gh_run_rerun': self._run_rerun,
            'gh_status': self._status,
            'gh_widget_prs': self._widget_prs,
            'gh_widget_ci': self._widget_ci,
            'gh_widget_notifications': self._widget_notifications,
        }
        handler = handlers.get(action_id)
        if handler is None:
            return {'success': False, 'message': f'Unknown action: {action_id}'}
        return handler(config)

    # --- gh CLI helpers ------------------------------------------------------

    def _gh(
        self, args: List[str], config: Dict[str, Any], timeout: int = 120
    ) -> Dict[str, Any]:
        """Run a gh subcommand in the resolved repository."""
        if not self.gh_path:
            return {
                'success': False,
                'message': 'gh CLI not found',
                'details': 'Install it from https://cli.github.com',
            }

        cwd = context.resolve_cwd(config.get('cwd'))
        repo_root = context.git_repo_root(cwd)
        if repo_root is None:
            return {
                'success': False,
                'message': 'Not a git repository',
                'details': f'{cwd} is not inside a git repository.',
            }

        try:
            result = sr.run([GH_BINARY, *args], cwd=repo_root, timeout=timeout)
        except sr.BinaryNotFoundError as e:
            return {'success': False, 'message': str(e)}

        text = secrets.redact(result.output)
        if not result.ok:
            return {
                'success': False,
                'message': 'gh command failed' if not result.timed_out
                           else 'gh command timed out',
                'details': text or f'exit code {result.exit_code}',
                'data': {'repo': repo_root},
            }

        return {
            'success': True,
            'message': result.summary() or 'Done',
            'data': {'output': text, 'repo': repo_root},
        }

    # --- gh CLI actions ------------------------------------------------------

    def _pr_list(self, config: Dict[str, Any]) -> Dict[str, Any]:
        limit = str(int(config.get('limit') or 10))
        return self._gh(['pr', 'list', '--limit', limit], config)

    def _pr_create(self, config: Dict[str, Any]) -> Dict[str, Any]:
        args = ['pr', 'create']
        if config.get('web', True):
            # Safer default: the user reviews and submits in the browser rather
            # than VDock opening a PR on a single button press.
            args.append('--web')
        else:
            args.append('--fill')
            title = (config.get('title') or '').strip()
            if title:
                args += ['--title', title]
            if config.get('draft'):
                args.append('--draft')
        return self._gh(args, config)

    def _pr_checkout(self, config: Dict[str, Any]) -> Dict[str, Any]:
        pr = str(config.get('pr') or '').strip()
        if not pr:
            return {'success': False, 'message': 'No PR number configured'}
        return self._gh(['pr', 'checkout', pr], config)

    def _pr_view(self, config: Dict[str, Any]) -> Dict[str, Any]:
        args = ['pr', 'view', '--web']
        pr = str(config.get('pr') or '').strip()
        if pr:
            args.insert(2, pr)
        return self._gh(args, config)

    def _pr_checks(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return self._gh(['pr', 'checks'], config)

    def _issue_list(self, config: Dict[str, Any]) -> Dict[str, Any]:
        limit = str(int(config.get('limit') or 10))
        return self._gh(['issue', 'list', '--limit', limit], config)

    def _issue_create(self, config: Dict[str, Any]) -> Dict[str, Any]:
        title = (config.get('title') or '').strip()
        if not title:
            return {'success': False, 'message': 'No issue title configured'}

        args = ['issue', 'create', '--title', title]
        body = (config.get('body') or '').strip()
        if body:
            args += ['--body', context.expand_placeholders(body)]
        if config.get('web', True):
            args.append('--web')
        return self._gh(args, config)

    def _run_list(self, config: Dict[str, Any]) -> Dict[str, Any]:
        limit = str(int(config.get('limit') or 10))
        return self._gh(['run', 'list', '--limit', limit], config)

    def _run_rerun(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return self._gh(['run', 'rerun', '--failed'], config)

    def _status(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return self._gh(['status'], config)

    # --- REST widgets --------------------------------------------------------

    def _api(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """GET a GitHub REST endpoint with the configured token."""
        import requests

        token = secrets.get(secrets.GITHUB_TOKEN)
        if not token:
            raise PermissionError(secrets.GITHUB_TOKEN.reason())

        response = requests.get(
            f'{GITHUB_API}{path}',
            params=params or {},
            headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def _repo_slug(self, config: Dict[str, Any]) -> Optional[str]:
        """owner/name for the resolved repository, from its git remote."""
        cwd = context.resolve_cwd(config.get('cwd'))
        try:
            result = sr.run(['git', 'remote', 'get-url', 'origin'], cwd=cwd,
                            timeout=10)
        except sr.BinaryNotFoundError:
            return None
        if not result.ok:
            return None

        url = result.stdout.strip()
        if url.endswith('.git'):
            url = url[:-4]
        if url.startswith('git@'):
            _, _, path = url.partition(':')
        else:
            path = '/'.join(url.split('/')[-2:])
        parts = [p for p in path.split('/') if p]
        return '/'.join(parts[-2:]) if len(parts) >= 2 else None

    def _widget_error(self, message: str, details: str = '') -> Dict[str, Any]:
        return {
            'success': False, 'message': message, 'details': details,
            'data': {'badge': '!', 'status': 'error'},
        }

    def _widget_prs(self, config: Dict[str, Any]) -> Dict[str, Any]:
        slug = self._repo_slug(config)
        if not slug:
            return self._widget_error('Could not determine the repository')

        try:
            if config.get('only_mine'):
                data = self._api('/search/issues', {
                    'q': f'repo:{slug} is:pr is:open review-requested:@me',
                })
                count = data.get('total_count', 0)
                label = 'awaiting your review'
            else:
                data = self._api(f'/repos/{slug}/pulls', {'state': 'open',
                                                          'per_page': 100})
                count = len(data)
                label = 'open pull requests'
        except PermissionError as e:
            return self._widget_error('GITHUB_TOKEN is not set', str(e))
        except Exception as e:
            return self._widget_error('GitHub request failed',
                                      secrets.redact(str(e)))

        return {
            'success': True,
            'message': f'{count} {label}',
            'data': {
                'badge': str(count),
                'value': count,
                'status': 'normal' if count == 0 else 'warning',
                'sublabel': label,
                'repo': slug,
            },
        }

    def _widget_ci(self, config: Dict[str, Any]) -> Dict[str, Any]:
        slug = self._repo_slug(config)
        if not slug:
            return self._widget_error('Could not determine the repository')

        branch = context.current_branch(config.get('cwd'))
        if not branch:
            return self._widget_error('Could not determine the branch')

        try:
            data = self._api(f'/repos/{slug}/actions/runs', {
                'branch': branch, 'per_page': 1,
            })
        except PermissionError as e:
            return self._widget_error('GITHUB_TOKEN is not set', str(e))
        except Exception as e:
            return self._widget_error('GitHub request failed',
                                      secrets.redact(str(e)))

        runs = data.get('workflow_runs') or []
        if not runs:
            return {
                'success': True, 'message': f'No runs on {branch}',
                'data': {'badge': '–', 'status': 'normal', 'sublabel': branch},
            }

        run = runs[0]
        status = run.get('status')
        conclusion = run.get('conclusion')

        if status != 'completed':
            state, badge = 'running', '…'
        elif conclusion == 'success':
            state, badge = 'success', '✓'
        elif conclusion in ('cancelled', 'skipped'):
            state, badge = 'normal', '–'
        else:
            state, badge = 'critical', '✕'

        return {
            'success': True,
            'message': f'{branch}: {conclusion or status}',
            'data': {
                'badge': badge, 'status': state, 'sublabel': branch,
                'conclusion': conclusion, 'run_status': status,
                'url': run.get('html_url'), 'repo': slug,
            },
        }

    def _widget_notifications(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = self._api('/notifications', {'per_page': 100})
        except PermissionError as e:
            return self._widget_error('GITHUB_TOKEN is not set', str(e))
        except Exception as e:
            return self._widget_error('GitHub request failed',
                                      secrets.redact(str(e)))

        count = len(data)
        return {
            'success': True,
            'message': f'{count} unread notifications',
            'data': {
                'badge': str(count), 'value': count,
                'status': 'normal' if count == 0 else 'warning',
                'sublabel': 'unread',
            },
        }
