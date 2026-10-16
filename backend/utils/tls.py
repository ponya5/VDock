"""TLS context for plain ``urllib`` HTTPS calls (DL-019).

A frozen macOS Python has no system CA bundle, so ``urlopen`` fails with
CERTIFICATE_VERIFY_FAILED. certifi ships with ``requests`` and is bundled in
the packaged app; use it when present, fall back to the platform default.
"""
import ssl


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001 - no certifi / unreadable bundle: platform default
        return ssl.create_default_context()
