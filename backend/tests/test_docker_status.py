"""DL-145 Phase 3: Docker / Compose status."""
import json

import pytest

from services import docker_status
from utils import subprocess_runner as sr

WEB = {'Name': 'proj-web-1', 'Service': 'web', 'State': 'running', 'Status': 'Up 2 minutes'}
DB = {'Name': 'proj-db-1', 'Service': 'db', 'State': 'running', 'Status': 'Up 2 minutes'}
JOB = {'Name': 'proj-job-1', 'Service': 'job', 'State': 'exited', 'Status': 'Exited (0)'}


def array(*rows):
    return json.dumps(list(rows))


def ndjson(*rows):
    return '\n'.join(json.dumps(r) for r in rows)


def result(stdout='', ok=True, stderr=''):
    return sr.CommandResult(ok=ok, exit_code=0 if ok else 1, stdout=stdout,
                            stderr=stderr, argv=[])


class FakeDocker:
    def __init__(self, mocker, ps='[]', daemon=True, ps_ok=True):
        self.calls = []
        self.ps = ps
        self.daemon = daemon
        self.ps_ok = ps_ok
        mocker.patch.object(sr, 'run', side_effect=self.run)

    def run(self, argv, cwd=None, timeout=0, **_):
        self.calls.append(list(argv))
        if argv[1] == 'info':
            return result('29.0.0' if self.daemon else '', ok=self.daemon)
        if 'ps' in argv:
            return result(self.ps, ok=self.ps_ok)
        return result('line one\nline two')


@pytest.fixture
def compose_repo(tmp_path):
    (tmp_path / 'compose.yaml').write_text('services: {}')
    return str(tmp_path)


@pytest.fixture
def plain_repo(tmp_path):
    return str(tmp_path)


def test_parse_array_and_ndjson_shapes():
    assert docker_status.parse_ps_json(array(WEB, DB)) == [WEB, DB]
    assert docker_status.parse_ps_json(ndjson(WEB, DB)) == [WEB, DB]
    assert docker_status.parse_ps_json(json.dumps(WEB)) == [WEB]
    assert docker_status.parse_ps_json('') == []
    assert docker_status.parse_ps_json('garbage\n' + json.dumps(WEB)) == [WEB]


def test_daemon_down_face(mocker, compose_repo):
    FakeDocker(mocker, daemon=False)
    out = docker_status.status(compose_repo)
    assert out['success'] is True
    assert out['data']['badge'] == '–'
    assert out['data']['sublabel'] == 'Docker not running'
    assert out['data']['status'] == 'normal'
    assert out['message'] == "Docker isn't running - start Docker Desktop"


def test_not_installed(mocker, compose_repo):
    mocker.patch.object(sr, 'run', side_effect=sr.BinaryNotFoundError('docker'))
    out = docker_status.status(compose_repo)
    assert out['success'] is True and out['data']['sublabel'] == 'Docker not installed'


def test_compose_mode_all_up(mocker, compose_repo):
    fake = FakeDocker(mocker, ps=ndjson(WEB, DB))
    out = docker_status.status(compose_repo)
    assert out['data']['badge'] == '2/2' and out['data']['status'] == 'normal'
    assert ['docker', 'compose', 'ps', '--all', '--format', 'json'] in fake.calls


def test_partial_up_is_warning(mocker, compose_repo):
    FakeDocker(mocker, ps=array(WEB, JOB))
    out = docker_status.status(compose_repo)
    assert out['data']['badge'] == '1/2' and out['data']['status'] == 'warning'


def test_compose_menu_items(mocker, compose_repo):
    FakeDocker(mocker, ps=array(WEB, JOB))
    menu = docker_status.status(compose_repo)['data']['menu']
    ids = [i['id'] for i in menu]
    assert ids[:2] == ['up', 'stop']
    assert {'restart:web', 'logs:web', 'restart:job', 'logs:job'} <= set(ids)
    assert next(i for i in menu if i['id'] == 'stop')['confirm']


