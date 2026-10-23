#!/usr/bin/env python3
"""D1 offline whole-F0 source and Ed25519 distribution inventory.

This produces INDEPENDENTLY INSPECTABLE EVIDENCE, not a trusted manifest:
the runtime operator must not be allowed to nominate their own expected hash
for a live authorization. No grants, network, source mutation or live runner.
"""
from __future__ import annotations
import base64
from hashlib import sha256
from importlib import metadata
from pathlib import Path
import os
import re
import sys
from f0_l2_d1_preflight import _git, verify_fixed_checkout_offline
from f0_l2_d1_grant import require_ed25519_backend

SOURCE_PREFIX="crypto-300-profit-mission/bsc-forward-follow-model/f0/"
HEX40=re.compile(r"[0-9a-f]{40}\Z")


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def tracked_f0_source_manifest_offline(root: Path, exact_sha: str):
    """Enumerate *every* tracked F0 file from the actual Git tree at SHA.

    This is not a hand-selected module list. Compare blob bytes, working tree,
    and paths; symlink entries or an empty subtree fail closed.
    """
    require(isinstance(root,Path) and root.is_absolute() and root.is_dir()
            and not root.is_symlink() and type(exact_sha) is str and
            bool(HEX40.fullmatch(exact_sha)), "D1_INVENTORY_ARGS_INVALID")
    raw=_git(root,"ls-tree","-rz","--full-tree",exact_sha,"--",SOURCE_PREFIX)
    manifest={}
    for entry in raw.split(b"\x00"):
        if not entry:
            continue
        try:
            info,p=entry.split(b"\t",1)
            mode,kind,blob=info.decode("ascii").split(" ")
            path=p.decode("utf-8")
        except (ValueError,UnicodeDecodeError) as exc:
            raise ValueError("D1_INVENTORY_GIT_TREE_INVALID") from exc
        require(mode=="100644" or mode=="100755",
                "D1_INVENTORY_TRACKED_SYMLINK_OR_SUBMODULE")
        require(kind=="blob" and path.startswith(SOURCE_PREFIX)
                and ".." not in path.split("/") and path not in manifest,
                "D1_INVENTORY_GIT_TREE_INVALID")
        content=_git(root,"show",exact_sha+":"+path)
        manifest[path]=sha256(content).hexdigest()
    require(len(manifest)>0,"D1_INVENTORY_EMPTY_TREE")
    verified=verify_fixed_checkout_offline(root,exact_sha,manifest)
    inventory=b"".join((key+" "+manifest[key]+"\n").encode("utf-8")
                       for key in sorted(manifest))
    return {
        "status":"OFFLINE_INVENTORY_NOT_INDEPENDENT_ATTESTATION",
        "source_commit_sha":exact_sha,
        "all_tracked_f0_files_checked":verified["verified_files"],
        "tracked_source_manifest_sha256":sha256(inventory).hexdigest(),
        "reviewed_path_digests":dict(sorted(manifest.items())),
    }


def installed_ed25519_distribution_inventory_offline():
    """Check installed cryptography wheel RECORD hashes, reporting gaps.

    RECORD and installed bytes are from the same local installation and can
    both be replaced by its operator. D2 needs separately audited wheel hashes
    and runtime dependency closure; this function MUST NOT authorize a run.
    """
    require_ed25519_backend()
    distribution=metadata.distribution("cryptography")
    files=distribution.files
    require(files is not None and len(files)>0,
            "D1_INVENTORY_DISTRIBUTION_FILE_LIST_ABSENT")
    hashes=[]
    no_record_hash=[]
    total=0
    for relative in sorted(files,key=str):
        relative_name=str(relative)
        path=Path(distribution.locate_file(relative))
        require(not path.is_symlink() and path.is_file(),
                "D1_INVENTORY_WHEEL_FILE_MISSING_OR_LINKED")
        raw=path.read_bytes()
        total+=len(raw)
        digest=sha256(raw).digest()
        expected=relative.hash
        if expected is None:
            no_record_hash.append(relative_name)
        else:
            require(expected.mode=="sha256" and
                    base64.urlsafe_b64decode(
                        expected.value+"="*((-len(expected.value))%4)
                    )==digest,"D1_INVENTORY_WHEEL_RECORD_MISMATCH")
        hashes.append(relative_name+" "+sha256(raw).hexdigest()+"\n")
    # The wheel RECORD itself normally lacks a RECORD digest: report as
    # uncovered, never pretend the distribution is externally attested.
    inventory="".join(hashes).encode()
    require(total>0,"D1_INVENTORY_DISTRIBUTION_EMPTY")
    return {
        "status":"LOCAL_WHEEL_RECORD_MATCH_NOT_INDEPENDENT_ATTESTATION",
        "distribution":"cryptography",
        "distribution_version":distribution.version,
        "files_read":len(files),
        "total_installed_bytes_checked":total,
        "wheel_file_manifest_sha256":sha256(inventory).hexdigest(),
        "record_entries_without_hash":no_record_hash,
        "python_version":sys.version.split()[0],
        "python_executable_sha256":sha256(Path(sys.executable).read_bytes()).hexdigest(),
        "interpreter_and_stdlib_externally_attested":False,
        "complete_dynamic_import_closure_attested":False,
        "production_trust_roots_enrolled":False,
    }
