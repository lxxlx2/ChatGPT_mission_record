"""Frozen policy identity; no market, social or GPT dependency."""
import hashlib,json
from pathlib import Path

POLICY_SHA256='83ebab1fbb8ec7e03950626137c5597a38b81b8a4085d9150610018cc78cedab'
USDC='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'

# Upper bounds for delivering a stage from its original on-chain buy. The
# accumulation window and the multiple-signal stale boundary are frozen in V1.
BUY_DELIVERY_MAX_AGE_SECONDS = {
    "FRANK_ACCUMULATION_SIGNAL": 3600,
    "FRANK_MULTIPLE_SIGNAL": 10800,
}

def load_policy(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=POLICY_SHA256:raise ValueError('FROZEN_POLICY_DRIFT')
    value=json.loads(raw)
    if value['policy_id']!='FRANK_LOCAL_SIGNAL_V1' or not value['frozen'] or not value['enabled']:raise ValueError('POLICY_NOT_ACTIVE')
    return value
