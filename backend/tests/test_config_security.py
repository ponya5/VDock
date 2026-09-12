"""Configuration safety checks for a publicly published repo.

Feature: ai-dev-integration-packs, Property 5: no credential ships in the
source, and no configuration is quietly insecure.

The repo is public. A working API key committed to it is a leaked key no matter
how it is labelled, and a fallback password is only ever a trap -- harmless
until someone turns authentication on, then a wide-open door.
"""
import ast
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent


# --- no credentials in source ------------------------------------------------

def test_no_default_weather_api_key():
    """A real key lived here as a 'demo' default; it was also dead config."""
    source = (BACKEND / 'config.py').read_text(encoding='utf-8')
    match = re.search(
        r"WEATHERAPI_KEY\s*=\s*os\.environ\.get\(\s*'WEATHERAPI_KEY'\s*,\s*'([^']*)'",
        source,
    )
    assert match, 'WEATHERAPI_KEY should read from the environment'
    assert match.group(1) == '', 'no API key may be hardcoded as a default'


def test_no_default_auth_password():
    source = (BACKEND / 'config.py').read_text(encoding='utf-8')
    match = re.search(
        r"AUTH_PASSWORD\s*=\s*os\.environ\.get\(\s*'AUTH_PASSWORD'\s*,\s*'([^']*)'",
        source,
    )
    assert match, 'AUTH_PASSWORD should read from the environment'
    assert match.group(1) == '', 'no fallback password may be baked in'


@pytest.mark.parametrize('name', [
    'config.py', 'services/secrets.py', 'integrations/claude_pack.py',
    'integrations/github_pack.py',
])
def test_no_long_credential_literals(name):
    """Catches a key pasted in during debugging and forgotten."""
    source = (BACKEND / name).read_text(encoding='utf-8')

    suspicious = re.findall(
        r"['\"](sk-[A-Za-z0-9_\-]{16,}|gh[pousr]_[A-Za-z0-9]{16,}|[a-f0-9]{32})['\"]",
        source,
    )
    assert not suspicious, f'{name} contains credential-shaped literals: {suspicious}'


def test_env_file_is_not_tracked():
    """A committed .env is the single most common way a key leaks."""
    assert not (BACKEND / '.env').exists() or _is_git_ignored('backend/.env'), (
        'backend/.env exists and is not gitignored'
    )


def _is_git_ignored(relative: str) -> bool:
    import subprocess
    result = subprocess.run(
        ['git', 'check-ignore', relative],
        cwd=str(REPO), capture_output=True, text=True,
    )
    return result.returncode == 0


def test_env_example_ships_no_real_values():
    """The example must be a template, not someone's working config."""
    example = (BACKEND / '.env.example').read_text(encoding='utf-8')

    for line in example.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        value = value.strip()
        if key.strip() in ('ANTHROPIC_API_KEY', 'GITHUB_TOKEN', 'WEATHERAPI_KEY',
                           'SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET'):
            assert value == '' or 'your' in value.lower() or 'replace' in value.lower(), (
                f'{key.strip()} in .env.example looks like a real value: {value!r}'
            )


# --- configuration that must not be quietly insecure -------------------------

def test_auth_on_without_a_password_refuses_to_start():
    previous = (Config.REQUIRE_AUTH, Config.AUTH_PASSWORD)
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = ''
    try:
        with pytest.raises(RuntimeError, match='AUTH_PASSWORD'):
            Config.validate()
    finally:
        Config.REQUIRE_AUTH, Config.AUTH_PASSWORD = previous


def test_auth_on_with_a_password_is_fine():
    previous = (Config.REQUIRE_AUTH, Config.AUTH_PASSWORD)
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = 'a-real-password'
    try:
        Config.validate()
    finally:
        Config.REQUIRE_AUTH, Config.AUTH_PASSWORD = previous


def test_auth_off_needs_no_password():
    """The default: a local deck with no login screen."""
    previous = (Config.REQUIRE_AUTH, Config.AUTH_PASSWORD)
    Config.REQUIRE_AUTH = False
    Config.AUTH_PASSWORD = ''
    try:
        Config.validate()
    finally:
        Config.REQUIRE_AUTH, Config.AUTH_PASSWORD = previous


def test_command_execution_is_off_by_default():
    """Arbitrary shell commands should be opt-in, not the default."""
    assert Config.ALLOW_COMMAND_EXECUTION is False


def test_server_binds_to_localhost_by_default():
    assert Config.HOST in ('127.0.0.1', 'localhost')
    assert Config.ALLOW_LAN is False


# --- the Python floor the installers promise ---------------------------------

def test_backend_source_parses_on_the_minimum_python():
    """setup.bat/setup.sh accept Python 3.9, so the source must run on it.

    PEP 604 unions (`X | None`) in a signature are evaluated when the function
    is defined, so a single one crashes the import on 3.9 -- after setup has
    already told the user they are fine. Caught exactly that in
    routes/templates.py.
    """
    offenders = []
    skip = {'venv', '__pycache__', 'node_modules', 'tests'}

    for path in BACKEND.rglob('*.py'):
        if any(part in skip for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except SyntaxError as e:  # pragma: no cover - would fail everywhere
            offenders.append(f'{path.name}: unparseable ({e})')
            continue

        for node in ast.walk(tree):
            # `X | Y` used as an annotation (PEP 604, 3.10+)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                annotations = [a.annotation for a in node.args.args if a.annotation]
                if node.returns:
                    annotations.append(node.returns)
                for ann in annotations:
                    if _uses_pep604(ann):
                        offenders.append(
                            f'{path.relative_to(BACKEND)}:{node.lineno} '
                            f'({node.name}) uses `X | Y` in a signature'
                        )

    assert not offenders, (
        'These need Python 3.10+, but the installers accept 3.9:\n  '
        + '\n  '.join(offenders)
    )


def _uses_pep604(node) -> bool:
    """True when an annotation contains a `X | Y` union."""
    return any(
        isinstance(child, ast.BinOp) and isinstance(child.op, ast.BitOr)
        for child in ast.walk(node)
    )
