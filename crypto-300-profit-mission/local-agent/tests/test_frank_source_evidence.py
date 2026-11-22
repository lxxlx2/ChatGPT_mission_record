"""Cross-module evidence failures: byte identity, clocks, precision, privacy."""
import hashlib
import json
from decimal import Decimal, localcontext
from urllib.error import HTTPError

import pytest

from mission_agent.mission_control.source_evidence import (
    SourceEvidenceError, build_source_ref, coverage, decimal_string,
    provider_id, raw_amount, safe_source_error, timestamp, token_amount,
)


SECRET_URL = "https://rpc.example.invalid/v2/SECRET_RPC_KEY?token=PRIVATE_TOKEN"
PRIVATE_PATH = "/Users/private/raw/SECRET_FILE.json"
RECEIPT = "1726d3ec-c0b9-47ee-b1a1-a11d3b2b812d"


def reference(**changes):
    args = dict(provider_identity=SECRET_URL, method="getMultipleAccounts",
                params=[["address"], {"commitment": "finalized"}],
                response_bytes=b'{ "result": {"value":[]} }',
                observed_at=100.125, received_at=101, slot=10,
                commitment="finalized", receipt_id=RECEIPT)
    args.update(changes)
    return build_source_ref(**args)


def test_exact_captured_bytes_not_reserialized_value_are_bound_and_private_fields_absent():
    raw = b'{ "result": {"value":[]} }'
    a = reference(response_bytes=raw)
    equivalent_json = json.dumps(json.loads(raw)).encode()
    b = reference(response_bytes=equivalent_json)
    assert a["response_sha256"] == hashlib.sha256(raw).hexdigest()
    assert a["response_sha256"] != b["response_sha256"]
    assert a["request_hash"] == b["request_hash"]
    public = json.dumps(a)
    assert not any(x in public for x in [SECRET_URL, "SECRET_RPC_KEY", "PRIVATE_TOKEN", "address", "result"])
    assert a["provider_id"] == provider_id(SECRET_URL)
    assert a["receipt_id"] == RECEIPT


def test_canonical_request_preserves_array_order_and_method_while_ignoring_mapping_order():
    first = reference(params=[["a", "b"], {"encoding": "jsonParsed", "commitment": "finalized"}])
    equivalent = reference(params=[["a", "b"], {"commitment": "finalized", "encoding": "jsonParsed"}])
    other_order = reference(params=[["b", "a"], {"commitment": "finalized", "encoding": "jsonParsed"}])
    other_method = reference(method="getAccountInfo", params=[["a", "b"], {"encoding": "jsonParsed", "commitment": "finalized"}])
    assert first["request_hash"] == equivalent["request_hash"]
    assert first["request_hash"] != other_order["request_hash"]
    assert first["request_hash"] != other_method["request_hash"]


def test_response_tampering_and_provider_change_cannot_keep_same_evidence_identity():
    first = reference()
    assert reference(response_bytes=b'{ "result": {"value":[1]} }')["response_sha256"] != first["response_sha256"]
    assert reference(provider_identity="another-existing-provider")["provider_id"] != first["provider_id"]


def test_cache_read_does_not_refresh_source_clock_or_require_current_time():
    first = reference()
    reread = reference()
    assert first == reread
    assert first["observed_at"] == "100.125"
    assert first["received_at"] == "101"
    assert "served_at" not in first and "age_seconds" not in first
    with pytest.raises(SourceEvidenceError, match="^SOURCE_CLOCK_ORDER_INVALID$"):
        reference(observed_at=102, received_at=101)


@pytest.mark.parametrize("value", [True, False, None, float("nan"), float("inf"), -1, "NaN", "Infinity", " 1", "1_0"])
def test_invalid_or_future_clock_inputs_fail_without_becoming_fresh_data(value):
    with pytest.raises(SourceEvidenceError, match="^TIMESTAMP_INVALID$"):
        timestamp(value)


@pytest.mark.parametrize("changes,code", [
    ({"method": SECRET_URL}, "SOURCE_METHOD_INVALID"),
    ({"response_bytes": {"result": 0}}, "SOURCE_RESPONSE_BYTES_REQUIRED"),
    ({"slot": True}, "SOURCE_SLOT_INVALID"),
    ({"slot": -1}, "SOURCE_SLOT_INVALID"),
    ({"commitment": [PRIVATE_PATH]}, "SOURCE_COMMITMENT_INVALID"),
    ({"receipt_id": PRIVATE_PATH}, "SOURCE_RECEIPT_ID_INVALID"),
    ({"provider_identity": ""}, "PROVIDER_IDENTITY_INVALID"),
    ({"params": {"bad": float("nan")}}, "SOURCE_REQUEST_INVALID"),
])
def test_malformed_provenance_never_reflects_sensitive_value(changes, code):
    with pytest.raises(SourceEvidenceError) as raised:
        reference(**changes)
    assert str(raised.value) == code
    assert PRIVATE_PATH not in str(raised.value) and SECRET_URL not in str(raised.value)


