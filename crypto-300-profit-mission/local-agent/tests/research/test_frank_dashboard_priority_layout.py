"""Frank Dashboard navigation and DOM priority only; no live trading or API calls."""
from html.parser import HTMLParser
from pathlib import Path


STATIC = Path(__file__).resolve().parents[2] / "mission_agent/mission_control/static"


class HTMLIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.identifiers = []
        self.section_ids = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        ident = data.get("id")
        if ident:
            self.identifiers.append(ident)
            if tag in {"section", "details"}:
                self.section_ids.append(ident)


def parsed():
    markup = (STATIC / "index.html").read_text(encoding="utf-8")
    page = HTMLIds()
    page.feed(markup)
    return markup, page


def test_follow_opportunities_before_overview_trades_and_watch_pool():
    markup, page = parsed()
    expected = [
        "follow-opportunities",
        "stats",
        "frank-watch-panel",
        "decision-history",
        "coverage-details",
    ]
    order = page.identifiers
    assert all(order.count(name) == 1 for name in expected)
    # "trades" is an inner feed div; its section must precede the watch table.
    assert order.index("follow-opportunities") < order.index("stats")
    assert order.index("stats") < order.index("trades")
    assert order.index("trades") < order.index("frank-watch-panel")
    assert order.index("frank-watch-panel") < order.index("decision-history")
    assert order.index("decision-history") < order.index("coverage-details")
    assert 'id="signals-view"' in markup
    assert 'id="cluster-view"' in markup


def test_no_duplicate_dom_ids_and_all_runtime_bindings_retained():
    _markup, page = parsed()
    assert len(page.identifiers) == len(set(page.identifiers))
    for ident in (
        "candidates", "updated", "stats", "trades", "watch-search", "watch-filter",
        "watch-rows", "watch-summary", "watch-total-count", "watch-scope",
        "decisions", "ended", "review-activity", "coverage", "runtime",
        "cluster-form", "cluster-mint", "cluster-submit",
    ):
        assert ident in page.identifiers


def test_priority_panel_states_are_explanatory_not_executable():
    markup, _page = parsed()
    css = (STATIC / "styles.css").read_text(encoding="utf-8")
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert 'id="follow-opportunities"' in markup
    assert "WAIT / NO_BUY 不是买入信号" in markup
    assert "观察池不触发提醒或交易" in markup
    assert ".priority-panel" in css
    assert "function renderCandidates(rows)" in js
    assert "function renderTrades(rows)" in js
    assert "function renderFrankWatchlist(payload)" in js
    assert "当前没有需要跟踪的 Frank 候选" in js


def test_ca_research_form_and_history_sections_not_removed():
    markup, page = parsed()
    assert "CA 链上查询" in markup
    assert "历史判断记录" in markup
    assert "最近结束" in markup
    assert "待复核链上行为" in markup
    assert "数据来源与覆盖范围" in markup
    assert "Frank 最近买卖" in markup
    assert "Frank 持续观察池" in markup
    assert "当前跟单机会" in markup
    assert "cluster-form" in page.identifiers
