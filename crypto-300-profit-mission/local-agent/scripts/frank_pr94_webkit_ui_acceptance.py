"""QA-only real WebKit against native localhost Dashboard, frozen PR94 + reviewed F01.

No real RPC, production data, wallet, file cleanup, Gmail, trades, or Mac service.
Run only from the disposable reviewed-source assembled CI checkout.
"""
from __future__ import annotations

from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import threading
import time

from playwright.sync_api import sync_playwright
from mission_agent.mission_control.server import Handler


A = "So11111111111111111111111111111111111111112"
B = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
RECEIPT = "PR94_REAL_WEBKIT_SYNTHETIC_NATIVE_HTTP_ACCEPTANCE_PASS"
OUTPUT = Path(os.environ.get("FRANK_PR94_WEBKIT_EVIDENCE_DIR", "/tmp/frank-pr94-webkit-evidence"))
VALID_PRICE = "0.012500"
NEW_PRICE = "0.021000"


def row(mint: str, decision: str, price: str) -> dict:
    observed = datetime.now(timezone.utc).isoformat()
    validated = {"execution_price_usdc": price, "price_impact_pct": "0.5"}
    return {
        "mint": mint, "person_id": "frank", "decision": decision,
        "source_signal_id": "qa-fixed-" + mint, "source_signal_type": "BUY",
        "pattern": "MULTIPLE", "episode_id": "SYNTHETIC_ONLY",
        "position_state": "OPEN", "latest_side": "BUY", "latest_at": time.time() - 3,
        "latest_buy_at": time.time() - 3, "decision_created_at": observed,
        "quote_observed_at": observed,
        "current_raw": "150000", "buy_count": 2, "sell_count": 0,
        "metrics": {"execution_price_usdc": price, "price_impact_pct": "0.5"},
        "decision_quote": {"status": "OK", "route_exists": True,
                           "execution_price_usdc": price, "price_impact_pct": "0.5"},
        "validated_follow_quote": validated,
        "latest_buy_price_usdc": "0.01",
    }


class ReadOnlySyntheticState:
    def __init__(self):
        self.mode = "valid"
        self.calls = 0
        self.invalid_runtime = False

    def runtime(self):
        return {"status": "LIVE", "heartbeat_age_seconds": 1}

    def mission_control_health(self):
        return {"status": "OK", "manual_review_breakdown_available": True,
                "manual_review_actionable_count": 0}

    def candidates(self):
        return []

    def follow_opportunities(self):
        self.calls += 1
        now = time.time()
        base = row(A, "BUY", VALID_PRICE)
        if self.mode == "drift" and self.calls > 1:
            # One independently refreshed F01 quote is different, same Mint and signal ID.
            base["validated_follow_quote"]["execution_price_usdc"] = NEW_PRICE
            base["decision_quote"]["execution_price_usdc"] = NEW_PRICE
            base["metrics"]["execution_price_usdc"] = NEW_PRICE
        if self.mode == "zero" and self.calls > 1:
            return {"status": "OK", "schema_version": 1, "as_of_epoch": now,
                    "eligible": [], "eligible_count": 0, "not_followed": [], "excluded_count": 0}
        return {"status": "OK", "schema_version": 1, "as_of_epoch": now,
                "eligible": [base], "eligible_count": 1, "not_followed": [],
                "excluded_count": 0}

    def recent_trades(self):
        return []

    def review_activity(self):
        return []

    def decisions(self):
        return []

    def activity_coverage(self):
        return {"status": "OK", "windows": {"24h": {
            "indexed_signatures": 2, "recognized_trades": 2,
            "recognized_buys": 2, "recognized_sells": 0,
            "unknown_needs_review": 0}, "7d": {}, "30d": {}}}

    def frank_observed_watchlist(self):
        return {"status": "OK", "summary": {}, "rows": []}


