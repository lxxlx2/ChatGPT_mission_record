# Wubbushi Debits / Credits Holder Drop 项目、规则与钱包安全核验

Updated: 2026-09-30 Asia/Bangkok
Category: NFT / holder-gated derivative artwork
State: LIVE DROP / AUTHENTIC OFFICIAL DOMAIN / WALLET PROMPT MUST MATCH OFFICIAL RULES

Official project:
- https://www.wubbushi.com/debits/
- https://drop.wubbushi.com/
- Artist site: https://www.wubbushi.com/
- Official X: https://x.com/wubbushi

## Identity and relationship to Credits

CONFIRMED:
- Debits is a Wubbushi artwork/collection.
- Wubbushi's official root domain `wubbushi.com` directly features Debits as a collection and links the mint CTA to `https://drop.wubbushi.com/`.
- The official site states that Wubbushi makes art that lives on Ethereum.
- Debits is explicitly "Not affiliated with the makers of Credits." It uses the Credits art code under its MIT License.
- Jack Butcher's official Credits page describes Credits as a 2026 artwork generated from X Money payment transaction IDs.

Therefore:
- `drop.wubbushi.com` is a first-party Wubbushi subdomain and the canonical drop URL currently linked by the artist's official site.
- Debits should not be described as an official Jack Butcher / Visualize Value sequel or collaboration unless a first-party Credits/Jack source later says so.

## What a Debit is

Each Credit has four CMYK plates. The second the original Credit was paid for determined which plates printed.

For matching number N:
- Credit #N shows the plates that printed.
- Debit #N shows the plates that were kept.
- If one wallet holds both Credit #N and Debit #N, the Debit renders "Rich" using all four plates.
- If the Credit is burned, its Debit becomes permanently "Settled".

Official Debits scoring material states that 114,020 Credits owe a Debit. The drop's final minted edition is determined by how many eligible Debits are actually minted during the drop plus defined gifts/reserves; unminted Debits remain unminted after the edition is sealed.

## Current drop mechanics

Official live drop rules currently state:
1. Eligibility is based on holding a Credit in a wallet that held one at the snapshot: 10:14 pm CT on 2026-09-28, and still holding it.
2. Champion signup requires a wallet message signature plus X login.
3. The official page says the wallet step is "no transaction, no gas, no approval".
4. X login is described as read-only and the project says it never posts for the user.
5. Current drop page says the drop starts at 1,000 champions.
6. Each qualifying champion receives one free Debit first. The project pays gas to send it.
7. After the champion distribution, paid minting opens for the matching Debits of snapshot Credits still held, at about USD 7 in ETH each.
8. Paid minting lasts 24 hours; one mint transaction supports at most 100 Debits.
9. Additional reservation/gift/artist-reserve Debits are drawn after close.
10. After close and delivery, the edition is sealed and no additional Debit can ever be minted.

Important supply clarification:
- "1,000 champions" is not the final collection supply.
- The first 1,000 qualifying champions are the free distribution cohort under the current live rules.
- Paid matching mints and defined gifts/reserves can increase final supply above 1,000.
- Therefore social posts saying "only 1,000 total" are misleading if interpreted as final edition size.

## Official-page rule inconsistency

The live drop page currently says 1,000 champions are required and that all 1,000 champions receive the free Debit distribution.

The main Debits landing page still contains stale-looking copy saying the drop starts at 500 / first 500.

Treat the live drop page as current execution authority, but preserve this conflict. Do not infer a 500 cap from the older landing-page copy.

## Link / wallet safety assessment

AUTHENTICITY: HIGH CONFIDENCE
- The exact mint URL is a subdomain of the artist's established official root domain.
- The official root-domain Debits page directly links to `drop.wubbushi.com`.
- Independent same-day social posts show completed Debits champion registrations and link to `drop.wubbushi.com/champion/<number>`.
- No indexed phishing/malware/drainer report for the exact domain was found in the current search.

TRANSACTION-SAFETY LIMITATION:
- The live site text is inspectable, but no canonical Debits contract address was published in the indexed page text at the time of this review.
- The exact wallet signature payload has not been independently decoded from a real signing prompt.
- Therefore domain authenticity does not justify blindly signing an unexpected prompt.

Expected safe champion-registration behavior according to the first-party page:
- message signature only;
- no blockchain transaction;
- no gas;
- no token/NFT approval;
- read-only X authentication.

ABORT if the actual wallet prompt requests any of:
- `setApprovalForAll`;
- ERC-20/NFT `approve`;
- Permit / Permit2;
- Seaport order signature or asset-transfer order;
- direct transfer of Credit/NFT/token;
- a blockchain transaction or gas payment during champion signup;
- an unexpected spender/operator;
- X permissions to post, DM or perform write actions.

If the actual wallet prompt differs from the official "short message / no transaction / no approval" flow, stop and re-audit before signing.

## Current conclusion

The project itself is real and the supplied URL is the canonical Wubbushi drop URL with high confidence.

The conceptual collection is a holder-gated derivative artwork built on the Credits code, with dynamic Credit + Debit pairing mechanics. It is independent of the Credits makers.

For the free champion signup, the first-party specification is unusually explicit about safety: message signature only, no transaction, no gas and no approval. Actual wallet behavior must match that exactly.

Do not call the collection supply 1,000. Current official rules allow a larger final edition.
