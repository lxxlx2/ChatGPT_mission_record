# Frank Live + Write-Path Regression — 2026-09-29

Status: LIVE_PATH_PASS / FULL_30D_REPLAY_STILL_OPEN
No test email sent.

## Provider failover smoke

Both configured Alchemy Solana apps independently returned the same current finalized head signature for:
`498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

- primary `mkhr4iorbgonin56`: PASS
- backup `h6m5pairkgzet7vz`: PASS

This validates the new one-retry failover path at the provider-selection level.

## Passive-activity false-positive smoke

Latest five wallet-related finalized signatures were fetched and individually inspected.

All five:
- Frank signer = false;
- contained associated-token-account / passive receipt style activity;
- did not contain verified active swap proof.

Expected result: PASSIVE_FILTERED / NO BUY.
Observed test result: all five rejected as active Frank BUY.

A historical control transaction:
`3bUrntKXT3dLPVaqxWB2zbYGoTwXd6thepgEjYW1U24jVgBErgd7dFMReNr6vaaZmi9wkuCLa3zZ6zW2LqgFtj2p`
contains a Buy-like log plus ATA activity but Frank is not proven as the active signer in the parsed response. Under the hardened rule this remains passive/ambiguous and cannot become a Frank BUY solely from the token balance increase.

## GitHub blocking diagnosis

Earlier isolated field-by-field A/B writes all passed:
- cursor/health
- wallet + tx hash
- token/quote delta
- BUY/SELL labels
- USD amounts
- PRECONFIRM label/subject text

A second, more realistic write-sequence test was run after the priority-lane fix:

`monitoring-regression/sandbox/frank-sequence-2026-09-29/`
- attempt.md: PASS
- core.md: PASS
- frank.md: PASS
- completion.md: PASS

The Frank audit payload included 40 transaction-like rows, BUY/SELL/PASSIVE classifications, USD values, wallet address and PRECONFIRM-like fields. The ~3.8KB Frank write succeeded.

Conclusion:
- the prior automation block is not reproduced by Frank content itself;
- GitHub accepts the audit shape and field content;
- the failure domain is much more likely automation execution context / tool-call sequencing / provider timeout-rate behavior / runtime guard during the scheduled run;
- the new architecture reduces this risk by persisting core first, requiring a separate Frank audit, allowing one provider failover, and writing an authoritative post-lane completion artifact.

## Historical 30D replay status

The exhaustive 30D requirement remains OPEN.

A direct Alchemy pagination stress test attempted to walk backwards from current head:
- 9 consecutive pages succeeded before a provider 429;
- approximately 270 in-window signature records were encountered in that test sequence;
- because the connector response exposes only a bounded slice per call and the wallet is high activity, this is not enough to claim 30D completeness.

Correct result:
- FR-HIST full replay = NOT PASSED YET;
- no fake “30D complete” status is allowed.

## Regression mapping

- FR-LIVE-01 primary source -> PASS
- FR-LIVE-02 backup source availability -> PASS
- FR-LIVE-03 passive filtering -> PASS
- FR-LIVE-04 active-swap proof rule -> PASS by deterministic rule / no new live positive swap in this smoke
- FR-LIVE-05 ambiguous tx stalls/does not guess BUY -> PASS
- FR-LIVE-06 persist-before-Gmail semantics -> PASS by write-sequence test; no test mail sent
- FR-LIVE-07 pending event cannot be erased -> PASS by rule
- FR-LIVE-08 overall success requires Frank audit -> PASS by new runtime
- FR-HIST-01..04 exhaustive 30D replay -> OPEN

Live functionality is accepted for deployment. Historical strategy-recall validation is a separate unfinished test and remains explicitly marked open.
