(() => {
  "use strict";
  const API = "/api/research/positions";
  const ADDRESS = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
  const STATES = Object.freeze({
    OPEN_ACCOUNT_NONZERO: ["已核实非零", "positive"],
    OPEN_ACCOUNT_ZERO: ["已观察为零", "zero"],
    NO_OPEN_ACCOUNT_OBSERVED: ["未观察到开放账户", "absent"],
    SOURCE_UNAVAILABLE: ["来源不可用", "unknown"]
  });
  const READINESS = Object.freeze({
    FRESH_VERIFIED_ARCHIVED_OBSERVATION: ["来源有效的归档观察", "仅在核验通过、时效未过期时展示观察数量。"],
    STALE_ARCHIVED_SOURCE: ["来源已过期", "归档仍可追溯，但不能继续当作当前持仓；请手动另行采集并核验。"],
    LATEST_CAPTURE_ATTEMPT_FAILED: ["最近一次采集失败", "旧余额已遮罩，不能把此前的正余额当作当前持仓。"],
    LATEST_SOURCE_NOT_WIRE_VERIFIED: ["较新来源未经原文验证", "只有匹配完整原始 RPC 证据的最新来源才能显示余额。"],
    INCOMPLETE_OR_NO_LATEST_CAPTURE: ["没有完整双程序来源", "来源缺失或部分失败；无法核实当前余额。"]
  });
  let latest = null;
  const $ = (id) => document.getElementById(id);
  const text = (id, value) => { $(id).textContent = String(value ?? "—"); };
  const validAddress = (value) => typeof value === "string" && ADDRESS.test(value);
  const shorten = (value, first = 8, last = 6) => {
    if (typeof value !== "string") return "—";
    return value.length > first + last + 4
      ? value.slice(0, first) + "…" + value.slice(-last) : value;
  };
  const formatTime = (raw) => {
    if (!raw || !Number.isFinite(Date.parse(raw))) return "未核实";
    return new Date(raw).toLocaleString("zh-CN", { hour12: false });
  };
  const formatAge = (seconds) => {
    if (!Number.isFinite(seconds) || seconds < 0) return "来源年龄未知";
    if (seconds < 60) return seconds + " 秒前";
    if (seconds < 3600) return Math.floor(seconds / 60) + " 分钟前";
    return Math.floor(seconds / 3600) + " 小时 " + Math.floor(seconds % 3600 / 60) + " 分钟前";
  };
  const validated = (doc) => Boolean(
    doc && doc.kind === "F02_RESEARCH_ARCHIVED_OWNER_POSITIONS" &&
    typeof doc.person_id === "string" && validAddress(doc.wallet) &&
    doc.target_mint_count === 32 && Array.isArray(doc.mints) &&
    doc.mints.length === 32 && doc.mints.every(item => item && validAddress(item.mint))
  );
  function safeObservation(doc) {
    // The API has an approved independent UTC tie P3. Even where the API
    // says FRESH, the view refuses to display quantities if latest attempt
    // metadata is inconsistent with a complete source.
    return validated(doc) &&
      doc.readiness === "FRESH_VERIFIED_ARCHIVED_OBSERVATION" &&
      doc.archive_observation_usable === true &&
      doc.capture_fresh === true &&
      typeof doc.latest_capture_sha256 === "string" &&
      doc.latest_capture_sha256 === doc.verified_full_wire_capture_sha256 &&
      doc.latest_attempt_source_status === "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC" &&
      doc.source_observation_status === "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC" &&
      doc.latest_attempt_capture_sha256 === doc.latest_capture_sha256;
  }
  function make(tag, cls, value) {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (value !== undefined) el.textContent = String(value);
    return el;
  }
  function clear(container) {
    while (container.firstChild) container.removeChild(container.firstChild);
  }
  async function copyValue(value, button) {
    if (!value || !navigator.clipboard || !navigator.clipboard.writeText) {
      button.textContent = "无法复制";
      return;
    }
    try {
      await navigator.clipboard.writeText(value);
      button.textContent = "已复制";
    } catch (_) {
      button.textContent = "复制失败";
    }
  }
  function bindCopy(id, value) {
    const button = $(id);
    button.disabled = !value;
    button.onclick = value ? () => copyValue(value, button) : null;
  }
  function renderRows(doc, observationSafe) {
    const body = $("position-rows");
    clear(body);
    const search = $("mint-search").value.trim().toLowerCase();
    const filter = $("state-filter").value;
    const selected = doc.mints.filter(row => {
      const state = observationSafe ? row.state : "SOURCE_UNAVAILABLE";
      return row.mint.toLowerCase().includes(search) &&
        (filter === "all" || state === filter);
    });
    selected.forEach((item, index) => {
      const state = observationSafe ? item.state : "SOURCE_UNAVAILABLE";
      const descriptor = STATES[state] || STATES.SOURCE_UNAVAILABLE;
      const tr = make("tr");
      const mintCell = make("td");
      mintCell.append(make("code", "mint-code", item.mint));
      mintCell.append(make("div", "mint-secondary", "目标 " + (doc.mints.indexOf(item) + 1) + " / 32"));
      const stateCell = make("td");
      stateCell.append(make("span", "pill " + descriptor[1], descriptor[0]));
      const qtyCell = make("td", "number",
        observationSafe && item.observed_raw_amount !== null &&
        typeof item.observed_quantity === "string" ? item.observed_quantity : "—");
      const accountsCell = make("td", "number",
        observationSafe && Number.isInteger(item.token_account_count)
          ? item.token_account_count : "—");
      const actions = make("td");
      const holder = make("div", "row-actions");
      const copy = make("button", "", "复制 CA");
      copy.type = "button";
      copy.addEventListener("click", () => copyValue(item.mint, copy));
      holder.append(copy);
      const explorer = make("a", "", "Solscan ↗");
      explorer.href = "https://solscan.io/token/" + encodeURIComponent(item.mint);
      explorer.target = "_blank";
      explorer.rel = "noopener noreferrer";
      holder.append(explorer);
      actions.append(holder);
      tr.append(mintCell, stateCell, qtyCell, accountsCell, actions);
      body.append(tr);
    });
    if (!selected.length) {
      const tr = make("tr");
      const td = make("td", "empty", "没有符合条件的研究目标");
      td.colSpan = 5;
      tr.append(td);
      body.append(tr);
    }
    text("row-total", "显示 " + selected.length + " / 32 个冻结研究目标；该列表不构成跟单建议。");
  }
  function render(doc) {
    if (!validated(doc)) throw new Error("研究数据结构不完整");
    latest = doc;
    const safe = safeObservation(doc);
    const mismatch = doc.readiness === "FRESH_VERIFIED_ARCHIVED_OBSERVATION" && !safe;
    const readiness = mismatch
      ? ["来源信息不一致", "最新采集状态与完整来源信息不一致，页面已隐藏数量。"]
      : (READINESS[doc.readiness] || ["来源不可用", "无法核实当前状态。"]);
    text("source-state", readiness[0]);
    text("source-explainer", readiness[1]);
    $("source-state").parentElement.className = "status-panel " + (safe ? "fresh" : "stale");
    text("warning", safe
      ? "已核验的归档观察不构成可交易仓位或跟单信号，且来源将随时间失效。"
      : "此研究来源不可当作当前余额：全部数量已隐藏。刷新本页面只读取旧档案，不会重新采集链上数据。");
    text("person", doc.person_id + " · " + doc.wallet_binding_role);
    text("wallet", doc.wallet);
    bindCopy("copy-wallet", doc.wallet);
    text("observed-time", formatTime(doc.capture_observed_at_utc));
    text("age", "采集于 " + formatAge(doc.capture_age_seconds) + " · TTL " + doc.max_age_seconds + " 秒");
    text("slots", doc.slot_min !== null && doc.slot_max !== null
      ? doc.slot_min + " – " + doc.slot_max : "未核实");
    text("source-hash", shorten(doc.verified_full_wire_capture_sha256, 14, 10));
    bindCopy("copy-hash", doc.verified_full_wire_capture_sha256);
    text("latest-attempt", "最近尝试：" + (doc.latest_attempt_source_status || "未知") +
      " · " + formatTime(doc.latest_attempt_observed_at_utc));
    text("count-total", doc.target_mint_count);
    const rows = safe ? doc.mints : [];
    text("count-positive", rows.filter(x => x.state === "OPEN_ACCOUNT_NONZERO").length);
    text("count-zero", rows.filter(x => x.state === "OPEN_ACCOUNT_ZERO").length);
    text("count-unknown", safe ? rows.filter(x => x.state === "SOURCE_UNAVAILABLE").length : 32);
    renderRows(doc, safe);
  }
  function renderError(status) {
    latest = null;
    text("source-state", "无法读取隔离研究来源");
    text("source-explainer", "本机只读 API 返回 " + status + "；未连接生产数据库，也没有自动重试 RPC。");
    $("source-state").parentElement.className = "status-panel error";
    text("warning", "研究来源错误：不显示任何余额，不会退回旧仓位。请检查隔离研究进程与原始来源。");
    ["count-total","count-positive","count-zero","count-unknown","person","wallet",
      "observed-time","age","slots","source-hash","latest-attempt"].forEach(id => text(id, "—"));
    bindCopy("copy-wallet", null);
    bindCopy("copy-hash", null);
    const body = $("position-rows");
    clear(body);
    const row = make("tr");
    const cell = make("td", "empty", "来源不可用，无法核实研究余额");
    cell.colSpan = 5;
    row.append(cell);
    body.append(row);
    text("row-total", "无可用来源，未展示仓位。");
  }
  async function load() {
    $("reload").disabled = true;
    try {
      const response = await fetch(API, { cache: "no-store", credentials: "omit" });
      if (!response.ok) throw new Error("HTTP " + response.status);
      render(await response.json());
    } catch (error) {
      renderError(error && error.message ? error.message.slice(0, 64) : "UNKNOWN");
    } finally {
      $("reload").disabled = false;
    }
  }
  function init() {
    $("reload").addEventListener("click", load);
    $("mint-search").addEventListener("input", () => { if (latest) renderRows(latest, safeObservation(latest)); });
    $("state-filter").addEventListener("change", () => { if (latest) renderRows(latest, safeObservation(latest)); });
    load();
  }
  // Small, pure contract functions for standalone Node regression; no
  // network/socket activation unless the real browser has the static DOM.
  if (typeof window !== "undefined") {
    window.FrankF02Contract = Object.freeze({ validated, safeObservation, shorten });
  }
  if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
