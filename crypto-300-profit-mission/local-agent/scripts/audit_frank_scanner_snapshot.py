"""Reconcile a standalone Scanner backup and a supplied finalized wallet window."""
import argparse
import json
from pathlib import Path

from mission_agent.frank.archive import publish
from mission_agent.signals.reconciliation import ReconciliationError, reconcile_snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--reference-sha256", required=True)
    parser.add_argument("--scanner-source-id", required=True)
    parser.add_argument("--private-report", type=Path, help="New mode-0600 file with per-signature evidence")
    args = parser.parse_args(argv)
    try:
        result = reconcile_snapshot(args.snapshot, args.snapshot_sha256, args.reference,
                                    args.reference_sha256, scanner_source_id=args.scanner_source_id)
    except ReconciliationError as error:
        print(json.dumps({"status": "INVALID_INPUT", "reason": str(error)}))
        return 2
    if args.private_report is not None:
        try:
            publish(args.private_report, json.dumps(result, indent=2, sort_keys=True).encode() + b"\n")
        except OSError:
            print(json.dumps({"status": "PRIVATE_REPORT_NOT_PUBLISHED"}))
            return 2
    summary = {key: value for key, value in result.items() if key not in {"rows", "unexpected_signatures"}}
    print(json.dumps(summary, sort_keys=True))
    return 0 if result["status"] == "MATCHED_WITHIN_SUPPLIED_WINDOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
