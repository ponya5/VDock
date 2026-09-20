"""Session log inspection, client-event ingestion, and export (DL-029).

Log files live in ``Config.DATA_DIR`` (vdock.log, frontend.log, the
vdock-*-launcher.log files) plus ``backend/backend_run.log``. All files are
bounded: app loggers rotate via RotatingFileHandler and the launcher
truncates its logs when they exceed a cap, so this folder cannot grow
without limit.
"""
import io
import logging
import re
import zipfile
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

from auth import require_auth
from config import Config
from utils import setup_logger

logs_bp = Blueprint('logs', __name__)

LOG_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.\-]*\.log$')
MAX_TAIL_LINES = 2000
MAX_CLIENT_EVENTS = 100
MAX_CLIENT_MESSAGE = 2000

_client_logger = None


def _client_logger_get() -> logging.Logger:
    """Dedicated logger for events reported by the frontend."""
    global _client_logger
    if _client_logger is None:
        _client_logger = setup_logger(
            'vdock.frontend',
            log_file=Config.DATA_DIR / 'frontend.log'
        )
        _client_logger.propagate = False
    return _client_logger


def _log_dirs():
    return [Config.DATA_DIR, Config.BASE_DIR]


def _log_files():
    """All managed *.log files, newest first, deduped by name."""
    seen = {}
    for directory in _log_dirs():
        if not directory.exists():
            continue
        for path in directory.glob('*.log'):
            seen.setdefault(path.name, path)
    return sorted(seen.values(), key=lambda p: p.stat().st_mtime, reverse=True)


def _resolve_log(name: str):
    """Map a bare filename to a managed log path, or None."""
    if not LOG_NAME_RE.match(name):
        return None
    for directory in _log_dirs():
        candidate = directory / name
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


@logs_bp.route('/api/logs', methods=['GET'])
@require_auth
def list_logs():
    """List managed log files with size and last-modified time."""
    files = []
    total = 0
    for path in _log_files():
        try:
            stat = path.stat()
        except OSError:
            continue
        files.append({
            'name': path.name,
            'size': stat.st_size,
            'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(timespec='seconds'),
        })
        total += stat.st_size
    return jsonify({'success': True, 'logs': files, 'total_bytes': total})


@logs_bp.route('/api/logs/<name>', methods=['GET'])
@require_auth
def tail_log(name):
    """Return the last ``tail`` lines of a log file (default 300)."""
    path = _resolve_log(name)
    if path is None:
        return jsonify({'success': False, 'message': 'Log not found'}), 404

    try:
        tail = int(request.args.get('tail', 300))
    except (TypeError, ValueError):
        tail = 300
    tail = max(1, min(tail, MAX_TAIL_LINES))

    try:
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError as error:
        return jsonify({'success': False, 'message': str(error)}), 500

    return jsonify({
        'success': True,
        'name': path.name,
        'size': path.stat().st_size,
        'total_lines': len(lines),
        'lines': lines[-tail:],
    })


@logs_bp.route('/api/logs/export', methods=['GET'])
@require_auth
def export_logs():
    """Bundle every managed log into a zip download."""
    buffer = io.BytesIO()
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in _log_files():
            try:
                archive.write(path, arcname=path.name)
            except OSError:
                continue
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'vdock-logs-{stamp}.zip',
    )


@logs_bp.route('/api/logs/client', methods=['POST'])
@require_auth
def client_events():
    """Append frontend error/event entries to ``frontend.log``.

    Payload: ``{events: [{ts, level, source, message}]}`` — capped per
    request and per message so the UI can't flood the log.
    """
    data = request.get_json(silent=True) or {}
    events = data.get('events')
    if not isinstance(events, list) or not events:
        return jsonify({'success': False, 'message': 'events must be a non-empty list'}), 400

    logger = _client_logger_get()
    level_map = {
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
    }
    written = 0
    for event in events[:MAX_CLIENT_EVENTS]:
        if not isinstance(event, dict):
            continue
        source = str(event.get('source') or 'client')[:60]
        message = str(event.get('message') or '')[:MAX_CLIENT_MESSAGE]
        if not message:
            continue
        level = level_map.get(str(event.get('level', 'info')).lower(), logging.INFO)
        logger.log(level, '[%s] %s', source, message)
        written += 1

    return jsonify({'success': True, 'written': written})


@logs_bp.route('/api/logs', methods=['DELETE'])
@require_auth
def clear_logs():
    """Truncate managed logs: close file handlers first so writers reopen
    at position 0 instead of leaving sparse null-byte gaps."""
    managed = {p.resolve() for p in _log_files()}

    # Release backend logger file handles so truncation is clean.
    for logger_name in list(logging.root.manager.loggerDict) + ['']:
        logger_obj = logging.getLogger(logger_name) if logger_name else logging.root
        for handler in getattr(logger_obj, 'handlers', []):
            base = getattr(handler, 'baseFilename', None)
            if base and Path(base).resolve() in managed:
                try:
                    handler.close()
                except Exception:
                    pass

    cleared = 0
    for path in managed:
        try:
            path.write_text('', encoding='utf-8')
            cleared += 1
        except OSError:
            pass

    return jsonify({'success': True, 'cleared': cleared})
