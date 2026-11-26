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
    parser.add_argument("--buy-qualifications", type=Path, help="Optional pinned offline buy qualification file")
    parser.add_argument("--buy-qualifications-sha256")
    parser.add_argument("--buy-qualification-as-of", type=int, help="Qualification observation cutoff in Unix seconds")
    parser.add_argument("--buy-archive-root", type=Path, help="Trusted absolute archive directory for legacy buys")
    parser.add_argument("--buy-legacy-archive-root", type=Path, help="Optional second trusted archive directory")
    args = parser.parse_args(argv)
    buy_options = (args.buy_qualifications, args.buy_qualifications_sha256, args.buy_qualification_as_of)
    if any(x is not None for x in buy_options) and not all(x is not None for x in buy_options):
        parser.error("supply all three buy qualification options or none")
    if ((args.buy_archive_root is not None and (None in buy_options or not args.buy_archive_root.is_absolute()))
            or (args.buy_legacy_archive_root is not None
                and (args.buy_archive_root is None or not args.buy_legacy_archive_root.is_absolute()))):
        parser.error("supply buy qualification inputs and absolute archive paths, with the primary archive first")
    try:
        result = reconcile_snapshot(args.snapshot, args.snapshot_sha256, args.reference,
                                    args.reference_sha256, scanner_source_id=args.scanner_source_id,
                                    buy_qualifications=buy_options if args.buy_qualifications is not None else None,
                                    buy_archive_root=args.buy_archive_root, buy_legacy_archive_root=args.buy_legacy_archive_root)
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
