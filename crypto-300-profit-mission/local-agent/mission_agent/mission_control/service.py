"""Mission Meme V1 cycle: Frank state -> Jupiter quote -> fixed decision -> delivery."""
from __future__ import annotations

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


class MissionMemeService:
    def __init__(self, *, production_root: Path, control_root: Path, policy_path: Path, live_delivery: bool = False, gmail_config: Path | None = None, jupiter_api_key: str | None = None):
        self.production_root = Path(production_root)
        self.control_root = Path(control_root)
        self.control_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.control = ControlDB(self.control_root / "mission-control.sqlite")
        self.frank = FrankReader(self.production_root)
        self.policy, self.policy_hash = load_policy(policy_path)
        self.live_delivery_requested = bool(live_delivery)
        self.delivery_allowed = bool(self.live_delivery_requested and self.policy.get("status") == "FROZEN_APPROVED" and self.policy.get("live_delivery_approved") is True)
        self.gmail_config = gmail_config or (self.production_root / "gmail-existing-source.json")
        self.jupiter = JupiterQuoteClient(jupiter_api_key or os.environ.get("JUPITER_API_KEY"))
        self.local = LocalDelivery(self.control)
        self.gmail = GmailDelivery(self.control)

    def close(self): self.control.close()

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
        if cached is not None: return cached
        if candidate.get("token_decimals") is None:
            result={"status":"UNAVAILABLE","reason":"TOKEN_DECIMALS_UNKNOWN","source":"JUPITER_OFFICIAL","observed_at":time.time()}
        else:
            result=self.jupiter.quote_usdc_to_token(candidate["mint"],candidate["token_decimals"],usdc_amount=amount,slippage_bps=int(self.policy["decision"]["slippage_bps"]))
        ttl=int(self.policy["decision"]["quote_cache_seconds"] if result.get("status")=="OK" else 5)
        self.control.cache_put(key,result,time.time()+ttl)
        return result

    @staticmethod
    def _decision_inputs(candidate: dict, quote: dict) -> dict:
        return {k:candidate.get(k) for k in (
            "person_id","mint","episode_id","runtime_status","pattern","source_signal_id","source_signal_type",
            "position_state","current_raw","buy_count","sell_count","latest_side","latest_signature","latest_at",
            "latest_buy_at","latest_buy_price_usdc","token_decimals"
        )} | {"quote":quote}

    def cycle(self) -> dict:
        runtime=self.frank.runtime(); candidates=self.frank.candidates(); events=[]; now=time.time()
        bootstrap=self.control.db.execute("SELECT count(*) FROM decision_events").fetchone()[0]==0
        initial_max_age=int(self.policy["decision"]["initial_notification_max_age_seconds"])
        for candidate in candidates:
            candidate={**candidate,"runtime_status":runtime.get("status")}; quote=self._quote(candidate); result=evaluate(candidate,quote,self.policy,now=now)
            payload={
                "person_id":candidate["person_id"],"mint":candidate["mint"],"episode_id":candidate.get("episode_id"),
                "source_signal_id":candidate.get("source_signal_id"),"source_signal_type":candidate.get("source_signal_type") or "NONE",
                "decision":result["decision"],"created_at":utc(),"policy_id":self.policy["policy_id"],"policy_hash":self.policy_hash,
                "inputs":self._decision_inputs(candidate,quote),"metrics":result["metrics"],"reasons":result["reasons"],"missing":result["missing"],"invalidation":result["invalidation"],
            }
            recorded=self.control.record(payload,self.policy["policy_id"],self.policy_hash)
            if not recorded["changed"]: continue
            event=recorded["event"]; previous=event.get("previous_decision")
            notify=should_notify(previous,payload["decision"])
            if bootstrap and previous is None:
                latest_at=candidate.get("latest_at"); notify=bool(notify and latest_at and 0 <= now-float(latest_at) <= initial_max_age)
            if notify:
                forbidden=not self.delivery_allowed
                self.local.enqueue(event,forbidden=forbidden)
                self.gmail.enqueue(event,mode="LIVE" if self.delivery_allowed else "DRY_RUN_AUDIT",forbidden=forbidden)
            events.append({"decision_id":event["decision_id"],"decision":payload["decision"],"previous":previous,"mint":payload["mint"],"notification_enqueued":notify})
        if self.delivery_allowed:
            self.local.drain(); self.gmail.drain(existing_provider(self.gmail_config))
        return {"runtime":runtime,"candidate_count":len(candidates),"decision_events":events,"delivery_allowed":self.delivery_allowed,"bootstrap":bootstrap,"policy_id":self.policy["policy_id"],"policy_hash":self.policy_hash}

    def loop(self, interval_seconds: int = 5):
        while True:
            self.cycle(); time.sleep(max(1,interval_seconds))
