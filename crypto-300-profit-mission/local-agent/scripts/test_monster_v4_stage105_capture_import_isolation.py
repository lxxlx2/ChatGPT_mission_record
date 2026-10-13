#!/usr/bin/env python3
"""No-network NEW-PROCESS proof: capture loader does not execute historical models.

The malicious fixture makes an explicit filesystem marker at import time.
The 3 production capture/gate modules must not import Stage91/38/80,
Shadow or historical_replay, even when those imports have malicious effects.
"""
from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

SRC=Path(__file__).resolve().parent
PRODUCTION=(
    "monster_v4_stage105_capture_universe_core.py",
    "monster_v4_stage97_one_shot_usdm_capture.py",
    "monster_v4_stage99_mac_launchd_one_shot.py",
    "monster_v4_stage102_claude_chat_review_gate.py",
)
NOT_CAPTURE_DEPENDENCIES=(
    "monster_v4_stage91_forward_oos_replay_gate",
    "monster_v4_stage38_usdm_original_v4_1m_pilot",
    "monster_v4_stage80_dual_entry_core",
    "monster_v4_shadow",
    "monster_v4_historical_replay",
)


class FreshInterpreterImports(unittest.TestCase):
    def test_malicious_historical_module_never_imports(self):
        with tempfile.TemporaryDirectory(prefix="monster-stage105-import-") as td:
            root=Path(td)
            for file in PRODUCTION:
                shutil.copyfile(SRC/file,root/file)
            marker=root/"UNREVIEWED_HISTORICAL_IMPORT_EXECUTED"
            # A module could run arbitrary top-level side effects when imported.
            for name in NOT_CAPTURE_DEPENDENCIES:
                (root/(name+".py")).write_text(
                    "from pathlib import Path\n"
                    f"Path({str(marker)!r}).write_text({name!r})\n"
                    "raise RuntimeError('UNREVIEWED_DEPENDENCY_WAS_EXECUTED')\n")
            code=(
                "import sys,json\n"
                "import monster_v4_stage99_mac_launchd_one_shot as x\n"
                "import monster_v4_stage102_claude_chat_review_gate as gate\n"
                "import monster_v4_stage97_one_shot_usdm_capture as p\n"
                f"disallowed={list(NOT_CAPTURE_DEPENDENCIES)!r}\n"
                "assert not any(n in sys.modules for n in disallowed)\n"
                "assert len(x.stage91.WINDOWS)==3\n"
                "assert len(gate.REQUIRED_SOURCES)>=8\n"
                "assert p.freeze is x.stage91\n"
                "print('STAGE105_FRESH_PROCESS_NO_HISTORICAL_IMPORT_PASS')\n"
            )
            done=subprocess.run([sys.executable,"-c",code],cwd=root,
                capture_output=True,text=True,timeout=18,check=False)
            self.assertEqual(done.returncode,0,done.stderr)
            self.assertIn("NO_HISTORICAL_IMPORT_PASS",done.stdout)
            self.assertFalse(marker.exists())


if __name__=="__main__":
    unittest.main(verbosity=2)
