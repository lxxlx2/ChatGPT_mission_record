import csv
from decimal import Decimal
import hashlib
import io
from datetime import datetime,timezone
import unittest
import zipfile

import monster_v4_stage130_first_listed_minute_sha_replay as m


def fixture_zip(symbol,day,opens,step_start=None):
    start=m.ms(day+"T00:00:00Z") if step_start is None else step_start
    table=io.StringIO()
    w=csv.writer(table)
    for i,v in enumerate(opens):
        t=start+i*m.MINUTE
        o,h,l,c,q,n=v
        w.writerow([t,str(o),str(h),str(l),str(c),"0",t+59999,str(q),n,"0","0","0"])
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{symbol}-1m-{day}.csv",table.getvalue())
    raw=mem.getvalue()
    return raw,(hashlib.sha256(raw).hexdigest()+"  "+symbol+".zip\n").encode()


class Stage130Test(unittest.TestCase):
    def test_verified_first_partial_day_sha_and_unicode(self):
        sym="币安人生USDT";day="2025-01-25"
        start=m.ms("2025-01-25T05:00:00Z")
        prices=[("1","1.04","0.99","1.01","1000",3),
                ("1.01","1.12","1","1.11","2000",10)]
        data,sha=fixture_zip(sym,day,prices,start)
        calls=[]
        def fetch(uri, limit):
            calls.append(uri)
            return sha if uri.endswith(".CHECKSUM") else data
        bars,rec=m.verified_day(sym,day,fetch=fetch)
        self.assertEqual(len(bars),2)
        self.assertEqual(bars[0][0],start)
        self.assertTrue(rec["publisher_sha256_verified"])
        self.assertEqual(len(calls),2)

    def test_corrupted_original_publisher_checksum_fails_closed(self):
        sym="VINEUSDT";day="2025-01-25"
        raw,_=fixture_zip(sym,day,[("1","1","1","1","20",1)])
        def fetch(uri,limit):
            return b"0"*64 if uri.endswith("CHECKSUM") else raw
        with self.assertRaisesRegex(ValueError,"PUBLISHER_CHECKSUM_MISMATCH"):
            m.verified_day(sym,day,fetch=fetch)

    def test_causal_momentum_not_impacted_by_later_future_high(self):
        start=m.ms("2025-01-25T05:00:00Z")
        def gen(vs):
            return [(start+i*m.MINUTE,Decimal(str(p)),Decimal(str(p)),Decimal(str(p)),
                     Decimal(str(p)),Decimal("20000"),20) for i,p in enumerate(vs)]
        baseline=gen([1,1,1,1,1,1,1.2,1.2,1.25,1.3,1.4,1.5])
        x=m.momentums(baseline)
        later=baseline+gen([20,25,30])[0:0]
        self.assertEqual(x,m.momentums(later))
        changed=baseline+[(start+i*m.MINUTE,Decimal("99"),Decimal("99"),Decimal("99"),Decimal("99"),Decimal("300000"),1) for i in range(12,20)]
        self.assertEqual(x,[a for a in m.momentums(changed) if a["event_epoch_ms"]<=start+12*m.MINUTE])
        self.assertTrue(x)

    def test_first_minute_source_replay_with_postlisting_positive_and_negative(self):
        anchor="2025-01-19"
        end=m.prev.window(anchor)[1]
        start=m.ms("2025-01-25T05:00:00Z")
        sym="VINEUSDT"
        records=[]
        for i in range((end-start)//m.MINUTE):
            t=start+i*m.MINUTE
            p=Decimal("1")
            if i>=30:
                p=Decimal("1.25")
            if i>=300:
                p=Decimal("2.05")
            records.append((t,str(p),str(p),str(p),str(p),"20000",20))
        calendar=["2025-01-25","2025-01-26"]
        mapping={}
        for d in calendar:
            v=[(r[1],r[2],r[3],r[4],r[5],r[6]) for r in records if m.utc(r[0])[:10]==d]
            timestamps=[r[0] for r in records if m.utc(r[0])[:10]==d]
            mapping[d]=fixture_zip(sym,d,v,step_start=timestamps[0])
        def fetch(uri,limit):
            day=uri.split("-1m-")[-1].split(".zip")[0]
            if day not in mapping:
                raise FileNotFoundError(day)
            return mapping[day][1 if uri.endswith("CHECKSUM") else 0]
        hourly={"first_1h_open_utc":"2025-01-25T05:00:00Z",
                "first_open_USDT":"1"}
        case={"date":anchor,"symbol":sym}
        v=m.score_case(case,hourly,fetch=fetch)
        self.assertTrue(v["gross_first1m_2x_case_evaluation_only"])
        self.assertTrue(v["first_observed_close_before_2x_5m"])
        self.assertTrue(v["momentum_research_early_5m_before_2x"])
        self.assertEqual(v["actual_bid_ask_fills_fee_net"],"UNKNOWN")
        self.assertEqual(v["minute_rows"],len(records))
        self.assertEqual(v["verified_publisher_day_count"],2)

    def test_original31_prior_source_is_fixed_without_network(self):
        rows=m.prev.run()["all_source_cohort_rows"]
        self.assertEqual(len(rows),31)
        self.assertEqual({r["symbol"] for r in rows if r["gte_2x_gross_firsthour_proxy"]},
                         {"VINEUSDT","APRUSDT"})
        self.assertTrue(all(r["analysis_status"].startswith("COMPLETE") for r in rows))


if __name__=="__main__":
    unittest.main()
