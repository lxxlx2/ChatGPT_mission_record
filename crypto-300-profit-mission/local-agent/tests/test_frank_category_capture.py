"""One-shot source capture tests, with no real credentials or requests."""
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from urllib.error import HTTPError

from mission_agent.meme.holder_ranks import _b58
from mission_agent.signals.buy_admission import BACKPACK_MINT
from mission_agent.signals.category_capture import capture, write_new_sidecar
from mission_agent.signals.category_evidence import COINGECKO_SOLANA, read_category_evidence


A, B, C = [_b58(bytes([n])*32) for n in (81, 82, 83)]
AT = 1792683600


class Reply(io.BytesIO):
    def __init__(self, url, mint):
        self.url = url
        super().__init__(json.dumps({
            "name": "Fixture Meme", "preview_listing": False,
            "platforms": {"solana": mint},
            "detail_platforms": {"solana": {"contract_address": mint}},
            "categories": ["Meme"],
        }).encode())

    def geturl(self):
        return self.url


class CategoryCaptureTest(unittest.TestCase):
    def test_positive_then_rate_limit_preserves_prior_receipt_without_retries(self):
        calls = []

        def wire(request, timeout):
            url = request.full_url
            calls.append(url)
            self.assertEqual(request.get_header("X-cg-demo-api-key"), "test-inert-key")
            self.assertGreater(timeout, 0)
            if url.endswith(B):
                raise HTTPError(url, 429, "controlled", {}, None)
            return Reply(url, A)

        bundle, counts = capture([BACKPACK_MINT, A, A, B, C], api_key="test-inert-key", open_url=wire, clock=lambda: AT)
        self.assertEqual(calls, [COINGECKO_SOLANA+A, COINGECKO_SOLANA+B])
        self.assertEqual(counts, {"HARD_EXCLUDED": 1, "VERIFIED_MEME": 1, "SOURCE_RATE_LIMIT": 1})
        self.assertNotIn("test-inert-key", json.dumps(bundle))
        with tempfile.TemporaryDirectory() as work:
            path = Path(work)/"category.json"
            write_new_sidecar(path, bundle)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(read_category_evidence(path, AT)[A].status, "VERIFIED_MEME")
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                write_new_sidecar(path, {"version": 1, "records": []})
            self.assertEqual(path.read_bytes(), before)

    def test_wrong_identity_and_redirect_never_archive(self):
        for kind in ("wrong", "redirect", "http_redirect"):
            with self.subTest(kind=kind):
                def wire(request, timeout):
                    if kind == "http_redirect":
                        raise HTTPError(request.full_url, 302, "controlled", {}, None)
                    return Reply(request.full_url if kind == "wrong" else "https://example.invalid/", B)
                bundle, counts = capture([A], api_key="test-inert-key", open_url=wire, clock=lambda: AT)
                self.assertEqual(bundle["records"], [])
                self.assertEqual(counts, {"SOURCE_RECEIPT_UNUSABLE" if kind == "wrong" else "SOURCE_REDIRECT_REFUSED": 1})

    def test_invalid_input_cannot_open_transport(self):
        def unexpected(*args, **kwargs):
            raise AssertionError("invalid input cannot reach transport")
        for mints, token in ((["not-a-mint"], "fixture"), ([A], ""), ([A]*7, "fixture")):
            with self.subTest(mints=mints, token_len=len(token)):
                with self.assertRaises(ValueError):
                    capture(mints, api_key=token, open_url=unexpected)
