from mission_agent.meme.market import DexScreenerMarketClient
from test_meme_market_and_rpc import Response

def test_self_quote_must_be_rejected():
    mint='So11111111111111111111111111111111111111112'
    pair={'chainId':'solana','pairAddress':'bad','baseToken':{'address':mint,'name':'Agency','symbol':'Agency'},'quoteToken':{'address':mint},'priceUsd':'100'}
    out=DexScreenerMarketClient(open_url=lambda *a,**k:Response([pair])).token_snapshot(mint)
    assert out['status']=='UNAVAILABLE'

def test_quote_side_price_is_not_input_mint_price():
    mint='So11111111111111111111111111111111111111112'
    pair={'chainId':'solana','pairAddress':'reverse','baseToken':{'address':'other'},'quoteToken':{'address':mint},'priceUsd':'100'}
    out=DexScreenerMarketClient(open_url=lambda *a,**k:Response([pair])).token_snapshot(mint)
    assert out['market_match_status']=='PAIR_MISMATCH'
    assert out['rejected_pairs'][0]['reason']=='INPUT_MINT_IS_QUOTE_PRICE_IS_BASE'
