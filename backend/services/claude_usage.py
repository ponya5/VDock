"""Claude Code token usage, cost and context fill from local transcripts (DL-145 Phase 2).

Claude Code writes every session to ``<claude home>/projects/<cwd-slug>/<session id>.jsonl``
(subagents under ``<session id>/subagents/``). The files are large and only ever
appended to, so each one is read incrementally: a per-file aggregate remembers
how far it has parsed and only new bytes are read on the next call.

What the records give us (verified against Claude Code 2.1.x on disk):

* ``assistant`` records carry ``message.{id, model, usage}``. The same
  ``message.id`` repeats once per content block with identical usage, so each
  id is counted once.
* a ``cost-state`` record (``totalCostUSD``) is written when a session closes -
  exact, but absent for a live session.

Cost is therefore exact only for a finished session; everything else is an
estimate from the list-price table below.
"""
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import date, datetime, time as dtime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger('vdock')

CONTEXT_WINDOW_DEFAULT = 200_000
CONTEXT_WINDOW_LARGE = 1_000_000
CONTEXT_WARNING_PCT = 80
CONTEXT_CRITICAL_PCT = 95

#: USD per million tokens, from https://platform.claude.com/docs/en/about-claude/pricing
#: (checked 2026-10-03). First matching needle wins, so specific ids come first.
#: ``write_5m`` / ``write_1h`` are the two cache-write tiers.
PRICES_PER_MTOK: Tuple[Tuple[str, Dict[str, float]], ...] = (
    ('opus-5-5', {'input': 4.0, 'output': 20.0, 'write_5m': 5.0, 'write_1h': 8.0, 'read': 0.20}),
    ('opus-4-1', {'input': 15.0, 'output': 75.0, 'write_5m': 18.75, 'write_1h': 30.0, 'read': 1.50}),
    ('opus-4-2025', {'input': 15.0, 'output': 75.0, 'write_5m': 18.75, 'write_1h': 30.0, 'read': 1.50}),
    ('opus', {'input': 5.0, 'output': 25.0, 'write_5m': 6.25, 'write_1h': 10.0, 'read': 0.50}),
    ('sonnet-5', {'input': 2.0, 'output': 10.0, 'write_5m': 2.5, 'write_1h': 4.0, 'read': 0.20}),
    ('sonnet', {'input': 3.0, 'output': 15.0, 'write_5m': 3.75, 'write_1h': 6.0, 'read': 0.30}),
    ('haiku', {'input': 1.0, 'output': 5.0, 'write_5m': 1.25, 'write_1h': 2.0, 'read': 0.10}),
)


def claude_home() -> Path:
    """Claude Code's data directory (same place the hook installer writes)."""
    return Path.home() / '.claude'


@dataclass
class Tokens:
    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0
    #: the part of ``cache_write`` billed at the 1-hour rate
    cache_write_1h: int = 0

    @property
    def total(self) -> int:
        return self.input + self.output + self.cache_read + self.cache_write

    def __add__(self, other: 'Tokens') -> 'Tokens':
        return Tokens(
            self.input + other.input, self.output + other.output,
            self.cache_read + other.cache_read,
            self.cache_write + other.cache_write,
            self.cache_write_1h + other.cache_write_1h)

    def to_dict(self) -> Dict[str, int]:
        return {'input': self.input, 'output': self.output,
                'cache_read': self.cache_read, 'cache_write': self.cache_write,
                'total': self.total}


@dataclass
class FileAgg:
    tokens_by_model: Dict[str, Tokens] = field(default_factory=dict)
    today_by_model: Dict[str, Tokens] = field(default_factory=dict)
    last_context_tokens: int = 0
    last_model: str = ''
    cost_state_usd: Optional[float] = None
    cost_state_unknown: bool = False
    #: True while the latest ``cost-state`` is still the file's last usage
    #: record. A resumed session keeps writing after an old cost-state, which
    #: then understates the session.
    cost_state_current: bool = False
    offset: int = 0
    size: int = 0
    mtime: float = 0.0
    seen_ids: Set[str] = field(default_factory=set)
    day: str = ''


_cache: Dict[str, FileAgg] = {}
_lock = threading.Lock()


def reset_cache() -> None:
    with _lock:
        _cache.clear()


