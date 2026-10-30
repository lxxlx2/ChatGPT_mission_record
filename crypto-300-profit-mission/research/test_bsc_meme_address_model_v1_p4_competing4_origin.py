"""Source-pinned P4 competing-pool factory origin and liquidity negative controls."""
import copy
import unittest
from bsc_meme_address_model_v1_p4_competing4_origin import ROOT, load, validate

class P4Competing4OriginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=load(ROOT)

    def test_four_creation_events_and_initial_mint(self):
        x=validate(self.docs)
        s=x["summary"]
        self.assertEqual((s["preexisting_competitors_total"],s["fully_creation_checked"],
                          s["remaining_untested_competitors"]), (17,4,13))
        self.assertEqual((s["creation_positive_liquidity"],s["creation_zero_active_liquidity"],
                          s["creation_block_with_swap"]), (3,1,2))
        self.assertEqual([r["creation_block"] for r in x["rows"]],
                         [116207845,116156658,115919188,112642885])
        self.assertEqual(len(x["source_manifest"]),6)

    def test_zero_active_at_mint_not_marketed_as_tradable(self):
        x=validate(self.docs)
        negative=x["rows"][2]
        self.assertEqual(negative["token"],"牛来")
        self.assertEqual(negative["venue"],"V3")
        self.assertEqual(negative["fee_pips"],10000)
        self.assertEqual(negative["creation_state"],"V3_CREATION_MINT_ZERO_ACTIVE_LIQUIDITY")
        self.assertEqual(negative["creation_liquidity_or_reserves_raw"],"0")
        self.assertEqual(x["summary"]["confirmed_global_first_tradable"],0)
        self.assertEqual(x["summary"]["confirmed_followable_profitable_misses"],0)
        self.assertEqual(x["summary"]["production"],"NO_GO")
        self.assertTrue(all(y["qualified_wallet_miss"]=="UNRESOLVED"
                            and y["follower_PnL"]=="UNRESOLVED" for y in x["rows"]))

    def test_pool_creation_wrong_tx_rejected(self):
        d=copy.deepcopy(self.docs)
        d[2]["records"][0]["mint_event_at_creation"]["transactionHash"]="0x"+"f"*64
        with self.assertRaises(ValueError):
            validate(d)

    def test_wrong_v3_liquidity_flag_rejected(self):
        d=copy.deepcopy(self.docs)
        d[3]["records"][0]["raw_creation_state"]="0x"+"1".rjust(64,"0")
        with self.assertRaises(ValueError):
            validate(d)

    def test_mismatched_factory_creation_rejected(self):
        d=copy.deepcopy(self.docs)
        d[2]["records"][1]["created_event"]["topics"][3]="0x"+"0"*64
        with self.assertRaises(ValueError):
            validate(d)

    def test_fake_swap_rejected(self):
        d=copy.deepcopy(self.docs)
        d[4]["records"][0]["events"][0]["address"]="0x"+"f"*40
        with self.assertRaises(ValueError):
            validate(d)

if __name__=="__main__":
    unittest.main()
