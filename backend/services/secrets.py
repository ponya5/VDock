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
)

GITHUB_TOKEN = SecretSpec(
    env_var='GITHUB_TOKEN',
    label='GitHub token',
    help_url='https://github.com/settings/tokens',
    missing_reason=(
        'GITHUB_TOKEN is not set in backend/.env. The gh CLI actions use your '
        'existing gh login; only the live PR/CI widgets need a token.'
    ),
)

ALL_SECRETS = (ANTHROPIC_API_KEY, GITHUB_TOKEN)


def get(spec: SecretSpec) -> Optional[str]:
    """Return the secret's value, or None when unset or blank."""
    value = os.environ.get(spec.env_var, '').strip()
    return value or None


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
    return text