def test_stack_all_stopped_has_no_stop_item(mocker, compose_repo):
    FakeDocker(mocker, ps=array(JOB))
    ids = [i['id'] for i in docker_status.status(compose_repo)['data']['menu']]
    assert 'stop' not in ids and 'up' in ids


def test_plain_mode_lists_running_containers(mocker, plain_repo):
    fake = FakeDocker(mocker, ps=ndjson({'Names': 'redis', 'State': 'running'}))
    out = docker_status.status(plain_repo)
    assert out['data']['badge'] == '1/1'
    assert ['docker', 'ps', '--format', 'json'] in fake.calls
    assert [i['id'] for i in out['data']['menu']] == ['logs:redis']


def test_plain_mode_empty(mocker, plain_repo):
    FakeDocker(mocker, ps='')
    out = docker_status.status(plain_repo)
    assert out['message'] == 'No containers running' and out['data']['badge'] == '0'


def test_ps_failure_is_friendly(mocker, compose_repo):
    FakeDocker(mocker, ps_ok=False)
    assert docker_status.status(compose_repo)['data']['sublabel'] == 'Docker error'


def test_logs_returns_redacted_panel_text(mocker, compose_repo):
    fake = FakeDocker(mocker, ps=array(WEB))
    mocker.patch.object(docker_status.secrets, 'redact', side_effect=lambda t: t.upper())
    out = docker_status.run_op(compose_repo, 'logs:web')
    assert out['data']['panel_text'] == 'LINE ONE\nLINE TWO'
    assert ['docker', 'compose', 'logs', '--tail', '80', '--no-color', 'web'] in fake.calls


def test_plain_logs_use_container_name(mocker, plain_repo):
    fake = FakeDocker(mocker, ps=ndjson({'Names': 'redis', 'State': 'running'}))
    docker_status.run_op(plain_repo, 'logs:redis')
    assert ['docker', 'logs', '--tail', '80', 'redis'] in fake.calls


def test_unknown_service_rejected_before_any_command(mocker, compose_repo):
    fake = FakeDocker(mocker, ps=array(WEB))
    for op in ('logs:--help', 'restart:nope', 'logs:web; rm -rf'):
        assert docker_status.run_op(compose_repo, op)['success'] is False
    assert not any(c[:2] == ['docker', 'compose'] and c[2] in ('logs', 'restart')
                   for c in fake.calls)


def test_up_stop_restart_argv(mocker, compose_repo):
    fake = FakeDocker(mocker, ps=array(WEB))
    assert docker_status.run_op(compose_repo, 'up')['success'] is True
    assert docker_status.run_op(compose_repo, 'stop')['success'] is True
    assert docker_status.run_op(compose_repo, 'restart:web')['success'] is True
    assert ['docker', 'compose', 'up', '-d'] in fake.calls
    assert ['docker', 'compose', 'stop'] in fake.calls
    assert ['docker', 'compose', 'restart', 'web'] in fake.calls


def test_up_without_compose_file_refused(mocker, plain_repo):
    fake = FakeDocker(mocker)
    assert docker_status.run_op(plain_repo, 'up')['success'] is False
    assert fake.calls == []


def test_never_builds_destructive_argv(mocker, compose_repo):
    fake = FakeDocker(mocker, ps=array(WEB, JOB))
    docker_status.status(compose_repo)
    for op in ('up', 'stop', 'restart:web', 'logs:web', 'down', 'rm', 'prune',
               'up:web', 'down:web'):
        docker_status.run_op(compose_repo, op)
    flat = {arg for call in fake.calls for arg in call}
    assert not flat & {'down', 'rm', 'prune', '-v', '--volumes', 'kill',
                       '--force', '-f'}


def test_failed_command_message_is_redacted(mocker, compose_repo):
    mocker.patch.object(sr, 'run', side_effect=[
        result(array(WEB)), result('boom token', ok=False)])
    mocker.patch.object(docker_status.secrets, 'redact', return_value='[hidden]')
    assert docker_status.run_op(compose_repo, 'restart:web')['message'] == '[hidden]'
