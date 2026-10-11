"""Official short-listing 1m replay: no invented preceding 24h bars."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"scripts/monster_v4_short_history_replay.py"
sp=importlib.util.spec_from_file_location("monster_v4_short_history_replay",P)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)


class ShortHistoryReplayTests(unittest.TestCase):
    def test_actual_first_listing_history_deduplicates_overlapping_rest_pages(self):
        p=m.EVIDENCE/"monster_v4_replay_1m_futures_RECALLUSDT_2025-10-15.json"
        src,bars,dups=m.normalize_partial(p)
        self.assertEqual(src["data_integrity"],"INCOMPLETE")
        self.assertGreater(dups,0)
        self.assertGreater(len(bars),1440)
        self.assertEqual(bars[0][0],m.full.parse_ms("2025-10-15T12:30:00Z"))
        self.assertTrue(all(bars[i][0]-bars[i-1][0]==60000
                            for i in range(1,len(bars))))

    def test_actual_new_listing_uses_same_v4_observer_without_24h_fabrication(self):
        p=m.EVIDENCE/"monster_v4_replay_1m_futures_RECALLUSDT_2025-10-15.json"
        data=m.replay_partial(*m.normalize_partial(p))
        self.assertFalse(data["full_24h_warmup"])
        self.assertFalse(data["first_listing_time_officially_verified"])
        self.assertGreater(data["polls"],10)
        self.assertEqual(data["trading"],"NO_GO")
        self.assertTrue(data["rolling_24h_quote"].startswith("SUM_OF_AVAILABLE_"))

    def test_all_20_incomplete_sources_handled_separately(self):
        r=m.run_short()
        self.assertEqual(r["eligible"]+r["source_failures"],20)
        self.assertEqual(r["new_listing_venue_cases"],10)
        self.assertEqual(r["deploy_gate"],"NO_GO")
        self.assertFalse(r["future_profitability_validated"])

    def test_changed_overlap_must_be_rejected_instead_of_last_write_wins(self):
        src_path=m.EVIDENCE/"monster_v4_replay_1m_futures_RECALLUSDT_2025-10-15.json"
        src=json.loads(src_path.read_text(encoding="utf-8"))
        times={}
        for i,item in enumerate(src["bars"]):
            t=item[0]
            if t in times:
                src["bars"][i][5]=str(float(item[5])+1.0)
                break
            times[t]=i
        else:
            self.fail("Expected actual REST historical page overlap")
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/"mutated.json"
            file.write_text(json.dumps(src),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"CONFLICTING_OVERLAPPING"):
                m.normalize_partial(file)


if __name__=="__main__":
    unittest.main()
