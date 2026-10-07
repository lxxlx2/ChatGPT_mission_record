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


DECISION_ZH={"BUY":"可跟","SMALL_BUY":"小仓跟","WAIT":"等待","NO_BUY":"不跟"}
PATTERN_ZH={"MULTIPLE":"多次强加仓","ACCUMULATION":"持续建仓","REENTRY_WATCH":"重新建仓观察","NONE":"无模式"}
STATE_ZH={"OPEN":"持仓中","CLOSED":"已退出","INVENTORY_UNDETERMINED":"仓位不明"}
ACTION_ZH={"BUY":"买入","ADD":"加仓","REENTRY":"重新建仓","SELL":"卖出","EXIT":"清仓","SELL_POSITION_UNRESOLVED":"卖出后仓位待确认"}
REASON_ZH={
    "FRANK_RUNTIME_NOT_LIVE":"Frank 实时监控不在线",
    "POSITION_STATE_CLOSED":"Frank 已退出该仓位",
    "POSITION_STATE_INVENTORY_UNDETERMINED":"Frank 仓位无法确认",
    "INVENTORY_UNDETERMINED":"Frank 当前持仓数量无法确认",
    "ZERO_OR_NEGATIVE_INVENTORY":"Frank 当前已无可确认持仓",
    "LATEST_ACTION_SELL":"Frank 最新动作是卖出",
    "NO_FOLLOW_PATTERN":"尚未形成可跟随模式",
    "FRANK_BUY_SIGNAL_STALE_OR_UNKNOWN":"Frank 最近有效买入已过期或时间未知",
    "CRITICAL_DATA_INCOMPLETE":"关键报价/价格数据不完整",
    "QUOTE_METRICS_INVALID":"Jupiter 报价指标不完整",
    "NO_EXECUTABLE_JUPITER_ROUTE":"Jupiter 当前无可执行路径",
    "PRICE_TOO_FAR_FROM_FRANK":"当前价格离 Frank 买入价过远",
    "EXECUTION_IMPACT_TOO_HIGH":"当前 30 USDC 跟单价格冲击过高",
    "FRANK_MULTIPLE_ACTIVE":"Frank 当前处于多次强加仓模式",
    "PRICE_STILL_CLOSE_TO_FRANK":"当前成交价仍接近 Frank 参考买入价",
    "EXECUTION_IMPACT_ACCEPTABLE":"当前预计价格冲击可接受",
    "FRANK_PATTERN_ACTIVE":"Frank 当前仍处于可跟随建仓模式",
    "FOLLOWABLE_WITH_SMALL_SIZE":"当前条件只适合小仓跟随",
    "ACCUMULATION_NOT_MULTIPLE":"目前只是持续建仓，尚未升级为 MULTIPLE",
    "PRICE_DEVIATION_ABOVE_BUY_LIMIT":"价格偏离超过正常跟随阈值",
    "PRICE_IMPACT_ABOVE_BUY_LIMIT":"价格冲击超过正常跟随阈值",
    "FRANK_REENTRY_WATCH_ACTIVE":"Frank 清仓后重新建仓，当前先观察",
}
MISSING_ZH={
    "FRESH_FRANK_BUY":"缺少 10 分钟内的新鲜 Frank 买入",
    "LIVE_FRANK_RUNTIME":"Frank 实时监控不在线",
    "QUOTE_TIMESTAMP":"Jupiter 报价缺少时间戳",
    "QUOTE_STALE":"Jupiter 报价已过期",
    "EXECUTION_PRICE_OR_IMPACT":"缺少当前成交价或价格冲击",
    "TOKEN_DECIMALS_UNKNOWN":"Token decimals 未确认",
    "JUPITER_QUOTE_UNAVAILABLE":"Jupiter 报价不可用",
    "SOL_EVENT_TIME_USDC_UNAVAILABLE":"缺少事件时间 SOL/USDC 参考价",
}
USDC_MINT="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
WSOL_MINT="So11111111111111111111111111111111111111112"

def _zh(mapping,value,fallback="未知"):
    if value in (None,""):return fallback
    return mapping.get(value,str(value))

def _asset(value):
    if value==USDC_MINT:return "USDC"
    if value in {"SOL",WSOL_MINT}:return "SOL"
    return str(value or "未知资产")

def _display(value,suffix=""):
    return "暂无" if value in (None,"") else str(value)+suffix

