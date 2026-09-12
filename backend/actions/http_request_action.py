"""Generic HTTP request action.

The highest-leverage single action in VDock: with it, anything that speaks HTTP
becomes a button without writing code. Discord and Slack webhooks, n8n and
Zapier triggers, Home Assistant, Node-RED, Philips Hue, a self-hosted API, a
CI trigger -- all configuration rather than a new integration.

Every other "integration" VDock lacks is some flavour of this, which is why it
lands before any of them.

Safety notes
------------
The URL is user-supplied, so this refuses non-HTTP schemes (``file://``,
``gopher://``) outright. It does *not* try to block private address ranges:
pointing a button at ``192.168.1.10`` or ``localhost`` is the whole point for
Home Assistant and Hue users. This runs on the user's own machine, under their
own control, at their own explicit configuration -- the same trust level as the
existing "Run Command" action, and rather lower risk.

Headers may carry tokens, so failures report the status and a truncated body,
never the request headers.
"""
import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from .base_action import BaseAction, ActionResult

logger = logging.getLogger('vdock')

ALLOWED_METHODS = ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD')
ALLOWED_SCHEMES = ('http', 'https')
DEFAULT_TIMEOUT = 15
MAX_TIMEOUT = 120
#: Responses are bound for a notification; there is no point holding more.
MAX_BODY_CHARS = 4000


class HTTPRequestAction(BaseAction):
    """Send an HTTP request and report the response."""

    def validate(self) -> bool:
        url = (self.config.get('url') or '').strip()
        if not url:
            return False

        parsed = urlparse(url)
        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            return False
        if not parsed.netloc:
            return False

        method = (self.config.get('method') or 'GET').upper()
        return method in ALLOWED_METHODS

    def _parse_headers(self) -> Dict[str, str]:
        """Headers may be a dict or a 'Key: value' block from a textarea."""
        raw = self.config.get('headers')
        if not raw:
            return {}
        if isinstance(raw, dict):
            return {str(k): str(v) for k, v in raw.items()}

        headers: Dict[str, str] = {}
        for line in str(raw).splitlines():
            line = line.strip()
            if not line or ':' not in line:
                continue
            key, _, value = line.partition(':')
            headers[key.strip()] = value.strip()
        return headers

    def _parse_body(self) -> tuple:
        """Return (json_body, text_body); at most one is not None."""
        body = self.config.get('body')
        if body is None or body == '':
            return None, None

        if isinstance(body, (dict, list)):
            return body, None

        text = str(body)
        content_type = self.config.get('content_type', 'json')
        if content_type == 'json':
            try:
                return json.loads(text), None
            except (ValueError, TypeError):
                # Not valid JSON: send it as-is rather than silently dropping.
                return None, text
        return None, text

    def execute(self) -> ActionResult:
        if not self.validate():
            return ActionResult(
                False,
                'Invalid configuration: an http(s) URL and a valid method are '
                'required'
            )

        try:
            import requests
        except ImportError:  # pragma: no cover - requests is a hard dependency
            return ActionResult(False, 'The requests library is not installed')

        url = self.config['url'].strip()
        method = (self.config.get('method') or 'GET').upper()
        timeout = min(
            int(self.config.get('timeout') or DEFAULT_TIMEOUT), MAX_TIMEOUT
        )
        json_body, text_body = self._parse_body()

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._parse_headers(),
                json=json_body,
                data=text_body,
                timeout=timeout,
                allow_redirects=True,
            )
        except requests.Timeout:
            return ActionResult(False, f'Request timed out after {timeout}s')
        except requests.ConnectionError:
            return ActionResult(
                False, f'Could not connect to {urlparse(url).netloc}'
            )
        except requests.RequestException as e:
            # Deliberately not echoing headers: they may carry a token.
            return ActionResult(False, f'Request failed: {type(e).__name__}')

        body = (response.text or '')[:MAX_BODY_CHARS]
        data: Dict[str, Any] = {
            'status_code': response.status_code,
            'ok': response.ok,
            'body': body,
            'elapsed_ms': int(response.elapsed.total_seconds() * 1000),
        }

        # Surface a JSON field on the button when asked, so an endpoint can
        # drive a badge.
        pointer = (self.config.get('result_path') or '').strip()
        if pointer:
            data['value'] = _extract(response, pointer)

        if response.ok:
            message = f'{method} {response.status_code}'
            if pointer and data.get('value') is not None:
                message = f'{message} — {data["value"]}'
            return ActionResult(True, message, data)

        return ActionResult(
            False,
            f'{method} {response.status_code} {response.reason}',
            data,
            details=body[:500] or None,
        )

    def get_description(self) -> str:
        method = (self.config.get('method') or 'GET').upper()
        return f"HTTP {method} {self.config.get('url', '')}"


def _extract(response: Any, pointer: str) -> Optional[Any]:
    """Pull a dotted path out of a JSON response, e.g. 'data.0.name'."""
    try:
        current = response.json()
    except ValueError:
        return None

    for part in pointer.split('.'):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
        if current is None:
            return None
    return current
