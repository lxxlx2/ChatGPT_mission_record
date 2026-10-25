"""No-network guardrails for frozen 69 WATCH original-source research replay."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import monster_v4_shadow as original
import monster_v4_adr005_real69_original_sqlite_replay as full


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = (ROOT / "monster" / "evidence" /
             "MONSTER_SPOT511_4088_REAL_ORIGINAL_CORE_53_WATCH_IDENTITIES_20261025.json")
NEW_16_UTC = (
    ("BMTUSDT","01:57"), ("EPICUSDT","03:21"), ("QUICKUSDT","03:21"),
    ("AVAUSDT","08:33"), ("TREEUSDT","09:24"), ("QUICKUSDT","10:06"),
    ("LAUSDT","11:00"), ("STRAXUSDT","11:18"), ("KATUSDT","11:30"),
    ("WOOUSDT","12:00"), ("BMTUSDT","12:03"), ("ERAUSDT","13:27"),
    ("ANIMEUSDT","15:15"), ("QUICKUSDT","15:39"),
    ("ANIMEUSDT","17:09"), ("EPICUSDT","17:36"),
)


def pinned_synthetic_69():
    original_rows = json.loads(INVENTORY.read_bytes())["real_original_core_watch_identity_rows"]
    old = [(x["symbol"],x["observed_ms"],x["event_id"]) for x in original_rows]
    extra = []
    for symbol, hour_minute in NEW_16_UTC:
        ms = int(datetime.fromisoformat(
            f"2026-10-24T{hour_minute}:00+00:00").timestamp()*1000)
        extra.append((symbol,ms,original.event_key("spot",symbol,"WATCH_EARLY",ms)))
    return tuple(sorted(old+extra,key=lambda r:(r[1],r[2])))


class Frozen69Tests(unittest.TestCase):
    def test_original53_plus_16_makes_exact_pinned_69_digest(self):
        rows = pinned_synthetic_69()
        self.assertEqual(len(rows),69)
        self.assertEqual(len(set(x[2] for x in rows)),69)
        raw="".join(f"{sym}\t{ms}\t{eid}\n" for sym,ms,eid in rows)
        self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(),
                         full.PINNED_69_WATCH_SHA256)

    def test_real_69_needs_only_69_symbol_days_and_12_on_oct24(self):
        needed = full.required_days_69(pinned_synthetic_69())
        self.assertEqual(len(needed),69)
        self.assertEqual(len(set(sym for sym,_ in needed)),46)
        self.assertEqual(sum(day=="2026-10-24" for _,day in needed),12)

    def test_53_cannot_silently_be_used_as_69(self):
        with self.assertRaisesRegex(ValueError,"FROZEN_69_WATCH_ROWS"):
            full.required_days_69(pinned_synthetic_69()[:-16])

    def test_bad_watch_timestamp_type_fails(self):
        x=list(pinned_synthetic_69())
        x[0]=(x[0][0],True,x[0][2])
        with self.assertRaisesRegex(ValueError,"FROZEN_69_WATCH_CLOCK"):
            full.required_days_69(tuple(x))

    def test_forged_4599_json_rejected_before_any_watches(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"fake-4599.json"
            file.write_text('{"d0_watch_count":69}')
            with self.assertRaisesRegex(ValueError,"ORIGINAL_4599_FULL_REPORT_SHA_MISMATCH"):
                full.load_pinned_69(file,{"watch_identity_rows":()})

    def test_early_source_asof_refused_without_creating_sqlite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            paths=dict(original_4599=root/"4599",
                       original_4088=root/"4088",
                       old_reference=root/"ref",publisher_dir=root,
                       ledger_path=root/"research.sqlite")
            with self.assertRaisesRegex(ValueError,"SOURCE_MUST_HAVE_BEEN_OBTAINED"):
                full.replay(**paths,asof_utc=datetime(2026,10,25,6,tzinfo=timezone.utc))
            with self.assertRaisesRegex(ValueError,"SOURCE_MUST_HAVE_BEEN_OBTAINED"):
                full.replay(**paths,asof_utc=datetime(2026,10,25,8))
            self.assertFalse(paths["ledger_path"].exists())


if __name__=="__main__":
    unittest.main()
