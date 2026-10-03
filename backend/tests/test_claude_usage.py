"""Claude Code usage reader (DL-145 Phase 2). Fixtures are synthetic."""
import json
import os
from datetime import date, datetime, time as dtime, timedelta, timezone
from pathlib import Path

import pytest

from services import claude_usage as cu

TODAY = date.today()


def _ts(day: date, hour: int = 12) -> str:
    local = datetime.combine(day, dtime(hour)).astimezone()
    return local.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def assistant(msg_id, model='claude-sonnet-5', day=TODAY, inp=10, out=20,
              read=100, write=50, write_1h=0, sidechain=False):
    return {
        'type': 'assistant', 'timestamp': _ts(day), 'isSidechain': sidechain,
        'message': {'id': msg_id, 'model': model, 'usage': {
            'input_tokens': inp, 'output_tokens': out,
            'cache_read_input_tokens': read,
            'cache_creation_input_tokens': write,
            'cache_creation': {'ephemeral_1h_input_tokens': write_1h,
                               'ephemeral_5m_input_tokens': write - write_1h},
        }},
    }


def cost_state(total, unknown=False):
    return {'type': 'cost-state', 'totalCostUSD': total,
            'hasUnknownModelCost': unknown}


def write(path: Path, records, trailing_newline=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = '\n'.join(json.dumps(r) for r in records)
    path.write_text(text + ('\n' if trailing_newline else ''), encoding='utf-8')
    return path


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(cu, 'claude_home', lambda: tmp_path)
    cu.reset_cache()
    yield tmp_path
    cu.reset_cache()


def transcript(home, session='s1', slug='proj'):
    return home / 'projects' / slug / f'{session}.jsonl'


def test_repeated_message_id_counted_once(home):
    path = write(transcript(home), [assistant('m1'), assistant('m1'), assistant('m2')])
    agg = cu.scan_file(path, TODAY)
    assert agg.tokens_by_model['claude-sonnet-5'].input == 20


def test_partial_last_line_is_deferred_then_counted(home):
    path = transcript(home)
    path.parent.mkdir(parents=True)
    line = json.dumps(assistant('m1'))
    path.write_text(json.dumps(assistant('m0')) + '\n' + line[:25], encoding='utf-8')
    assert cu.scan_file(path, TODAY).tokens_by_model['claude-sonnet-5'].input == 10
    with open(path, 'a', encoding='utf-8') as handle:
        handle.write(line[25:] + '\n')
    assert cu.scan_file(path, TODAY).tokens_by_model['claude-sonnet-5'].input == 20


def test_complete_last_line_without_newline_is_counted(home):
    path = write(transcript(home), [assistant('m1')], trailing_newline=False)
    assert cu.scan_file(path, TODAY).tokens_by_model['claude-sonnet-5'].input == 10


def test_incremental_scan_reads_only_appended_bytes(home, monkeypatch):
    path = write(transcript(home), [assistant('m1'), assistant('m2')])
    cu.scan_file(path, TODAY)
    parsed = []
    original = cu._parse_line
    monkeypatch.setattr(cu, '_parse_line', lambda line: parsed.append(line) or original(line))
    cu.scan_file(path, TODAY)
    assert parsed == []  # unchanged file: nothing parsed
    with open(path, 'a', encoding='utf-8') as handle:
        handle.write(json.dumps(assistant('m3')) + '\n')
    agg = cu.scan_file(path, TODAY)
    assert len(parsed) == 1
    assert agg.tokens_by_model['claude-sonnet-5'].input == 30


def test_shrunk_file_is_reread_from_start(home):
    path = write(transcript(home), [assistant('m1'), assistant('m2')])
    cu.scan_file(path, TODAY)
    write(path, [assistant('m9')])
    assert cu.scan_file(path, TODAY).tokens_by_model['claude-sonnet-5'].input == 10


def test_new_day_rescans_so_today_is_recomputed(home):
    path = write(transcript(home), [assistant('m1', day=TODAY)])
    assert cu.scan_file(path, TODAY).today_by_model
    assert not cu.scan_file(path, TODAY + timedelta(days=1)).today_by_model


def test_yesterday_counts_in_totals_but_not_today(home):
    yesterday = TODAY - timedelta(days=1)
    path = write(transcript(home), [assistant('m1', day=yesterday), assistant('m2')])
    agg = cu.scan_file(path, TODAY)
    assert agg.tokens_by_model['claude-sonnet-5'].input == 20
    assert agg.today_by_model['claude-sonnet-5'].input == 10


def test_cost_state_found_anywhere_and_unknown_types_ignored(home):
    path = write(transcript(home), [
        {'type': 'mystery', 'x': 1}, cost_state(1.5), assistant('m1'),
        cost_state(2.5, unknown=True), {'not': 'typed'},
    ])
    agg = cu.scan_file(path, TODAY)
    assert agg.cost_state_usd == 2.5 and agg.cost_state_unknown is True


def test_invalid_json_lines_are_skipped(home):
    path = transcript(home)
    path.parent.mkdir(parents=True)
    path.write_text('not json\n' + json.dumps(assistant('m1')) + '\n[1,2]\n', encoding='utf-8')
    assert cu.scan_file(path, TODAY).tokens_by_model['claude-sonnet-5'].input == 10


def test_synthetic_model_is_ignored(home):
    path = write(transcript(home), [assistant('m1', model='<synthetic>')])
    assert cu.scan_file(path, TODAY).tokens_by_model == {}


def test_session_files_include_subagents(home):
    main = write(transcript(home), [assistant('m1')])
    sub = write(main.parent / 's1' / 'subagents' / 'agent-a.jsonl', [assistant('m2')])
    assert cu.session_files('s1') == [main, sub]
    assert cu.session_files('missing') == []
    assert cu.session_files('../x') == []


def test_today_files_filters_by_mtime(home):
    fresh = write(transcript(home, 'new'), [assistant('m1')])
    stale = write(transcript(home, 'old'), [assistant('m2')])
    old = (datetime.now() - timedelta(days=3)).timestamp()
    os.utime(stale, (old, old))
    assert cu.today_files(TODAY) == [fresh]


# --- cost + context -----------------------------------------------------------

def test_estimate_cost_hand_computed():
    tokens = cu.Tokens(input=1_000_000, output=1_000_000,
                       cache_read=1_000_000, cache_write=2_000_000,
                       cache_write_1h=1_000_000)
    # sonnet 5: 2 + 10 + 0.20 + 1M*2.5 (5m) + 1M*4 (1h) = 18.7
    assert cu.estimate_cost('claude-sonnet-5', tokens) == pytest.approx(18.7)


@pytest.mark.parametrize('model,expected_input', [
    ('claude-sonnet-5-5', 2.0), ('claude-sonnet-5', 2.0),
    ('claude-sonnet-4-6', 3.0), ('claude-opus-5', 5.0),
    ('claude-opus-5-5', 4.0), ('claude-opus-4-1-20250805', 15.0),
    ('claude-haiku-4-5', 1.0),
])
def test_price_lookup_per_model(model, expected_input):
    assert cu.estimate_cost(model, cu.Tokens(input=1_000_000)) == pytest.approx(expected_input)


def test_unknown_model_has_no_price():
    assert cu.estimate_cost('gpt-5', cu.Tokens(input=1)) is None


def test_context_window_rule():
    assert cu.context_window('claude-sonnet-5', 150_000) == 200_000
    assert cu.context_window('claude-sonnet-5', 250_000) == 1_000_000
    assert cu.context_window('claude-opus-5[1m]', 10) == 1_000_000


def test_session_usage_estimates_when_live(home):
    write(transcript(home), [assistant('m1', inp=1_000_000, out=0, read=0, write=0)])
    usage = cu.session_usage('s1', TODAY)
    assert usage['estimate'] is True
    assert usage['cost_usd'] == pytest.approx(2.0)
    assert usage['model'] == 'claude-sonnet-5'


def test_session_usage_prefers_cost_state_at_end(home):
    write(transcript(home), [assistant('m1', inp=1_000_000), cost_state(0.42)])
    usage = cu.session_usage('s1', TODAY)
    assert usage['estimate'] is False and usage['cost_usd'] == 0.42


def test_stale_mid_file_cost_state_is_not_exact(home):
    write(transcript(home), [cost_state(0.42), assistant('m1', inp=1_000_000, out=0, read=0, write=0)])
    usage = cu.session_usage('s1', TODAY)
    assert usage['estimate'] is True and usage['cost_usd'] == pytest.approx(2.0)


def test_unknown_model_cost_state_is_an_estimate(home):
    write(transcript(home), [assistant('m1'), cost_state(0.42, unknown=True)])
    assert cu.session_usage('s1', TODAY)['estimate'] is True


def test_session_usage_adds_subagent_tokens(home):
    main = write(transcript(home), [assistant('m1', inp=10)])
    write(main.parent / 's1' / 'subagents' / 'agent-a.jsonl', [assistant('m2', inp=5)])
    assert cu.session_usage('s1', TODAY)['tokens']['input'] == 15


def test_context_pct_and_status(home):
    write(transcript(home), [assistant('m1', inp=0, read=170_000, write=0)])
    usage = cu.session_usage('s1', TODAY)
    assert usage['context_pct'] == 85 and usage['status'] == 'warning'
    write(transcript(home, 's2'), [assistant('m2', inp=0, read=195_000, write=0)])
    assert cu.session_usage('s2', TODAY)['status'] == 'critical'
    write(transcript(home, 's3'), [assistant('m3', inp=0, read=20_000, write=0)])
    assert cu.session_usage('s3', TODAY)['status'] == 'normal'


def test_sidechain_records_do_not_move_context(home):
    write(transcript(home), [assistant('m1', inp=0, read=1000, write=0),
                             assistant('m2', inp=0, read=99_000, write=0, sidechain=True)])
    assert cu.session_usage('s1', TODAY)['context_tokens'] == 1000


def test_session_usage_none_without_transcript(home):
    assert cu.session_usage('nope', TODAY) is None


def test_today_usage_sums_models_and_counts_sessions(home):
    main = write(transcript(home), [assistant('m1', inp=1_000_000, out=0, read=0, write=0)])
    write(main.parent / 's1' / 'subagents' / 'agent-a.jsonl',
          [assistant('m2', model='claude-haiku-4-5', inp=1_000_000, out=0, read=0, write=0)])
    write(transcript(home, 'other'), [assistant('m3', day=TODAY - timedelta(days=1))])
    usage = cu.today_usage(TODAY)
    assert usage['estimate'] is True
    assert usage['sessions'] == 1  # the subagent belongs to s1; 'other' is yesterday
    assert usage['cost_usd'] == pytest.approx(3.0)
    assert usage['tokens']['input'] == 2_000_000


def test_today_usage_empty(home):
    usage = cu.today_usage(TODAY)
    assert usage['cost_usd'] == 0 and usage['sessions'] == 0
