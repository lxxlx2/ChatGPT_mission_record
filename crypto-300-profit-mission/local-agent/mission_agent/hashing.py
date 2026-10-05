"""MISSION_JSON_V1: NFC UTF-8, sorted keys, integers/decimal strings, no floats."""
import hashlib
import json
import unicodedata


def normalize(value):
    if value is None or type(value) in (bool, int):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize(x) for x in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON keys must be strings")
            key = normalize(key)
            if key in result:
                raise ValueError("normalized duplicate key")
            result[key] = normalize(item)
        return result
    raise ValueError("only JSON integers/decimal strings, no float or non-JSON value")


def canonical(value):
    return json.dumps(normalize(value), sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        key = normalize(key)
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def loads(data):
    return normalize(json.loads(data, object_pairs_hook=_pairs,
                               parse_constant=lambda x: (_ for _ in ()).throw(ValueError("invalid constant"))))


def seal(envelope):
    if "payload_sha256" in envelope:
        raise ValueError("already sealed")
    return {**envelope, "payload_sha256": digest(envelope)}


def verify(envelope):
    if not isinstance(envelope, dict) or "payload_sha256" not in envelope:
        raise ValueError("missing hash")
    body = {k: v for k, v in envelope.items() if k != "payload_sha256"}
    if digest(body) != envelope["payload_sha256"]:
        raise ValueError("hash mismatch")
