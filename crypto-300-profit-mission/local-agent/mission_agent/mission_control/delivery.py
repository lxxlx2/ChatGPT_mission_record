"""Mission Meme delivery adapters.

Delivery state lives only in mission-control.sqlite. Historical/review mode is
fail-closed. Gmail uses the existing authorized OAuth provider; no credentials
are created or persisted here.
"""
from __future__ import annotations

import base64,email,json,re,shutil,subprocess
from datetime import datetime, timezone
from email import policy as mime_policy
from email.message import EmailMessage

from ..hashing import digest
from ..signals.gmail import CredentialBlocked,RetryableError,PermanentError,AmbiguousSend
from .db import ControlDB,utc


def _short(mint:str)->str:return mint[:7]+"…"+mint[-5:]


def _seconds_since(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, (datetime.now(timezone.utc) - datetime.fromisoformat(value)).total_seconds())
    except (TypeError, ValueError):
        return None


def render(event:dict)->dict:
    body=json.loads(event["body"]) if isinstance(event.get("body"),str) else event["body"]
    metrics=body.get("metrics") or {};inputs=body["inputs"]
    subject=f"[Mission Meme] {body['decision']} {_short(body['mint'])}"
    text="\n".join([
        f"Decision: {body['decision']}",f"Previous: {body.get('previous_decision') or 'NONE'}",f"Token CA: {body['mint']}",
        f"Frank pattern: {inputs.get('pattern')}",f"Frank position: {inputs.get('position_state')}",f"Frank BUY/SELL: {inputs.get('buy_count')}/{inputs.get('sell_count')}",
        f"Latest action: {inputs.get('latest_side')}",f"Latest signature: {inputs.get('latest_signature') or 'N/A'}",
        f"Frank latest buy price: {metrics.get('frank_latest_buy_price_usdc') or 'N/A'} USDC",f"Executable price: {metrics.get('execution_price_usdc') or 'N/A'} USDC",
        f"Price deviation: {metrics.get('price_deviation_pct') or 'N/A'}%",f"Quote impact: {metrics.get('price_impact_pct') or 'N/A'}%",
        "Reasons: "+(", ".join(body.get("reasons") or []) or "N/A"),"Missing: "+(", ".join(body.get("missing") or []) or "NONE"),
        "Invalidation: "+(", ".join(body.get("invalidation") or []) or "NONE"),f"Decision ID: {body['decision_id']}",f"Policy: {body['policy_id']} / {body['policy_hash']}"
    ])
    return {"subject":subject,"body":text,"content_hash":digest({"subject":subject,"body":text})}


class LocalDelivery:
    def __init__(self,control:ControlDB,run=subprocess.run):self.control,self.run=control,run
    def enqueue(self,event:dict,*,forbidden:bool)->None:
        content=render(event);status="DRY_RUN_AUDIT" if forbidden else "PENDING"
        self.control.enqueue(event["decision_id"],"local",content["content_hash"],status)
        self.control.db.execute("INSERT OR IGNORE INTO local_delivery(decision_id,status,content_hash,created_at) VALUES(?,?,?,?)",(event["decision_id"],status,content["content_hash"],utc()))
    def drain(self)->None:
        rows=self.control.db.execute("SELECT d.*,e.body FROM local_delivery d JOIN decision_events e USING(decision_id) WHERE d.status IN ('PENDING','RETRY_PENDING') ORDER BY d.created_at").fetchall()
        for row in rows:
            event={"decision_id":row["decision_id"],"body":json.loads(row["body"])};content=render(event);summary=" | ".join(content["body"].splitlines()[:7]);binary=shutil.which("terminal-notifier")
            if binary:args=[binary,"-title",content["subject"],"-message",summary,"-group",row["decision_id"]];mechanism="terminal-notifier-group"
            else:
                script="display notification "+json.dumps(summary,ensure_ascii=False)+" with title "+json.dumps(content["subject"],ensure_ascii=False);args=["/usr/bin/osascript","-e",script];mechanism="osascript-notification"
            try:
                result=self.run(args,capture_output=True,text=True,timeout=15)
                if result.returncode:raise RuntimeError("LOCAL_NOTIFICATION_COMMAND_FAILED")
                receipt={"decision_id":row["decision_id"],"accepted_at":utc(),"mechanism":mechanism}
                self.control.db.execute("UPDATE local_delivery SET status='COMMAND_ACCEPTED',delivered_at=?,mechanism=?,last_error=NULL,receipt=? WHERE decision_id=?",(utc(),mechanism,json.dumps(receipt),row["decision_id"]))
                self.control.db.execute("UPDATE decision_outbox SET status='COMMAND_ACCEPTED',attempts=attempts+1,last_error=NULL,receipt=? WHERE decision_id=? AND channel='local'",(json.dumps(receipt),row["decision_id"]))
            except Exception as exc:
                self.control.db.execute("UPDATE local_delivery SET status='RETRY_PENDING',last_error=? WHERE decision_id=?",(type(exc).__name__,row["decision_id"]))
                self.control.db.execute("UPDATE decision_outbox SET status='RETRY_PENDING',attempts=attempts+1,last_error=? WHERE decision_id=? AND channel='local'",(type(exc).__name__,row["decision_id"]))


