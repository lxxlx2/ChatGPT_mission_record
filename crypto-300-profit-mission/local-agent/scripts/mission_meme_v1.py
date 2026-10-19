#!/usr/bin/env python3
"""Manual entry point for Mission Meme V1 review build.

No scheduler/LaunchAgent is created by this script.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

from mission_agent.mission_control.release_approval import verify_signed_release_approval
from mission_agent.mission_control.server import serve
from mission_agent.mission_control.service import MissionMemeService


def parser():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["cycle", "loop", "serve"])
    p.add_argument("--production-root", type=Path, required=True)
    p.add_argument("--control-root", type=Path, required=True)
    p.add_argument(
        "--policy",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "config" / "follow_policy_v1.review.json",
    )
    p.add_argument("--gmail-config", type=Path)
    p.add_argument("--live-delivery", action="store_true")
    p.add_argument(
        "--approved-policy-sha256",
        help="Required in addition to FROZEN_APPROVED + live_delivery_approved + --live-delivery. Must exactly match the loaded policy bytes.",
    )
    p.add_argument("--approval-record", type=Path)
    p.add_argument("--approval-signature", type=Path)
    p.add_argument("--interval", type=int, default=5)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    return p


def main():
    args = parser().parse_args()
    if args.command == "serve":
        serve(args.production_root, args.control_root, args.host, args.port)
        return
    expires_at = None
    if args.live_delivery:
        if not args.approval_record or not args.approval_signature:
            raise SystemExit("SIGNED_USER_APPROVAL_REQUIRED_FOR_LIVE_DELIVERY")
        # A release manifest must bind to actual checked-out source, rather
        # than a caller-supplied or self-generated commit SHA.
        checkout = Path(__file__).resolve().parents[1]
        code_sha = subprocess.check_output(
            ["git", "-C", str(checkout), "rev-parse", "--verify", "HEAD"],
            text=True, timeout=5,
        ).strip()
        dirty = subprocess.check_output(
            ["git", "-C", str(checkout), "status", "--porcelain", "--untracked-files=no"],
            text=True, timeout=5,
        )
        if dirty:
            raise SystemExit("LIVE_RELEASE_WORKTREE_DIRTY")
        proof = verify_signed_release_approval(
            record_path=args.approval_record,
            signature_path=args.approval_signature,
            policy_path=args.policy,
            externally_approved_sha=args.approved_policy_sha256,
            code_commit_sha=code_sha,
        )
        expires_at = datetime.fromisoformat(proof["expires_at"]).timestamp()
    service = MissionMemeService(
        production_root=args.production_root,
        control_root=args.control_root,
        policy_path=args.policy,
        live_delivery=args.live_delivery,
        gmail_config=args.gmail_config,
        approved_policy_sha256=args.approved_policy_sha256,
        approval_expires_at=expires_at,
    )
    try:
        if args.command == "cycle":
            print(json.dumps(service.cycle(), indent=2, ensure_ascii=False, default=str))
        else:
            service.loop(args.interval)
    finally:
        service.close()


if __name__ == "__main__":
    main()
