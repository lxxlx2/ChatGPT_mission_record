"""Run four targeted Frank P4 QA regressions WITHOUT installing pytest.

This invokes four existing fixture-style tests with temporary SQLite files,
using only standard-library pathlib/tempfile/importlib and the audited
mission_agent pure analysis code. It makes no localhost/RPC/network requests.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile


LOCAL_AGENT = Path(__file__).resolve().parents[1]
TEST = LOCAL_AGENT / "tests" / "test_frank_option3_p4_qa.py"
sys.path.insert(0, str(LOCAL_AGENT))
sys.path.insert(0, str(LOCAL_AGENT / "scripts"))


class ScopedPatch:
    def __init__(self):
        self._restore = []

    def setattr(self, obj, name, value):
        existing = getattr(obj, name)
        self._restore.append((obj, name, existing))
        setattr(obj, name, value)

    def undo(self):
        for obj, name, previous in reversed(self._restore):
            setattr(obj, name, previous)


def main():
    spec = importlib.util.spec_from_file_location("frank_p4_qa_test", TEST)
    if spec is None or spec.loader is None:
        raise RuntimeError("QA_TEST_FILE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    passed = 0
    for name, needs_patch in (
        ("test_exact_trigger_join_rejects_old_same_mint_and_wrong_episode", True),
        ("test_source_timestamp_change_is_not_silent_causal_pass", True),
        ("test_signal_first_finds_verified_source_signal_before_same_episode_sale_only", False),
    ):
        patch = ScopedPatch()
        try:
            with tempfile.TemporaryDirectory(prefix="frank-p4-qa-") as directory:
                if needs_patch:
                    getattr(module, name)(Path(directory), patch)
                else:
                    getattr(module, name)(Path(directory))
            passed += 1
            print(name + ": PASS", flush=True)
        finally:
            patch.undo()
    module.test_p4_historical_fake_notices_separate_unresolved_sell_from_index_exit()
    passed += 1
    print("test_p4_historical_fake_notices_separate_unresolved_sell_from_index_exit: PASS",
          flush=True)
    print("FRANK_P4_STDLIB_SELFTEST:", str(passed) + "/4 PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
