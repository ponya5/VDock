"""Tests for background execution of long-running actions.

Feature: ai-dev-integration-packs, Property 1.3: an action that outlives the
HTTP request still reports its result.

The frontend's axios client times out after 30 seconds. claude_prompt routinely
takes longer and is allowed up to ten minutes, so running it synchronously made
the UI report a timeout while the work carried on invisibly, with no way to
learn whether it had succeeded. Long actions are now submitted to a background
pool: the request returns 202 with a job id immediately, and the outcome arrives
over Socket.IO with polling as a fallback.
"""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actions.base_action import ActionResult  # noqa: E402
from services.job_runner import (  # noqa: E402
    STATUS_FAILED,
    STATUS_RUNNING,
    STATUS_SUCCEEDED,
    JobRunner,
)


@pytest.fixture
def runner():
    r = JobRunner(max_workers=2)
    yield r
    r.shutdown()


def wait_for(job, runner, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = runner.get_job(job.id)
        if current and current.finished_at is not None:
            return current
        time.sleep(0.02)
    raise AssertionError(f'job {job.id} did not finish within {timeout}s')


# --- submission returns immediately ------------------------------------------

def test_submit_returns_before_the_work_finishes(runner):
    started = time.time()

    job = runner.submit('slow', lambda: (time.sleep(0.4),
                                         ActionResult(True, 'done'))[1])

    assert time.time() - started < 0.2, 'submit must not block'
    assert job.status == STATUS_RUNNING
    wait_for(job, runner)


def test_successful_job_records_its_result(runner):
    job = runner.submit('ok', lambda: ActionResult(True, 'all good',
                                                   {'x': 1}))

    finished = wait_for(job, runner)

    assert finished.status == STATUS_SUCCEEDED
    assert finished.result['success'] is True
    assert finished.result['message'] == 'all good'
    assert finished.result['data'] == {'x': 1}


def test_failed_action_is_marked_failed_not_succeeded(runner):
    job = runner.submit('bad', lambda: ActionResult(False, 'it broke'))

    finished = wait_for(job, runner)

    assert finished.status == STATUS_FAILED
    assert finished.result['message'] == 'it broke'


def test_raised_exception_is_captured_not_lost(runner):
    def boom():
        raise RuntimeError('kaboom')

    finished = wait_for(runner.submit('boom', boom), runner)

    assert finished.status == STATUS_FAILED
    assert 'kaboom' in finished.result['message']


def test_duration_is_recorded(runner):
    job = runner.submit('timed', lambda: (time.sleep(0.15),
                                          ActionResult(True, 'ok'))[1])

    finished = wait_for(job, runner)

    assert finished.to_dict()['duration'] >= 0.1


# --- broadcasting ------------------------------------------------------------

def test_running_and_final_events_are_broadcast(runner):
    events = []
    runner.set_emitter(lambda event, payload: events.append(payload))

    job = runner.submit('ok', lambda: ActionResult(True, 'done'))
    wait_for(job, runner)

    statuses = [e['status'] for e in events]
    assert statuses == [STATUS_RUNNING, STATUS_SUCCEEDED]
    assert all(e['job_id'] == job.id for e in events)


def test_button_id_is_attributed_so_the_face_can_show_progress(runner):
    events = []
    runner.set_emitter(lambda event, payload: events.append(payload))

    job = runner.submit('ok', lambda: ActionResult(True, 'done'),
                        button_id='btn_42')
    wait_for(job, runner)

    assert all(e['button_id'] == 'btn_42' for e in events)


def test_a_broken_emitter_does_not_break_the_job(runner):
    def explode(event, payload):
        raise RuntimeError('socket is down')

    runner.set_emitter(explode)

    finished = wait_for(runner.submit('ok', lambda: ActionResult(True, 'done')),
                        runner)

    assert finished.status == STATUS_SUCCEEDED


def test_works_without_an_emitter_at_all(runner):
    finished = wait_for(runner.submit('ok', lambda: ActionResult(True, 'done')),
                        runner)

    assert finished.status == STATUS_SUCCEEDED


# --- bookkeeping -------------------------------------------------------------

def test_unknown_job_id_returns_none(runner):
    assert runner.get_job('nope') is None


def test_active_count_tracks_running_jobs(runner):
    job = runner.submit('slow', lambda: (time.sleep(0.3),
                                         ActionResult(True, 'ok'))[1])

    assert runner.active_count() == 1
    wait_for(job, runner)
    assert runner.active_count() == 0


def test_job_table_does_not_grow_without_bound(runner):
    from services.job_runner import MAX_TRACKED_JOBS

    for _ in range(MAX_TRACKED_JOBS + 20):
        wait_for(runner.submit('x', lambda: ActionResult(True, 'ok')), runner)

    assert len(runner._jobs) <= MAX_TRACKED_JOBS + 1


# --- the HTTP contract -------------------------------------------------------

def test_long_action_returns_202_with_a_job_id(mocker):
    import app as app_module

    mocker.patch.object(app_module.action_executor, 'is_long_running',
                        return_value=True)
    mocker.patch.object(app_module.action_executor, 'execute_action',
                        return_value=ActionResult(True, 'finished'))
    client = app_module.app.test_client()

    response = client.post('/api/actions/execute',
                           json={'action': {'type': 'claude_prompt',
                                            'config': {}}})

    assert response.status_code == 202
    body = response.get_json()
    assert body['pending'] is True
    assert body['job_id']


def test_short_action_still_runs_synchronously(mocker):
    import app as app_module

    mocker.patch.object(app_module.action_executor, 'is_long_running',
                        return_value=False)
    mocker.patch.object(app_module.action_executor, 'execute_action',
                        return_value=ActionResult(True, 'immediate'))
    client = app_module.app.test_client()

    response = client.post('/api/actions/execute',
                           json={'action': {'type': 'url', 'config': {}}})

    assert response.status_code == 200
    assert response.get_json()['message'] == 'immediate'
    assert 'job_id' not in response.get_json()


def test_wait_flag_forces_synchronous_execution(mocker):
    """An explicit caller can still block, e.g. a script or a test."""
    import app as app_module

    mocker.patch.object(app_module.action_executor, 'is_long_running',
                        return_value=True)
    mocker.patch.object(app_module.action_executor, 'execute_action',
                        return_value=ActionResult(True, 'blocking'))
    client = app_module.app.test_client()

    response = client.post('/api/actions/execute',
                           json={'action': {'type': 'claude_prompt',
                                            'config': {}}, 'wait': True})

    assert response.status_code == 200
    assert response.get_json()['message'] == 'blocking'


def test_job_can_be_polled_over_http(mocker):
    import app as app_module

    mocker.patch.object(app_module.action_executor, 'is_long_running',
                        return_value=True)
    mocker.patch.object(app_module.action_executor, 'execute_action',
                        return_value=ActionResult(True, 'polled'))
    client = app_module.app.test_client()

    job_id = client.post(
        '/api/actions/execute',
        json={'action': {'type': 'claude_prompt', 'config': {}}},
    ).get_json()['job_id']

    for _ in range(100):
        body = client.get(f'/api/actions/jobs/{job_id}').get_json()
        if body['status'] != STATUS_RUNNING:
            break
        time.sleep(0.02)

    assert body['status'] == STATUS_SUCCEEDED
    assert body['result']['message'] == 'polled'


def test_polling_an_unknown_job_is_a_404():
    import app as app_module

    response = app_module.app.test_client().get('/api/actions/jobs/nope')

    assert response.status_code == 404


def test_only_pack_actions_are_long_running():
    """Built-in actions are fast; marking them async would add latency."""
    import app as app_module

    executor = app_module.action_executor
    for action_type in ('url', 'hotkey', 'cross_platform', 'macro'):
        assert executor.is_long_running(action_type) is False, action_type
