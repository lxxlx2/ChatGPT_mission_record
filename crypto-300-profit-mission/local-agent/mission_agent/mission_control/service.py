"""Mission Meme V1 cycle: Frank state -> Jupiter quote -> fixed decision -> delivery."""
from __future__ import annotations

import json
import os
import time
from decimal import Decimal
from pathlib import Path

from ..signals.gmail_api import existing_provider
from .db import ControlDB, utc
from .delivery import GmailDelivery, LocalDelivery
from .frank import FrankReader
from .jupiter import JupiterQuoteClient
from .policy import evaluate, load_policy, should_notify


_TRANSIENT_WAIT_REASONS = {
    "CRITICAL_DATA_INCOMPLETE",
    "FRANK_RUNTIME_NOT_LIVE",
    "FRANK_BUY_SIGNAL_STALE_OR_UNKNOWN",
    "QUOTE_METRICS_INVALID",
}
_ACTIONABLE = {"BUY", "SMALL_BUY"}


class MissionMemeService:
    def __init__(
        self,
        *,
        production_root: Path,
        control_root: Path,
        policy_path: Path,
        live_delivery: bool = False,
        gmail_config: Path | None = None,
        jupiter_api_key: str | None = None,
        approved_policy_sha256: str | None = None,
    ):
        self.production_root = Path(production_root)
        self.control_root = Path(control_root)
        self.control_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.control = ControlDB(self.control_root / "mission-control.sqlite")
        self.frank = FrankReader(self.production_root)
        self.policy, self.policy_hash = load_policy(policy_path)
        self.live_delivery_requested = bool(live_delivery)
        self.approved_policy_sha256 = approved_policy_sha256
        self.delivery_allowed = bool(
            self.live_delivery_requested
            and self.policy.get("status") == "FROZEN_APPROVED"
            and self.policy.get("live_delivery_approved") is True
            and self.approved_policy_sha256 == self.policy_hash
        )
        self.gmail_config = gmail_config or (self.production_root / "gmail-existing-source.json")
        self.jupiter = JupiterQuoteClient(jupiter_api_key or os.environ.get("JUPITER_API_KEY"))
        self.local = LocalDelivery(self.control)
        self.gmail = GmailDelivery(self.control)
        self.health_path = self.control_root / "mission-control-health.json"

    def close(self):
        self.control.close()

    def _write_health(self, status: str, **extra) -> None:
        payload = {
            "status": status,
            "updated_at": utc(),
            "policy_id": self.policy.get("policy_id"),
            "policy_hash": self.policy_hash,
            "delivery_allowed": self.delivery_allowed,
            **extra,
        }
        tmp = self.health_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str))
        os.replace(tmp, self.health_path)
        try:
            self.health_path.chmod(0o600)
        except OSError:
            pass

    def _quote(self, candidate: dict) -> dict:
        if candidate.get("runtime_status") != "LIVE":
            return {"status":"SKIPPED","reason":"FRANK_RUNTIME_NOT_LIVE","source":"JUPITER_OFFICIAL","observed_at":time.time()}
        if candidate.get("position_state") in set(self.policy["decision"]["hard_no_buy_position_states"]):
            return {"status":"SKIPPED","reason":"POSITION_NOT_FOLLOWABLE","source":"JUPITER_OFFICIAL","observed_at":time.time()}
        if candidate.get("latest_side") == "SELL":
            return {"status":"SKIPPED","reason":"LATEST_ACTION_SELL","source":"JUPITER_OFFICIAL","observed_at":time.time()}
        amount = Decimal(str(self.policy["decision"]["quote_usdc_amount"]))
        key = f"jupiter:{candidate['mint']}:{candidate.get('token_decimals')}:{amount}"
        cached = self.control.cache_get(key, time.time())
        if cached is not None:
            return cached
        if candidate.get("token_decimals") is None:
            result={"status":"UNAVAILABLE","reason":"TOKEN_DECIMALS_UNKNOWN","source":"JUPITER_OFFICIAL","observed_at":time.time()}
        else:
            result=self.jupiter.quote_usdc_to_token(candidate["mint"],candidate["token_decimals"],usdc_amount=amount,slippage_bps=int(self.policy["decision"]["slippage_bps"]))
        ttl=int(self.policy["decision"]["quote_cache_seconds"] if result.get("status")=="OK" else 5)
        self.control.cache_put(key,result,time.time()+ttl)
        return result

    @staticmethod
    def _stable_quote_inputs(quote: dict) -> dict:
        """Keep only decision-relevant, canonical fields in the durable input hash."""
        keys = (
            "status",
            "reason",
            "source",
            "input_usdc",
            "out_amount_raw",
            "token_out",
            "execution_price_usdc",
            "price_impact_pct",
            "other_amount_threshold",
            "route_exists",
        )
        return {key: quote.get(key) for key in keys}

    @classmethod
    def _decision_inputs(cls, candidate: dict, quote: dict) -> dict:
        return {k:candidate.get(k) for k in (
            "person_id","mint","episode_id","runtime_status","pattern","source_signal_id","source_signal_type","source_signal_at",
            "position_state","current_raw","buy_count","sell_count","latest_side","latest_signature","latest_at",
            "latest_buy_at","latest_buy_price_usdc","latest_buy_price_status","latest_buy_quote_asset","latest_buy_quote_quantity","token_decimals"
        )} | {"quote":cls._stable_quote_inputs(quote)}

    @staticmethod
    def _fresh_initial(latest_at, now: float, max_age: int) -> bool:
        try:
            age = now - float(latest_at)
        except (TypeError, ValueError, OverflowError):
            return False
        return 0 <= age <= max_age

    @staticmethod
    def _transient_wait(result: dict) -> bool:
        return result.get("decision") == "WAIT" and bool(set(result.get("reasons") or []) & _TRANSIENT_WAIT_REASONS)

    def _notification_intent(self, *, candidate: dict, result: dict, event: dict, now: float, initial_max_age: int) -> bool:
        previous = event.get("previous_decision")
        notify = should_notify(previous, result["decision"])
        if previous is None:
            # Every newly appearing episode is eligible for its first notification
            # when the underlying Frank activity itself is fresh. This prevents
            # historical bootstrap mail while still notifying tokens that first
            # appear after the service has already been running.
            notify = bool(notify and self._fresh_initial(candidate.get("latest_at"), now, initial_max_age))
        if self._transient_wait(result) and previous not in _ACTIONABLE:
            # Initial/non-actionable data-quality WAITs stay dashboard-only. But a
            # BUY/SMALL_BUY invalidated by runtime/data staleness is a meaningful
            # state transition and must be delivered once.
            notify = False
        last_enqueued = self.control.last_enqueued_decision(candidate["person_id"], candidate["mint"], candidate.get("episode_id"))
        if last_enqueued == result["decision"]:
            notify = False
        return notify

    def cycle(self) -> dict:
        runtime = self.frank.runtime()
        candidates = self.frank.candidates()
        events = []
        errors = []
        bootstrap = self.control.db.execute("SELECT count(*) FROM decision_events").fetchone()[0] == 0
        initial_max_age = int(self.policy["decision"]["initial_notification_max_age_seconds"])
        max_candidates = int(self.policy["decision"].get("max_candidates_per_cycle", 50))
        selected = candidates[:max_candidates]

        for candidate in selected:
            try:
                candidate = {**candidate, "runtime_status": runtime.get("status")}
                quote = self._quote(candidate)
                # Quote acquisition happens inside this loop. Read the evaluation
                # clock after the quote is returned so a freshly observed quote
                # can never look like it came from the future.
                evaluation_now = time.time()
                result = evaluate(candidate, quote, self.policy, now=evaluation_now)
                payload = {
                    "person_id":candidate["person_id"],"mint":candidate["mint"],"episode_id":candidate.get("episode_id"),
                    "source_signal_id":candidate.get("source_signal_id"),"source_signal_type":candidate.get("source_signal_type") or "NONE",
                    "decision":result["decision"],"created_at":utc(),"policy_id":self.policy["policy_id"],"policy_hash":self.policy_hash,
                    "inputs":self._decision_inputs(candidate,quote),"metrics":result["metrics"],"reasons":result["reasons"],"missing":result["missing"],"invalidation":result["invalidation"],
                }

                self.control.db.execute("BEGIN IMMEDIATE")
                try:
                    # Mutable latest row is refreshed every cycle so dashboard
                    # prices/impact remain current without growing the audit trail.
                    self.control.upsert_latest(payload,self.policy["policy_id"],self.policy_hash)
                    recorded = self.control.record(payload,self.policy["policy_id"],self.policy_hash)
                    event = recorded["event"]
                    previous = event.get("previous_decision")
                    notify = False
                    if recorded["changed"]:
                        notify = self._notification_intent(candidate=candidate,result=result,event=event,now=evaluation_now,initial_max_age=initial_max_age)
                    if notify:
                        forbidden = not self.delivery_allowed
                        self.local.enqueue(event,forbidden=forbidden)
                        self.gmail.enqueue(event,mode="LIVE" if self.delivery_allowed else "DRY_RUN_AUDIT",forbidden=forbidden)
                    self.control.db.execute("COMMIT")
                except Exception:
                    self.control.db.execute("ROLLBACK")
                    raise

                if recorded["changed"]:
                    events.append({
                        "decision_id":event["decision_id"],"decision":payload["decision"],"previous":previous,"mint":payload["mint"],
                        "notification_enqueued":notify,
                    })
            except Exception as exc:
                errors.append({"mint": candidate.get("mint"), "error": type(exc).__name__, "message": str(exc)[:240]})
                continue

        if self.delivery_allowed:
            self.local.drain()
            self.gmail.drain(existing_provider(self.gmail_config))

        status = "OK" if not errors else "DEGRADED"
        result = {
            "runtime":runtime,
            "candidate_count":len(candidates),
            "evaluated_count":len(selected),
            "decision_events":events,
            "candidate_errors":errors,
            "delivery_allowed":self.delivery_allowed,
            "bootstrap":bootstrap,
            "policy_id":self.policy["policy_id"],
            "policy_hash":self.policy_hash,
            "approved_policy_sha256_match":self.approved_policy_sha256 == self.policy_hash if self.approved_policy_sha256 else False,
            "status":status,
        }
        self._write_health(status, candidate_count=len(candidates), evaluated_count=len(selected), candidate_error_count=len(errors))
        return result

    def loop(self, interval_seconds: int = 5):
        while True:
            try:
                self.cycle()
            except Exception as exc:
                self._write_health("ERROR", error=type(exc).__name__, message=str(exc)[:240])
            time.sleep(max(1,interval_seconds))
