import unittest
from decimal import Decimal
from crypto_tge_fdv_scan import fill_budget, order_levels, match_text, issuer_status, polymarket, APIError

class FakeReader:
    def __init__(self,pages):self.pages=pages;self.index=0
    def get(self,url,params=None,headers=None):
        if self.index>=len(self.pages):raise APIError('unexpected extra page')
        x=self.pages[self.index];self.index+=1
        if isinstance(x,Exception):raise x
        return x

class TestAudit(unittest.TestCase):
    def test_sort_levels(self):
        self.assertEqual(order_levels({'asks':[{'price':'0.95','size':'10'},['0.9','100'],['0','1']]}),[(Decimal('0.9'),Decimal('100')),(Decimal('0.95'),Decimal('10'))])
    def test_fill_single(self):
        x=fill_budget([(Decimal('0.90'),Decimal(200))],100)
        self.assertTrue(x['fully_fillable']);self.assertAlmostEqual(x['shares'],111.111111111,places=6);self.assertAlmostEqual(x['gross_profit_if_no'],11.11111111,places=6)
    def test_fill_slippage(self):
        x=fill_budget([(Decimal('0.9'),Decimal(100)),(Decimal('0.95'),Decimal(100))],100)
        self.assertTrue(x['fully_fillable']);self.assertAlmostEqual(x['vwap'],100/(100+10/.95),places=5)
    def test_no_depth_not_zero(self):
        x=fill_budget([(Decimal('0.95'),Decimal(5))],100)
        self.assertFalse(x['fully_fillable']);self.assertAlmostEqual(x['fillable_spend'],4.75)
    def test_scan_relevant_only(self):
        e={'title':'Will Printr launch a token by 2027?', 'slug':'will-printr-launch-a-token-by',
           'markets':[{'id':'m1','question':'Will Printr launch a token by Dec 2027?', 'clobTokenIds':'["Y1","N1"]', 'outcomes':'["Yes","No"]','active':True, 'closed':False}]}
        other={'title':'Who wins sports?','slug':'sports-event','markets':[{'id':'m2','question':'Who wins sports?','active':True}]}
        result,cover=polymarket(FakeReader([[e,other]]),1,500)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['no_token'],'N1')
        self.assertEqual(result[0]['issuer_status'],'OFFICIAL_TOKEN_CANCELLATION')
        self.assertTrue(cover['enumeration_completed'])
    def test_partial_error(self):
        result,cover=polymarket(FakeReader([APIError('DNS_ERROR')]),10,500)
        self.assertFalse(cover['enumeration_completed']);self.assertEqual(len(result),0);self.assertIn('DNS',cover['error'])
    def test_search(self):
        self.assertTrue(match_text({'title':'ABC FDV above $100m one day after launch?'}))
        self.assertFalse(match_text({'title':'Bitcoin up/down 5min'}))

if __name__=='__main__':unittest.main()