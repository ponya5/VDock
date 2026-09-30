# Notes from the orchestrator

## W1 (now-playing): use `winrt`, not `winsdk`

`pip install winsdk` fails on Python 3.13 — no prebuilt wheel, source build
needs a C++/CMake toolchain that isn't installed. Installed instead (all
3.2.1, cp313 win_amd64 wheels):

- `winrt-runtime`
- `winrt-Windows.Media.Control`
- `winrt-Windows.Foundation`
- `winrt-Windows.Media`
- `winrt-Windows.Storage`
- `winrt-Windows.Storage.Streams`

The pywinrt API is the same objects, different top package:

```python
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)
from winrt.windows.storage.streams import Buffer, InputStreamOptions

async def read_once():
    mgr = await SessionManager.request_async()
    session = mgr.get_current_session()          # None when nothing plays
    props = await session.try_get_media_properties_async()
    info = session.get_playback_info()
    # info.playback_status == PlaybackStatus.playing
    # session.source_app_user_model_id -> e.g. spotify.exe / chrome.exe
    # props.title / .artist / .album_title
```

Verified working on this machine (Python 3.13): request_async +
try_get_media_properties_async + get_playback_info all succeed; session is
None when nothing is playing.

If you already wrote `winsdk` imports, that's fine — keep the lazy import but
try both paths (`try: winsdk… except ImportError: winrt…`); the orchestrator
will adjust during integration either way. For album art:
`props.thumbnail` → `open_async()` → read via Buffer/DataReader from
`winrt.windows.storage.streams`.

## All workers

`soundcard==0.4.6` and `numpy==2.5.3` are installed in backend/venv —
write lazy imports anyway (the packaged app must not hard-crash on machines
without them; requirements get sys_platform-marked optional lines).
