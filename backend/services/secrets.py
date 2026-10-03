"""Credential access for integration packs.

Secrets live in ``backend/.env`` (loaded by ``app.py`` via python-dotenv), the
same place ``WEATHERAPI_KEY`` already comes from. Nothing here is ever
serialised to the frontend: the action catalog exposes only a boolean saying
whether an integration is configured, and the reason string a pack shows when
it is not.

Keeping this in one module means there is a single place to audit for
"does a credential leak into a response", and a single place to change if
VDock later grows an encrypted store or an OS keyring backend.
"""
import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger('vdock')


@dataclass(frozen=True)
class SecretSpec:
    """A credential an integration can use."""
    env_var: str
    label: str
    help_url: str = ''
    #: Shown in the picker when the secret is missing.
    missing_reason: str = ''
    #: One line for the Settings "Accounts & keys" page.
    unlocks: str = ''
    #: Set when the integration works without this key (a free built-in
    #: provider covers it) - Settings then shows "Built-in", not "Not set".
    builtin_label: str = ''

    def reason(self) -> str:
        if self.missing_reason:
            return self.missing_reason
        return f'{self.label} is not set ({self.env_var} in backend/.env)'


ANTHROPIC_API_KEY = SecretSpec(
    env_var='ANTHROPIC_API_KEY',
    label='Anthropic API key',
    help_url='https://console.anthropic.com/settings/keys',
    missing_reason=(
        'ANTHROPIC_API_KEY is not set in backend/.env. The Claude Code CLI '
        'actions work without it; only the direct API action needs a key.'
    ),
    unlocks='The direct Claude API prompt action',
)

GITHUB_TOKEN = SecretSpec(
    env_var='GITHUB_TOKEN',
    label='GitHub token',
    help_url='https://github.com/settings/tokens',
    missing_reason=(
        'GITHUB_TOKEN is not set in backend/.env. The gh CLI actions use your '
        'existing gh login; only the live PR/CI widgets need a token.'
    ),
    unlocks='Live PR / CI / notification buttons',
)

WEATHERAPI_KEY = SecretSpec(
    env_var='WEATHERAPI_KEY',
    label='WeatherAPI key',
    help_url='https://www.weatherapi.com/signup.aspx',
    missing_reason=(
        'WEATHERAPI_KEY is not set in backend/.env. Only the backend Weather '
        'action needs it; the screensaver weather uses Open-Meteo (no key).'
    ),
    unlocks=(
        'The backend Weather action. Works out of the box with the free '
        'Open-Meteo service; add your own key to use WeatherAPI.com instead.'
    ),
    builtin_label='Built-in (Open-Meteo)',
)

ALL_SECRETS = (ANTHROPIC_API_KEY, GITHUB_TOKEN, WEATHERAPI_KEY)


#: Credentials discovered at runtime (e.g. the token behind ``gh auth login``).
#: They are not in the environment, but they must still be scrubbed from any
#: message or log line that could echo them.
_runtime_secrets: set = set()


def register_runtime_secret(value: Optional[str]) -> None:
    """Make ``redact`` scrub ``value`` too (ignored when blank)."""
    if value and value.strip():
        _runtime_secrets.add(value.strip())


#: Template text people leave behind when they copy an example file (the old
#: .env.example shipped ``demo-key-replace-with-your-own``). Not a credential.
_PLACEHOLDER_HINTS = ('replace-with', 'replace_with', 'your-', 'your_', 'demo-key', 'changeme')


def _looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(hint in lowered for hint in _PLACEHOLDER_HINTS)


def get(spec: SecretSpec) -> Optional[str]:
    """Return the secret's value, or None when unset or blank."""
    value = os.environ.get(spec.env_var, '').strip()
    if not value or _looks_like_placeholder(value):
        return None
    return value


def is_configured(spec: SecretSpec) -> bool:
    """True when the secret has a non-empty value."""
    return get(spec) is not None


def status() -> Dict[str, bool]:
    """Which secrets are configured. Safe to send to the frontend.

    Values are booleans only -- never the secrets themselves.
    """
    return {spec.env_var: is_configured(spec) for spec in ALL_SECRETS}


def redact(text: str) -> str:
    """Remove any configured secret from ``text``.

    CLI tools echo their arguments in error messages, and those messages end up
    in notifications and the log file. This is the backstop that keeps a token
    out of both.
    """
    if not text:
        return text
    for spec in ALL_SECRETS:
        value = get(spec)
        if value and value in text:
            text = text.replace(value, f'[{spec.env_var} redacted]')
    for value in _runtime_secrets:
        if value in text:
            text = text.replace(value, '[token redacted]')
    return text
