"""Real serve path under a bounded synthetic localhost Dashboard GET burst."""
import json
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from mission_agent.mission_control import server as product


def test_dashboard_serves_parallel_panel_reads_without_connection_resets(tmp_path, monkeypatch):
    state=SimpleNamespace(
        runtime=lambda:{'status':'TEST_FIXTURE'},
        mission_control_health=lambda:{'status':'TEST_FIXTURE'},
        candidates=lambda:[],
        follow_opportunities=lambda:{'status':'TEST_FIXTURE','eligible':[]},
    )
    # Capture the server created by the actual serve() entry point so it can be
    # closed; older source has only the stdlib class, which exposes the defect.
    real_class=getattr(product,'DashboardHTTPServer',product.ThreadingHTTPServer)
    ready=threading.Event();instances=[]
    def factory(*args,**kwargs):
        instance=real_class(*args,**kwargs);instances.append(instance);ready.set();return instance
    monkeypatch.setattr(product,'DashboardState',lambda *_:state)
    monkeypatch.setattr(product,'ThreadingHTTPServer',factory)
    monkeypatch.setattr(product,'DashboardHTTPServer',factory,raising=False)
    monkeypatch.setattr(product.Handler,'log_message',lambda *_:None)
    had_state=hasattr(product.Handler,'state');prior_state=getattr(product.Handler,'state',None)
    thread=threading.Thread(target=product.serve,args=(tmp_path/'prod',tmp_path/'control','127.0.0.1',0),daemon=True)
    thread.start();assert ready.wait(3),'temporary server startup'
    httpd=instances[0];origin='http://127.0.0.1:'+str(httpd.server_port)
    paths=['/api/runtime','/api/control-health','/api/candidates','/api/follow-opportunities']
    def read(index):
        try:
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(origin+paths[index%4],timeout=5) as response:
                value=json.load(response)
                return response.status==200 and (value==[] or value.get('status')=='TEST_FIXTURE')
        except OSError:
            return False
    try:
        with ThreadPoolExecutor(max_workers=24) as pool:
            results=list(pool.map(read,range(100)))
        assert all(results),f'{sum(results)}/100 parallel panel reads succeeded'
    finally:
        httpd.shutdown();httpd.server_close();thread.join(3)
        if had_state:product.Handler.state=prior_state
        else:delattr(product.Handler,'state')
    assert not thread.is_alive()
