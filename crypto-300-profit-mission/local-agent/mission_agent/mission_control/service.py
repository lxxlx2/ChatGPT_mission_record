"""Mission Meme V1 cycle: Frank state -> Jupiter quote -> fixed decision -> delivery."""
from __future__ import annotations

import json
import os
import time
from decimal import Decimal
from pathlib import Path

from ..signals.gmail_api import existing_provider
from .db import ControlDB, utc
from .debounce import TransitionDebounce
from .delivery import GmailDelivery, LocalDelivery
from .frank import FrankReader
from .jupiter import JupiterQuoteClient
from .observations import ObservationStore
from .outcomes import OutcomeTracker
from .sol_mirror import SolNormalizedMirror
from .policy import evaluate, load_policy, should_notify, live_delivery_policy_authorized


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
        self.debounce = TransitionDebounce(self.control.db)
        self.observations = ObservationStore(self.control.db)
        self.frank = FrankReader(self.production_root)
        frozen_frank_policy = Path(__file__).resolve().parents[2] / "config" / "frank_local_signal_v1.json"
        self.sol_mirror = SolNormalizedMirror(
            self.production_root / "forward.sqlite",
            self.control_root / "sol-normalized-v1.sqlite",
            frozen_frank_policy,
        )
        self.policy, self.policy_hash = load_policy(policy_path)
        self.live_delivery_requested = bool(live_delivery)
        self.approved_policy_sha256 = approved_policy_sha256
        self.delivery_allowed = bool(
            self.live_delivery_requested
            and live_delivery_policy_authorized(
                self.policy, self.policy_hash, self.approved_policy_sha256
            )
        )
        self.gmail_config = gmail_config or (self.production_root / "gmail-existing-source.json")
        self.jupiter = JupiterQuoteClient(jupiter_api_key or os.environ.get("JUPITER_API_KEY"))
        self.outcomes = OutcomeTracker(self.control.db, self.jupiter)
        self.local = LocalDelivery(self.control)
        self.gmail = GmailDelivery(
            self.control,
            max_decision_age_seconds=int(self.policy["decision"].get("initial_notification_max_age_seconds", 600)),
        )
        self.health_path = self.control_root / "mission-control-health.json"

    def close(self):
        self.sol_mirror.close()
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
            "latest_buy_at","latest_buy_price_usdc","latest_buy_price_status","latest_buy_quote_asset","latest_buy_quote_quantity",
            "latest_buy_original_quote_asset","latest_buy_original_quote_quantity","latest_buy_quote_was_normalized",
            "latest_buy_usdc_equivalent","latest_buy_model_quote_asset","latest_buy_model_quote_quantity","candidate_source","token_decimals"
        )} | {
            "quote":cls._stable_quote_inputs(quote),
            # Preserve the actual Jupiter observation for the frozen Gmail body.
            # Do not add it to stable quote decision metrics or reinterpret as
            # a current executable price at delivery time.
            "quote_observed_at":quote.get("observed_at"),
        }

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
            notify = bool(notify and self._fresh_initial(candidate.get("latest_at"), now, initial_max_age))
        if self._transient_wait(result) and previous not in _ACTIONABLE:
            notify = False
        last_enqueued = self.control.last_enqueued_decision(candidate["person_id"], candidate["mint"], candidate.get("episode_id"))
        if last_enqueued == result["decision"]:
            notify = False
        return notify

    def cycle(self) -> dict:
        runtime = self.frank.runtime()
        sol_normalization = self.sol_mirror.sync()
        base_candidates = self.frank.candidates()
        # Sidecar is research-only until an explicitly reviewed policy change.
        # Never feed shadow-converted SOL amounts into decision/outbox delivery.
        candidates = base_candidates
        events = []
        errors = []
        debounced = []
        outcome_registered = 0
        bootstrap = self.control.db.execute("SELECT count(*) FROM decision_events").fetchone()[0] == 0
        rules = self.policy["decision"]
        initial_max_age = int(rules["initial_notification_max_age_seconds"])
        grace = int(rules.get("transient_wait_grace_seconds", 0))
        reset_gap = int(rules.get("transient_wait_reset_gap_seconds", max(grace * 10, grace + 1)))
        bucket_seconds = int(rules.get("observation_bucket_seconds", 60))
        retention_seconds = int(rules.get("observation_retention_seconds", 1209600))
        max_candidates = int(rules.get("max_candidates_per_cycle", 50))
        selected = candidates[:max_candidates]

        for candidate in selected:
            try:
                candidate = {**candidate, "runtime_status": runtime.get("status")}
                quote = self._quote(candidate)
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
                    self.control.upsert_latest(payload,self.policy["policy_id"],self.policy_hash)
                    self.observations.record(
                        candidate=candidate,
                        result=result,
                        quote=quote,
                        now=evaluation_now,
                        bucket_seconds=bucket_seconds,
                    )
                    outcome_fresh_at = candidate.get("source_signal_at") or candidate.get("latest_at")
                    if self._fresh_initial(outcome_fresh_at,evaluation_now,initial_max_age):
                        if self.outcomes.register(candidate=candidate,result=result,quote=quote,now=evaluation_now):
                            outcome_registered += 1
                    prior = self.control.latest_event(candidate["person_id"], candidate["mint"], candidate.get("episode_id"))
                    previous_decision = prior["decision"] if prior else None
                    transient = self._transient_wait(result)
                    reason = (result.get("reasons") or result.get("missing") or ["TRANSIENT_WAIT"])[0]
                    allowed = self.debounce.allow(
                        person_id=candidate["person_id"],
                        mint=candidate["mint"],
                        episode_id=candidate.get("episode_id"),
                        previous_decision=previous_decision,
                        target_decision=result["decision"],
                        transient=transient,
                        reason=reason,
                        now=evaluation_now,
                        grace_seconds=grace,
                        reset_gap_seconds=reset_gap,
                    )
                    if not allowed:
                        self.control.db.execute("COMMIT")
                        debounced.append({
                            "mint": candidate["mint"],
                            "from": previous_decision,
                            "to": result["decision"],
                            "reason": reason,
                            "grace_seconds": grace,
                            "reset_gap_seconds": reset_gap,
                        })
                        continue

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
                errors.append({"mint": candidate.get("mint"), "error": type(exc).__name__,
                               "message": "CANDIDATE_EVALUATION_FAILED"})
                continue

        outcome_tracking = self.outcomes.sample_due(
            now=time.time(),
            slippage_bps=int(rules["slippage_bps"]),
        )
        outcome_tracking["registered"] = outcome_registered
        pruned = self.observations.prune(time.time(), retention_seconds)
        if self.delivery_allowed:
            self.local.drain()
            self.gmail.drain(existing_provider(self.gmail_config))

        status = "OK" if not errors else "DEGRADED"
        result = {
            "runtime":runtime,
            "sol_normalization":sol_normalization,
            "candidate_count":len(candidates),
            "evaluated_count":len(selected),
            "decision_events":events,
            "debounced_transitions":debounced,
            "candidate_errors":errors,
            "observation_rows_pruned":pruned,
            "outcome_tracking":outcome_tracking,
            "delivery_allowed":self.delivery_allowed,
            "bootstrap":bootstrap,
            "policy_id":self.policy["policy_id"],
            "policy_hash":self.policy_hash,
            "approved_policy_sha256_match":self.approved_policy_sha256 == self.policy_hash if self.approved_policy_sha256 else False,
            "status":status,
        }
        self._write_health(
            status,
            candidate_count=len(candidates),
            evaluated_count=len(selected),
            candidate_error_count=len(errors),
            debounced_transition_count=len(debounced),
            outcome_active=outcome_tracking.get("active",0),
            outcome_sampled=outcome_tracking.get("sampled",0),
            outcome_error_count=len(outcome_tracking.get("errors") or []),
            sol_normalization_status=sol_normalization.get("status"),
            sol_normalization_copied=sol_normalization.get("copied",0),
            sol_normalization_resolved=sol_normalization.get("sol_resolved",0),
            sol_normalization_unresolved=sol_normalization.get("sol_unresolved",0),
            sol_normalization_added_signals=sol_normalization.get("added_signal_count",0),
        )
        return result

    def loop(self, interval_seconds: int = 5):
        while True:
            try:
                self.cycle()
            except Exception as exc:
                self._write_health("ERROR", error=type(exc).__name__, message="MISSION_CYCLE_FAILED")
            time.sleep(max(1,interval_seconds))
