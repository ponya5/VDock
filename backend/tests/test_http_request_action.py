"""Tests for the generic HTTP request action.

Feature: ai-dev-integration-packs, Property 3.1: any HTTP endpoint becomes a
button without writing code.

This is the highest-leverage action in the catalog -- it turns Discord and Slack
webhooks, n8n, Zapier, Home Assistant and any REST API into configuration
rather than a bespoke integration. VDock had nothing like it.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actions.http_request_action import HTTPRequestAction  # noqa: E402


class FakeResponse:
    def __init__(self, status_code=200, text='', payload=None, reason='OK'):
        self.status_code = status_code
        self.text = text
        self._payload = payload
        self.reason = reason

        class _Elapsed:
            @staticmethod
            def total_seconds():
                return 0.05

        self.elapsed = _Elapsed()

    @property
    def ok(self):
        return 200 <= self.status_code < 400

    def json(self):
        if self._payload is None:
            raise ValueError('not json')
        return self._payload


@pytest.fixture
def request_mock(mocker):
    import requests
    return mocker.patch.object(requests, 'request',
                               return_value=FakeResponse(text='pong'))


# --- validation --------------------------------------------------------------

@pytest.mark.parametrize('url', [
    'https://example.com/hook',
    'http://192.168.1.10:8123/api/webhook/x',   # Home Assistant on the LAN
    'http://localhost:5678/webhook/test',        # n8n locally
])
def test_http_and_https_urls_are_accepted(url):
    assert HTTPRequestAction({'url': url}).validate() is True


@pytest.mark.parametrize('url', [
    'file:///C:/Windows/System32/config/SAM',
    'ftp://example.com/x',
    'gopher://example.com',
    'javascript:alert(1)',
])
def test_non_http_schemes_are_refused(url):
    """A URL is user-supplied; only http(s) may be dialled."""
    assert HTTPRequestAction({'url': url}).validate() is False


def test_a_url_without_a_host_is_refused():
    assert HTTPRequestAction({'url': 'https://'}).validate() is False


def test_an_empty_url_is_refused():
    assert HTTPRequestAction({'url': ''}).validate() is False


def test_an_unknown_method_is_refused():
    assert HTTPRequestAction(
        {'url': 'https://example.com', 'method': 'TRACE'}
    ).validate() is False


def test_invalid_config_reports_instead_of_raising():
    result = HTTPRequestAction({'url': 'file:///etc/passwd'}).execute()

    assert result.success is False
    assert 'Invalid configuration' in result.message


# --- request building --------------------------------------------------------

def test_method_and_url_are_passed_through(request_mock):
    HTTPRequestAction({'url': 'https://example.com/hook',
                       'method': 'post'}).execute()

    kwargs = request_mock.call_args.kwargs
    assert kwargs['method'] == 'POST'
    assert kwargs['url'] == 'https://example.com/hook'


def test_headers_are_parsed_from_a_text_block(request_mock):
    HTTPRequestAction({
        'url': 'https://example.com',
        'headers': 'Authorization: Bearer abc123\nX-Custom:  1 ',
    }).execute()

    assert request_mock.call_args.kwargs['headers'] == {
        'Authorization': 'Bearer abc123', 'X-Custom': '1',
    }


def test_headers_may_also_be_a_dict(request_mock):
    HTTPRequestAction({'url': 'https://example.com',
                       'headers': {'X-A': '1'}}).execute()

    assert request_mock.call_args.kwargs['headers'] == {'X-A': '1'}


def test_a_json_body_is_sent_as_json(request_mock):
    HTTPRequestAction({
        'url': 'https://discord.com/api/webhooks/x',
        'body': '{"content": "Deploy finished"}',
    }).execute()

    kwargs = request_mock.call_args.kwargs
    assert kwargs['json'] == {'content': 'Deploy finished'}
    assert kwargs['data'] is None


def test_body_that_is_not_valid_json_is_sent_as_text(request_mock):
    """Better to send it than to silently drop it."""
    HTTPRequestAction({'url': 'https://example.com',
                       'body': 'just some text'}).execute()

    kwargs = request_mock.call_args.kwargs
    assert kwargs['json'] is None
    assert kwargs['data'] == 'just some text'


def test_raw_text_mode_never_parses_json(request_mock):
    HTTPRequestAction({'url': 'https://example.com', 'body': '{"a": 1}',
                       'content_type': 'text'}).execute()

    assert request_mock.call_args.kwargs['data'] == '{"a": 1}'


def test_timeout_is_capped(request_mock):
    from actions.http_request_action import MAX_TIMEOUT

    HTTPRequestAction({'url': 'https://example.com',
                       'timeout': 99999}).execute()

    assert request_mock.call_args.kwargs['timeout'] == MAX_TIMEOUT


# --- responses ---------------------------------------------------------------

def test_success_reports_the_status(request_mock):
    result = HTTPRequestAction({'url': 'https://example.com'}).execute()

    assert result.success is True
    assert '200' in result.message
    assert result.data['status_code'] == 200
    assert result.data['body'] == 'pong'


def test_error_status_is_a_failure_with_details(mocker):
    import requests
    mocker.patch.object(requests, 'request', return_value=FakeResponse(
        status_code=404, text='no such hook', reason='Not Found'))

    result = HTTPRequestAction({'url': 'https://example.com'}).execute()

    assert result.success is False
    assert '404' in result.message
    assert 'no such hook' in result.details


def test_a_value_can_be_pulled_out_of_a_json_response(mocker):
    import requests
    mocker.patch.object(requests, 'request', return_value=FakeResponse(
        payload={'data': [{'name': 'alpha'}]}, text='{}'))

    result = HTTPRequestAction({'url': 'https://example.com',
                                'result_path': 'data.0.name'}).execute()

    assert result.data['value'] == 'alpha'
    assert 'alpha' in result.message


def test_a_bad_result_path_yields_none_not_an_error(mocker):
    import requests
    mocker.patch.object(requests, 'request',
                        return_value=FakeResponse(payload={'a': 1}, text='{}'))

    result = HTTPRequestAction({'url': 'https://example.com',
                                'result_path': 'nope.deeper'}).execute()

    assert result.success is True
    assert result.data['value'] is None


def test_body_is_truncated(mocker):
    import requests
    from actions.http_request_action import MAX_BODY_CHARS
    mocker.patch.object(requests, 'request',
                        return_value=FakeResponse(text='x' * 50_000))

    result = HTTPRequestAction({'url': 'https://example.com'}).execute()

    assert len(result.data['body']) == MAX_BODY_CHARS


# --- failure modes -----------------------------------------------------------

def test_timeout_is_reported_not_raised(mocker):
    import requests
    mocker.patch.object(requests, 'request', side_effect=requests.Timeout())

    result = HTTPRequestAction({'url': 'https://example.com',
                                'timeout': 5}).execute()

    assert result.success is False
    assert 'timed out' in result.message.lower()


def test_connection_error_is_reported_not_raised(mocker):
    import requests
    mocker.patch.object(requests, 'request',
                        side_effect=requests.ConnectionError())

    result = HTTPRequestAction({'url': 'https://example.com'}).execute()

    assert result.success is False
    assert 'connect' in result.message.lower()


def test_failure_message_does_not_echo_headers(mocker):
    """Headers can carry a token; they must not reach a notification."""
    import requests
    mocker.patch.object(requests, 'request',
                        side_effect=requests.RequestException('boom'))

    result = HTTPRequestAction({
        'url': 'https://example.com',
        'headers': 'Authorization: Bearer super-secret-token',
    }).execute()

    assert result.success is False
    assert 'super-secret-token' not in result.message
    assert 'super-secret-token' not in (result.details or '')


# --- dispatch ----------------------------------------------------------------

def test_it_is_reachable_through_the_executor(request_mock):
    from actions.action_executor import ActionExecutor

    result = ActionExecutor().execute_action({
        'type': 'http_request',
        'config': {'url': 'https://example.com', 'method': 'GET'},
    })

    assert result.success is True
