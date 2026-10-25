"""D2-A proposed physical HTTPS source identity, NOT an executable source.

The proposal is an immutable identity-only data value. Any Python caller may
construct a plausible proposal: shape validation NEVER authenticates D2/D3,
and no factory, socket, signer, dispatcher, grant or clock is exposed here.
The ONE existing coordinator deliberately refuses every such proposal.
"""
from __future__ import annotations

from dataclasses import dataclass

from f0_l2_d1_preflight import ENDPOINT, HEX40, HEX64, RPC


@dataclass(frozen=True, slots=True)
class UnreleasedPhysicalHTTPSProposal:
    """Exact fixed-endpoint descriptor; contains NO executable transport."""

    reviewed_sha: str
    source_manifest_sha256: str
    permit_sha256: str
    candidate_intent_sha256: str
    endpoint: str = ENDPOINT
    chain_id: int = 56
    methods: tuple[str, ...] = RPC
    max_inflight: int = 3

    def __post_init__(self):
        if (type(self.reviewed_sha) is not str
                or not HEX40.fullmatch(self.reviewed_sha)
                or type(self.source_manifest_sha256) is not str
                or not HEX64.fullmatch(self.source_manifest_sha256)
                or type(self.permit_sha256) is not str
                or not HEX64.fullmatch(self.permit_sha256)
                or type(self.candidate_intent_sha256) is not str
                or not HEX64.fullmatch(self.candidate_intent_sha256)
                or type(self.endpoint) is not str
                or self.endpoint != ENDPOINT
                or type(self.chain_id) is not int or self.chain_id != 56
                or type(self.methods) is not tuple or self.methods != RPC
                or type(self.max_inflight) is not int
                or self.max_inflight != 3):
            raise ValueError("D2A_PHYSICAL_PROPOSAL_SCOPE_INVALID")

    def to_diagnostic(self):
        """Identity and release state only, no private keys or approval."""
        return {
            "reviewed_sha": self.reviewed_sha,
            "source_manifest_sha256": self.source_manifest_sha256,
            "permit_sha256": self.permit_sha256,
            "candidate_intent_sha256": self.candidate_intent_sha256,
            "endpoint": self.endpoint,
            "chain_id": self.chain_id,
            "methods": list(self.methods),
            "max_inflight": self.max_inflight,
            "trusted_d2": False,
            "trusted_d3": False,
            "production_marker_consumed": False,
            "physical_source_constructed": False,
            "network_requests": 0,
            "decision": "D1_BLOCKED_AUTHORITY",
            "production": "PRODUCTION_NO_GO",
        }


def send_live(*_args, **_kwargs):
    """No alternative physical transport entry or user-supplied factory."""
    raise ValueError("D2A_PHYSICAL_SOURCE_NOT_RELEASED")
