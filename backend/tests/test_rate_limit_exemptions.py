"""Blueprints the frontend polls on a timer must be exempt from rate limiting.

Mission Control polls /api/agent-mission every 15 s (240 req/h); with an
opt-in cap such as 50/hour that alone trips 429 for the whole deck.
"""
import pytest

import app as app_module

# blueprint name -> why it must be exempt
POLLED_BLUEPRINTS = {
    'agent_mission': 'Mission Control polls every 15 s',
    'agent_sessions': 'session picker polls every 4 s',
    'agent_events': 'agent hooks must never be throttled',
    'system_metrics': 'metric widgets poll',
    'app_monitor': 'running-app detection polls',
    'news': 'news widget refreshes on a timer',
    'market': 'market widget refreshes on a timer',
    'weather': 'weather widget refreshes on a timer',
    'now_playing': 'now-playing widget polls',
    'config': 'settings/health reads',
    'logs': 'frontend error posts can burst',
    'triggers': 'localhost webhook + settings CRUD',
    'mcp': 'MCP clients poll rapidly',
    'update': 'update banner polls status',
}


@pytest.mark.parametrize('name', sorted(POLLED_BLUEPRINTS))
def test_polled_blueprint_is_rate_limit_exempt(name):
    exempt = app_module.limiter.limit_manager._blueprint_exemptions
    assert name in exempt, f'{name}: {POLLED_BLUEPRINTS[name]}'
