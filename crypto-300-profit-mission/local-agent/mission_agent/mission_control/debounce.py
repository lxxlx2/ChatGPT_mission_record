"""Durable debounce for transient actionable->WAIT transitions."""
from __future__ import annotations

from ..hashing import digest

ACTIONABLE=frozenset({'BUY','SMALL_BUY'})


class TransitionDebounce:
    def __init__(self,db):
        self.db=db
        self.db.execute('''CREATE TABLE IF NOT EXISTS transition_debounce(
            entity_key TEXT PRIMARY KEY,
            person_id TEXT NOT NULL,
            mint TEXT NOT NULL,
            episode_id TEXT,
            target_decision TEXT NOT NULL,
            first_seen_at REAL NOT NULL,
            last_seen_at REAL NOT NULL,
            seen_count INTEGER NOT NULL,
            reason TEXT
        )''')

    @staticmethod
    def _key(person_id,mint,episode_id):
        return digest({'person_id':person_id,'mint':mint,'episode_id':episode_id})

    def clear(self,person_id,mint,episode_id):
        self.db.execute('DELETE FROM transition_debounce WHERE entity_key=?',(self._key(person_id,mint,episode_id),))

    def allow(self,*,person_id,mint,episode_id,previous_decision,target_decision,transient,reason,now,grace_seconds):
        """Return True when the transition may enter the immutable event ledger.

        Only actionable->transient WAIT transitions are delayed. Candidate latest
        state can still update immediately so the dashboard shows degraded data.
        Recovery before the grace window clears the pending transition and creates
        no WAIT/recovery event pair. A zero/negative grace disables debounce and
        preserves legacy immediate-transition behavior for old fixtures/replays.
        """
        key=self._key(person_id,mint,episode_id)
        if float(grace_seconds)<=0:
            self.db.execute('DELETE FROM transition_debounce WHERE entity_key=?',(key,))
            return True
        if not transient or previous_decision not in ACTIONABLE or target_decision!='WAIT':
            self.db.execute('DELETE FROM transition_debounce WHERE entity_key=?',(key,))
            return True
        row=self.db.execute('SELECT * FROM transition_debounce WHERE entity_key=?',(key,)).fetchone()
        if row is None or row['target_decision']!=target_decision:
            self.db.execute('INSERT OR REPLACE INTO transition_debounce VALUES(?,?,?,?,?,?,?,?,?)',(key,person_id,mint,episode_id,target_decision,float(now),float(now),1,reason))
            return False
        self.db.execute('UPDATE transition_debounce SET last_seen_at=?,seen_count=seen_count+1,reason=? WHERE entity_key=?',(float(now),reason,key))
        if float(now)-float(row['first_seen_at'])<float(grace_seconds):return False
        self.db.execute('DELETE FROM transition_debounce WHERE entity_key=?',(key,))
        return True
