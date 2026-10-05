# GOMO / Gomo App payout and on-chain audit

Updated: 2026-10-06 Asia/Bangkok
Project domain: https://gomofamily.life/
Canonical Solana mint: `9XKzy4KahcZaGJPJtz1PtqGPB3CiseoBrx7TcQhEpump`
Status: `WATCH / PAYOUT_UNVERIFIED`

## Research policy

Use an adversarial default:
- project statements, website copy and social posts are leads only;
- a payout counts only when a recipient can be tied to an actual settled payment or independently verifiable receipt;
- internal GOMO transfers, wallet splitting, market buys/sells and token-holder changes do not count as paying users;
- direct chain state is primary evidence for on-chain legs;
- off-chain payments such as X Money require a verifiable payment record or recipient receipt;
- a Git repository counts as product evidence only when its relationship to Gomo can be independently established.

## Primary question: has Gomo actually paid users / creators?

### Current verdict

`NO CONFIRMED PAYOUT FOUND`.

Under the Mission evidence standard, treat Gomo as **not yet proven to have paid users or creators**.

### What is claimed

BuyBacks publicly describes a model in which creator fees are routed through its system, with 80% paid to the named recipient via X Money and 20% used to buy back the launched token. GOMO is displayed among BuyBacks live markets.

These are platform/project claims. Listing GOMO as a live market is not evidence that a GOMO payout settled.

### What was actually verified

As of this review, no GOMO-specific evidence was found for any of the following:
- a settled X Money payout receipt to a GOMO user/creator;
- a public payout record containing recipient + amount + GOMO claim;
- an on-chain SOL/USDC payment to an identifiable reward recipient;
- a GOMO-specific creator-fee claim that can be paired with the promised 20% on-chain buyback;
- an independently verified recipient publicly proving receipt of funds.

Therefore the claimed fee -> payout / buyback loop remains `UNVERIFIED` for GOMO.

Because the claimed 80% leg uses X Money, Solana alone cannot prove that leg. A real verification would require a GOMO-specific payment receipt or publicly attributable payout record. The corresponding 20% buyback should then be independently identifiable on-chain for the same claim cycle.

## Git / product evidence

No public GitHub repository independently attributable to Gomo / Gomo Family was found in searches using the project domain, social identity and exact mint. Returned GitHub results were third-party scanners/trading datasets rather than an attributable Gomo source repository.

Current classification: `REAL_PUBLIC_GIT = NOT FOUND / UNVERIFIED`.

## Separate market-supply observation

The earlier investigation found a confirmed coordinated GOMO wallet split and subsequent programmatic selling. This is relevant to market supply risk but **does not count as user payout evidence**.

Confirmed chain observation:
- wallet `FsYRQmoe8zCupamq3Jw4j1oZb1HnAFt3HcXZb8Dgggfi` redistributed 26,000,000 GOMO to three wallets within 55 seconds;
- one 10M recipient subsequently sold equal `69,444.444444 GOMO` chunks at roughly 15-minute intervals;
- no evidence currently links that wallet cluster to the Gomo project/team/treasury.

Classification: `COORDINATED_WALLET_CLUSTER / PROJECT_IDENTITY_UNRESOLVED`.

This observation must not be described as a Gomo reward distribution or creator payout.

## Evidence needed to upgrade payout status

Upgrade `PAYOUT_UNVERIFIED` only if at least one GOMO-specific payout can be independently reproduced, preferably with both sides of the claimed mechanism:
1. identifiable claim / fee event;
2. recipient and amount;
3. settled X Money receipt or on-chain payment;
4. matching 20% GOMO buyback transaction where applicable.

## Decision state

`WATCH`

Reason: GOMO is a real traded on-chain asset, but the project's central payout/value-flow claim has not yet been independently demonstrated with a GOMO-specific settled payment. Until such evidence exists, treat "Gomo has paid users/creators" as unconfirmed.