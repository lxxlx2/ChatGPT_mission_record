"""D2/D3 proposed signing format must NOT confer authorization or reuse TEST."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import socket
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import f0_l2_d2_production_signature_spec as spec
from f0_l2_d1_grant import SCHEMA as TEST_D1_SCHEMA, PINNED_LIVE_TRUST_ROOTS
from f0_l2_d2b_signed_execution_offline import (
    D3_SIGNING_DOMAIN as TEST_D3_DOMAIN,
    PRODUCTION_D2_D3_TRUST_ROOTS,
)


class ProposedProductionSignatureBytesTests(unittest.TestCase):
    def setUp(self):
        self.common = {
            "grant_id": "test-grant-only-0001",
            "permit_sha256": "a" * 64,
            "reviewed_sha": "b" * 40,
            "source_manifest_sha256": "c" * 64,
        }
        self.d3 = {**self.common, "run_id": "test-run-only-0002",
                   "intent_sha256": "d" * 64}

    @staticmethod
    def unpack_without_using_source_encoder(raw):
        """Decode independently of the production proposal function."""
        offset = 0
        def field():
            nonlocal offset
            n = struct.unpack(">I", raw[offset:offset + 4])[0]
            offset += 4
            b = raw[offset:offset + n]
            offset += n
            return b
        domain = field()
        count = struct.unpack(">I", raw[offset:offset + 4])[0]
        offset += 4
        result = []
        for _ in range(count):
            result.append((field().decode("ascii"), field()))
        if offset != len(raw):
            raise AssertionError("TRAILING_ENCODING_BYTES")
        return domain, result

    def test_d2_user_bytes_have_exact_source_and_scope_fields(self):
        raw = spec.proposed_d2_signing_bytes(role="user", **self.common)
        domain, rows = self.unpack_without_using_source_encoder(raw)
        self.assertEqual(domain, spec.D2_PROPOSED_DOMAIN)
        fields = dict(rows)
        self.assertEqual(len(rows), 8)
        self.assertEqual(fields["role"], b"user")
        self.assertEqual(fields["grant_id"], self.common["grant_id"].encode())
        self.assertEqual(fields["permit_raw_sha256"], b"a" * 64)
        self.assertEqual(fields["reviewed_git_sha"], b"b" * 40)
        self.assertEqual(fields["source_manifest_sha256"], b"c" * 64)
        self.assertEqual(fields["endpoint"], spec.ENDPOINT.encode())
        self.assertEqual(fields["chain_id"], b"56")

    def test_d2_user_and_reviewer_bytes_separately_bound(self):
        u = spec.proposed_d2_signing_bytes(role="user", **self.common)
        r = spec.proposed_d2_signing_bytes(role="reviewer", **self.common)
        self.assertNotEqual(u, r)
        self.assertNotEqual(sha256(u).hexdigest(), sha256(r).hexdigest())
        self.assertEqual(dict(self.unpack_without_using_source_encoder(r)[1])
                         ["role"], b"reviewer")

    def test_d3_operator_binds_exact_intent_run_and_d2(self):
        raw = spec.proposed_d3_signing_bytes(**self.d3)
        domain, rows = self.unpack_without_using_source_encoder(raw)
        fields = dict(rows)
        self.assertEqual(domain, spec.D3_PROPOSED_DOMAIN)
        self.assertEqual(len(rows), 9)
        self.assertEqual(fields["role"], b"operator")
        self.assertEqual(fields["intent_raw_sha256"], b"d" * 64)
        self.assertEqual(fields["permit_raw_sha256"], b"a" * 64)
        self.assertEqual(fields["run_id"], self.d3["run_id"].encode())

    def test_domain_separate_from_all_existing_test_signatures(self):
        self.assertNotEqual(spec.D2_PROPOSED_DOMAIN,
                            TEST_D1_SCHEMA.encode())
        self.assertNotEqual(spec.D3_PROPOSED_DOMAIN,
                            TEST_D3_DOMAIN.encode())
        self.assertNotEqual(spec.D2_PROPOSED_DOMAIN,
                            spec.D3_PROPOSED_DOMAIN)
        self.assertNotIn(b"TEST-ONLY", spec.D2_PROPOSED_DOMAIN)
        self.assertIn(b"PROPOSAL", spec.D2_PROPOSED_DOMAIN)
        self.assertIn(b"PROPOSAL", spec.D3_PROPOSED_DOMAIN)

    def test_one_field_change_alters_proposed_message(self):
        baseline = spec.proposed_d3_signing_bytes(**self.d3)
        for key, different in (
                ("run_id", "test-run-only-0003"),
                ("grant_id", "test-grant-only-0009"),
                ("intent_sha256", "e" * 64),
                ("permit_sha256", "f" * 64),
                ("reviewed_sha", "0" * 40),
                ("source_manifest_sha256", "1" * 64)):
            altered = dict(self.d3, **{key: different})
            self.assertNotEqual(baseline,
                                spec.proposed_d3_signing_bytes(**altered))

    def test_malformed_digest_or_source_sha_rejected(self):
        for key, value in (
                ("permit_sha256", "A" * 64),
                ("permit_sha256", "a" * 63),
                ("reviewed_sha", "b" * 41),
                ("source_manifest_sha256", "g" * 64)):
            changed = dict(self.common, **{key: value})
            with self.assertRaises(ValueError):
                spec.proposed_d2_signing_bytes(role="user", **changed)

    def test_invalid_roles_and_identifier_shape_rejected(self):
        for role in ("operator", "USER", "", None):
            with self.assertRaisesRegex(ValueError, "D2_SPEC_ROLE_INVALID"):
                spec.proposed_d2_signing_bytes(role=role, **self.common)
        for ident in ("short", "../attack-run", "x" * 81, 3, ""):
            with self.assertRaisesRegex(ValueError, "D2_SPEC_GRANT_ID_INVALID"):
                spec.proposed_d2_signing_bytes(
                    role="user", **dict(self.common, grant_id=ident))

    def test_d3_run_must_be_distinct_from_grant(self):
        with self.assertRaisesRegex(ValueError, "ID_COLLISION"):
            spec.proposed_d3_signing_bytes(
                **dict(self.d3, run_id=self.common["grant_id"]))
        with self.assertRaisesRegex(ValueError, "RUN_ID_INVALID"):
            spec.proposed_d3_signing_bytes(**dict(self.d3, run_id="x"))

    def test_counted_encoding_prevents_field_boundary_ambiguity(self):
        # Independent counted decoder recovers exactly ordered fields, even
        # when IDs include hyphen/underscore; no JSON canonicalization.
        args = dict(self.d3, grant_id="grant_a_b-c_123",
                    run_id="run_a-b_c-0012")
        raw = spec.proposed_d3_signing_bytes(**args)
        _, rows = self.unpack_without_using_source_encoder(raw)
        self.assertEqual(len(rows), len(dict(rows)))
        self.assertEqual(dict(rows)["grant_id"], b"grant_a_b-c_123")
        self.assertEqual(dict(rows)["run_id"], b"run_a-b_c-0012")

    def test_no_signing_live_roots_network_or_marker_access(self):
        self.assertEqual(PINNED_LIVE_TRUST_ROOTS, {})
        self.assertEqual(PRODUCTION_D2_D3_TRUST_ROOTS, {})
        with (
            patch("http.client.HTTPSConnection",
                  side_effect=AssertionError("NETWORK_FORBIDDEN")) as https,
            patch.object(socket, "create_connection",
                         side_effect=AssertionError("SOCKET_FORBIDDEN")) as sock,
            patch("os.open", side_effect=AssertionError("MARKER_FORBIDDEN"))
                  as opened,
        ):
            self.assertIsInstance(
                spec.proposed_d2_signing_bytes(role="reviewer", **self.common),
                bytes)
            self.assertIsInstance(spec.proposed_d3_signing_bytes(**self.d3),
                                  bytes)
            with self.assertRaisesRegex(
                    ValueError, "SPEC_NOT_AUTHORIZATION"):
                spec.send_live(approved=True)
            https.assert_not_called()
            sock.assert_not_called()
            opened.assert_not_called()


if __name__ == "__main__":
    unittest.main()