class GmailDelivery:
    READBACK_BACKOFF_SECONDS=60
    CREDENTIAL_BACKOFF_SECONDS=300
    MAX_SEND_ATTEMPTS=5

    def __init__(self,control:ControlDB):self.control,self.db=control,control.db
    def enqueue(self,event:dict,*,mode:str,forbidden:bool)->None:
        content=render(event);decision_id=event["decision_id"];forbidden=forbidden or mode!="LIVE";wire="<mission."+digest({"decision_id":decision_id,"mode":mode})+"@local.invalid>";status="DRY_RUN_AUDIT" if forbidden else "PENDING"
        self.db.execute("INSERT OR IGNORE INTO gmail_delivery(decision_id,delivery_mode,delivery_forbidden,subject,body,content_hash,wire_message_id,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(decision_id,mode,int(forbidden),content["subject"],content["body"],content["content_hash"],wire,status,utc()))
        row=self.row(decision_id)
        if row["content_hash"]!=content["content_hash"] or row["delivery_mode"]!=mode or row["delivery_forbidden"]!=int(forbidden):raise ValueError("IMMUTABLE_DECISION_GMAIL_IDENTITY_CONFLICT")
        self.control.enqueue(decision_id,"gmail",content["content_hash"],status)
    def row(self,decision_id:str)->dict:return dict(self.db.execute("SELECT * FROM gmail_delivery WHERE decision_id=?",(decision_id,)).fetchone())
    def _wire_body(self,row:dict)->str:return row["body"]+"\n\nMission-Decision-Identity: "+row["decision_id"]+"\nMission-Content-SHA256: "+row["content_hash"]+"\n"
    def _wire(self,row:dict,recipient:str)->bytes:
        if not re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+",recipient or ""):raise CredentialBlocked("RECIPIENT_NOT_CONFIGURED")
        msg=EmailMessage();msg["To"]=recipient;msg["From"]=recipient;msg["Subject"]=row["subject"];msg["Message-ID"]=row["wire_message_id"];msg["X-Mission-Decision-ID"]=row["decision_id"];msg["X-Mission-Content-Hash"]=row["content_hash"];msg.set_content(self._wire_body(row));return msg.as_bytes()
    def _verify(self,row:dict,message:dict)->dict:
        if not message.get("id") or "SENT" not in message.get("labelIds",[]):raise PermanentError("NOT_A_SENT_RECEIPT")
        raw=base64.urlsafe_b64decode(message["raw"]+"===");msg=email.message_from_bytes(raw,policy=mime_policy.default)
        checks=[str(msg["Subject"])==row["subject"],str(msg["X-Mission-Decision-ID"]).strip()==row["decision_id"],str(msg["X-Mission-Content-Hash"]).strip()==row["content_hash"],msg.get_content().replace("\r\n","\n")==self._wire_body(row)]
        if not all(checks):raise PermanentError("SENT_IDENTITY_OR_CONTENT_MISMATCH")
        return {"decision_id":row["decision_id"],"gmail_message_id":message["id"],"gmail_thread_id":message.get("threadId"),"verified_at":utc()}
    def _set(self,decision_id:str,status:str,error:str|None=None)->None:
        self.db.execute("UPDATE gmail_delivery SET status=?,last_error=?,last_attempt_at=? WHERE decision_id=?",(status,error,utc(),decision_id));self.db.execute("UPDATE decision_outbox SET status=?,last_error=? WHERE decision_id=? AND channel='gmail'",(status,error,decision_id))
    def _verified(self,decision_id:str,receipt:dict)->None:
        self.db.execute("UPDATE gmail_delivery SET status='SENT_VERIFIED',sent_at=COALESCE(sent_at,?),gmail_message_id=?,gmail_thread_id=?,readback_verified=1,last_error=NULL,receipt=? WHERE decision_id=?",(utc(),receipt["gmail_message_id"],receipt.get("gmail_thread_id"),json.dumps(receipt),decision_id))
        self.db.execute("UPDATE decision_outbox SET status='SENT_VERIFIED',receipt=?,last_error=NULL WHERE decision_id=? AND channel='gmail'",(json.dumps(receipt),decision_id))
    def _due(self,row:dict)->bool:
        age=_seconds_since(row.get("last_attempt_at"))
        if row["status"] in {"SENDING","SENT_UNVERIFIED"}:
            return age is None or age>=self.READBACK_BACKOFF_SECONDS
        if row["status"]=="CREDENTIAL_BLOCKED":
            return age is None or age>=self.CREDENTIAL_BACKOFF_SECONDS
        if row["status"]=="RETRYABLE_ERROR":
            if int(row.get("attempt_count") or 0)>=self.MAX_SEND_ATTEMPTS:
                self._set(row["decision_id"],"MANUAL_REVIEW","GMAIL_RETRY_LIMIT_REACHED")
                return False
            return age is None or age>=self.READBACK_BACKOFF_SECONDS
        return True
    def drain(self,provider)->None:
        rows=self.db.execute("SELECT * FROM gmail_delivery WHERE delivery_forbidden=0 AND status NOT IN ('SENT_VERIFIED','PERMANENT_ERROR','DRY_RUN_AUDIT','MANUAL_REVIEW') ORDER BY created_at").fetchall()
        for raw_row in rows:
            row=dict(raw_row)
            if not self._due(row):continue
            decision_id=row["decision_id"];uncertain=row["status"] in {"SENDING","SENT_UNVERIFIED"} or bool(row["gmail_message_id"])
            try:
                if provider is None:raise CredentialBlocked("NO_LOCAL_GMAIL_CREDENTIAL")
                provider.ready();candidates=[provider.get(row["gmail_message_id"])] if row["gmail_message_id"] else [provider.get(mid) for mid in provider.find_sent(row["wire_message_id"],decision_id)]
                if len(candidates)>1:raise PermanentError("MULTIPLE_SENT_IDENTITIES_REQUIRE_REVIEW")
                if candidates:self._verified(decision_id,self._verify(row,candidates[0]));continue
                if uncertain:self._set(decision_id,"SENT_UNVERIFIED","SEND_OUTCOME_UNCERTAIN_WAITING_SENT");continue
                wire=self._wire(row,provider.recipient)
                self.db.execute("UPDATE gmail_delivery SET status='SENDING',attempt_count=attempt_count+1,last_attempt_at=? WHERE decision_id=?",(utc(),decision_id));self.db.execute("UPDATE decision_outbox SET status='SENDING',attempts=attempts+1 WHERE decision_id=? AND channel='gmail'",(decision_id,))
                # From this point onward, any exception is ambiguous: the provider may
                # have accepted the message. Never automatically resend until Sent
                # readback proves absence/presence through the stable identity.
                uncertain=True
                response=provider.send(wire)
                if not response.get("id"):raise AmbiguousSend("SEND_RETURNED_NO_MESSAGE_ID")
                self.db.execute("UPDATE gmail_delivery SET status='SENT_UNVERIFIED',gmail_message_id=?,gmail_thread_id=?,sent_at=? WHERE decision_id=?",(response["id"],response.get("threadId"),utc(),decision_id));self._verified(decision_id,self._verify(self.row(decision_id),provider.get(response["id"])))
            except CredentialBlocked:self._set(decision_id,"SENT_UNVERIFIED" if uncertain else "CREDENTIAL_BLOCKED","LOCAL_GMAIL_CREDENTIAL_UNAVAILABLE")
            except (AmbiguousSend,RetryableError,OSError,TimeoutError):self._set(decision_id,"SENT_UNVERIFIED" if uncertain else "RETRYABLE_ERROR","GMAIL_DELIVERY_OR_READBACK_RETRY_PENDING")
            except (PermanentError,ValueError,TypeError) as exc:self._set(decision_id,"PERMANENT_ERROR",str(exc))
