"""Reverse-regression probes for F1 (misbound failed tx), F2 (HTTP exception family), F6 (sanitizer).
Run with PYTHONPATH pointing at a given local-agent tree. Prints one line per probe."""
import http.client, json, socket, ssl, sqlite3, tempfile, urllib.error
from pathlib import Path
from mission_agent.frank.rpc import SolanaRPC
from mission_agent.mission_control.ata_backfill import derive_ata, scan_ata_mints, WALLET, TOKEN_2022
from mission_agent.mission_control.evidence_sync import safe
from scripts import frank_ata_backfill as cli
J7 = "J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump"
SIG = "5" * 68 + "A" * 20; OTHER = "3" * 68 + "C" * 20
ATA, _ = derive_ata(WALLET, J7, TOKEN_2022)
def tx(sig, err):
    return {"slot": 454705300, "blockTime": 1791505760,
            "transaction": {"signatures": [sig], "message": {"accountKeys": [
                {"pubkey": WALLET, "signer": True, "writable": True}, {"pubkey": ATA, "signer": False, "writable": True},
                {"pubkey": J7, "signer": False, "writable": False}]}},
            "meta": {"err": err, "loadedAddresses": {"writable": [], "readonly": []},
                     "preTokenBalances": [{"accountIndex": 1, "mint": J7, "owner": WALLET, "programId": TOKEN_2022, "uiTokenAmount": {"amount": "0", "decimals": 6}}],
                     "postTokenBalances": [{"accountIndex": 1, "mint": J7, "owner": WALLET, "programId": TOKEN_2022, "uiTokenAmount": {"amount": "5000000", "decimals": 6}}]}}
class FakeRPC:
    def call(self, method, params):
        if method == "getSignaturesForAddress":
            return [{"signature": SIG, "slot": 454705300, "blockTime": 1791505760, "err": None}] if params[0] == ATA else []
        return tx(OTHER, {"InstructionError": [0, "Custom"]})
class Ctx:
    def __init__(s, e): s.e = e
    def __enter__(s): return s
    def __exit__(s, *a): return False
    def read(s): raise s.e
def rpc_raising(e):
    return SolanaRPC(request=lambda req, timeout=20: Ctx(e), sleep=lambda s: None, jitter=lambda: 0.0, min_interval=0)
# F1 end-to-end through the real CLI run()
with tempfile.TemporaryDirectory() as d:
    db = Path(d) / "f.sqlite"; c = sqlite3.connect(db); c.execute("CREATE TABLE signatures(person_id TEXT, signature TEXT)"); c.commit(); c.close()
    out = Path(d) / "f1.json"
    r = cli.run(["--database", str(db), "--mint", J7, "--output", str(out), "--pages-per-ata", "1"], rpc=FakeRPC())
    code = 2 if r["git_sync"] == "SYNC_FAILED_LOCAL_FILE_RETAINED" else 3 if r["scan_status"] != "BOUNDED_COMPLETED" else 0
    print(f"F1 cli scan_status={r['scan_status']} exit_code={code}")
# F2 across the HTTP exception family + EOFError, via the real CLI
for name, e in [("BadStatusLine", http.client.BadStatusLine("x")), ("LineTooLong", http.client.LineTooLong("x")),
                ("IncompleteRead", http.client.IncompleteRead(b"x")), ("RemoteDisconnected", http.client.RemoteDisconnected("x")),
                ("socket.timeout", socket.timeout("x")), ("SSLEOFError", ssl.SSLEOFError("x")),
                ("URLError", urllib.error.URLError("x")), ("EOFError", EOFError("x"))]:
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "f.sqlite"; c = sqlite3.connect(db); c.execute("CREATE TABLE signatures(person_id TEXT, signature TEXT)"); c.commit(); c.close()
        out = Path(d) / "f2.json"
        try:
            r = cli.run(["--database", str(db), "--mint", J7, "--output", str(out), "--pages-per-ata", "1"], rpc=rpc_raising(e))
            print(f"F2 {name:18s} scan_status={r['scan_status']} artifact={out.exists()}")
        except Exception as x:
            print(f"F2 {name:18s} UNCAUGHT {type(x).__name__} artifact={out.exists()}")
# F6 sanitizer probes
probes = {
 "file_uri": "file:///Users/alice/Library/FrankMeme/state.db", "parenthesized": "state (/Users/alice/private/state.db) ok",
 "quoted": '"/Users/alice/private/state.db"', "tilde": "~/Library/Application Support/FrankMeme/policy.json",
 "colon_prefix": "path:/home/alice/.config/app.json", "alchemy_path_key": "https://solana-mainnet.g.alchemy.com/v2/FAKE_TEST_KEY_1234567890abcdef",
 "email": "contact ops.person@example.com now", "github_long_branch": "https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/frank-wallet-v2-d0-readonly-20261011/x.json",
 "benign_profile_colon": "profile: ok", "benign_tilde_space": "deposit ~ approx 3",
}
for k, v in probes.items():
    print(f"F6 {k:22s} -> {json.dumps(safe(v), ensure_ascii=False)}")
