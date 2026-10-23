"""Synthetic, no-network regressions for bounded Spot511 official source batches."""
import hashlib
import io
import sys
import tempfile
import unittest
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import monster_spot511_manual_publisher_batch as m


ROSTER = [f"X{i:03d}USDT" for i in range(511)]
DAY = date(2026, 10, 16)
NOW = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)


def synthetic_publisher(symbol=ROSTER[0], day=DAY):
    t = int(datetime.combine(day, datetime.min.time(), timezone.utc).timestamp()) * 10**6
    lines = []
    for index in range(1440):
        opening = t + index * 60 * 10**6
        lines.append(f"{opening},1,1.1,0.9,1,10,{opening+60*10**6-1},100,2,5,50,0")
    stream = io.BytesIO()
    filename = f"{symbol}-1m-{day.isoformat()}.csv"
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(filename, "\n".join(lines)+"\n")
    original = stream.getvalue()
    sha = hashlib.sha256(original).hexdigest()
    checksum = f"{sha}  {symbol}-1m-{day.isoformat()}.zip\n".encode()
    return original, checksum


class BatchTests(unittest.TestCase):
    def test_plan_never_reads_network_or_writes_archive(self):
        def forbidden(*_):
            self.fail("Plan must not fetch any HTTP data")
        with tempfile.TemporaryDirectory() as d:
            got = m.batch(DAY, d, count=2, now=NOW,
                          fetcher=forbidden, roster=ROSTER)
            self.assertEqual(got["execution"], "PLAN_ONLY")
            self.assertEqual(len(got["source_records"]),2)
            self.assertEqual(got["verified_downloads"],0)
            self.assertFalse(Path(d, ROSTER[0]).exists())

    def test_verified_download_and_idempotent_second_run(self):
        original, checksum = synthetic_publisher()
        requests = []
        def fetch(url, _limit):
            requests.append(url)
            return checksum if url.endswith(".CHECKSUM") else original
        with tempfile.TemporaryDirectory() as d:
            x = m.batch(DAY, d, count=1, download=True, now=NOW,
                        fetcher=fetch, roster=ROSTER)
            self.assertEqual(x["verified_downloads"],1)
            self.assertEqual(x["source_records"][0]["status"],"VERIFIED_FULL_DAY_1440")
            zip_path, check_path = m.stage166.daily_paths(d, ROSTER[0], DAY)
            self.assertEqual(zip_path.read_bytes(), original)
            self.assertEqual(check_path.read_bytes(), checksum)
            self.assertEqual(len(requests),2)
            y = m.batch(DAY, d, count=1, download=True, now=NOW,
                        fetcher=lambda *_: self.fail("Redownloaded valid source"),
                        roster=ROSTER)
            self.assertEqual(y["source_records"][0]["status"],"ALREADY_VERIFIED_LOCAL")

    def test_bad_checksum_keeps_original_directory_clean(self):
        original, checksum = synthetic_publisher()
        def fetch(url, _):
            return b"f"*64 + checksum[64:] if url.endswith(".CHECKSUM") else original
        with tempfile.TemporaryDirectory() as d:
            x = m.batch(DAY, d, count=1, download=True, now=NOW,
                        fetcher=fetch, roster=ROSTER)
            self.assertEqual(x["source_records"][0]["status"],"SOURCE_UNAVAILABLE_OR_REJECTED")
            zip_path, check_path = m.stage166.daily_paths(d, ROSTER[0], DAY)
            self.assertFalse(zip_path.exists())
            self.assertFalse(check_path.exists())

    def test_valid_sha_but_missing_1440_minute_rows_rejected(self):
        original, checksum = synthetic_publisher()
        with zipfile.ZipFile(io.BytesIO(original)) as z:
            filename=z.namelist()[0]
            data=z.read(filename).splitlines()
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(filename,b"\n".join(data[:-1])+b"\n")
        bad_zip=stream.getvalue()
        updated = (hashlib.sha256(bad_zip).hexdigest().encode()
                   +checksum[64:])
        def fetch(url, _):
            return updated if url.endswith(".CHECKSUM") else bad_zip
        with tempfile.TemporaryDirectory() as d:
            x=m.batch(DAY,d,count=1,download=True,now=NOW,
                      fetcher=fetch,roster=ROSTER)
            self.assertEqual(x["source_records"][0]["status"],"SOURCE_UNAVAILABLE_OR_REJECTED")
            self.assertIn("INCOMPLETE_1440",x["source_records"][0]["error"])

    def test_corrupt_zip_with_matching_checksum_records_failure_and_continues(self):
        bad_zip = b"not a ZIP archive"
        bad_sum = (hashlib.sha256(bad_zip).hexdigest()
                   + "  " + ROSTER[0] + "-1m-" + DAY.isoformat() + ".zip\n").encode()
        good_zip, good_sum = synthetic_publisher(symbol=ROSTER[1])
        def fetch(url, _limit):
            first = "/" + ROSTER[0] + "/"
            is_first = first in url
            if is_first:
                return bad_sum if url.endswith(".CHECKSUM") else bad_zip
            return good_sum if url.endswith(".CHECKSUM") else good_zip
        with tempfile.TemporaryDirectory() as d:
            result = m.batch(DAY, d, count=2, download=True, now=NOW,
                             fetcher=fetch, roster=ROSTER)
            self.assertEqual([x["status"] for x in result["source_records"]],
                             ["SOURCE_UNAVAILABLE_OR_REJECTED", "VERIFIED_FULL_DAY_1440"])
            self.assertIn("BadZipFile", result["source_records"][0]["error"])
            self.assertEqual(result["verified_downloads"], 1)

    def test_concurrent_writer_never_overwritten_by_source_commit(self):
        data, checksum = synthetic_publisher()
        def fetch(url, _limit):
            return checksum if url.endswith(".CHECKSUM") else data
        with tempfile.TemporaryDirectory() as d:
            _, dest_checksum = m.stage166.daily_paths(d, ROSTER[0], DAY)
            link = m.os.link
            def concurrent_link(src, dst):
                if Path(dst) == dest_checksum and not dest_checksum.exists():
                    dest_checksum.write_bytes(b"competing evidence")
                return link(src, dst)
            with patch.object(m.os, "link", side_effect=concurrent_link):
                result = m.batch(DAY, d, count=1, download=True, now=NOW,
                                 fetcher=fetch, roster=ROSTER)
            self.assertEqual(result["source_records"][0]["status"],
                             "SOURCE_UNAVAILABLE_OR_REJECTED")
            target_zip, _ = m.stage166.daily_paths(d, ROSTER[0], DAY)
            self.assertFalse(target_zip.exists())
            self.assertEqual(dest_checksum.read_bytes(), b"competing evidence")

    def test_symlink_target_is_never_followed_or_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            original = Path(d) / "other-evidence.zip"
            original.write_bytes(b"important original bytes")
            target_zip, _ = m.stage166.daily_paths(d, ROSTER[0], DAY)
            target_zip.parent.mkdir(parents=True)
            target_zip.symlink_to(original)
            result = m.batch(DAY, d, count=1, download=True, now=NOW,
                             roster=ROSTER,
                             fetcher=lambda *_: self.fail("unexpected network"))
            self.assertEqual(result["source_records"][0]["status"],
                             "LOCAL_SOURCE_SYMLINK_REJECTED_NO_OVERWRITE")
            self.assertEqual(original.read_bytes(), b"important original bytes")

    def test_original_t0_unicode_symbols_are_admitted_without_network(self):
        # Original Stage163 T0 includes two Chinese-named Binance pairs.
        # The previous ASCII-only regex incorrectly blocked ALL 511 sources.
        with tempfile.TemporaryDirectory() as d:
            result = m.batch(DAY,d,count=1,now=NOW,
                             fetcher=lambda *_: self.fail("Plan performed HTTP"))
            self.assertEqual(result["frozen_total"],511)
            self.assertEqual(result["source_records"][0]["symbol"],"0GUSDT")

    def test_official_unicode_symbol_checksum_and_percent_encoded_url(self):
        symbol="币安人生USDT"
        roster=sorted(ROSTER[:-1]+[symbol])
        self.assertEqual(len(roster),511)
        original, checksum=synthetic_publisher(symbol=symbol)
        def fetch(url, _limit):
            self.assertIn("%E5%B8%81%E5%AE%89%E4%BA%BA%E7%94%9FUSDT",url)
            return checksum if url.endswith(".CHECKSUM") else original
        with tempfile.TemporaryDirectory() as d:
            result=m.batch(DAY,d,start_index=510,count=1,now=NOW,
                           download=True,roster=roster,fetcher=fetch)
            self.assertEqual(result["verified_downloads"],1)
            self.assertEqual(result["source_records"][0]["status"],
                             "VERIFIED_FULL_DAY_1440")
            self.assertEqual(result["source_records"][0]["symbol"],symbol)

    def test_future_utc_day_never_downloaded(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"DAY_NOT_YET_ENDED"):
                m.batch(date(2026,10,24),d,count=1,
                        now=NOW,download=True,roster=ROSTER)

    def test_explicit_frozen_slice_bounded_and_no_default_amount(self):
        with tempfile.TemporaryDirectory() as d:
            for start,count in [(-1,1),(0,0),(0,65),(500,20)]:
                with self.assertRaisesRegex(ValueError,"UNBOUNDED_OR_INVALID"):
                    m.batch(DAY,d,start_index=start,count=count,
                            now=NOW,roster=ROSTER)
            with self.assertRaisesRegex(ValueError,"DAY_OUTSIDE"):
                m.batch(date(2026,10,15),d,now=NOW,roster=ROSTER)
            x=m.batch(DAY,d,start_index=510,count=1,now=NOW,roster=ROSTER)
            self.assertEqual(x["source_records"][0]["symbol"],ROSTER[-1])
            self.assertEqual(x["G6"],"NO_GO")

    def test_partial_local_pair_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            target,_=m.stage166.daily_paths(d,ROSTER[0],DAY)
            target.parent.mkdir(parents=True)
            target.write_bytes(b"previous evidence")
            x=m.batch(DAY,d,count=1,now=NOW,download=True,roster=ROSTER,
                      fetcher=lambda *_: self.fail("Unexpected network"))
            self.assertEqual(x["source_records"][0]["status"],
                             "INCOMPLETE_EXISTING_LOCAL_PAIR_NO_OVERWRITE")
            self.assertEqual(target.read_bytes(),b"previous evidence")

    def test_redirect_cannot_change_to_unknown_host(self):
        from urllib.request import Request
        handler=m.SameHostRedirects()
        with self.assertRaisesRegex(m.SourceRejected,"REDIRECT_OUTSIDE"):
            handler.redirect_request(Request("https://data.binance.vision/x"),
                                     None,302,"redirect",{},
                                     "https://untrusted.example/file.zip")


if __name__ == "__main__":
    unittest.main()
