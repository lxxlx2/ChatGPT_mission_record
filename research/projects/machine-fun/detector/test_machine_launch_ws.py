"""Local loopback-only WebSocket integration. No external RPC or production services."""
import asyncio
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from websockets.asyncio.client import connect as real_connect
from websockets.asyncio.server import serve
from machine_launch_detector import Detector, Journal, listen
from test_machine_launch_detector import FakeRpc, entry, tx_template


class WebSocketRoundtripTests(unittest.TestCase):
    def test_detector_subscribes_and_handles_launch_notification(self):
        async def scenario():
            seen = []
            async def handle(ws):
                subscribe = json.loads(await ws.recv())
                seen.append(subscribe)
                await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "result": 42}))
                await ws.send(json.dumps({"jsonrpc": "2.0", "method": "logsNotification", "params": {
                    "subscription": 42, "result": {"context": {"slot": 1234}, "value": {
                        "signature": "new", "err": None, "logs": ["Program log: Instruction: InitializeV2"]
                    }}
                }}))
                await asyncio.sleep(0.5)

            with tempfile.TemporaryDirectory() as root:
                journal = Journal(Path(root) / "db")
                rpc = FakeRpc([entry("old", 1000)], {"new": tx_template()})
                detector = Detector(rpc, journal)
                async with serve(handle, "127.0.0.1", 0) as server:
                    port = server.sockets[0].getsockname()[1]
                    def loopback_only_connect(url, **kwargs):
                        self.assertEqual(url, f"wss://127.0.0.1:{port}")
                        return real_connect(f"ws://127.0.0.1:{port}", **kwargs)
                    with patch("websockets.asyncio.client.connect", side_effect=loopback_only_connect):
                        with contextlib.redirect_stdout(io.StringIO()) as output, contextlib.redirect_stderr(io.StringIO()):
                            task = asyncio.create_task(listen(f"wss://127.0.0.1:{port}", detector, refresh_seconds=5))
                            try:
                                for _ in range(100):
                                    if journal.state("new") == "STDOUT_EMITTED":
                                        break
                                    await asyncio.sleep(0.02)
                                self.assertEqual(journal.state("new"), "STDOUT_EMITTED")
                                self.assertIn("MACHINE_FUN_CHAIN_CANDIDATE", output.getvalue())
                            finally:
                                task.cancel()
                                with self.assertRaises(asyncio.CancelledError):
                                    await task
                journal.close()
            self.assertEqual(len(seen), 1)
            self.assertEqual(seen[0]["method"], "logsSubscribe")
            self.assertEqual(seen[0]["params"][0]["mentions"], [detector.platform])
        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
