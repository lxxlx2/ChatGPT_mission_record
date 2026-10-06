import sqlite3

from mission_agent.mission_control.debounce import TransitionDebounce


def db():
    value=sqlite3.connect(':memory:');value.row_factory=sqlite3.Row;return value


def test_zero_grace_disables_debounce_for_legacy_fixtures():
    conn=db();gate=TransitionDebounce(conn)
    assert gate.allow(person_id='frank',mint='A',episode_id='e',previous_decision='BUY',target_decision='WAIT',transient=True,reason='FRANK_RUNTIME_NOT_LIVE',now=100,grace_seconds=0) is True
    assert conn.execute('select count(*) from transition_debounce').fetchone()[0]==0


def test_short_actionable_to_wait_is_debounced_and_recovery_clears():
    conn=db();gate=TransitionDebounce(conn)
    assert gate.allow(person_id='frank',mint='A',episode_id='e',previous_decision='BUY',target_decision='WAIT',transient=True,reason='FRANK_RUNTIME_NOT_LIVE',now=100,grace_seconds=60) is False
    assert conn.execute('select count(*) from transition_debounce').fetchone()[0]==1
    assert gate.allow(person_id='frank',mint='A',episode_id='e',previous_decision='BUY',target_decision='BUY',transient=False,reason='RECOVERED',now=110,grace_seconds=60) is True
    assert conn.execute('select count(*) from transition_debounce').fetchone()[0]==0


def test_persistent_transient_wait_is_allowed_after_grace():
    conn=db();gate=TransitionDebounce(conn)
    assert gate.allow(person_id='frank',mint='A',episode_id='e',previous_decision='SMALL_BUY',target_decision='WAIT',transient=True,reason='QUOTE_METRICS_INVALID',now=100,grace_seconds=60) is False
    assert gate.allow(person_id='frank',mint='A',episode_id='e',previous_decision='SMALL_BUY',target_decision='WAIT',transient=True,reason='QUOTE_METRICS_INVALID',now=159,grace_seconds=60) is False
    assert gate.allow(person_id='frank',mint='A',episode_id='e',previous_decision='SMALL_BUY',target_decision='WAIT',transient=True,reason='QUOTE_METRICS_INVALID',now=160,grace_seconds=60) is True
    assert conn.execute('select count(*) from transition_debounce').fetchone()[0]==0


def test_non_actionable_or_nontransient_transition_is_not_delayed():
    conn=db();gate=TransitionDebounce(conn)
    assert gate.allow(person_id='frank',mint='A',episode_id='e',previous_decision='WAIT',target_decision='WAIT',transient=True,reason='FRANK_RUNTIME_NOT_LIVE',now=1,grace_seconds=60) is True
    assert gate.allow(person_id='frank',mint='A',episode_id='e',previous_decision='BUY',target_decision='NO_BUY',transient=False,reason='POSITION_CLOSED',now=2,grace_seconds=60) is True
