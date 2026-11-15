"""Multi-mint injected source capture and pure USD reference valuation."""
import copy
import hashlib
import io
import json
import urllib.error
from decimal import Decimal
import pytest

from mission_agent.meme.holder_ranks import _b58
from mission_agent.meme.market import DexScreenerMarketClient
from mission_agent.mission_control.market_observations import (
    capture_market, normalize_market, portfolio_valuation,
)


def key(n):
    return _b58(n.to_bytes(32, "big"))


def snapshot(mint, price="2.5", when=100):
    return {"status": "OK", "source": "DEXSCREENER_API", "mint": mint,
            "observed_at": when, "price_usd": price,
            "market_cap_usd": "10", "fdv_usd": "20",
            "main_pair": {"pair_address": key(5000), "base_address": mint,
                          "quote_address": key(6000), "dex_id": "example",
                          "liquidity_usd": "30", "volume": {"h24": "0"}}}


class Client:
    def __init__(self, values):
        self.values, self.calls = values, []

    def token_snapshot(self, mint):
        self.calls.append(mint)
        value = self.values[mint]
        if isinstance(value, Exception):
            raise value
        return copy.deepcopy(value)


def test_all_distinct_mints_without_fixed_cohort_truncation_and_duplicate_source_reads():
    mints = [key(i) for i in range(1, 42)]
    client = Client({m: snapshot(m) for m in mints})
    result = capture_market(mints + [mints[0]], client, clock=lambda: 101)
    assert client.calls == mints
    assert len(result) == 41
    assert all(row["status"] == "OK" for row in result)
    assert {r["mint"] for r in result} == set(mints)


def test_failed_mints_and_no_pair_recorded_without_erasing_success_or_exposing_exception():
    a, b, c = key(1), key(2), key(3)
    client = Client({a: snapshot(a), b: TimeoutError("https://secret.invalid/key"),
                     c: {"status": "UNAVAILABLE", "source": "DEXSCREENER_API",
                         "reason": "NO_BASE_TOKEN_PAIR", "observed_at": 100}})
    out = capture_market([a, b, c, "invalid"], client, clock=lambda: 101)
    assert len(out) == 4 and sum(row["status"] == "OK" for row in out) == 1
    assert [r["reason"] for r in out] == [None, "SOURCE_TIMEOUT", "NO_BASE_TOKEN_PAIR", "MINT_INVALID"]
    assert "secret" not in str(out)
    assert client.calls == [a, b, c]


@pytest.mark.parametrize("mutation,reason", [
    (lambda s: s.update(mint=key(9)), "MINT_IDENTITY_MISMATCH"),
    (lambda s: s.update(chainId="ethereum"), "CHAIN_IDENTITY_MISMATCH"),
    (lambda s: s["main_pair"].update(chain_id="base"), "PAIR_IDENTITY_MISMATCH"),
    (lambda s: s["main_pair"].update(base_address=key(9)), "PAIR_IDENTITY_MISMATCH"),
    (lambda s: s["main_pair"].update(pair_address=key(1)), "PAIR_IDENTITY_MISMATCH"),
    (lambda s: s["main_pair"].update(quote_address=key(1)), "PAIR_IDENTITY_MISMATCH"),
    (lambda s: s.update(source="OTHER"), "SOURCE_IDENTITY_MISMATCH"),
])
def test_exact_chain_mint_and_pair_identity(mutation, reason):
    value = snapshot(key(1)); mutation(value)
    out = normalize_market(key(1), value, received_at=101)
    assert out["reason"] == reason and out["price_usd"] is None


@pytest.mark.parametrize("price", [None, "NaN", "Infinity", "-Infinity", "-1", "0", True, "bad"])
def test_price_is_finite_positive_decimal_or_explicitly_unpriced(price):
    out = normalize_market(key(1), snapshot(key(1), price), received_at=101)
    assert out["status"] == "UNAVAILABLE" and out["price_usd"] is None


def test_canonical_source_hash_and_observation_hash_do_not_mutate_input():
    value = snapshot(key(1)); original = copy.deepcopy(value)
    a = normalize_market(key(1), value, received_at=101)
    b = normalize_market(key(1), dict(reversed(list(value.items()))), received_at=101)
    assert value == original
    assert a["source_payload_sha256"] == b["source_payload_sha256"]
    assert a["observation_sha256"] == b["observation_sha256"]
    assert a["source_hash_kind"] == "CANONICAL_CLIENT_SNAPSHOT_NOT_RAW_HTTP"
    assert a["source_market_asof"] is None
    assert a["volume_h24_usd"] == "0"


