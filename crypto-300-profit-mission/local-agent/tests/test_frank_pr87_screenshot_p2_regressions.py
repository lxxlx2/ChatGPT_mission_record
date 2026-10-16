"""Real isolated P2 repro regressions for Frank synthetic screenshot QA."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import types
import unittest
from unittest import mock
from zipfile import ZipFile


SOURCE = Path(__file__).resolve().parents[1] / "scripts/frank_browser_screenshot_bundle.py"
spec = importlib.util.spec_from_file_location("frank_browser_screenshot_bundle_under_test", SOURCE)
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


def child_script(folder, name, receipt):
    script = folder / (name + ".py")
    code = "\n".join((
        "import json, os, pathlib, socket, time",
        "root=pathlib.Path(__file__).parent",
        "sock=socket.socket()",
        "sock.bind(('127.0.0.1',0))",
        "sock.listen(1)",
        "(root/'child.pid').write_text(str(os.getpid()))",
        "(root/'child.port').write_text(str(sock.getsockname()[1]))",
        f"payload={receipt!r}",
        "if payload: print(json.dumps(payload),flush=True)",
        "time.sleep(20)",
    )) + "\n"
    script.write_text(code)
    return script


def not_listening(port):
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", int(port))) != 0


class TestStartupOwnsFailedChild(unittest.TestCase):
    def exercise(self, receipt, timeout):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            repo=root / "repo"
            (repo / "crypto-300-profit-mission/local-agent").mkdir(parents=True)
            folder=root / "logs"
            folder.mkdir()
            launcher=child_script(root, "fake_launcher", receipt)
            if receipt:
                with self.assertRaisesRegex(RuntimeError, "LAUNCHER_SOURCE_FAILED"):
                    bundle.start(root, repo, launcher, folder, handshake_timeout=timeout)
            else:
                with self.assertRaisesRegex(TimeoutError, "QA_LAUNCHER_TIMEOUT"):
                    bundle.start(root, repo, launcher, folder, handshake_timeout=timeout)
            port=int((root / "child.port").read_text())
            pid=int((root / "child.pid").read_text())
            self.assertTrue(not_listening(port), "failed launcher left real listener alive")
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)
            self.assertTrue((folder / "launcher.log").is_file())

    def test_bad_attestation_reaps_actual_listener(self):
        self.exercise(
            {"status": "MAC_PR85_SYNTHETIC_HTTP_SMOKE_PASS",
             "source_tree_sha": "WRONG_TREE", "real_rpc": False}, 4
        )

    def test_timeout_reaps_actual_listener(self):
        self.exercise(None, 2.0)


class TestSymlinkBoundaries(unittest.TestCase):
    def test_launcher_symlink_outside_qa_never_executes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t) / "approved"
            root.mkdir()
            (root / "repo").mkdir()
            runtime=root / "qa-runtime"
            runtime.mkdir()
            outside=Path(t) / "outside_launcher.py"
            sentinel=Path(t) / "executed_sentinel"
            outside.write_text("from pathlib import Path\nPath("+repr(str(sentinel))+").write_text('EXECUTED')\n")
            (runtime / "frank-pr85-safari.py").symlink_to(outside)
            def fake_git(_repo, *args):
                return bundle.TREE if args == ("rev-parse", "HEAD^{tree}") else ""
            argv=["bundle", "--qa-root",str(root),
                  "--launcher-file",str(runtime / "frank-pr85-safari.py")]
            with mock.patch.object(bundle,"ROOT",root), mock.patch.object(bundle,"git",fake_git), \
                 mock.patch.object(sys,"argv",argv):
                with self.assertRaisesRegex(ValueError,"QA_PATH_SYMLINK_FORBIDDEN"):
                    bundle.main()
            self.assertFalse(sentinel.exists())
            self.assertFalse((root/"qa-evidence").exists())

    def test_symlink_repo_runtime_and_evidence_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"qa"
            root.mkdir()
            outside=Path(t)/"outside"
            outside.mkdir()
            for rel in ("repo", "qa-runtime", "qa-evidence"):
                (root/rel).symlink_to(outside,target_is_directory=True)
                with self.assertRaisesRegex(ValueError,"QA_PATH_SYMLINK_FORBIDDEN"):
                    bundle.confined(root,rel)
                (root/rel).unlink()

    def test_root_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            actual=Path(t)/"actual"
            actual.mkdir()
            link=Path(t)/"link"
            link.symlink_to(actual,target_is_directory=True)
            with mock.patch.object(bundle,"ROOT",link), self.assertRaisesRegex(ValueError,"QA_ROOT_NOT_APPROVED"):
                bundle.check(link)


class TestPartialConsolePreservation(unittest.TestCase):
    def test_real_event_callback_survives_first_image_failure(self):
        logs=[]
        class FakePage:
            def __init__(self):
                self.handlers={}
                self.url="http://127.0.0.1:10000/research/positions"
            def on(self,event,listener):
                self.handlers[event]=listener
            def goto(self,*args,**kwargs):
                self.handlers["console"](types.SimpleNamespace(
                    type="error",text="REVIEW_CAPTURE_FAILURE_CONSOLE_SENTINEL"))
            def wait_for_function(self,*args,**kwargs):
                pass
            def locator(self,*args):
                return self
            def fill(self,*args):
                pass
            def wait_for_timeout(self,*args):
                pass
        class FakeContext:
            def __init__(self):
                self.listener=None
                self.closed=False
            def route(self,*args):
                pass
            def on(self,event,listener):
                assert event=="page"
                self.listener=listener
            def new_page(self):
                page=FakePage()
                self.listener(page)
                return page
            def close(self):
                self.closed=True
        context=FakeContext()
        browser=types.SimpleNamespace(new_context=lambda **kw:context)
        receipt={"urls":{"f02_research_only":"http://127.0.0.1:10000/research/positions"},
                 "mint_a":"synthetic"}
        seen=[]
        def failing_shot(page, folder, manifest, name, desc, open_details=True):
            seen.append(name)
            manifest["images"].append({"file":name+".png"})
            if len(seen)==2:
                raise ValueError("INJECTED_FAILURE_AFTER_FIRST_IMAGE")
        with mock.patch.object(bundle,"shot",failing_shot),self.assertRaisesRegex(
            ValueError,"INJECTED_FAILURE_AFTER_FIRST_IMAGE"
        ):
            bundle.take(browser, receipt, Path("/tmp"), {"images":[]}, logs)
        self.assertTrue(context.closed,"WebKit context must close after screenshot exception")
        self.assertEqual(len(seen),2)
        self.assertTrue(any(x["text"]=="REVIEW_CAPTURE_FAILURE_CONSOLE_SENTINEL" for x in logs))

    def test_main_partial_zip_keeps_events(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"approved"
            root.mkdir()
            (root/"repo").mkdir()
            runtime=root/"qa-runtime"
            runtime.mkdir()
            launcher=runtime/"frank-pr85-safari.py"
            launcher.write_text("pass\n")
            def fake_git(_repo,*args):
                return bundle.TREE if args==("rev-parse","HEAD^{tree}") else ""
            mock_process=mock.Mock(returncode=0)
            browser=mock.Mock()
            webkit=types.SimpleNamespace(launch=lambda **kw:browser)
            class Manager:
                def __enter__(self): return types.SimpleNamespace(webkit=webkit)
                def __exit__(self,*args): return False
            pkg=types.ModuleType("playwright")
            pkg.__path__=[]
            sub=types.ModuleType("playwright.sync_api")
            sub.sync_playwright=lambda:Manager()
            def fail_after_console(_browser,_receipt,_folder,manifest,logs):
                manifest["images"].append({"file":"01-f02-fresh-32-all.png",
                                           "description":"first screenshot","utc":"test"})
                logs.append({"type":"error","text":"REVIEW_CAPTURE_FAILURE_CONSOLE_SENTINEL"})
                raise RuntimeError("REVIEW_CAPTURE_FAILURE_AFTER_CONSOLE")
            argv=["bundle","--qa-root",str(root),"--launcher-file",str(launcher)]
            fake_start=(mock_process,None,{"status":"MAC_PR85_SYNTHETIC_HTTP_SMOKE_PASS"})
            with mock.patch.object(bundle,"ROOT",root), \
                 mock.patch.object(bundle,"git",fake_git), \
                 mock.patch.object(bundle,"start",return_value=fake_start), \
                 mock.patch.object(bundle,"stop_process"), \
                 mock.patch.object(bundle,"take",side_effect=fail_after_console), \
                 mock.patch.dict(sys.modules,{"playwright":pkg,"playwright.sync_api":sub}), \
                 mock.patch.object(sys,"argv",argv), \
                 self.assertRaises(SystemExit) as cm:
                bundle.main()
            self.assertEqual(cm.exception.code,1)
            archives=list((root/"qa-evidence").glob("*.zip"))
            self.assertEqual(len(archives),1)
            with ZipFile(archives[0]) as z:
                console=json.loads(z.read("browser-console.json"))
                manifest=json.loads(z.read("manifest.json"))
                self.assertEqual(manifest["status"],"PARTIAL_OR_FAILED")
                self.assertIn("REVIEW_CAPTURE_FAILURE_CONSOLE_SENTINEL",str(console))
                self.assertIn("REVIEW_CAPTURE_FAILURE_AFTER_CONSOLE",str(manifest["errors"]))


if __name__=="__main__":
    unittest.main()
