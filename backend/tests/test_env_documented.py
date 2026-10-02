"""Env contract (DL-146 Phase 1): backend/.env.example documents exactly the
variables the backend reads, and ships no secret values."""
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
EXAMPLE = BACKEND / '.env.example'
FRONTEND_EXAMPLE = REPO / 'frontend' / '.env.example'

OS_VARS = {'APPDATA', 'LOCALAPPDATA', 'ProgramFiles', 'ProgramFiles(x86)', 'XDG_DATA_HOME', 'PATH'}
SKIP_DIRS = {'venv', 'tests', 'test-scripts', 'data', '__pycache__', 'build', 'dist'}

READ_RE = re.compile(r"""(?:environ\.get|getenv)\(\s*['"]([A-Z][A-Za-z0-9_()]+)['"]""")
SPEC_RE = re.compile(r"""env_var\s*=\s*['"]([A-Z][A-Z0-9_]+)['"]""")


def _py_sources():
    for path in BACKEND.rglob('*.py'):
        if SKIP_DIRS & set(path.relative_to(BACKEND).parts):
            continue
        yield path


def _vars_read():
    names = set()
    for path in _py_sources():
        text = path.read_text(encoding='utf-8', errors='ignore')
        names.update(READ_RE.findall(text))
        names.update(SPEC_RE.findall(text))
    return names - OS_VARS


def _documented():
    names = set()
    for line in EXAMPLE.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^#?\s*([A-Z][A-Z0-9_]+)=', line)
        if m:
            names.add(m.group(1))
    return names


def _example_values():
    values = {}
    for line in EXAMPLE.read_text(encoding='utf-8').splitlines():
        if line.lstrip().startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        values[key.strip()] = value.strip()
    return values


def test_every_backend_env_var_is_documented():
    missing = _vars_read() - _documented()
    assert not missing, f'read by the backend but missing from backend/.env.example: {sorted(missing)}'


def test_every_documented_var_is_read():
    dead = _documented() - _vars_read()
    assert not dead, f'documented in backend/.env.example but never read: {sorted(dead)}'


def test_example_ships_no_secret_values():
    values = _example_values()
    for key in ('SECRET_KEY', 'AUTH_PASSWORD', 'GITHUB_TOKEN', 'ANTHROPIC_API_KEY', 'WEATHERAPI_KEY'):
        assert values.get(key, '') == '', f'{key} must be empty in the example'


def test_example_rate_limit_matches_code_default():
    values = _example_values()
    assert values.get('RATELIMIT_ENABLED', 'False').lower() == 'false'


def test_example_debug_and_lan_are_safe_defaults():
    values = _example_values()
    assert values.get('DEBUG', 'False').lower() == 'false'
    assert values.get('ALLOW_LAN', 'False').lower() == 'false'
    assert values.get('REQUIRE_COMMAND_CONFIRMATION', 'True').lower() == 'true'
    assert values.get('ALLOW_COMMAND_EXECUTION', 'False').lower() == 'false'


def test_frontend_example_documents_vite_vars():
    assert FRONTEND_EXAMPLE.exists(), 'frontend/.env.example is missing'
    documented = set()
    for line in FRONTEND_EXAMPLE.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^#?\s*(VITE_[A-Z_]+)=', line)
        if m:
            documented.add(m.group(1))
    used = set()
    for path in (REPO / 'frontend' / 'src').rglob('*'):
        if path.suffix in {'.ts', '.vue', '.js'} and 'tests' not in path.parts:
            used.update(re.findall(r'import\.meta\.env\.(VITE_[A-Z_]+)', path.read_text(encoding='utf-8', errors='ignore')))
    for required in ('VITE_PORT', 'VITE_BACKEND_PORT', 'VITE_WS_URL'):
        assert required in documented
    assert not used - documented, f'VITE vars used but undocumented: {sorted(used - documented)}'