@pytest.mark.parametrize("when,reason", [(None, "OBSERVATION_TIME_INVALID"),
                                        (True, "OBSERVATION_TIME_INVALID"),
                                        (102, "FUTURE_OBSERVATION")])
def test_source_time_unavailable_or_future_never_inherits_current_clock(when, reason):
    out = normalize_market(key(1), snapshot(key(1), when=when), received_at=101)
    assert out["reason"] == reason and out["price_usd"] is None


def test_pure_valuation_all_provided_positions_exact_quantity_usd_not_usdc(monkeypatch):
    a, b = key(1), key(2)
    capture = capture_market([a, b], Client({a: snapshot(a, "1.0000000000000000000000000001"),
                                            b: snapshot(b, "3")}), clock=lambda: 101)
    # The getter has no client or transport, and must not use wall-clock time.
    monkeypatch.setattr("time.time", lambda: (_ for _ in ()).throw(AssertionError("NO_WALL_CLOCK")))
    out = portfolio_valuation([{"mint": a, "raw": "1000000", "decimals": 6},
                               {"mint": b, "raw": 2000000, "decimals": 6}], capture, 101)
    assert Decimal(out["total_value_usd"]) == Decimal("7.0000000000000000000000000001")
    assert out["currency"] == "USD" and out["covered_positions"] == 2
    assert out["valuation_complete_for_provided_positions"]
    assert out["pnl_calculated"] is False and out["executable_quote"] is False
    assert out["scope"] == "PROVIDED_POSITIONS_ONLY"


@pytest.mark.parametrize("as_of,reason", [(161, "STALE_OBSERVATION"), (99, "FUTURE_OBSERVATION")])
def test_old_or_future_price_leaves_value_unknown(as_of, reason):
    market = normalize_market(key(1), snapshot(key(1)), received_at=101)
    out = portfolio_valuation([{"mint": key(1), "raw": "5", "decimals": 0}], [market], as_of)
    assert out["rows"][0]["reason"] == reason
    assert out["rows"][0]["value_usd"] is None and out["total_value_usd"] is None
    assert out["unpriced_positions"] == 1


def test_mixed_missing_price_never_turns_priced_subtotal_into_total_nav():
    a, b, c = key(1), key(2), key(3)
    observations = [normalize_market(a, snapshot(a), received_at=101),
                    normalize_market(b, snapshot(b, None), received_at=101)]
    positions = [{"mint": m, "raw": "100", "decimals": 2} for m in [a, b, c]]
    out = portfolio_valuation(positions, observations, 101)
    assert out["priced_subtotal_usd"] == "2.500"
    assert out["total_value_usd"] is None
    assert out["covered_positions"] == 1 and out["unpriced_positions"] == 2
    assert [r["value_usd"] for r in out["rows"]] == ["2.500", None, None]


def test_mutated_normalized_observation_is_rejected():
    market = normalize_market(key(1), snapshot(key(1)), received_at=101)
    market["price_usd"] = "999"
    out = portfolio_valuation([{"mint": key(1), "raw": "1", "decimals": 0}], [market], 101)
    assert out["total_value_usd"] is None
    assert out["rows"][0]["reason"] == "OBSERVATION_MISSING_OR_INVALID"


@pytest.mark.parametrize("raw,decimals", [(True, 6), ("-1", 6), ("1.1", 6), (1, True), (1, -1), (1, 256)])
def test_invalid_integer_position_is_unpriced_not_zero(raw, decimals):
    out = portfolio_valuation([{"mint": key(1), "raw": raw, "decimals": decimals}], [], 101)
    assert out["rows"][0]["reason"] == "POSITION_INVALID"
    assert out["rows"][0]["value_usd"] is None
    assert out["total_value_usd"] is None


def test_zero_balance_is_zero_only_with_known_valid_price():
    obs = normalize_market(key(1), snapshot(key(1)), received_at=101)
    position = {"mint": key(1), "raw": "0", "decimals": 6}
    assert Decimal(portfolio_valuation([position], [obs], 101)["total_value_usd"]) == 0
    assert portfolio_valuation([position], [], 101)["total_value_usd"] is None


