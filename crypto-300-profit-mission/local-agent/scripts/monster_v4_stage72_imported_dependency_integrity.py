#!/usr/bin/env python3
"""Stage72: pinned *actual imported modules* for Monster Stage65/66 offline replay.

Only fixed original historical research dependencies, not deployed live code.
Reject path shadowing, mutated imported source and alias-graph changes. This
cannot guarantee the integrity of the runtime interpreter or transitive stdlib
and is not a substitute for real publisher-SHA evidence.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parent
MANIFEST={
    "monster_v4_stage37_usdm_sixdate_full900_hourly_labels":
      "bd4e2e8f0c5e1f31f41066a2807018a976726979",
    "monster_v4_stage38_usdm_original_v4_1m_pilot":
      "a26445dbb72aea185940abab247376305ecb3244",
    "monster_v4_stage39_usdm_all900_sixday_original_1m":
      "1a6fee9f745acb64bd56a836d03d781000db03e4",
    "monster_v4_stage44_six_blind_hourly_truth":
      "8d6936a99f91ac10fc3d913f5a95eff2c460a131",
    "monster_v4_stage51_pinnedP1v03_full900_causal_minute_replay":
      "fdd0d0820afbed4fa7b400dc6a28660057e27024",
    "monster_v4_shadow":
      "bc958b3d90a8a52afa51515cb53f7e5fafaffaaa",
    "monster_v4_historical_replay":
      "95b2595281f5aa8675c6a95e542d40d36b78e847",
}


def git_blob(path):
    raw=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def assert_modules(modules, *, graph=()):
    """Must receive actual imported modules; do NOT check separate unattached files.

    graph contains (parent_module, attribute_name, child_module) triples:
    requiring imported dependencies actually point to these precise modules.
    """
    if not modules:
        raise ValueError("STAGE72_EMPTY_IMPORTED_DEPENDENCY_SET")
    results={}
    for name,module in modules.items():
        expected=MANIFEST.get(name)
        if not expected:
            raise ValueError("STAGE72_UNKNOWN_UNPINNED_MODULE "+name)
        origin=Path(getattr(module,"__file__","")).resolve()
        canonical=(SCRIPTS/(name+".py")).resolve()
        if origin != canonical or getattr(module,"__name__",None) not in (name,"scripts."+name):
            raise ValueError("STAGE72_IMPORTED_DEPENDENCY_PATH_SHADOWED "+name)
        if not canonical.is_file():
            raise ValueError("STAGE72_DEPENDENCY_FILE_MISSING "+name)
        actual=git_blob(canonical)
        if actual != expected:
            raise ValueError("STAGE72_MUTATED_IMPORTED_DEPENDENCY_SOURCE "+name+" "+actual)
        results[name]={"original_git_blob":actual,"loaded_path":str(canonical)}
    for parent,attribute,child in graph:
        if getattr(parent,attribute,None) is not child:
            raise ValueError("STAGE72_IMPORTED_DEPENDENCY_ALIAS_GRAPH_CHANGED "+attribute)
    return results


def assert_integrity_stage65(stage44):
    return assert_modules({
        "monster_v4_stage44_six_blind_hourly_truth":stage44,
        "monster_v4_stage37_usdm_sixdate_full900_hourly_labels":stage44.archive,
    },graph=[(stage44,"archive",stage44.archive)])


def assert_integrity_stage66(stage38,stage39,stage51,stage44):
    return assert_modules({
        "monster_v4_stage37_usdm_sixdate_full900_hourly_labels":stage44.archive,
        "monster_v4_stage38_usdm_original_v4_1m_pilot":stage38,
        "monster_v4_stage39_usdm_all900_sixday_original_1m":stage39,
        "monster_v4_stage44_six_blind_hourly_truth":stage44,
        "monster_v4_stage51_pinnedP1v03_full900_causal_minute_replay":stage51,
        "monster_v4_shadow":stage38.production,
        "monster_v4_historical_replay":stage38.replay,
    },graph=[
        (stage44,"archive",stage44.archive),
        (stage39,"original",stage38),
        (stage51,"src",stage38),
        (stage51,"originalV4",stage39),
        (stage38.replay,"live",stage38.production),
    ])
