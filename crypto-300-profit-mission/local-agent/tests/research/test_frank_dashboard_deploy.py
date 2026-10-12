"""Offline pinned dashboard deploy checks. No real Mac, Gmail, launchctl or GitHub mutations."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
from unittest import mock

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "deploy_frank_dashboard_review_badge.py"
spec = importlib.util.spec_from_file_location("review_deployer", SCRIPT)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
REPO = Path(__file__).resolve().parents[4]


def git_blob(sha):
    return subprocess.run(["git","-C",str(REPO),"cat-file","blob",sha],
                          check=True,capture_output=True).stdout


def sample_root(tmp_path, version):
    root=tmp_path/"mission_control"
    (root/"static").mkdir(parents=True)
    for name, hashes in app.PATCHES.items():
        blob=hashes[version]
        if blob is not None:
            (root/name).write_bytes(git_blob(blob))
    return root


def fake_remote(monkeypatch, altered=None):
    def read(url, timeout=None):
        name=url.split("/mission_control/")[-1]
        assert url.split("/")[5] == app.COMMIT
        assert name in app.PATCHES
        data=git_blob(app.PATCHES[name]["target"])
        if altered==name:
            data+=b"corrupt"
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return None
            def read(self,limit=None): return data[:limit]
        return Response()
    monkeypatch.setattr(app.urllib.request,"urlopen",read)


@pytest.mark.parametrize("version",["baseline","legacy","target"])
def test_preflight_supports_only_explicit_verified_local_versions(tmp_path,monkeypatch,version):
    root=sample_root(tmp_path,version)
    fake_remote(monkeypatch)
    value,data=app.preflight(root)
    assert value==version
    assert len(data)==3
    assert all(app.blob_sha(data[name])==record["target"]
               for name,record in app.PATCHES.items())


def test_mixed_local_files_fail_closed_without_network(tmp_path,monkeypatch):
    root=sample_root(tmp_path,"legacy")
    (root/"server.py").write_bytes(git_blob(app.PATCHES["server.py"]["baseline"]))
    with mock.patch.object(app.urllib.request,"urlopen") as network:
        with pytest.raises(RuntimeError,match="LOCAL_SOURCE_DIFFERENT"):
            app.preflight(root)
        network.assert_not_called()


def test_fake_remote_blob_mismatch_aborts_before_any_file_write(tmp_path,monkeypatch):
    root=sample_root(tmp_path,"legacy")
    before={k:(root/k).read_bytes() for k in app.PATCHES}
    fake_remote(monkeypatch,altered="server.py")
    with pytest.raises(RuntimeError,match="REMOTE_GIT_BLOB_MISMATCH"):
        app.preflight(root)
    assert all((root/k).read_bytes()==value for k,value in before.items())


def test_dry_run_never_restarts_or_changes_source(tmp_path,monkeypatch):
    root=sample_root(tmp_path,"legacy")
    before={k:(root/k).read_bytes() for k in app.PATCHES}
    monkeypatch.setattr(app,"local_dashboard_source",lambda:root)
    fake_remote(monkeypatch)
    with mock.patch.object(app,"restart_dashboard") as restart:
        assert app.main([])==0
        restart.assert_not_called()
    assert all((root/k).read_bytes()==value for k,value in before.items())


@pytest.mark.parametrize("version",["baseline","legacy"])
def test_install_rolls_back_exact_source_bytes_on_failed_health(tmp_path,monkeypatch,version):
    root=sample_root(tmp_path,version)
    saved={k:(root/k).read_bytes() if (root/k).exists() else None
           for k in app.PATCHES}
    monkeypatch.setattr(app.Path,"home",lambda:tmp_path)
    restart_calls=[]
    monkeypatch.setattr(app,"restart_dashboard",lambda:restart_calls.append(True))
    def force_failure():
        raise RuntimeError("CONTROL_DB_MISMATCH")
    monkeypatch.setattr(app,"verify_dashboard",force_failure)
    def check_restored(root_arg,original):
        assert original==saved
        for name,data in saved.items():
            assert ((root_arg/name).read_bytes() if (root_arg/name).exists()
                    else None)==data
    monkeypatch.setattr(app,"verify_rollback",check_restored)
    new={name:git_blob(rec["target"]) for name,rec in app.PATCHES.items()}
    with pytest.raises(RuntimeError,match="CONTROL_DB_MISMATCH"):
        app.install(root,new)
    assert len(restart_calls)==2
    assert all(((root/name).read_bytes() if (root/name).exists() else None)==data
               for name,data in saved.items())
    assert not list(root.rglob(".frank-review-*"))
    assert not list(root.rglob(".frank-restore-*"))


def test_repeated_deploy_is_idempotent_and_never_kickstarts(tmp_path,monkeypatch):
    root=sample_root(tmp_path,"target")
    fake_remote(monkeypatch)
    monkeypatch.setattr(app,"local_dashboard_source",lambda:root)
    with mock.patch.object(app,"restart_dashboard") as kickstart, \
         mock.patch.object(app,"verify_dashboard") as readback:
        assert app.main(["--apply"])==0
    kickstart.assert_not_called()
    readback.assert_called_once()


def test_real_dashboard_http_and_sqlite_count_agree(tmp_path,monkeypatch):
    # The real DashboardState and actual ControlDB are used behind an HTTP
    # endpoint; the network target is 127.0.0.1, not the user's Mac daemon.
    import http.server
    import threading
    from mission_agent.mission_control.db import ControlDB
    from mission_agent.mission_control.server import DashboardState
    from test_delivery_review_integration import seed

    ctl=tmp_path/"control"
    ctl.mkdir()
    prod=tmp_path/"prod"
    prod.mkdir()
    db=ControlDB(ctl/"mission-control.sqlite")
    (ctl/"mission-control-health.json").write_text(json.dumps({"status":"OK"}))
    seed(db)
    for state in ("SENDING","SENT_UNVERIFIED","SENT_UNVERIFIED"):
        seed(db,state,attempts=1,gmail_attempts=1)
    state=DashboardState(prod,ctl)
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            body=json.dumps(state.mission_control_health()).encode()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    http=http.server.HTTPServer(("127.0.0.1",0),Handler)
    thread=threading.Thread(target=http.serve_forever,daemon=True)
    thread.start()
    monkeypatch.setattr(app,"control_root",lambda:ctl)
    monkeypatch.setattr(app,"health_endpoint",
                        lambda c:f"http://127.0.0.1:{http.server_port}/api/control-health")
    try:
        app.verify_dashboard()
    finally:
        http.shutdown()
        thread.join(timeout=2)
        http.server_close()
        db.close()


@pytest.mark.parametrize("kind",["legacy","self_consistent_wrong"])
def test_dashboard_verify_rejects_hidden_or_inaccurate_http_counts(tmp_path,monkeypatch,kind):
    from mission_agent.mission_control.db import ControlDB
    from test_delivery_review_integration import seed
    ctl=tmp_path/"control"
    ctl.mkdir()
    db=ControlDB(ctl/"mission-control.sqlite")
    seed(db,"SENT_UNVERIFIED",attempts=1,gmail_attempts=1)
    monkeypatch.setattr(app,"control_root",lambda:ctl)
    monkeypatch.setattr(app,"health_endpoint",lambda root:"http://127.0.0.1:9999/api/control-health")
    monkeypatch.setattr(app.time,"sleep",lambda _:None)
    if kind=="legacy":
        payload={"manual_review_breakdown_available":True,
                 "manual_review_expired_unsent_count":0,
                 "manual_review_actionable_count":0,"manual_review_total_count":0}
    else:
        payload={"manual_review_breakdown_available":True,
                 "manual_review_breakdown_error":None}
        payload.update({key:0 for key in app.actual_delivery_counts(ctl)})
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):return None
        def read(self,*args):return json.dumps(payload).encode()
    with mock.patch.object(app.urllib.request,"urlopen",return_value=Response()):
        with pytest.raises(RuntimeError,match="DASHBOARD_DATABASE_READBACK_FAILED"):
            app.verify_dashboard()
    db.close()
