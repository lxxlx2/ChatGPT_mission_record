"""Watch pool is opt-in research; urgent follow decisions always come first."""
from html.parser import HTMLParser
from pathlib import Path

STATIC = Path(__file__).resolve().parents[2] / "mission_agent/mission_control/static"


class AuditHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
        self.tags = []

    def handle_starttag(self, tag, attrs):
        vals = dict(attrs)
        self.tags.append((tag, vals))
        if tag not in {"meta","link","input","img","br","hr","source"}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in {"meta", "link", "input", "img", "br", "hr", "source"}:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(tag)
        else:
            self.stack.pop()


def test_collapsed_watch_panel_is_accessible_and_not_urgent_decision():
    html = (STATIC / "index.html").read_text()
    fragment = html[html.index('id="frank-watch-panel"'):]
    assert html.index('id="follow-opportunities"') < html.index('id="trades"')
    assert html.index('id="trades"') < html.index('id="frank-watch-panel"')
    assert '<details class="panel frank-watch-panel ended-panel" id="frank-watch-panel">' in html
    assert ' open' not in fragment[:fragment.index("</summary>")]
    assert '<summary class="panel-title">' in fragment[:400]
    assert 'id="watch-focus-count"' in fragment
    assert 'id="watch-total-count"' in fragment
    assert '观察池不代表可跟单机会' in fragment
    assert '</details>' in fragment


def test_watch_filters_and_api_binding_ids_preserved():
    html = (STATIC / "index.html").read_text()
    js = (STATIC / "app.js").read_text()
    parser = AuditHTML()
    parser.feed(html)
    assert parser.errors == [] and parser.stack == []
    ids = [attrs["id"] for _, attrs in parser.tags if "id" in attrs]
    assert len(ids) == len(set(ids))
    for ident in ("watch-rows","watch-filter","watch-search","watch-summary",
                  "watch-focus-count","watch-total-count","watch-scope",
                  "candidates","trades","stats","cluster-form"):
        assert ids.count(ident) == 1
    assert "$('watch-focus-count').textContent = String(focusCount);" in js
    assert "' · 重点待观察 ' + String(focusCount)" in js
    assert "function renderFrankWatchlist(payload)" in js


def test_watch_research_not_turned_into_trade_or_mail_signal():
    js = (STATIC / "app.js").read_text()
    html = (STATIC / "index.html").read_text()
    assert "观察池不触发提醒或交易" in html
    assert "SNAPSHOT_NONZERO" in html
    assert "本地模型持有" in html
    assert "仅被动转入" in html
    assert "renderFrankWatchlist(watch);" in js
    css = (STATIC / "styles.css").read_text()
    assert ".frank-watch-panel>summary" in css
    assert ".frank-watch-panel[open]>summary" in css
