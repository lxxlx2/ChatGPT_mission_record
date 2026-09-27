# Mission live connector verification after scheduler repair

run_time: 2026-09-27T12:20:31+07:00
run_mode: manual_live_verification
automatic_run_proof: false
status: core_sources_verified

## Public market
- PONSUSDT mark: 0.61180000
- PONS funding: 0.00011864
- BTCUSDT mark: 84361.92463768
- ETHUSDT mark: 2695.07464585
- stored PONS futures hard stop 0.4980: not crossed
- stored Robinhood downside trigger 0.598: not crossed at this sample

## Direct-chain active wallet telemetry
- Robinhood PONS raw balance matches 54.799953441979625 PONS
- Robinhood native ETH raw balance unchanged from latest canonical snapshot
- BNB GSTOCK raw balance matches 1183.5967247073113 GSTOCK
- BNB native balance raw value available
- Solana native SOL: 0.128587689
- Solana canonical USDC: 328.018516
- Solana PAID Token-2022: 947.685473
- Solana KARDASHEV Token-2022: 0

## Diagnosis
Interactive market and wallet sources are currently functioning. The remaining Mission problem is scheduled-run persistence/execution reliability, not a current inability to read the core data sources.

The next :29 scheduler cycle must create attempt + final/final-retry under the new scheduler-survival rules.