def test_u64_balance_limits_signed_deltas_and_zero_preserve_exact_integer_semantics():
    maximum = str(2**64 - 1)
    assert raw_amount(maximum) == maximum
    assert raw_amount("0") == "0"
    assert raw_amount("-" + maximum, signed=True) == "-" + maximum
    with pytest.raises(SourceEvidenceError):
        raw_amount(2**64)
    with pytest.raises(SourceEvidenceError):
        raw_amount(-(2**64), signed=True)
    with pytest.raises(SourceEvidenceError):
        raw_amount(-1)


@pytest.mark.parametrize("value", [True, 1.0, Decimal("1"), "1.0", "1e2", "01", "-0", "+1", " 1", None])
def test_raw_balances_do_not_coerce_fractional_float_or_noncanonical_integer(value):
    with pytest.raises(SourceEvidenceError):
        raw_amount(value)


def test_derived_units_remain_exact_at_max_balance_and_high_mint_precision():
    with localcontext() as context:
        context.prec = 3
        out = token_amount(2**64 - 1, 9)
        assert out == {"raw_amount": "18446744073709551615", "decimals": 9, "ui_amount": "18446744073.709551615"}
        assert token_amount(1, 255)["ui_amount"] == "0." + "0" * 254 + "1"
        assert token_amount(0, 255)["ui_amount"] == "0"
        assert token_amount(1000000, 6)["ui_amount"] == "1"


@pytest.mark.parametrize("decimals", [True, -1, 256, "6", 6.0])
def test_mint_decimals_must_be_the_real_u8_integer(decimals):
    with pytest.raises(SourceEvidenceError, match="^TOKEN_DECIMALS_INVALID$"):
        token_amount(1, decimals)


def test_finite_decimal_normalization_does_not_round_using_global_context():
    with localcontext() as context:
        context.prec = 3
        assert decimal_string("123456789.123456789000") == "123456789.123456789"
        assert decimal_string("1e-9") == "0.000000001"
        assert decimal_string(Decimal("-0.0")) == "0"
    assert decimal_string("0", nonnegative=True) == "0"
    with pytest.raises(SourceEvidenceError):
        decimal_string("0", positive=True)
    with pytest.raises(SourceEvidenceError):
        decimal_string("-1", nonnegative=True)


@pytest.mark.parametrize("value", [True, 0.1, None, "NaN", "Infinity", "-Infinity", "1_0", " 1.0 ", SECRET_URL])
def test_decimal_amounts_reject_float_nonfinite_and_untrusted_input(value):
    with pytest.raises(SourceEvidenceError):
        decimal_string(value)


def test_coverage_dimensions_do_not_upgrade_partial_history_from_complete_account_enumeration():
    out = coverage("OPEN_OWNER_ACCOUNTS", enumeration_status="COMPLETE_WITHIN_SCOPE",
                   history_status="PARTIAL", missing_items=["CLOSED_ACCOUNTS_UNPROVEN", "CLOSED_ACCOUNTS_UNPROVEN"],
                   stop_reason="PROVIDER_EMPTY_PAGE")
    assert out["history_status"] == "PARTIAL"
    assert out["classification_status"] == out["parity_status"] == "NOT_REQUESTED"
    assert out["missing_items"] == ["CLOSED_ACCOUNTS_UNPROVEN"]
    assert "complete" not in out


@pytest.mark.parametrize("change", [
    {"scope": PRIVATE_PATH}, {"history_status": "DONE"},
    {"missing_items": [SECRET_URL]}, {"missing_items": "UNKNOWN"},
    {"stop_reason": RuntimeError(SECRET_URL)},
])
def test_coverage_does_not_embed_arbitrary_provider_error_or_private_path(change):
    args = {"scope": "OPEN_OWNER_ACCOUNTS"}
    args.update(change)
    with pytest.raises(SourceEvidenceError) as raised:
        coverage(**args)
    assert PRIVATE_PATH not in str(raised.value) and SECRET_URL not in str(raised.value)


def test_transport_error_codes_are_whitelisted_and_exception_text_is_never_reflected():
    assert safe_source_error(HTTPError(SECRET_URL, 429, PRIVATE_PATH, {}, None)) == "HTTP_429"
    assert safe_source_error(HTTPError(SECRET_URL, 403, PRIVATE_PATH, {}, None)) == "HTTP_403"
    assert safe_source_error(TimeoutError(SECRET_URL)) == "SOURCE_TIMEOUT"
    assert safe_source_error(ConnectionError(PRIVATE_PATH)) == "CONNECTION_ERROR"
    assert safe_source_error("HTTP_503") == "HTTP_503"
    assert safe_source_error(RuntimeError("HTTP_429 " + SECRET_URL)) == "SOURCE_UNAVAILABLE"
    assert safe_source_error(SECRET_URL) == "SOURCE_UNAVAILABLE"
    assert safe_source_error("HTTP_999") == "SOURCE_UNAVAILABLE"
