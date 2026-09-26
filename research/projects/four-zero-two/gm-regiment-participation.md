# Four Zero Two / GM Regiment Ink Agent 注册与每日 GM 参与记录

Updated: 2026-09-27
Status: READY_FOR_MANUAL_SETUP
Category: early-stage project participation
Network: Ink mainnet
Chain ID: 57073

## Purpose

记录 Four Zero Two / 402Protocol 发布的 GM Regiment MCP 参与流程、链上合约、人工执行步骤、钱包与交易状态，以及后续与 TRACES / 402 Agent 生态可能产生的关联。

本记录只保存公开信息、地址、交易哈希和参与状态。

**禁止写入：**
- private key
- seed phrase
- keystore password
- browser/session secret
- API secret

Agent 钱包应使用独立小额钱包，不使用主钱包私钥。

## Confirmed sources

Official repository:
- https://github.com/402Protocol/gm-regiment-mcp
- package: `gm-regiment-mcp`
- repository version observed: `0.1.0`
- required Node.js: `>=20`

Ink mainnet:
- Chain ID: `57073`
- default RPC in project: `https://rpc-gel.inkonchain.com`

ERC-8004 Identity Registry:
- `0x7274e874CA62410a93Bd8bf61c69d8045E399c02`
- verified contract on Ink
- contract name observed: `IdentityRegistryUpgradeable`

DailyAgentGM:
- `0x2B9DD9Eede2AeCB095455ce45122101109E4AeC7`
- verified contract on Ink
- contract name observed: `DailyAgentGM`
- constructor points to the ERC-8004 Identity Registry above
- live successful `gm()` transactions have been observed

## Participation thesis

Cost is very low and the action creates an early onchain footprint in the same 402 / ERC-8004 / Ink Agent ecosystem being researched for the Four Zero Two project.

Potential useful history:
- early ERC-8004 identity registration timestamp
- early interaction with DailyAgentGM
- continuous GM streak
- possible future qualification or social proof if 402Protocol later references historical Agent activity

There is currently no confirmed token, airdrop, NFT entitlement, reward, or guaranteed economic return from GM Regiment.

## Official tool flow

The current repository exposes:

1. `gm_create_wallet`
2. `gm_register_agent`
3. `gm_agent_gm`
4. `gm_agent_gm_to`
5. `gm_agent_status`
6. `gm_agent_last_gm`

The current code does **not** require a separate onchain `enlist` transaction.

Operational sequence:

`create dedicated wallet -> fund small Ink ETH -> register ERC-8004 identity -> send first GM -> maintain 24h cadence`

## Security posture

The MCP package states that:
- wallet private keys are generated locally;
- the server does not persist the key;
- write actions are dry-run by default;
- `confirm:true` is required before broadcast;
- a gas gate blocks writes when the wallet balance is below `0.0001 ETH`.

However, the private key is still returned to the MCP caller during wallet creation and must therefore be treated as exposed to the local Agent/MCP execution environment.

Rules for this mission:
- use a fresh dedicated wallet only;
- initially fund approximately `0.0005 ETH`;
- do not send valuable assets to this wallet;
- never commit the private key to this repository;
- store only the public address and transaction hashes after successful setup.

## Manual setup checklist

### Step 1: verify local runtime

Run:

```bash
node -v
npm -v
npx -v
git --version
```

Requirement:
- Node.js version must be 20 or newer.

Status: PENDING_USER_EXECUTION

### Step 2: obtain GM Regiment

Preferred first attempt:

```bash
npx -y gm-regiment-mcp
```

If npm package resolution fails because the package is too new, use GitHub source:

```bash
cd ~/Downloads
git clone https://github.com/402Protocol/gm-regiment-mcp.git
cd gm-regiment-mcp
npm install
npm run typecheck
npm test
npm run build
```

Expected build output:
- `dist/server.js`

Status: PENDING_USER_EXECUTION

### Step 3: configure MCP client

npm package mode:

```json
{
  "mcpServers": {
    "gm-regiment": {
      "command": "npx",
      "args": ["-y", "gm-regiment-mcp"]
    }
  }
}
```

local GitHub build mode:

```json
{
  "mcpServers": {
    "gm-regiment": {
      "command": "node",
      "args": ["/absolute/path/to/gm-regiment-mcp/dist/server.js"]
    }
  }
}
```

Status: PENDING_USER_EXECUTION

### Step 4: create dedicated Agent wallet

Ask the MCP-capable Agent to use:

`gm_create_wallet`

Record only the public wallet address here after creation.

Agent wallet:
- address: TBD
- created at: TBD

Private key:
- NEVER STORE IN GIT

Status: PENDING

### Step 5: fund gas

Target initial balance:
- approximately `0.0005 ETH` on Ink

Hard MCP gas gate:
- wallet below `0.0001 ETH` will not prepare writes

Funding source can be any supported bridge or an existing Ink wallet.

Funding transaction:
- tx hash: TBD
- funded amount: TBD

Status: PENDING

### Step 6: register ERC-8004 identity

Call:
- `gm_register_agent`

First execute dry-run.
Confirm destination:
- `0x7274e874CA62410a93Bd8bf61c69d8045E399c02`

Only after checking the prepared transaction, approve the real write with:
- `confirm: true`

Record:
- chosen agent name: TBD
- registration tx hash: TBD
- agent ID / NFT ID if returned: TBD

Status: PENDING

### Step 7: send first GM

Call:
- `gm_agent_gm`

First execute dry-run.
Confirm destination:
- `0x2B9DD9Eede2AeCB095455ce45122101109E4AeC7`
- value should be `0`
- only gas is paid

Then approve:
- `confirm: true`

Record:
- first GM tx hash: TBD
- first GM timestamp: TBD

Status: PENDING

### Step 8: verify status

Call:
- `gm_agent_status`

Expected fields:
- `isAgent: true`
- `lastGM > 0`
- `canGmNow: false` immediately after GM
- `nextEligibleAt` approximately 24 hours later

Status: PENDING

## Daily operating rule

DailyAgentGM uses a 24-hour cooldown.

For manual operation:
1. run `gm_agent_status`;
2. confirm `canGmNow: true`;
3. dry-run `gm_agent_gm`;
4. review destination and value;
5. approve `confirm:true`;
6. record tx hash if useful.

Do not create an additional repository automation solely for this setup unless explicitly requested.

## Current mission state

As of 2026-09-27:
- repository inspected: YES
- Ink contracts verified: YES
- live `gm()` transactions observed: YES
- participation available now: YES
- local installation: PENDING
- Agent wallet created: PENDING
- Agent funded: PENDING
- ERC-8004 registered: PENDING
- first GM: PENDING
- streak active: PENDING

## Follow-up relation to Four Zero Two / TRACES

Keep this record separate from future TRACES NFT mint analysis.

If TRACES mint mechanics later use any of the following, cross-reference this participation record:
- ERC-8004 agent ownership
- registration age
- gm.ink activity
- GM streak
- 402Protocol interaction history
- Agent reputation / allowlist qualification

No such eligibility linkage is confirmed at this time.