def _local_date(timestamp: Any) -> Optional[date]:
    if not isinstance(timestamp, str):
        return None
    try:
        return datetime.fromisoformat(timestamp.replace('Z', '+00:00')).astimezone().date()
    except ValueError:
        return None


def _int(value: Any) -> int:
    return value if isinstance(value, int) and value > 0 else 0


def _usage_tokens(usage: Dict[str, Any]) -> Tokens:
    creation = usage.get('cache_creation')
    one_hour = _int(creation.get('ephemeral_1h_input_tokens')) \
        if isinstance(creation, dict) else 0
    return Tokens(
        input=_int(usage.get('input_tokens')),
        output=_int(usage.get('output_tokens')),
        cache_read=_int(usage.get('cache_read_input_tokens')),
        cache_write=_int(usage.get('cache_creation_input_tokens')),
        cache_write_1h=one_hour)


def _apply(agg: FileAgg, record: Dict[str, Any], today: date) -> None:
    kind = record.get('type')
    if kind == 'cost-state':
        total = record.get('totalCostUSD')
        if isinstance(total, (int, float)):
            agg.cost_state_usd = float(total)
            agg.cost_state_unknown = bool(record.get('hasUnknownModelCost'))
            agg.cost_state_current = True
        return
    if kind != 'assistant':
        return
    message = record.get('message')
    if not isinstance(message, dict):
        return
    usage = message.get('usage')
    model = message.get('model')
    message_id = message.get('id')
    if not isinstance(usage, dict) or not isinstance(model, str) \
            or not model or model.startswith('<'):
        return  # '<synthetic>' placeholders carry no real usage
    if isinstance(message_id, str):
        if message_id in agg.seen_ids:
            return
        agg.seen_ids.add(message_id)

    tokens = _usage_tokens(usage)
    agg.cost_state_current = False
    agg.tokens_by_model[model] = agg.tokens_by_model.get(model, Tokens()) + tokens
    if _local_date(record.get('timestamp')) == today:
        agg.today_by_model[model] = agg.today_by_model.get(model, Tokens()) + tokens
    if not record.get('isSidechain'):
        agg.last_context_tokens = tokens.input + tokens.cache_read + tokens.cache_write
        agg.last_model = model


def _parse_line(line: bytes) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line:
        return None
    try:
        record = json.loads(line)
    except ValueError:
        return None
    return record if isinstance(record, dict) else None


def scan_file(path: Path, today: date) -> FileAgg:
    """Aggregate ``path``, reading only what was appended since the last call."""
    key = str(path)
    stat = path.stat()
    with _lock:
        agg = _cache.get(key)
        if agg is None or stat.st_size < agg.offset or agg.day != today.isoformat():
            agg = FileAgg(day=today.isoformat())
            _cache[key] = agg
        if stat.st_size == agg.offset:
            agg.size, agg.mtime = stat.st_size, stat.st_mtime
            return agg

        with open(path, 'rb') as handle:
            handle.seek(agg.offset)
            chunk = handle.read()
        end = chunk.rfind(b'\n')
        lines: List[bytes] = chunk[:end].split(b'\n') if end >= 0 else []
        consumed = end + 1
        tail = chunk[consumed:]
        if tail.strip() and _parse_line(tail) is not None:
            lines.append(tail)  # complete record that simply lacks a final newline
            consumed = len(chunk)
        for line in lines:
            record = _parse_line(line)
            if record is not None:
                _apply(agg, record, today)
        agg.offset += consumed
        agg.size, agg.mtime = stat.st_size, stat.st_mtime
        return agg


def _projects_dir() -> Path:
    return claude_home() / 'projects'


def session_files(session_id: str) -> List[Path]:
    """The session transcript (main file first) plus its subagent transcripts."""
    if not session_id or any(sep in session_id for sep in ('/', '\\', '..')):
        return []
    root = _projects_dir()
    if not root.is_dir():
        return []
    files = list(root.glob(f'*/{session_id}.jsonl'))
    files.extend(sorted(root.glob(f'*/{session_id}/subagents/*.jsonl')))
    return files


