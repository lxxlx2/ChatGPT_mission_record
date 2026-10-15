"""Create a pinned, disposable F01+C02+F02 working tree, never a deployment.

Default PLAN_ONLY. --assemble copies Git history into a new temporary
checkout and locally merges *exact* commits. It never mutates its source,
starts services, reads production SQLite or initiates chain RPC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

MAIN = "662ba4aceb9d53cb7a541ad3f251f9e12b8c09ea"
C02 = "8898134a8a302e1187138f7fb3da87a554567e6d"
F01 = "516e3335a134c608f477019b79027982f43af32a"
REVIEWED_PARENT = "d998fb5966fac2eee5dbeedca5f78126d1b51b6d"
MARKER = "frank-isolated-source-pins.json"
EVIDENCE_REF = "refs/remotes/origin/evidence/frank-ca-local"
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


def _run(*parts: str, cwd: Path | None = None) -> str:
    finished = subprocess.run(
        list(parts), cwd=cwd, check=True, capture_output=True, text=True,
        timeout=120,
    )
    return finished.stdout.strip()


def _root(repo: Path) -> Path:
    resolved = repo.resolve(strict=True)
    found = Path(_run("git", "-C", str(resolved),
                      "rev-parse", "--show-toplevel")).resolve(strict=True)
    if resolved != found:
        raise ValueError("FRANK_SOURCE_MUST_BE_GIT_ROOT")
    return found


def _destination(staging_root: Path, name: str, source: Path) -> Path:
    if (not isinstance(name, str) or not name.startswith("frank-joint-")
            or not re.fullmatch(r"[a-zA-Z0-9_-]{12,64}", name)):
        raise ValueError("FRANK_ISOLATED_NAME_REQUIRED")
    root = staging_root.resolve(strict=True)
    if not root.is_dir() or root == source or source in root.parents:
        raise ValueError("FRANK_ISOLATED_TEMP_ROOT_INVALID")
    target = root / name
    if target.exists() or target.is_symlink():
        raise ValueError("FRANK_ISOLATED_DESTINATION_ALREADY_EXISTS")
    if target == source or target in source.parents or source in target.parents:
        raise ValueError("FRANK_ISOLATED_SOURCE_OVERLAP")
    return target


def _pins(integration_sha: str) -> dict:
    if not isinstance(integration_sha, str) or not COMMIT.fullmatch(
            integration_sha):
        raise ValueError("FRANK_INTEGRATION_PIN_INVALID")
    return {"main": MAIN, "integrated_review_candidate": integration_sha,
            "c02": C02, "f01": F01, "approved_parent": REVIEWED_PARENT}


def _git_marker(destination: Path) -> Path:
    marker = destination / ".git" / MARKER
    if (not (destination / ".git").is_dir()
            or marker.is_symlink() or
            destination.is_symlink()):
        raise ValueError("FRANK_ISOLATED_MARKER_UNSAFE")
    return marker


def assemble(repo: Path, staging_root: Path, name: str,
             integration_sha: str) -> dict:
    source = _root(repo)
    dest = _destination(staging_root, name, source)
    pins = _pins(integration_sha)
    # No network, no mutation of source. Git clone copies only committed
    # files/objects and cannot drag the user's dirty worktree into staging.
    _run("git", "clone", "--no-local", "--no-checkout", "--quiet",
         str(source), str(dest))
    for sha in (MAIN, integration_sha, C02, F01, REVIEWED_PARENT):
        _run("git", "-C", str(dest), "fetch", "--no-tags", "--quiet",
             str(source), sha)
        if _run("git", "-C", str(dest), "rev-parse", "FETCH_HEAD") != sha:
            raise ValueError("FRANK_ISOLATED_FETCH_PIN_MISMATCH")
    # Existing evidence-backed regression requires this explicitly archived
    # branch. Carry the exact *local* object/ref, not a live Git/network fetch.
    evidence_head = _run("git", "-C", str(source), "rev-parse", EVIDENCE_REF)
    if not COMMIT.fullmatch(evidence_head):
        raise ValueError("FRANK_ISOLATED_EVIDENCE_REF_INVALID")
    _run("git", "-C", str(dest), "fetch", "--no-tags", "--quiet",
         str(source), f"{EVIDENCE_REF}:{EVIDENCE_REF}")
    if _run("git", "-C", str(dest), "rev-parse", EVIDENCE_REF) != evidence_head:
        raise ValueError("FRANK_ISOLATED_EVIDENCE_REF_MISMATCH")
    _run("git", "-C", str(dest), "merge-base", "--is-ancestor",
         REVIEWED_PARENT, integration_sha)
    _run("git", "-C", str(dest), "checkout", "--detach", "--quiet", MAIN)
    for sha in (integration_sha, C02, F01):
        _run("git", "-C", str(dest), "-c", "user.name=Frank Isolated QA",
             "-c", "user.email=frank-qa@example.invalid",
             "merge", "--no-ff", "--no-edit", "--no-gpg-sign", sha)
    head = _run("git", "-C", str(dest), "rev-parse", "HEAD")
    if not COMMIT.fullmatch(head):
        raise ValueError("FRANK_ISOLATED_BAD_MERGE_SHA")
    for sha in pins.values():
        _run("git", "-C", str(dest), "merge-base", "--is-ancestor", sha, head)
    if _run("git", "-C", str(dest), "status", "--porcelain"):
        raise ValueError("FRANK_ISOLATED_CHECKOUT_DIRTY")
    manifest = {
        "kind": "FRANK_F01_C02_F02_DISPOSABLE_GIT_WORKSPACE",
        "schema_version": 1,
        "pins": pins,
        "integrated_head": head,
        "historical_evidence_ref": EVIDENCE_REF,
        "historical_evidence_sha": evidence_head,
        "isolated_source_only": True,
        "network_invoked": False,
        "source_modified": False,
        "production_deployment": False,
        "real_rpc_invoked": False,
    }
    marker = _git_marker(dest)
    marker.write_text(json.dumps(manifest, sort_keys=True) + "\n",
                      encoding="utf-8")
    return {"status": "FRANK_ISOLATED_ASSEMBLED",
            "directory": str(dest), "integrated_head": head,
            "pins": pins, "manifest_sha256": hashlib.sha256(
                marker.read_bytes()).hexdigest(),
            "production_deployment": False}


def verify(staging_root: Path, name: str) -> dict:
    root = staging_root.resolve(strict=True)
    if not name.startswith("frank-joint-") or not re.fullmatch(
            r"[a-zA-Z0-9_-]{12,64}", name):
        raise ValueError("FRANK_ISOLATED_NAME_REQUIRED")
    target = root / name
    if target.is_symlink() or not target.is_dir() or target.parent != root:
        raise ValueError("FRANK_ISOLATED_DIRECTORY_MISSING")
    marker = _git_marker(target)
    if not marker.is_file():
        raise ValueError("FRANK_ISOLATED_MARKER_MISSING")
    saved = json.loads(marker.read_text(encoding="utf-8"))
    if (saved.get("kind") != "FRANK_F01_C02_F02_DISPOSABLE_GIT_WORKSPACE"
            or saved.get("schema_version") != 1
            or saved.get("pins") != _pins(
                saved.get("pins", {}).get("integrated_review_candidate"))):
        raise ValueError("FRANK_ISOLATED_MANIFEST_INVALID")
    if (saved.get("historical_evidence_ref") != EVIDENCE_REF
            or not COMMIT.fullmatch(
                saved.get("historical_evidence_sha", ""))):
        raise ValueError("FRANK_ISOLATED_EVIDENCE_MANIFEST_INVALID")
    if (_run("git", "-C", str(target), "rev-parse", EVIDENCE_REF)
            != saved["historical_evidence_sha"]):
        raise ValueError("FRANK_ISOLATED_EVIDENCE_REF_DRIFT")
    head = _run("git", "-C", str(target), "rev-parse", "HEAD")
    if head != saved["integrated_head"]:
        raise ValueError("FRANK_ISOLATED_HEAD_DRIFT")
    if _run("git", "-C", str(target), "status", "--porcelain"):
        raise ValueError("FRANK_ISOLATED_DIRTY")
    for sha in saved["pins"].values():
        _run("git", "-C", str(target), "merge-base", "--is-ancestor", sha, head)
    return {"status": "FRANK_ISOLATED_VERIFIED",
            "integrated_head": head,
            "pins": saved["pins"],
            "directory": str(target),
            "source_modified": False,
            "production_deployment": False}


def cleanup(staging_root: Path, name: str) -> dict:
    """Explicitly remove ONLY a clean, manifest-verified disposable checkout."""
    result = verify(staging_root, name)
    directory = Path(result["directory"])
    if directory.is_symlink() or directory.name != name:
        raise ValueError("FRANK_ISOLATED_CLEANUP_UNSAFE")
    shutil.rmtree(directory)
    return {"status": "FRANK_ISOLATED_REMOVED", "name": name,
            "source_modified": False, "production_deployment": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--assemble", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--cleanup", action="store_true")
    parser.add_argument("--source-repo", type=Path,
                        default=Path(__file__).resolve().parents[3])
    parser.add_argument("--staging-root", type=Path,
                        default=Path(os.getenv("RUNNER_TEMP",
                                             tempfile.gettempdir())))
    parser.add_argument("--name", default="frank-joint-manual-qa")
    parser.add_argument("--integration-sha")
    args = parser.parse_args(argv)
    if not args.assemble and not args.verify and not args.cleanup:
        print(json.dumps({
            "status": "PLAN_ONLY",
            "required_inputs": ["main", "C02", "F01", "integration SHA"],
            "pinned": {"main": MAIN, "c02": C02, "f01": F01,
                       "approved_parent": REVIEWED_PARENT},
            "workspace_created": False, "network_invoked": False,
            "production_deployment": False,
        }, sort_keys=True))
        return 0
    try:
        if args.verify:
            result = verify(args.staging_root, args.name)
        elif args.cleanup:
            result = cleanup(args.staging_root, args.name)
        else:
            result = assemble(args.source_repo, args.staging_root,
                              args.name, args.integration_sha)
    except (ValueError, OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, KeyError, TypeError,
            json.JSONDecodeError):
        print("FRANK_ISOLATED_WORKSPACE_REJECTED", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
