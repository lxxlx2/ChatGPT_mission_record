"""A stopped loop must not appear healthy from its historical heartbeat."""
from datetime import datetime, timezone
import json

import pytest
from mission_agent.mission_control import server

NOW = datetime(2026, 10, 31, 15, 0, tzinfo=timezone.utc).timestamp()


def snapshot(tmp_path, monkeypatch, updated_at):
    production = tmp_path / 'production'
    control = tmp_path / 'control'
    production.mkdir()
    control.mkdir()
    state = server.DashboardState(production, control)
    body = {'status': 'OK', 'updated_at': updated_at, 'candidate_count': 7}
    state.control_health.write_text(json.dumps(body))
    before = state.control_health.read_bytes()
    monkeypatch.setattr(server.time, 'time', lambda: NOW)
    result = state.mission_control_health()
    assert state.control_health.read_bytes() == before
    assert not state.control_db.exists()
    assert result['candidate_count'] == 7
    return result


def test_stopped_loop_historical_ok_is_stale_without_rewriting_file(tmp_path, monkeypatch):
    result = snapshot(tmp_path, monkeypatch, '2026-10-29T00:00:00+00:00')
    assert result['status'] == 'STALE'
    assert result['recorded_status'] == 'OK'
    assert result['heartbeat_age_seconds'] > 120


@pytest.mark.parametrize('updated_at', ['2026-10-31T14:59:30Z', '2026-10-31T21:59:30+07:00'])
def test_recent_timezone_aware_heartbeat_remains_ok(tmp_path, monkeypatch, updated_at):
    result = snapshot(tmp_path, monkeypatch, updated_at)
    assert result['status'] == 'OK'
    assert result['heartbeat_age_seconds'] == 30


@pytest.mark.parametrize('updated_at', [None, 'not-a-time', '2026-10-31T15:00:00',
                                        '2026-10-31T15:01:00+00:00', 12345])
def test_invalid_or_future_heartbeat_cannot_report_ok(tmp_path, monkeypatch, updated_at):
    result = snapshot(tmp_path, monkeypatch, updated_at)
    assert result['status'] == 'UNKNOWN'
    assert result['recorded_status'] == 'OK'
