"use strict";

/*
 * BSC V1 bounded manually started, READ-ONLY post-block Transfer log recorder.
 * Requires Node.js >=24 (native WebSocket). The DEFAULT is offline --dry-run.
 * --live requires an explicit BSC_WSS_URL environment variable and --output.
 * NO swaps, wallet, transactions, signals, email, alarms or background agent.
 * No provider URL / API key is ever written to the result JSON file.
 */
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const GRID = "bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json";
const GRID_BLOB = "f88ed9abfcb0f321ec31e98a029303aca48a8623";
const TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef";
const RESEARCH = __dirname;

function gitBlob(raw) {
    const preamble = Buffer.from("blob " + raw.length + "\0", "ascii");
    return crypto.createHash("sha1").update(preamble).update(raw).digest("hex");
}
function frozenGrid() {
    const raw = fs.readFileSync(path.join(RESEARCH, GRID));
    if (gitBlob(raw) !== GRID_BLOB) throw new Error("FROZEN_GRID_BLOB_MISMATCH");
    const data = JSON.parse(raw.toString("utf8"));
    const wallets = data.wallets.map(x => String(x.wallet).toLowerCase());
    const cas = data.markets.map(x => String(x.ca).toLowerCase());
    if (wallets.length !== 23 || cas.length !== 19
            || new Set(wallets).size !== 23 || new Set(cas).size !== 19) {
        throw new Error("FROZEN_23X19_DENOMINATOR_DRIFT");
    }
    return { wallets, cas };
}
function word(addr) { return "0x" + "0".repeat(24) + addr.slice(2).toLowerCase(); }
function args(argv) {
    const a = { live: false, duration: 120, maxEvents: 100, output: null };
    for (let i = 0; i < argv.length; i++) {
        const opt = argv[i];
        if (opt === "--dry-run") {
            a.live = false;
        } else if (opt === "--live") {
            a.live = true;
        } else if (["--duration-seconds", "--max-events", "--output"].includes(opt)) {
            if (i + 1 >= argv.length) throw new Error("ARG_VALUE_MISSING:" + opt);
            const v = argv[++i];
            if (opt === "--duration-seconds") a.duration = Number(v);
            if (opt === "--max-events") a.maxEvents = Number(v);
            if (opt === "--output") a.output = v;
        } else {
            throw new Error("UNKNOWN_ARG:" + opt);
        }
    }
    if (!Number.isInteger(a.duration) || a.duration < 1 || a.duration > 600)
        throw new Error("DURATION_MUST_BE_1_TO_600_SECONDS");
    if (!Number.isInteger(a.maxEvents) || a.maxEvents < 1 || a.maxEvents > 250)
        throw new Error("MAX_EVENTS_MUST_BE_1_TO_250");
    if (a.live && !a.output) throw new Error("LIVE_OUTPUT_PATH_REQUIRED");
    return a;
}
function subscriptionFilter(grid) {
    return { address: grid.cas, topics: [TRANSFER, null, grid.wallets.map(word)] };
}
function clockClaim() {
    const src = process.env.BSC_CLOCK_SYNC_SOURCE;
    const offset = process.env.BSC_CLOCK_MAX_ABS_OFFSET_MS;
    const n = Number(offset);
    if (src && offset !== undefined && Number.isFinite(n) && n >= 0 && n < 10000) {
        return { sync_state: "REPORTED_SYNCED", source: src,
                 max_abs_offset_ms: n, independence: "SELF_REPORTED_NOT_ATTESTED" };
    }
    return { sync_state: "UNKNOWN", source: "NO_CALIBRATION_SUPPLIED",
             max_abs_offset_ms: null, independence: "NOT_ATTESTED" };
}
function main() {
    const a = args(process.argv.slice(2));
    const grid = frozenGrid();
    const filter = subscriptionFilter(grid);
    if (!a.live) {
        process.stdout.write(JSON.stringify({
            mode: "OFFLINE_DRY_RUN_NO_NETWORK",
            websocket_method: "eth_subscribe",
            params: ["logs", filter],
            original_wallets: 23, exact_cas: 19,
            duration_seconds_if_live: a.duration,
            max_events_if_live: a.maxEvents,
            means_original_wallet_signed_buy: false,
            production: "NO_GO"
        }, null, 2) + "\n");
        return;
    }
    if (typeof WebSocket !== "function") throw new Error("NODE_24_NATIVE_WEBSOCKET_REQUIRED");
    const wss = process.env.BSC_WSS_URL;
    if (!wss) throw new Error("BSC_WSS_URL_ENV_REQUIRED");
    const target = new URL(wss);
    if (target.protocol !== "wss:" || target.username || target.password)
        throw new Error("WSS_SECURE_URL_REQUIRED");
    if (fs.existsSync(a.output)) throw new Error("OUTPUT_EXISTS_REFUSE_OVERWRITE");
    const started = new Date().toISOString();
    const id = "bsc-freeze-" + crypto.randomBytes(8).toString("hex");
    const events = [];
    const accepted = new Set();
    let subscriptionId = null, providerChainId = null, finished = false, timer = null, ws;
    let frames = 0, ignored = 0, state = "NOT_CONNECTED";

    function finish(why) {
        if (finished) return;
        finished = true;
        if (timer) clearTimeout(timer);
        try { if (ws) ws.close(1000, "bounded manual capture finished"); } catch (_) {}
        const output = {
            schema: "BSC_P4B_PUBLIC_OBSERVER_INGRESS_V1",
            capture_mode: "BOUNDED_PUBLIC_MINED_LOGS_ONLY_NOT_PENDING",
            run_id: id,
            network: "bnb-mainnet",
            provider_chain_id_confirmed: providerChainId,
            started_at_utc: started,
            stopped_at_utc: new Date().toISOString(),
            stop_reason: why, subscription_status: state,
            event_frames_seen: frames, locally_ignored_frames: ignored,
            provider_id: "MANUAL_WSS_NODE_URL_NOT_STORED",
            original_wallets: grid.wallets.length, exact_cas: grid.cas.length,
            clock_evidence: clockClaim(), events,
            approval: "NO_GO_NO_TRADE_NO_GMAIL_NO_DEPLOY",
            limitations: ["TRANSFER_TO_WALLET_NOT_SIGNED_SWAP",
                          "LOCAL_RECEIVED_AT_CLAIM_NOT_GLOBAL_PUBLIC_FIRST_SEEN",
                          "PENDING_MEMPOOL_FIRST_SEEN_NOT_CAPTURED",
                          "ROUTER_COST_AND_FOLLOWER_EXECUTION_NOT_PROVEN"]
        };
        // Exclusive creation; do not silently overwrite prior evidence.
        const fd = fs.openSync(a.output, "wx", 0o600);
        try { fs.writeFileSync(fd, JSON.stringify(output, null, 2) + "\n"); }
        finally { fs.closeSync(fd); }
        process.stdout.write(JSON.stringify({
            mode: "LIVE_READ_ONLY_CAPTURE_STOPPED",
            saved_to: a.output, events: events.length,
            stop_reason: why, subscription_status: state,
            public_U_verified: false, production: "NO_GO"
        }) + "\n");
        if (why.startsWith("PROVIDER_ERROR")) process.exitCode = 2;
        if (why === "MANUALLY_TERMINATED_SIGTERM") process.exitCode = 143;
    }

    ws = new WebSocket(wss);
    timer = setTimeout(() => finish("BOUND_DURATION_COMPLETE"), a.duration * 1000);
    ws.addEventListener("open", () => {
        state = "OPEN_VERIFYING_BNB_CHAIN";
        ws.send(JSON.stringify({ jsonrpc: "2.0", id: 1, method: "eth_chainId", params: [] }));
    });
    ws.addEventListener("message", e => {
        if (finished) return;
        const receivedAtUtc = new Date().toISOString();
        const monotonic = process.hrtime.bigint().toString();
        const raw = Buffer.from(String(e.data), "utf8");
        frames++;
        if (raw.length > 262144) { ignored++; return; }
        let frame;
        try { frame = JSON.parse(raw.toString("utf8")); }
        catch (_) { ignored++; return; }
        if (frame.id === 1 && state === "OPEN_VERIFYING_BNB_CHAIN") {
            if (frame.error || typeof frame.result !== "string" || !/^0x0*38$/i.test(frame.result))
                return finish("PROVIDER_ERROR_WRONG_CHAIN_ID");
            providerChainId = "0x38";
            state = "OPEN_SUBSCRIBING";
            ws.send(JSON.stringify({ jsonrpc: "2.0", id: 2, method: "eth_subscribe",
                                     params: ["logs", filter] }));
            return;
        }
        if (frame.id === 2 && state === "OPEN_SUBSCRIBING") {
            if (frame.error) return finish("PROVIDER_ERROR_SUBSCRIPTION_REFUSED");
            subscriptionId = frame.result || null;
            if (!subscriptionId) return finish("PROVIDER_ERROR_MISSING_SUBSCRIPTION");
            state = "SUBSCRIBED_OK";
            return;
        }
        if (state !== "SUBSCRIBED_OK" || frame.method !== "eth_subscription"
                || !frame.params || frame.params.subscription !== subscriptionId) {
            ignored++; return;
        }
        const log = frame.params.result;
        if (!log || typeof log !== "object"
                || typeof log.address !== "string" || !grid.cas.includes(log.address.toLowerCase())
                || !Array.isArray(log.topics) || log.topics.length !== 3
                || String(log.topics[0]).toLowerCase() !== TRANSFER
                || typeof log.topics[2] !== "string") {
            ignored++; return;
        }
        const wallet = "0x" + log.topics[2].slice(-40).toLowerCase();
        if (!grid.wallets.includes(wallet) || word(wallet) !== log.topics[2].toLowerCase()) {
            ignored++; return;
        }
        if (!/^0x[0-9a-fA-F]{64}$/.test(String(log.transactionHash))
                || !/^0x[0-9a-fA-F]{64}$/.test(String(log.blockHash))
                || typeof log.logIndex !== "string") {
            ignored++; return;
        }
        const uid = (String(log.blockHash) + ":" + log.transactionHash + ":" + log.logIndex).toLowerCase();
        const isRemoved = log.removed === true;
        const eventUid = uid + (isRemoved ? ":REMOVED" : ":INCLUDED");
        if (accepted.has(eventUid)) { ignored++; return; }
        accepted.add(eventUid);
        // A reorg emits the SAME blockHash/txHash/logIndex with removed=true.
        // Preserve both arrival and reversal as separate immutable evidence rows.
        events.push({
            event_id: id + ":" + eventUid,
            network: "bnb-mainnet",
            provider_chain_id: providerChainId,
            wallet, exact_ca: log.address.toLowerCase(),
            tx_hash: log.transactionHash.toLowerCase(),
            capture_kind: "PUBLIC_CONFIRMED_ERC20_TRANSFER_LOG_INGRESS",
            raw_event_base64: raw.toString("base64"),
            raw_sha256: crypto.createHash("sha256").update(raw).digest("hex"),
            observer_received_utc: receivedAtUtc,
            observer_monotonic_ns: monotonic,
            capture_machine_id: id,
            provider_id: "PUBLIC_BNB_WEBSOCKET_MANUAL",
            clock_sync: clockClaim()
        });
        if (events.length >= a.maxEvents) finish("MAX_EVENTS_REACHED");
    });
    ws.addEventListener("error", () => {
        if (!finished) finish("PROVIDER_ERROR_WEBSOCKET");
    });
    ws.addEventListener("close", () => {
        if (!finished) finish("PROVIDER_ERROR_SOCKET_CLOSED");
    });
    process.once("SIGINT", () => finish("MANUALLY_STOPPED"));
    process.once("SIGTERM", () => finish("MANUALLY_TERMINATED_SIGTERM"));
}
try { main(); }
catch (err) { process.stderr.write("BSC_READONLY_COLLECTOR_ERROR:" + err.message + "\n"); process.exitCode = 1; }