def native_server(state):
    class NativeHandler(Handler):
        pass

    NativeHandler.state = state
    server = ThreadingHTTPServer(("127.0.0.1", 0), NativeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def banner(page):
    page.evaluate("""() => {
      const div=document.createElement('aside');
      div.id='pr94-synthetic-only-banner';
      div.textContent='SYNTHETIC QA · 模拟数据 · 禁止交易 · PR94 WebKit 测试';
      div.style.cssText='position:sticky;top:0;z-index:999999;background:#fff4b5;color:#241b00;font:bold 16px sans-serif;padding:12px;text-align:center';
      document.body.prepend(div);
    }""")


def screenshot(page, filename):
    banner(page)
    page.screenshot(path=str(OUTPUT / filename), full_page=True, animations="disabled")


def card(page):
    return page.locator("#candidates .candidate-card").first


def verified(page):
    return card(page).get_attribute("data-f01-guard-state") == "VERIFIED"


def ensure(condition, text):
    if not condition:
        raise AssertionError(text)


def open_case(browser, base, state, mode, page_errors, console_errors, output):
    state.mode = mode
    state.calls = 0
    state.invalid_runtime = False
    page = browser.new_page(viewport={"width": 1440, "height": 900}, locale="zh-CN")
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.goto(base, wait_until="domcontentloaded", timeout=15000)
    page.locator("#candidates .candidate-card").first.wait_for(timeout=10000)
    ensure(page.locator("button.view-tab").count() == 2, "OFFICIAL_TWO_TABS_REQUIRED")
    ensure(page.locator("button[data-view='signals']").count() == 1, "F01_TAB_MISSING")
    ensure(page.locator("button[data-view='cluster']").count() == 1, "C02_TAB_MISSING")
    ensure(page.locator("button[data-view='f02']").count() == 0, "THIRD_F02_TAB_FORBIDDEN")
    if mode == "valid":
        page.wait_for_function("""() => document.querySelector('#candidates .candidate-card')?.dataset.f01GuardState === 'VERIFIED'""", timeout=10000)
        ensure("可跟" in card(page).locator(".candidate-head .badge").inner_text(),
               "FRESH_VERIFIED_BUY_NOT_VISIBLE")
        ensure(VALID_PRICE in page.locator("#candidates").inner_text(),
               "BUY_CARD_EXECUTABLE_QUOTE_MISSING")
        screenshot(page, "01-f01-verified-buy.png")
        page.locator("button[data-view='cluster']").click()
        ensure(page.locator("#cluster-view").evaluate("(el) => el.classList.contains('active')"),
               "C02_NAVIGATION_NOT_WORKING")
        screenshot(page, "02-c02-official-tab.png")
    elif mode in {"drift", "zero"}:
        page.wait_for_function("""() => {
          const el=document.querySelector('#candidates .candidate-card');
          return el && el.dataset.f01GuardState === 'UNVERIFIED';
        }""", timeout=10000)
        # The second F01 GET may still be in flight; wait until it completed.
        page.wait_for_timeout(800)
        ensure(not verified(page), mode + "_BUY_MUST_NOT_VERIFY")
        ensure("可跟" not in card(page).locator(".candidate-head .badge").inner_text(),
               mode + "_OLD_BUY_BADGE_STILL_GREEN")
        screenshot(page, "03-f01-"+mode+"-masked.png")
    elif mode == "expiry":
        page.wait_for_function("""() => document.querySelector('#candidates .candidate-card')?.dataset.f01GuardState === 'VERIFIED'""", timeout=10000)
        state.invalid_runtime = True
        page.wait_for_function("""() => document.querySelector('#candidates .candidate-card')?.dataset.f01GuardState === 'UNVERIFIED'""", timeout=13000)
        ensure("可跟" not in card(page).locator(".candidate-head .badge").inner_text(),
               "STALE_BUY_REMAINED_ACTIONABLE")
        screenshot(page, "04-f01-expired-with-runtime-unavailable.png")
    output.append({"case": mode, "result": "PASS", "f01_requests": state.calls})
    page.close()


def main():
    # Refuse to run as evidence against a different product without a new QA review.
    work = Path.cwd()
    ensure((work / "mission_agent/mission_control/static/frank_f01_primary_freshness.js").is_file(),
           "PR94_GUARD_NOT_PRESENT")
    expected = os.environ.get("FRANK_PR94_EXPECTED_SHA", "")
    ensure(expected == "19d5d8be92b944f1c9814a1f527d233290bf2dfc",
           "PR94_FIXED_SOURCE_SHA_REQUIRED")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    os.environ.pop("FRANK_SOURCE_CONTEXT_PORT", None)
    state = ReadOnlySyntheticState()
    server, thread = native_server(state)
    cases = []
    page_errors, console_errors = [], []
    try:
        with sync_playwright() as playwright:
            browser = playwright.webkit.launch(headless=True)
            try:
                base = "http://127.0.0.1:" + str(server.server_port) + "/"
                for scenario in ("valid", "drift", "zero", "expiry"):
                    open_case(browser, base, state, scenario,
                              page_errors, console_errors, cases)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    ensure(not thread.is_alive(), "NATIVE_LOCALHOST_LISTENER_LEAK")
    ensure(not page_errors, "PAGE_JS_ERRORS: " + repr(page_errors))
    # Missing optional research bridge (503) is expected: console errors may
    # exist due to intentional fail-closed source. Preserve, don't hide.
    receipt = {
        "status": RECEIPT, "product_sha": expected, "synthetic_only": True,
        "real_rpc": False, "wallet_production": False,
        "browser": "Playwright WebKit (NOT Safari.app)",
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "cases": cases, "page_errors": page_errors,
        "console_errors": console_errors,
        "server_closed": not thread.is_alive(),
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    ensure(len(cases) == 4, "INCOMPLETE_BROWSER_ACCEPTANCE")
    print(RECEIPT)


if __name__ == "__main__":
    main()
