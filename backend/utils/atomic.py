"""Crash-safe file writes.

Electron's ``kill()`` on Windows is TerminateProcess and a touch panel is often
power-cycled, so a plain ``open(path, 'w')`` can leave a truncated profile.
Writing a sibling temp file and ``os.replace``-ing it keeps either the old or
the new content, never half of one.
"""
import os
import time
from pathlib import Path
from typing import Union

_REPLACE_ATTEMPTS = 3
_REPLACE_DELAY_S = 0.05


def atomic_write_text(path: Union[str, Path], text: str, encoding: str = 'utf-8') -> None:
    """Write ``text`` to ``path`` atomically (tmp + fsync + replace).

    ``os.replace`` is retried briefly on ``PermissionError`` -- on Windows an
    antivirus scan or the search indexer can hold the target for a moment.
    A failed write removes its temp file and re-raises; the original stays.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    try:
        with open(tmp, 'w', encoding=encoding) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        for attempt in range(_REPLACE_ATTEMPTS):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if attempt == _REPLACE_ATTEMPTS - 1:
                    raise
                time.sleep(_REPLACE_DELAY_S)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
