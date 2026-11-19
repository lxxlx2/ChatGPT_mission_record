"""Option3 rehearses an isolated outcome without the V1 or any live sender."""
import hashlib
import pytest

from mission_agent.mission_control.frank_risk_rehearsal import RiskNotificationRehearsal
from mission_agent.mission_control.frank_risk_runs import FrankRiskRuns, RiskRunError
from test_frank_durable_risk_and_quote import NOW, capture, risk_row


def update(root):
    risks = FrankRiskRuns(root, clock=lambda: NOW)
    risks.create("fixture", load_inputs=lambda _: capture([risk_row()]))
    return risks.path, risks.page(kind="SELL_OBSERVED")["rows"][0]


def rehearsal(root, clock, age=60):
    return RiskNotificationRehearsal(root, kinds=["SELL_OBSERVED"], max_age_seconds=age, clock=lambda: clock[0])


class Simulator:
    def __init__(self):
        self.records = {}
        self.calls = []
        self.drop_response = False
        self.visible = True

    def record(self, identity, fingerprint):
        self.calls.append(identity)
        self.records[identity] = {"id": identity, "content_sha256": fingerprint, "scope": "FAKE"}
        if self.drop_response:
            raise TimeoutError("injected uncertain synthetic outcome")

    def lookup(self, identity):
        return self.records.get(identity) if self.visible else None


def test_lost_acknowledgment_restarts_as_readback_without_a_second_attempt(tmp_path):
    risk_path, event = update(tmp_path)
    before = hashlib.sha256(risk_path.read_bytes()).digest()
    clock = [NOW]
    queue = rehearsal(tmp_path, clock)
    identity = queue.enqueue(event)
    assert queue.enqueue(event) == identity and identity != event["update_id"]
    simulator = Simulator()
    simulator.drop_response = True
    assert queue.process(identity, simulator=simulator)["status"] == "OUTCOME_UNVERIFIED"
    simulator.visible = False
    clock[0] += 3600
    reopened = rehearsal(tmp_path, clock)
    assert reopened.process(identity, simulator=simulator)["status"] == "OUTCOME_UNVERIFIED"
    simulator.visible = True
    recovered = reopened.process(identity, simulator=simulator)
    assert recovered["status"] == "FAKE_RECEIPT_VERIFIED" and recovered["attempts"] == 1
    assert simulator.calls == [identity] and hashlib.sha256(risk_path.read_bytes()).digest() == before
    assert not (tmp_path / "mission-control.sqlite").exists()


@pytest.mark.parametrize("replacement", [False, True])
def test_expiry_or_policy_replacement_cannot_revive_a_pending_update(tmp_path, replacement):
    _, event = update(tmp_path)
    clock = [NOW]
    original = rehearsal(tmp_path, clock)
    identity = original.enqueue(event)
    if not replacement:
        clock[0] += 61
    current = rehearsal(tmp_path, clock, age=120 if replacement else 60)
    simulator = Simulator()
    result = current.process(identity, simulator=simulator)
    assert result["status"] == ("POLICY_CHANGED" if replacement else "INELIGIBLE_TIME")
    assert result["attempts"] == 0 and simulator.calls == []
    assert current.enqueue(event) == identity
    assert current.process(identity, simulator=simulator) == result


def test_tampered_update_and_wrong_receipt_do_not_prove_delivery(tmp_path):
    _, event = update(tmp_path)
    queue = rehearsal(tmp_path, [NOW])
    with pytest.raises(RiskRunError, match="INTEGRITY"):
        queue.enqueue({**event, "kind": "REENTRY_OBSERVED"})
    identity = queue.enqueue(event)
    simulator = Simulator()
    simulator.drop_response = True
    queue.process(identity, simulator=simulator)
    simulator.records[identity]["content_sha256"] = "0" * 64
    row = queue.process(identity, simulator=simulator)
    assert row["status"] == "OUTCOME_UNVERIFIED"
    assert row["attempts"] == 1 and simulator.calls == [identity]