def today_files(today: date) -> List[Path]:
    """Transcripts modified since local midnight on ``today``."""
    root = _projects_dir()
    if not root.is_dir():
        return []
    midnight = datetime.combine(today, dtime.min).timestamp()
    found: List[Path] = []
    for path in root.rglob('*.jsonl'):
        try:
            if path.stat().st_mtime >= midnight:
                found.append(path)
        except OSError:
            continue
    return found


# --- cost and context --------------------------------------------------------

def _prices(model: str) -> Optional[Dict[str, float]]:
    lowered = model.lower()
    for needle, prices in PRICES_PER_MTOK:
        if needle in lowered:
            return prices
    return None


def estimate_cost(model: str, tokens: Tokens) -> Optional[float]:
    """API-equivalent USD for ``tokens``; ``None`` for an unpriced model."""
    prices = _prices(model)
    if prices is None:
        return None
    five_minute = tokens.cache_write - tokens.cache_write_1h
    return (tokens.input * prices['input']
            + tokens.output * prices['output']
            + tokens.cache_read * prices['read']
            + five_minute * prices['write_5m']
            + tokens.cache_write_1h * prices['write_1h']) / 1_000_000


def context_window(model: str, context_tokens: int) -> int:
    if '1m' in model.lower() or context_tokens > CONTEXT_WINDOW_DEFAULT:
        return CONTEXT_WINDOW_LARGE
    return CONTEXT_WINDOW_DEFAULT


def _sum_cost(by_model: Dict[str, Tokens]) -> float:
    """Estimated USD; models without a price add tokens but no cost."""
    return sum(estimate_cost(model, tokens) or 0.0
               for model, tokens in by_model.items())


def _merge(target: Dict[str, Tokens], source: Dict[str, Tokens]) -> None:
    for model, tokens in source.items():
        target[model] = target.get(model, Tokens()) + tokens


def _total(by_model: Dict[str, Tokens]) -> Tokens:
    result = Tokens()
    for tokens in by_model.values():
        result = result + tokens
    return result


def limit_status(cost_usd: float, limit_usd: float) -> str:
    """Button tone for today's spend against the user's daily budget."""
    if limit_usd <= 0:
        return 'normal'
    ratio = cost_usd / limit_usd
    return 'critical' if ratio >= 1 else 'warning' if ratio >= 0.8 else 'normal'


def session_usage(session_id: str, today: date) -> Optional[Dict[str, Any]]:
    """Totals for one session, or ``None`` when no transcript exists."""
    files = session_files(session_id)
    if not files:
        return None
    main = scan_file(files[0], today) if files[0].name == f'{session_id}.jsonl' else None
    by_model: Dict[str, Tokens] = {}
    for path in files:
        _merge(by_model, scan_file(path, today).tokens_by_model)

    exact = (main is not None and main.cost_state_usd is not None
             and main.cost_state_current and not main.cost_state_unknown)
    if exact:
        cost, estimate = main.cost_state_usd, False
    else:
        cost, estimate = _sum_cost(by_model), True

    model = main.last_model if main else ''
    context_tokens = main.last_context_tokens if main else 0
    window = context_window(model, context_tokens)
    pct = min(100, round(context_tokens * 100 / window)) if context_tokens else 0
    status = ('critical' if pct >= CONTEXT_CRITICAL_PCT
              else 'warning' if pct >= CONTEXT_WARNING_PCT else 'normal')
    return {
        'session_id': session_id, 'model': model,
        'tokens': _total(by_model).to_dict(),
        'cost_usd': cost, 'estimate': estimate,
        'context_tokens': context_tokens, 'context_pct': pct, 'status': status,
    }


def today_usage(today: date) -> Dict[str, Any]:
    """Everything spent since local midnight (always an estimate)."""
    by_model: Dict[str, Tokens] = {}
    sessions: Set[str] = set()
    for path in today_files(today):
        try:
            agg = scan_file(path, today)
        except OSError as error:
            logger.debug('Skipping unreadable transcript %s: %s', path.name, error)
            continue
        if agg.today_by_model:
            _merge(by_model, agg.today_by_model)
            sessions.add(path.parent.parent.name if path.parent.name == 'subagents'
                         else path.stem)
    return {'tokens': _total(by_model).to_dict(), 'cost_usd': _sum_cost(by_model),
            'estimate': True, 'sessions': len(sessions)}
