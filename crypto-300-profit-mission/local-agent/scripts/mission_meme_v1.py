#!/usr/bin/env python3
"""Manual entry point for Mission Meme V1 review build.

No scheduler/LaunchAgent is created by this script.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

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
    p.add_argument("--interval", type=int, default=5)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    return p


def main():
    args = parser().parse_args()
    if args.command == "serve":
        serve(args.production_root, args.control_root, args.host, args.port)
        return
    service = MissionMemeService(
        production_root=args.production_root,
        control_root=args.control_root,
        policy_path=args.policy,
        live_delivery=args.live_delivery,
        gmail_config=args.gmail_config,
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
