"""Publisher exact SHA and HTTP fail-closed one-shot source acquisition tests."""
import hashlib
import importlib.util
from datetime import date,datetime,timezone
from io import BytesIO
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

S=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(S))
spec=importlib.util.spec_from_file_location("monster_actual_publisher",S/"monster_v4_forward_spot511_official_publisher_acquire.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fake_publisher(symbol="BTCUSDT",day="2026-10-16",*,corrupt=False,rows=1440):
    name=f"{symbol}-1m-{day}.zip"
    utc=int(datetime.combine(date.fromisoformat(day),datetime.min.time(),timezone.utc).timestamp())
    body="\n".join(
        f"{utc*1_000_000+n*60_000_000},1,1.1,0.9,1,10,{utc*1_000_000+(n+1)*60_000_000-1},100,2,5,50,0"
        for n in range(rows))+"\n"
    raw=BytesIO()
    with zipfile.ZipFile(raw,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(name.replace(".zip",".csv"),body)
    zipped=raw.getvalue()
    check=("f"*64 if corrupt else hashlib.sha256(zipped).hexdigest())+"  "+name+"\n"
    filename,url,checksum_url=m.url_parts(symbol,day)
    return {url:zipped,checksum_url:check.encode()}


def getter(mapping):
    def f(url):
        if url not in mapping:
            raise RuntimeError("PUBLISHER_HTTP_404")
        return mapping[url],{"observed_at_utc":"TEST_SYNTHETIC"}
    return f


class RealPublisherSourceTests(unittest.TestCase):
    def test_frozen_511_real_original_t0_is_not_approximated(self):
        roster=m.admitted.frozen_roster()
        self.assertEqual(len(roster),511)
        self.assertEqual(len(set(roster)),511)
        self.assertIn("BTCUSDT",roster)

    def test_success_requires_real_shape_issuer_checksum_and_1440_microsecond_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            r=m.one_pair("BTCUSDT","2026-10-16",Path(directory),
                         getter=getter(fake_publisher()))
            self.assertEqual(r["status"],"VERIFIED_FULL_DAY_1440")
            self.assertEqual(r["csv_closed_1m_rows"],1440)
            self.assertTrue(r["original_publisher_checksum_valid"])
            self.assertTrue(r["zip_sha256"])
            self.assertTrue((Path(directory)/"BTCUSDT/1m/BTCUSDT-1m-2026-10-16.zip").exists())

    def test_checksum_mismatch_remains_unverified_and_no_source_files_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            r=m.one_pair("BTCUSDT","2026-10-16",Path(directory),
                         getter=getter(fake_publisher(corrupt=True)))
            self.assertEqual(r["status"],"SOURCE_REJECTED_OR_UNAVAILABLE")
            self.assertIn("CHECKSUM_SHA256_MISMATCH",r["error"])
            self.assertFalse(list(Path(directory).rglob("*.zip")))

    def test_incomplete_1439_minutes_rejected_even_with_valid_issuer_sha(self):
        with tempfile.TemporaryDirectory() as directory:
            r=m.one_pair("BTCUSDT","2026-10-16",Path(directory),
                         getter=getter(fake_publisher(rows=1439)))
            self.assertEqual(r["status"],"SOURCE_REJECTED_OR_UNAVAILABLE")
            self.assertIn("INCOMPLETE_1440",r["error"])

    def test_http_404_cannot_become_no_watch_or_zero_pnl(self):
        with tempfile.TemporaryDirectory() as directory:
            report=m.collect(Path(directory),roster=["BTCUSDT"],getter=getter({}))
            self.assertEqual(report["attempts_total"],2)
            self.assertEqual(report["status_counts"],{"SOURCE_REJECTED_OR_UNAVAILABLE":2})
            self.assertTrue(report["no_failed_archive_can_count_as_no_WATCH_or_no_SETUP"])
            self.assertEqual(report["G6"],"NO_GO")

    def test_unfrozen_symbol_day_or_network_url_refused(self):
        with self.assertRaisesRegex(ValueError,"FROZEN_SYMBOL_OR_DAY"):
            m.url_parts("BTCUSDT","2026-10-19")
        with self.assertRaisesRegex(ValueError,"FROZEN_SYMBOL_OR_DAY"):
            m.url_parts("../BTCUSDT","2026-10-16")
        with self.assertRaisesRegex(ValueError,"URL_NOT_ALLOWED"):
            m.fetch_one_url("https://evil.example.com/x.zip",100)

    def test_first_full_forward_day_2026_10_18_is_separate_source_scope(self):
        filename,url,checksum=m.url_parts("BTCUSDT","2026-10-18")
        self.assertEqual(filename,"BTCUSDT-1m-2026-10-18.zip")
        with tempfile.TemporaryDirectory() as directory:
            fixtures=fake_publisher(day="2026-10-18")
            result=m.collect(Path(directory),roster=["BTCUSDT"],days=("2026-10-18",),
                             getter=getter(fixtures))
            self.assertEqual(result["days_utc"],["2026-10-18"])
            self.assertEqual(result["attempts_total"],1)
            self.assertEqual(result["status_counts"],{"VERIFIED_FULL_DAY_1440":1})

    def test_unicode_symbol_and_zip_name_must_use_percent_encoded_official_path(self):
        symbol="币安人生USDT"
        filename,zip_url,checksum_url=m.url_parts(symbol,"2026-10-16")
        self.assertEqual(filename,"币安人生USDT-1m-2026-10-16.zip")
        self.assertIn("%E5%B8%81",zip_url)
        self.assertNotIn(symbol,zip_url)
        self.assertTrue(checksum_url.endswith(".zip.CHECKSUM"))
        self.assertIn(symbol,m.admitted.frozen_roster())

    def test_unicode_filename_zip_and_issuer_checksum_can_be_validated_offline(self):
        symbol="牛来USDT"
        with tempfile.TemporaryDirectory() as directory:
            fake=fake_publisher(symbol)
            actual=m.one_pair(symbol,"2026-10-16",Path(directory),getter=getter(fake))
            self.assertEqual(actual["status"],"VERIFIED_FULL_DAY_1440")
            self.assertEqual(actual["csv_closed_1m_rows"],1440)

    def test_actual_http_redirect_fails_before_disallowed_server_get(self):
        """Genuine two HTTP servers, no getter mock: redirected target GET must be zero."""
        hits={"official":0,"disallowed":0}
        redirect_code={"status":302}

        class Disallowed(BaseHTTPRequestHandler):
            def do_GET(self):
                hits["disallowed"]+=1
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"not an issuer")

            def log_message(self, *args):
                pass

        blocked=ThreadingHTTPServer(("127.0.0.1",0),Disallowed)

        class Allowed(BaseHTTPRequestHandler):
            def do_GET(self):
                hits["official"]+=1
                self.send_response(redirect_code["status"])
                self.send_header(
                    "Location",
                    f"http://127.0.0.1:{blocked.server_port}/non-publisher.zip"
                )
                self.end_headers()

            def log_message(self, *args):
                pass

        allowed=ThreadingHTTPServer(("127.0.0.1",0),Allowed)
        threads=[threading.Thread(target=x.serve_forever,daemon=True)
                 for x in (blocked,allowed)]
        for thread in threads:
            thread.start()
        try:
            base=f"http://127.0.0.1:{allowed.server_port}/data/spot/daily/klines"
            with mock.patch.object(m,"BASE",base):
                source=base+"/BTCUSDT/1m/BTCUSDT-1m-2026-10-16.zip"
                for status in (301,302,303,307,308):
                    with self.subTest(status=status):
                        redirect_code["status"]=status
                        with self.assertRaisesRegex(
                            ValueError,"PUBLISHER_REDIRECT_BLOCKED_BEFORE_FOLLOW"
                        ):
                            m.fetch_one_url(source,64)
                        self.assertEqual(hits["disallowed"],0)
            self.assertEqual(hits["official"],5)
            self.assertEqual(hits["disallowed"],0)
        finally:
            for server in (allowed,blocked):
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=5)

    def test_actual_http_direct_200_publisher_source_still_works(self):
        """The redirect veto must not break the ordinary HTTP 200 path."""
        payload=b"verified caller-controlled test bytes"
        hits={"source":0}

        class Direct(BaseHTTPRequestHandler):
            def do_GET(self):
                hits["source"]+=1
                self.send_response(200)
                self.send_header("Content-Type","application/octet-stream")
                self.send_header("Content-Length",str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self,*args):
                pass

        server=ThreadingHTTPServer(("127.0.0.1",0),Direct)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            base=f"http://127.0.0.1:{server.server_port}/data/spot/daily/klines"
            with mock.patch.object(m,"BASE",base):
                source=base+"/BTCUSDT/1m/BTCUSDT-1m-2026-10-16.zip"
                received,meta=m.fetch_one_url(source,128)
            self.assertEqual(received,payload)
            self.assertEqual(meta["http_status"],200)
            self.assertEqual(hits["source"],1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_existing_source_pair_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            fixtures=fake_publisher()
            r1=m.one_pair("BTCUSDT","2026-10-16",Path(directory),getter=getter(fixtures))
            self.assertEqual(r1["status"],"VERIFIED_FULL_DAY_1440")
            original=(Path(directory)/"BTCUSDT/1m/BTCUSDT-1m-2026-10-16.zip").read_bytes()
            r2=m.one_pair("BTCUSDT","2026-10-16",Path(directory),getter=getter(fixtures))
            self.assertEqual(r2["status"],"SOURCE_REJECTED_OR_UNAVAILABLE")
            self.assertIn("ALREADY_EXISTS",r2["error"])
            # The collector must not delete an existing valid file on retry.
            self.assertEqual((Path(directory)/"BTCUSDT/1m/BTCUSDT-1m-2026-10-16.zip").read_bytes(),original)


if __name__=="__main__":
    unittest.main()
