"""DL-145 Phase 3: git context service."""
import pytest

from services import git_context
from utils import subprocess_runner as sr

CLEAN = """# branch.oid e9b38cd055757ce06c70a83ec86adbce6cd166ea
# branch.head main
# branch.upstream origin/main
# branch.ab +0 -0
"""
AHEAD_BEHIND = """# branch.oid e9b38cd055757ce06c70a83ec86adbce6cd166ea
# branch.head feature/x
# branch.upstream origin/feature/x
# branch.ab +2 -1
1 .M N... 100644 100644 100644 aaa bbb src/a.py
? new.txt
"""
NO_UPSTREAM = """# branch.oid e9b38cd055757ce06c70a83ec86adbce6cd166ea
# branch.head topic
1 M. N... 100644 100644 100644 aaa bbb a.py
"""
DETACHED = """# branch.oid 0123456789abcdef0123456789abcdef01234567
# branch.head (detached)
"""
CONFLICT = """# branch.oid e9b38cd055757ce06c70a83ec86adbce6cd166ea
# branch.head main
# branch.upstream origin/main
# branch.ab +0 -0
u UU N... 100644 100644 100644 100644 a b c conflicted.py
2 R. N... 100644 100644 100644 a b R100 new.py\told.py
"""


def result(stdout='', ok=True, argv=()):
    return sr.CommandResult(ok=ok, exit_code=0 if ok else 1, stdout=stdout,
                            stderr='' if ok else stdout, argv=list(argv))


def test_parse_clean_on_upstream():
    info = git_context.parse_status_v2(CLEAN)
    assert info == {'branch': 'main', 'upstream': 'origin/main', 'ahead': 0,
                    'behind': 0, 'dirty': 0, 'conflicts': 0, 'detached': False}


def test_parse_ahead_behind_and_untracked_counts_dirty():
    info = git_context.parse_status_v2(AHEAD_BEHIND)
    assert (info['ahead'], info['behind'], info['dirty']) == (2, 1, 2)


def test_parse_no_upstream():
    info = git_context.parse_status_v2(NO_UPSTREAM)
    assert info['upstream'] == '' and info['ahead'] == 0 and info['dirty'] == 1


def test_parse_detached_head():
    info = git_context.parse_status_v2(DETACHED)
    assert info['detached'] is True and info['branch'] == 'detached @0123456'


def test_parse_conflicts_counted():
    info = git_context.parse_status_v2(CONFLICT)
    assert info['conflicts'] == 1 and info['dirty'] == 2


class FakeGit:
    """Routes mocked ``sr.run`` calls by git subcommand and records argv."""

    def __init__(self, mocker, root, status=CLEAN, stash=False, gh=True,
                 in_progress=False, repo=True):
        self.calls = []
        self.root = root
        self.status = status
        self.stash = stash
        self.repo = repo
        if in_progress:
            (root / '.git' / 'MERGE_HEAD').write_text('x')
        mocker.patch.object(sr, 'run', side_effect=self.run)
        mocker.patch.object(sr, 'find_binary',
                            return_value='gh.exe' if gh else None)

    def run(self, argv, cwd=None, timeout=0, **_):
        self.calls.append(list(argv))
        sub = argv[1] if len(argv) > 1 else ''
        if argv[:3] == ['git', 'rev-parse', '--show-toplevel']:
            return result(f'{self.root}\n' if self.repo else '', ok=self.repo)
        if sub == 'status':
            return result(self.status)
        if argv[:3] == ['git', 'rev-parse', '--git-path']:
            return result('.git/MERGE_HEAD\n.git/rebase-merge\n.git/rebase-apply\n')
        if argv[:2] == ['git', 'rev-parse'] and 'refs/stash' in argv:
            return result('abc\n' if self.stash else '', ok=self.stash)
        return result('ok')


@pytest.fixture
def tmp_root(tmp_path):
    """A fake repo root; ``in_progress`` creates a MERGE_HEAD marker."""
    (tmp_path / '.git').mkdir()
    return tmp_path


def make(mocker, tmp_root, **kwargs):
    return FakeGit(mocker, tmp_root, **kwargs)


def test_clean_face(mocker, tmp_root):
    make(mocker, tmp_root)
    data = git_context.status('C:/work/proj')['data']
    assert data['badge'] == '✓' and data['status'] == 'normal'
    assert data['sublabel'] == 'main'


def test_dirty_ahead_is_warning(mocker, tmp_root):
    make(mocker, tmp_root, status=AHEAD_BEHIND)
    data = git_context.status('x')['data']
    assert data['badge'] == '2' and data['status'] == 'warning'
    assert data['sublabel'] == 'feature/x ↑2 ↓1'


def test_behind_only_is_warning(mocker, tmp_root):
    make(mocker, tmp_root, status=CLEAN.replace('+0 -0', '+0 -3'))
    assert git_context.status('x')['data']['status'] == 'warning'


def test_conflicts_and_in_progress_are_critical(mocker, tmp_root):
    make(mocker, tmp_root, status=CONFLICT)
    assert git_context.status('x')['data']['status'] == 'critical'


def test_merge_in_progress_is_critical(mocker, tmp_root):
    make(mocker, tmp_root, in_progress=True)
    data = git_context.status('x')['data']
    assert data['status'] == 'critical' and 'merge/rebase' in data['sublabel']


def ids(out):
    return [item['id'] for item in out['data']['menu']]