def test_owner_snapshot_raw_amount_alias_and_mint_mapping_are_supported():
    mint = key(1)
    market = normalize_market(mint, snapshot(mint), received_at=101)
    result = portfolio_valuation([{"mint": mint, "raw_amount": "1500000", "decimals": 6}],
                                 {mint: market}, as_of=101)
    assert result["status"] == "OK" and Decimal(result["total_value_usd"]) == Decimal("3.75")


class RawReply:
    def __init__(self, raw):
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.raw


def pair_payload(mint, n=1, *, liquidity="10", price="2.5"):
    return {"chainId": "solana", "dexId": "example", "pairAddress": key(5000+n),
            "baseToken": {"address": mint}, "quoteToken": {"address": key(6000)},
            "liquidity": {"usd": liquidity}, "priceUsd": price}


def test_existing_free_client_retains_exact_response_bytes_and_every_discovered_pair():
    mint = key(1)
    payload = [pair_payload(mint, i) for i in range(41)]
    raw = (" \n" + json.dumps(payload, indent=2) + "\n").encode()
    client = DexScreenerMarketClient(open_url=lambda *a, **kw: RawReply(raw), clock=lambda: 100)
    observation = capture_market([mint], client, clock=lambda: 101)[0]
    evidence = client.last_response_evidence
    assert evidence["response_bytes"] == raw
    assert observation["source_ref"]["response_sha256"] == hashlib.sha256(raw).hexdigest()
    assert observation["source_ref"] == evidence["source_ref"]
    assert observation["source_ref"]["receipt_id"]
    assert evidence["method"] == "GET" and evidence["request_params"]["chain"] == "solana"
    # Read the client-normalized snapshot too; all 41 source pairs remain present.
    source = client.token_snapshot(mint)
    assert source["chain"] == "solana" and len(source["pool_candidates"]) == 41
    assert source["pool_candidates_not_selected"] == 0


@pytest.mark.parametrize("value", ["NaN", "Infinity", True])
def test_transport_invalid_numeric_liquidity_is_not_aggregate_zero(value):
    raw = json.dumps([pair_payload(key(1), liquidity=value, price=value)]).encode()
    client = DexScreenerMarketClient(open_url=lambda *a, **kw: RawReply(raw), clock=lambda: 100)
    source = client.token_snapshot(key(1))
    assert source["price_usd"] is None and source["main_pair"]["liquidity_usd"] is None
    assert source["aggregate_liquidity_usd"] is None
    assert source["aggregate_liquidity_complete_for_returned_pairs"] is False


def test_no_pair_and_http_error_keep_raw_receipt_and_safe_failure_observation():
    mint = key(1)
    client = DexScreenerMarketClient(open_url=lambda *a, **kw: RawReply(b"[]"), clock=lambda: 100)
    out = capture_market([mint], client, clock=lambda: 101)[0]
    assert out["reason"] == "NO_BASE_TOKEN_PAIR"
    assert out["source_ref"]["response_sha256"] == hashlib.sha256(b"[]").hexdigest()
    def forbidden(*args, **kwargs):
        raise urllib.error.HTTPError("https://api.dexscreener.com/private", 403, "no", {}, io.BytesIO(b"denied"))
    client = DexScreenerMarketClient(open_url=forbidden, clock=lambda: 100)
    out = capture_market([mint], client, clock=lambda: 101)[0]
    assert out["reason"] == "HTTP_403" and "private" not in str(out)
    assert out["source_ref"]["response_sha256"] == hashlib.sha256(b"denied").hexdigest()


def test_very_wide_exponent_sum_retains_rows_but_never_allocates_or_rounds_total():
    a, b = key(1), key(2)
    sources = [normalize_market(a, snapshot(a, "1e999999"), received_at=101),
               normalize_market(b, snapshot(b, "1e-999999"), received_at=101)]
    out = portfolio_valuation([{"mint": m, "raw_amount": "1", "decimals": 0} for m in [a, b]], sources, 101)
    assert len(out["rows"]) == 2 and out["covered_positions"] == 2
    assert out["priced_subtotal_usd"] is None and out["total_value_usd"] is None
