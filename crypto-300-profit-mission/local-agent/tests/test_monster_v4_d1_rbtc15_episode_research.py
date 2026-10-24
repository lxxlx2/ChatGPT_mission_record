"""Isolated SQLite ADR005 research queue: restart, censor, retries and expiry."""
from pathlib import Path
import tempfile
import unittest

import monster_v4_shadow as original
from monster_v4_d1_rbtc15_episode_research import (
    create_ledger,reopen_ledger,admit_original_watch,poll_episodes,summary
)

FIVE=300_000
T=3_600_000
WATCH=T-360_000
NEXT=T+360_000


def make_watch(ms=WATCH,symbol="COINUSDT"):
    return {"venue":"spot","symbol":symbol,"event_type":"WATCH_EARLY",
            "observed_ms":ms,
            "event_id":original.event_key("spot",symbol,"WATCH_EARLY",ms)}


def source(*,btc_strong=False, btc_missing=False, later_coin_spike=False):
    coin=[100,100,100,104,108,112,130 if later_coin_spike else 112,112]
    btc=[200,200,200,220 if btc_strong else 201,
         230 if btc_strong else 202,260 if btc_strong else 203,
         220 if btc_strong else 203,220 if btc_strong else 203]
    def candles(symbol,now):
        if btc_missing and symbol=="BTCUSDT":
            raise ValueError("BTC_ARCHIVE_MISSING")
        closes=coin if symbol=="COINUSDT" else btc
        if symbol not in ("COINUSDT","BTCUSDT"):
            raise ValueError("UNSUPPORTED_SYMBOL")
        base=(now//FIVE)*FIVE-6*FIVE
        rows=[]
        for i in range(6):
            start=base+i*FIVE
            idx=(start-1_800_000)//FIVE
            last=closes[idx] if 0<=idx<len(closes) else (100 if symbol=="COINUSDT" else 200)
            prior=closes[idx-1] if 0<idx<len(closes) else last
            q=10 if idx<3 else 20
            rows.append([start,str(prior),str(max(prior,last)+1),str(min(prior,last)-1),
                         str(last),"100",start+FIVE-1,str(q)])
        return rows
    return candles


class DurableEpisodeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"research-only.sqlite"
        self.db=create_ledger(self.path)
        self.addCleanup(self.db.close)

    def test_original_watch_admitted_once_with_exact_original_hash(self):
        watch=make_watch()
        self.assertTrue(admit_original_watch(self.db,watch))
        self.assertFalse(admit_original_watch(self.db,watch))
        self.assertEqual(summary(self.db)["episodes"],1)

    def test_first_pass_generates_one_distinct_research_not_original_setup(self):
        admit_original_watch(self.db,make_watch())
        result=poll_episodes(self.db,T,source())
        self.assertEqual(result[0][1],"RESEARCH_SETUP")
        ledger=summary(self.db)
        self.assertEqual(ledger["status_counts"],{"RESEARCH_SETUP":1})
        self.assertEqual(len([r for r in ledger["rows"] if r["research_event_id"]]),1)
        self.assertEqual(ledger["G6"],"NO_GO")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM research_setup").fetchone()[0],1)
        self.assertEqual(poll_episodes(self.db,T+180_000,source()),[])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM research_setup").fetchone()[0],1)

    def test_resume_sqlite_no_duplicate_research_setup(self):
        admit_original_watch(self.db,make_watch())
        poll_episodes(self.db,T,source())
        self.db.close()
        self.db=reopen_ledger(self.path)
        self.assertEqual(poll_episodes(self.db,T+180_000,source()),[])
        self.assertEqual(summary(self.db)["status_counts"]["RESEARCH_SETUP"],1)

    def test_new_filter_can_pass_later_after_original_would_stop(self):
        admit_original_watch(self.db,make_watch())
        first=poll_episodes(self.db,T,source(btc_strong=True,later_coin_spike=True))
        self.assertEqual(first[0][1],"RESEARCH_NO_SETUP_YET")
        same=poll_episodes(self.db,T+180_000,source(btc_strong=True,later_coin_spike=True))
        self.assertEqual(same[0][1],"SAME_BAR_NO_DUPLICATE")
        later=poll_episodes(self.db,NEXT,source(btc_strong=True,later_coin_spike=True))
        self.assertEqual(later[0][1],"RESEARCH_SETUP")
        self.assertEqual(summary(self.db)["status_counts"],{"RESEARCH_SETUP":1})
        self.assertEqual(summary(self.db)["rows"][0]["research_observed_ms"],NEXT)

    def test_missing_btc_does_not_become_negative_label(self):
        admit_original_watch(self.db,make_watch())
        got=poll_episodes(self.db,T,source(btc_missing=True))
        self.assertEqual(got[0][1],"SOURCE_CENSORED")
        row=summary(self.db)["rows"][0]
        self.assertEqual(row["source_censored_count"],1)
        self.assertEqual(row["status"],"PENDING")
        got=poll_episodes(self.db,T+180_000,source())
        self.assertEqual(got[0][1],"RESEARCH_SETUP")

    def test_partial_censor_then_deadline_valid_negative_is_unscored_after_restart(self):
        # Reproduces independent review P1: an earlier missing BTC check
        # cannot be treated as a confirmed negative from a later valid bar.
        admit_original_watch(self.db,make_watch())
        self.assertEqual(poll_episodes(self.db,T,source(btc_missing=True))[0][1],
                         "SOURCE_CENSORED")
        deadline=WATCH+900_000

        def negative_on_deadline(symbol,now):
            candles=source()(symbol,now)
            if symbol=="COINUSDT":
                # Force a valid last 5m down-close; OHLC invariants stay valid.
                candles[-1][4]="90"
                candles[-1][3]="89"
            return candles

        result=poll_episodes(self.db,deadline,negative_on_deadline)
        self.assertEqual(result[0][1],"SOURCE_UNSCORED")
        row=summary(self.db)["rows"][0]
        self.assertEqual(row["status"],"SOURCE_UNSCORED")
        self.assertEqual(row["source_censored_count"],1)
        self.assertIsNone(row["research_event_id"])
        self.assertIsNone(row["research_observed_ms"])
        self.assertEqual(poll_episodes(self.db,deadline+180_000,source()),[])
        self.db.close()
        self.db=reopen_ledger(self.path)
        self.assertEqual(summary(self.db)["status_counts"],{"SOURCE_UNSCORED":1})
        self.assertEqual(summary(self.db)["rows"][0]["source_censored_count"],1)
        self.assertEqual(poll_episodes(self.db,deadline+360_000,source()),[])

    def test_no_censor_deadline_valid_negative_is_true_no_setup(self):
        admit_original_watch(self.db,make_watch())
        deadline=WATCH+900_000

        def negative_at_deadline(symbol,now):
            candles=source()(symbol,now)
            if symbol=="COINUSDT":
                candles[-1][4]="90"
                candles[-1][3]="89"
            return candles

        result=poll_episodes(self.db,deadline,negative_at_deadline)
        self.assertEqual(result[0][1],"NO_SETUP")
        ledger=summary(self.db)
        self.assertEqual(ledger["status_counts"],{"NO_SETUP":1})
        self.assertEqual(ledger["rows"][0]["source_censored_count"],0)
        self.assertIsNone(ledger["rows"][0]["research_event_id"])

    def test_partial_censor_then_deadline_positive_still_generates_setup(self):
        admit_original_watch(self.db,make_watch())
        self.assertEqual(poll_episodes(self.db,T,source(btc_missing=True))[0][1],
                         "SOURCE_CENSORED")
        deadline=WATCH+900_000
        self.assertEqual(poll_episodes(self.db,deadline,source())[0][1],
                         "RESEARCH_SETUP")
        ledger=summary(self.db)
        self.assertEqual(ledger["status_counts"],{"RESEARCH_SETUP":1})
        self.assertEqual(ledger["rows"][0]["source_censored_count"],1)
        self.assertIsNotNone(ledger["rows"][0]["research_event_id"])
        self.assertEqual(poll_episodes(self.db,deadline+180_000,source()),[])

    def test_always_missing_source_ends_as_unscored(self):
        admit_original_watch(self.db,make_watch())
        for tick in (T,T+180_000,NEXT,WATCH+900_000):
            poll_episodes(self.db,tick,source(btc_missing=True))
        done=poll_episodes(self.db,WATCH+900_000+180_000,source(btc_missing=True))
        self.assertEqual(done[0][1],"SOURCE_UNSCORED")
        self.assertNotIn("NO_SETUP",summary(self.db)["status_counts"])

    def test_original_watch_at_poll_must_wait_postwatch_bar(self):
        admit_original_watch(self.db,make_watch(T))
        r=poll_episodes(self.db,T,source())
        self.assertEqual(r[0][1],"WAIT_POST_WATCH_CLOSED_5M")
        self.assertEqual(summary(self.db)["rows"][0]["status"],"PENDING")

    def test_original_invalid_watch_hash_rejected(self):
        v=make_watch();v["event_id"]="f"*64
        with self.assertRaisesRegex(ValueError,"ORIGINAL_WATCH_ID_MISMATCH"):
            admit_original_watch(self.db,v)

    def test_btc_cannot_be_research_target_even_if_original_watches_it(self):
        with self.assertRaisesRegex(ValueError,"ORIGINAL_WATCH_IDENTITY"):
            admit_original_watch(self.db,make_watch(symbol="BTCUSDT"))

    def test_overlapping_original_watch_is_not_silently_lost(self):
        admit_original_watch(self.db,make_watch())
        with self.assertRaisesRegex(ValueError,"SECOND_ORIGINAL_WATCH"):
            admit_original_watch(self.db,make_watch(WATCH+180_000))

    def test_research_db_cannot_overwrite_existing_output(self):
        with self.assertRaisesRegex(ValueError,"REFUSE_EXISTING_OUTPUT"):
            create_ledger(self.path)

    def test_no_research_event_is_written_into_original_db(self):
        original_path=Path(self.temp.name)/"original-core.sqlite"
        prod=original.open_store(original_path)
        prod.close()
        admit_original_watch(self.db,make_watch())
        poll_episodes(self.db,T,source())
        import sqlite3
        with sqlite3.connect(original_path) as read:
            self.assertEqual(read.execute("SELECT COUNT(*) FROM events").fetchone()[0],0)

    def test_invalid_limit_and_clock_are_rejected(self):
        admit_original_watch(self.db,make_watch())
        with self.assertRaisesRegex(ValueError,"RESEARCH_BAD_POLL"):
            poll_episodes(self.db,T+1,source())
        with self.assertRaisesRegex(ValueError,"RESEARCH_BAD_POLL"):
            poll_episodes(self.db,T,source(),limit=9)

    def test_deadline_does_not_get_extended(self):
        admit_original_watch(self.db,make_watch())
        deadline=WATCH+900_000
        self.assertEqual(self.db.execute("SELECT deadline_ms FROM episode").fetchone()[0],deadline)
        for tick in (T,T+180_000,NEXT,deadline):
            poll_episodes(self.db,tick,source(btc_strong=True))
        row=summary(self.db)["rows"][0]
        self.assertEqual(row["deadline_ms"],deadline)
        self.assertNotEqual(row["status"],"PENDING")

    def test_missing_or_invalid_ledger_reopen_rejected(self):
        with self.assertRaises(ValueError):
            reopen_ledger(Path(self.temp.name)/"not-found.sqlite")


if __name__=="__main__":
    unittest.main()
