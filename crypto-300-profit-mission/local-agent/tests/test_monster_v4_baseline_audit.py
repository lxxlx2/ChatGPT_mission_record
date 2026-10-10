"""Research-only data audit regressions; no online sources or runtime writes."""
import copy
import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
SCRIPT = HERE / "scripts/monster_v4_baseline_audit.py"
spec = importlib.util.spec_from_file_location("monster_v4_baseline_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class TestMonsterV4ResearchBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train = audit.read_json(HERE, "docs/results/monster_d1_v3_train.json")
        cls.validation = audit.read_json(HERE, "docs/results/monster_d1_v3_validation.json")
        cls.winner = audit.read_json(HERE, "config/monster_d1_v3_winner.json")
        cls.gate = audit.read_json(HERE, "config/monster_d1_v3_validation_gate.json")

    def test_reproduced_historical_baseline(self):
        result = audit.run(HERE)
        self.assertEqual(result["train_configs"], 72)
        self.assertEqual(result["train_ceiling_pass_configs"], 48)
        self.assertEqual(result["train_5x_pre_hits_ge_19_configs"], 24)
        self.assertEqual(result["train_config_5x_hits_histogram"], {
            "13": 8, "14": 8, "15": 24, "16": 4, "17": 4, "19": 24
        })
        self.assertEqual(result["frozen_winner"]["id"], "V3-062")
        self.assertEqual(result["frozen_winner"]["entity_5x"], {"events": 20, "prehit": 19})
        self.assertEqual(result["frozen_winner"]["entity_10x"], {"events": 7, "prehit": 6})
        self.assertEqual(result["exposed_validation"]["status"], "INSUFFICIENT_DATA")
        self.assertFalse(result["exposed_validation"]["ceiling_pass"])
        self.assertEqual((result["exposed_validation"]["median_entities_day"],
                          result["exposed_validation"]["p95_entities_day"]), (101.0, 152.0))
        self.assertEqual(result["exposed_validation"]["entity_5x_prehit"], 1)
        self.assertFalse(result["v4_historical_replay_completed"])
        self.assertFalse(result["v4_live_notification_authorized"])

    def test_mode_aggregates_do_not_disguise_train_as_holdout(self):
        groups = audit.run(HERE)["train_group_aggregate"]
        self.assertEqual(groups["QUALITY_OR_RS"]["train_ceiling_pass"], 12)
        self.assertEqual(groups["QUALITY"]["train_ceiling_pass"], 12)
        self.assertEqual(groups["QUALITY_AND_RS_OR_DUAL"]["train_ceiling_pass"], 24)
        self.assertEqual(groups["QUALITY_OR_RS"]["mean_5x_pre_hits_out_of_20"], 19.0)
        self.assertEqual(groups["QUALITY"]["mean_5x_pre_hits_out_of_20"], 15.0)
        self.assertEqual(groups["QUALITY_AND_RS_OR_DUAL"]["mean_5x_pre_hits_out_of_20"], 14.5)

    def test_duplicate_configuration_fails(self):
        mutated = copy.deepcopy(self.train)
        mutated[1]["config_id"] = mutated[0]["config_id"]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_TRAIN_CONFIG_ID"):
            audit.analyze(mutated, self.validation, self.winner, self.gate)

    def test_cherry_picked_winner_is_rejected(self):
        winner = copy.deepcopy(self.winner)
        winner["winner"]["entity"]["5"]["prehit"] = 20
        with self.assertRaisesRegex(ValueError, "FROZEN_TRAIN_WINNER_MISMATCH"):
            audit.analyze(self.train, self.validation, winner, self.gate)

    def test_changed_validation_winner_is_rejected(self):
        validation = copy.deepcopy(self.validation)
        validation["result"]["config_id"] = "V3-001"
        with self.assertRaisesRegex(ValueError, "VALIDATION_WINNER_CHANGED"):
            audit.analyze(self.train, validation, self.winner, self.gate)

    def test_unapproved_validation_gate_mutation_is_rejected(self):
        gate = copy.deepcopy(self.gate)
        gate["validation_ceiling_pass"] = True
        with self.assertRaisesRegex(ValueError, "VALIDATION_GATE_MISMATCH"):
            audit.analyze(self.train, self.validation, self.winner, gate)


if __name__ == "__main__":
    unittest.main()