def render(event:dict)->dict:
    body=json.loads(event["body"]) if isinstance(event.get("body"),str) else event["body"]
    metrics=body.get("metrics") or {};inputs=body["inputs"];quote=inputs.get("quote") or {}
    decision=body["decision"];pattern=inputs.get("pattern")
    subject=f"[Meme提醒] {_zh(DECISION_ZH,decision,decision)} | {_zh(PATTERN_ZH,pattern,pattern)} | {_short(body['mint'])}"
    original_asset=inputs.get("latest_buy_original_quote_asset") or inputs.get("latest_buy_quote_asset")
    original_qty=inputs.get("latest_buy_original_quote_quantity") or inputs.get("latest_buy_quote_quantity")
    payment=_display(original_qty," "+_asset(original_asset))
    if inputs.get("latest_buy_quote_was_normalized") and inputs.get("latest_buy_usdc_equivalent") not in (None,""):
        payment += " ≈ "+str(inputs.get("latest_buy_usdc_equivalent"))+" USDC（事件时间换算）"
    frank_price=metrics.get("frank_latest_buy_price_usdc") or inputs.get("latest_buy_price_usdc")
    exec_price=metrics.get("execution_price_usdc") or quote.get("execution_price_usdc")
    impact=metrics.get("price_impact_pct") or quote.get("price_impact_pct")
    deviation=metrics.get("price_deviation_pct")
    reasons="；".join(REASON_ZH.get(x,x) for x in (body.get("reasons") or [])) or "无额外说明"
    missing="；".join(MISSING_ZH.get(x,x) for x in (body.get("missing") or [])) or "无"
    sig=inputs.get("latest_signature")
    text="\n".join([
        "结论："+_zh(DECISION_ZH,decision,decision),
        "Frank 模式："+_zh(PATTERN_ZH,pattern,pattern),
        "CA："+body["mint"],
        "Frank 仓位："+_zh(STATE_ZH,inputs.get("position_state"),str(inputs.get("position_state") or "未知")),
        f"Frank 买/卖次数：{inputs.get('buy_count')}/{inputs.get('sell_count')}",
        "Frank 最近动作："+_zh(ACTION_ZH,inputs.get("latest_side"),str(inputs.get("latest_side") or "未知")),
        "Frank 原始支付："+payment,
        "Frank 参考买入价："+_display(frank_price," USDC"),
        "当前 30 USDC 可成交价："+_display(exec_price," USDC"),
        "相对 Frank 偏离："+_display(deviation,"%"),
        "预计价格冲击："+_display(impact,"%"),
        "判断原因："+reasons,
        "缺失/不可确认："+missing,
        "CA 页面：https://solscan.io/token/"+body["mint"],
        "最近交易："+("https://solscan.io/tx/"+sig if sig else "暂无"),
        "Decision ID："+body["decision_id"],
        "Policy："+body["policy_id"]+" / "+body["policy_hash"],
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
    SENT_UNVERIFIED_MAX_AGE_SECONDS=3600

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
            unresolved_age=_seconds_since(row.get("sent_at") or row.get("created_at"))
            if unresolved_age is not None and unresolved_age>=self.SENT_UNVERIFIED_MAX_AGE_SECONDS:
                self._set(row["decision_id"],"MANUAL_REVIEW","GMAIL_SENT_OUTCOME_UNRESOLVED_TOO_LONG")
                return False
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
                # readback proves presence through the stable identity.
                uncertain=True
                response=provider.send(wire)
                if not response.get("id"):raise AmbiguousSend("SEND_RETURNED_NO_MESSAGE_ID")
                self.db.execute("UPDATE gmail_delivery SET status='SENT_UNVERIFIED',gmail_message_id=?,gmail_thread_id=?,sent_at=? WHERE decision_id=?",(response["id"],response.get("threadId"),utc(),decision_id));self._verified(decision_id,self._verify(self.row(decision_id),provider.get(response["id"])))
            except CredentialBlocked:self._set(decision_id,"SENT_UNVERIFIED" if uncertain else "CREDENTIAL_BLOCKED","LOCAL_GMAIL_CREDENTIAL_UNAVAILABLE")
            except (AmbiguousSend,RetryableError,OSError,TimeoutError):self._set(decision_id,"SENT_UNVERIFIED" if uncertain else "RETRYABLE_ERROR","GMAIL_DELIVERY_OR_READBACK_RETRY_PENDING")
            except (PermanentError,ValueError,TypeError) as exc:self._set(decision_id,"PERMANENT_ERROR",str(exc))