def test_menu_omits_stash_when_clean_and_pop_without_stash(mocker, tmp_root):
    make(mocker, tmp_root)
    assert ids(git_context.status('x')) == ['pull', 'push', 'pr']


def test_menu_has_stash_when_dirty_and_pop_when_stash_exists(mocker, tmp_root):
    make(mocker, tmp_root, status=AHEAD_BEHIND, stash=True)
    assert ids(git_context.status('x')) == ['pull', 'push', 'stash', 'pop', 'pr']


def test_menu_omits_pr_without_gh(mocker, tmp_root):
    make(mocker, tmp_root, gh=False)
    assert 'pr' not in ids(git_context.status('x'))


def test_push_and_stash_carry_confirm_text(mocker, tmp_root):
    make(mocker, tmp_root, status=AHEAD_BEHIND)
    items = {i['id']: i for i in git_context.status('x')['data']['menu']}
    assert items['push']['confirm'] == 'Push feature/x to origin/feature/x?'
    assert items['stash']['confirm'] == 'Stash 2 changed files?'
    assert 'confirm' not in items['pull']


def test_push_without_upstream_confirm_names_origin(mocker, tmp_root):
    make(mocker, tmp_root, status=NO_UPSTREAM)
    items = {i['id']: i for i in git_context.status('x')['data']['menu']}
    assert items['push']['confirm'] == 'Push topic to origin?'


def test_not_a_repo_empty_state(mocker, tmp_root):
    make(mocker, tmp_root, repo=False)
    out = git_context.status('x')
    assert out['success'] is True and out['data']['badge'] == '–'
    assert out['message'] == ('Not a git repository - focus a project in '
                              'your editor')
    assert out['data']['menu'] == []


def test_git_missing_is_not_a_repo(mocker):
    mocker.patch.object(sr, 'run', side_effect=sr.BinaryNotFoundError('git'))
    assert git_context.status('x')['data']['badge'] == '–'


def test_push_uses_plain_push_with_upstream(mocker, tmp_root):
    fake = make(mocker, tmp_root, status=AHEAD_BEHIND)
    assert git_context.run_op('x', 'push')['success'] is True
    assert ['git', 'push'] in fake.calls


def test_push_without_upstream_sets_upstream(mocker, tmp_root):
    fake = make(mocker, tmp_root, status=NO_UPSTREAM)
    git_context.run_op('x', 'push')
    assert ['git', 'push', '-u', 'origin', 'HEAD'] in fake.calls


def test_pull_is_fast_forward_only_and_stash_includes_untracked(mocker, tmp_root):
    fake = make(mocker, tmp_root)
    git_context.run_op('x', 'pull')
    git_context.run_op('x', 'stash')
    assert ['git', 'pull', '--ff-only'] in fake.calls
    stash = next(c for c in fake.calls if c[:3] == ['git', 'stash', 'push'])
    assert stash[3] == '-u' and stash[4] == '-m' and stash[5].startswith('VDock ')


def test_pop(mocker, tmp_root):
    fake = make(mocker, tmp_root)
    git_context.run_op('x', 'pop')
    assert ['git', 'stash', 'pop'] in fake.calls


def test_pr_returns_existing_url(mocker, tmp_root):
    fake = make(mocker, tmp_root)
    orig = sr.run.side_effect

    def run(argv, **kw):
        if argv[0] == 'gh':
            fake.calls.append(list(argv))
            return result('https://github.com/o/r/pull/7\n')
        return orig(argv, **kw)
    sr.run.side_effect = run
    out = git_context.run_op('x', 'pr')
    assert out['data']['url'] == 'https://github.com/o/r/pull/7'


def test_pr_without_existing_creates_via_web(mocker, tmp_root):
    fake = make(mocker, tmp_root)
    orig = sr.run.side_effect

    def run(argv, **kw):
        if argv[0] == 'gh':
            fake.calls.append(list(argv))
            return result('no pull requests found', ok=argv[2] != 'view')
        return orig(argv, **kw)
    sr.run.side_effect = run
    assert git_context.run_op('x', 'pr')['success'] is True
    assert ['gh', 'pr', 'create', '--web'] in fake.calls


def test_unknown_op_refused_without_running(mocker, tmp_root):
    fake = make(mocker, tmp_root)
    out = git_context.run_op('x', 'reset')
    assert out['success'] is False and fake.calls == []


def test_failed_op_message_is_redacted(mocker, tmp_root):
    make(mocker, tmp_root)
    mocker.patch.object(git_context.secrets, 'redact', return_value='[hidden]')
    orig = sr.run.side_effect

    def run(argv, **kw):
        if argv[:2] == ['git', 'pull']:
            return result('token ghp_secret', ok=False)
        return orig(argv, **kw)
    sr.run.side_effect = run
    assert git_context.run_op('x', 'pull')['message'] == '[hidden]'


def test_no_destructive_flags_in_any_argv(mocker, tmp_root):
    fake = make(mocker, tmp_root, status=AHEAD_BEHIND, stash=True)
    git_context.status('x')
    for op in ('pull', 'push', 'stash', 'pop', 'pr'):
        git_context.run_op('x', op)
    flat = {arg for call in fake.calls for arg in call}
    assert not flat & {'--force', '-f', '--force-with-lease', 'reset', 'clean',
                       '--hard', 'rebase', 'checkout'}
