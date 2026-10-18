"""Stage164 scoped offline, no-market, no-wallet source-cohort regression."""
import copy
import importlib.util
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "scripts" / "monster_v4_stage164_fair8_nonconversion_audit.py"
spec = importlib.util.spec_from_file_location("monster_stage164_test_target", SRC)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fixture():
    base = 1_800_000_000_000
    candidates, queues = [], []
    for i in range(1, 4):
        gained = i < 3
        status = "EVALUATED" if gained else "EVALUATED"
        candidates.append({
            "id": i, "symbol": "TEST" + str(i) + "USDT",
            "first_seen_ms": base + 1000 * i,
            "deadline_ms": base + 1000 * i + 15 * 60_000,
            "baseline_first_evaluation_ms": None if gained else base + 1000 * i + 6 * 60_000,
            "alternative_first_evaluation_ms": base + 1000 * i + (9 if gained else 6) * 60_000,
            "alternative_selected_slots": 2,
            "baseline_status": "LATE" if gained else "EVALUATED",
            "alternative_status": status,
            "cohort": "PEAK_98" if gained else "OTHER_171"
        })
        queues.append({
            "id": i, "symbol": candidates[-1]["symbol"],
            "first_seen_ms": candidates[-1]["first_seen_ms"],
            "deadline_ms": candidates[-1]["deadline_ms"],
            "status": status,
            "last_error": "NO_SETUP_WITHIN_WINDOW"
        })
    return {
        "candidate_outcomes": candidates,
        "raw_alternative_queue": queues,
        "setup_new_ids": 0, "setup_lost_ids": 0,
        "setup_event_id_baseline": 1,
        "setup_event_id_alternative": 1,
        "setup_retained_ids": 1,
    }


class Stage164Tests(unittest.TestCase):
    def test_original_episode_id_join_and_no_setup_are_preserved(self):
        j = fixture()
        result = audit.make_report(j, strict=False)
        self.assertEqual(result["total_watch_episodes"], 3)
        self.assertEqual(result["gained_first_valid_d1"], 2)
        self.assertEqual(result["lost_first_valid_d1"], 0)
        self.assertEqual(result["gained_fair8_final_status"], {"EVALUATED": 2})
        self.assertEqual(result["gained_final_queue_error"], {"NO_SETUP_WITHIN_WINDOW": 2})
        self.assertEqual(result["gained_first_valid_delay_minutes"], {"9": 2})
        self.assertEqual(result["new_setup_count"], 0)
        self.assertEqual(result["specific_5m_feature_threshold_reasons"],
                         "UNVERIFIED_NOT_IN_STAGE162_CANDIDATE_TRACE")
        self.assertEqual(result["G6"], "NO_GO")

    def test_duplicate_episode_id_rejected_even_if_symbols_differ(self):
        j = fixture()
        j["candidate_outcomes"][1]["id"] = j["candidate_outcomes"][0]["id"]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CANDIDATE_ID"):
            audit.make_report(j, strict=False)

    def test_queue_episode_join_drift_rejected(self):
        j = fixture()
        j["raw_alternative_queue"][0]["first_seen_ms"] += 1000
        with self.assertRaisesRegex(ValueError, "QUEUE_TO_CANDIDATE|CANDIDATE_SOURCE_JOIN_DRIFT"):
            audit.make_report(j, strict=False)

    def test_future_after_deadline_evaluation_rejected(self):
        j = fixture()
        j["candidate_outcomes"][0]["alternative_first_evaluation_ms"] += 20 * 60_000
        with self.assertRaisesRegex(ValueError, "NOT_IN_WATCH_DEADLINE"):
            audit.make_report(j, strict=False)

    def test_setup_id_drift_is_never_silently_reclassified(self):
        j = fixture()
        j["setup_new_ids"] = 1
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_SETUP_ID_DRIFT"):
            audit.make_report(j, strict=False)

    def test_frozen_complete445_guard_wont_accept_small_fixture(self):
        with self.assertRaisesRegex(ValueError, "FROZEN_ORIGINAL_445_AB_SEMANTIC_DRIFT"):
            audit.make_report(fixture(), strict=True)


if __name__ == "__main__":
    unittest.main()
