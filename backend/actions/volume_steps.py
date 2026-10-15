"""Volume step normalisation shared by every platform.

Button presets disagree on units: the system presets ship ``step: 2000``
(NirCmd's 0-65535 scale) while the default profile ships ``step: 10`` (a
percentage). Each platform backend needs one unambiguous value.
"""

MAX_VOLUME_PERCENT = 100
DEFAULT_VOLUME_STEP_PERCENT = 10
NIRCMD_FULL_SCALE = 65535

# Windows has always defaulted to 2000 NirCmd units when no step is set.
WINDOWS_DEFAULT_VOLUME_STEP_PERCENT = 3


def parse_volume_step(raw_step, default_percent: int = DEFAULT_VOLUME_STEP_PERCENT) -> int:
    """Return a usable step as a 1-100 percentage.

    Values above 100 can only be NirCmd units and are converted; anything
    missing or non-numeric falls back to ``default_percent``.
    """
    try:
        step = abs(int(float(raw_step)))
    except (TypeError, ValueError):
        return default_percent

    if step == 0:
        return default_percent
    if step > MAX_VOLUME_PERCENT:
        return max(1, round(step / NIRCMD_FULL_SCALE * MAX_VOLUME_PERCENT))
    return step


def percent_to_nircmd_units(percent: int) -> int:
    return round(percent / MAX_VOLUME_PERCENT * NIRCMD_FULL_SCALE)


def nircmd_step_units(raw_step) -> int:
    """NirCmd step for Windows: NirCmd-scale values pass through untouched."""
    try:
        step = abs(int(float(raw_step)))
    except (TypeError, ValueError):
        step = 0

    if step > MAX_VOLUME_PERCENT:
        return step
    return percent_to_nircmd_units(
        parse_volume_step(raw_step, WINDOWS_DEFAULT_VOLUME_STEP_PERCENT)
    )
