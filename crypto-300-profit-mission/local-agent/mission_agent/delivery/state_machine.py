import uuid
from datetime import timedelta
from ..clock import parse_utc,stamp
from ..db.connection import transaction


class DeliveryEngine:
    def __init__(self,repo,provider,config):
        self.repo=repo;self.provider=provider;self.config=config

    def state(self,id):
        row=self.repo.db.execute('SELECT * FROM deliveries WHERE event_id=?',(id,)).fetchone()
        if row is None:raise ValueError('unknown delivery event')
        return row

    def _uncertain(self,id,token,error):
        now=stamp(self.repo.clock.now());cooldown=stamp(self.repo.clock.now()+timedelta(seconds=self.config.cooldown_seconds))
        with transaction(self.repo.db):
            self.repo.db.execute("UPDATE deliveries SET state='DELIVERY_UNCERTAIN',cooldown_until=?,last_error=?,updated_at=? WHERE event_id=? AND lease_token=? AND state IN('DELIVERY_SENDING','DELIVERY_UNCERTAIN')",(cooldown,error,now,id,token))

    def _resolve(self,id,token):
        matches=self.provider.search_sent(id)
        if len(matches)>1:
            with transaction(self.repo.db):
                self.repo.db.execute("UPDATE deliveries SET state='FAILED_MANUAL_REVIEW',last_error='MULTIPLE_SENT_MATCHES',updated_at=? WHERE event_id=? AND lease_token=? AND state IN('DELIVERY_SENDING','DELIVERY_UNCERTAIN')",(stamp(self.repo.clock.now()),id,token))
            return True
        if len(matches)==1 and self.provider.readback(matches[0],id):
            with transaction(self.repo.db):
                self.repo.db.execute("UPDATE deliveries SET state='DELIVERED',provider_message_id=?,last_error=NULL,cooldown_until=NULL,updated_at=? WHERE event_id=? AND lease_token=? AND state IN('DELIVERY_SENDING','DELIVERY_UNCERTAIN')",(matches[0],stamp(self.repo.clock.now()),id,token))
            return True
        return False

    def run(self,id,mode='SUCCESS',search_delay=0,crash_at=None):
        row=self.state(id);now=self.repo.clock.now()
        if row['state']=='DELIVERY_SENDING':
            if now>parse_utc(row['lease_expires_at']):
                self._uncertain(id,row['lease_token'],'EXPIRED_SENDING_INTENT')
            return self.state(id)['state']
        if row['state']=='DELIVERY_UNCERTAIN':
            if row['cooldown_until'] and now<parse_utc(row['cooldown_until']):
                return row['state']
            try:
                if not self._resolve(id,row['lease_token']):
                    self._uncertain(id,row['lease_token'],'SENT_NOT_YET_CONFIRMED')
            except Exception as exc:
                self._uncertain(id,row['lease_token'],type(exc).__name__)
            return self.state(id)['state']
        if row['state']!='DELIVERY_PENDING':
            return row['state']
        token=uuid.uuid4().hex
        with transaction(self.repo.db):
            cursor=self.repo.db.execute("UPDATE deliveries SET state='DELIVERY_SENDING',lease_token=?,fence=fence+1,lease_expires_at=?,last_sent_attempt_at=?,updated_at=? WHERE event_id=? AND state='DELIVERY_PENDING'",(token,stamp(now+timedelta(seconds=self.config.lease_seconds)),stamp(now),stamp(now),id))
            if cursor.rowcount!=1:
                return self.state(id)['state']
        if crash_at=='before_send':
            raise SystemExit('simulated crash after durable intent')
        try:
            if self._resolve(id,token):
                return self.state(id)['state']
            row=self.state(id)
            if row['lease_token']!=token or row['state']!='DELIVERY_SENDING' or self.repo.clock.now()>parse_utc(row['lease_expires_at']):
                return row['state']
            provider_id=self.provider.send(id,mode,search_delay)
            if crash_at=='after_send':
                raise SystemExit('simulated crash after provider acceptance')
            if mode=='SENT_BUT_RECEIPT_FAIL':
                raise RuntimeError('mock immediate receipt persistence failure')
            # Persist id immediately before readback, independently of transport summary.
            with transaction(self.repo.db):
                self.repo.db.execute("UPDATE deliveries SET provider_message_id=?,updated_at=? WHERE event_id=? AND lease_token=? AND state IN('DELIVERY_SENDING','DELIVERY_UNCERTAIN')",(provider_id,stamp(self.repo.clock.now()),id,token))
            if not self._resolve(id,token):
                self._uncertain(id,token,'READBACK_OR_SEARCH_DELAY')
        except Exception as exc:
            self._uncertain(id,token,type(exc).__name__)
        return self.state(id)['state']
