#!/usr/bin/env python3
"""Historical compatibility tombstone: local Claude CLI integration withdrawn.

Do not import as review authority. Real independent review is via Claude chat,
and approval is separately checked with Stage102/103 gate.
"""
from __future__ import annotations
import argparse

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("selftest","review-install","verify"))
    args=p.parse_args()
    if args.action=="selftest":
        assert "claude" not in globals()
        assert "review_then_install" not in globals()
        print("STAGE103_WITHDRAWN_CLAUDE_CLI_NO_RUNNABLE_INSTALL_PATH_PASS")
    else:
        p.error("WITHDRAWN: user uses Claude CHAT; no Claude CLI review or auto-install")

if __name__=="__main__":
    main()
