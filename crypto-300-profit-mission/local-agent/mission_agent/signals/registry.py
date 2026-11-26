"""Solana wallet assignment. The live service uses the Frank-only default."""
import json
from pathlib import Path
import re


def valid_person_id(value):
    return isinstance(value, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,47}", value) is not None


def load(path, *, isolated=False):
    value = json.loads(Path(path).read_text())
    persons = [p for p in value["persons"] if p.get("enabled", False)]
    ids = [person["person_id"] for person in persons]
    if not isolated and ids != ["frank"]:
        raise ValueError("FRANK_ONLY_ENABLED_REQUIRED")
    if any(not valid_person_id(person) for person in ids) or len(set(ids)) != len(ids):
        raise ValueError("INVALID_ENABLED_PERSON")
    wallets = {}
    for person in persons:
        addresses = person["wallets"]
        if not addresses:
            raise ValueError("ENABLED_WALLET_REQUIRED")
        for wallet in addresses:
            if wallet["chain"] != "solana":
                raise ValueError("SOLANA_ONLY")
            address = wallet["address"]
            if not isinstance(address, str) or not address.strip():
                raise ValueError("INVALID_WALLET")
            if address in wallets:
                raise ValueError("DUPLICATE_WALLET")
            wallets[address] = person["person_id"]
    if not wallets:
        raise ValueError("ENABLED_WALLET_REQUIRED")
    return value, wallets
