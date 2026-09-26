# Four Zero Two / GM Regiment Ink Agent 注册与每日 GM 参与记录

Updated: 2026-09-27
Status: CODEX_MCP_FIXED_PATH_VERIFIED
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

Observed local environment:
- Node.js: `v24.18.0`
- npm: `11.16.0`
- npx: `11.16.0`
- Git: `2.54.0 (Apple Git-157)`
- node path: `/Users/jerson/.nvm/versions/node/v24.18.0/bin/node`
- npm path: `/Users/jerson/.nvm/versions/node/v24.18.0/bin/npm`

Result:
- Node requirement satisfied
- npm/npx available
- Node and npm resolve from the same nvm installation
- no runtime blocker observed

Status: COMPLETE

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

Observed npm registry state:
- package: `gm-regiment-mcp`
- version: `0.1.0`
- dist-tag latest: `0.1.0`
- engines: `node >=20`
- binary: `gm-regiment-mcp -> dist/server.js`
- npm metadata query for author/repository did not return those optional fields; source authority remains the verified public GitHub repository `402Protocol/gm-regiment-mcp`.

Result:
- package is published and resolvable from npm
- local GitHub clone fallback is not currently required
- next action is package-content verification before first execution

Observed package-content verification:
- package: `gm-regiment-mcp@0.1.0`
- tarball filename: `gm-regiment-mcp-0.1.0.tgz`
- package size: `16.1 kB`
- unpacked size: `53.6 kB`
- total files: `16`
- shasum: `9722393ebc609f35e6dbcbe5c8ec2bcd17b62f9b`
- integrity: `sha512-CN1NKzvS9k+84KqUR1Tl+j8har638OKEG5hJAM6RURvKfgMKGiIMocMRCk0CfWEIBlTgwQjkGUu+K1cRgz6tsA==`
- tarball: `https://registry.npmjs.org/gm-regiment-mcp/-/gm-regiment-mcp-0.1.0.tgz`

Observed packaged runtime files include:
- `dist/server.js`
- `dist/chain.js`
- `dist/config.js`
- `dist/contracts.js`
- `README.md`
- `HUMAN_GUIDE.md`
- `LICENSE`
- `package.json`

Result:
- npm package metadata and tarball inspection are consistent with version `0.1.0`
- no unexpected executable/script directories were observed in the dry-run file list
- package has not yet been connected to the local MCP client

Status: COMPLETE

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

Observed Codex environment:
- Codex CLI: `0.156.0`
- MCP configuration command available: `codex mcp add`
- existing MCP registry is readable through `codex mcp list`
- local npx absolute path: `/Users/jerson/.nvm/versions/node/v24.18.0/bin/npx`

Configuration decision:
- use the absolute npx path when registering GM Regiment with Codex;
- this avoids dependence on shell-specific nvm PATH initialization when Codex is launched from another surface;
- no existing MCP entries should be removed or modified.

Planned command:

```bash
codex mcp add gm-regiment -- /Users/jerson/.nvm/versions/node/v24.18.0/bin/npx -y gm-regiment-mcp
```

Observed configuration result:
- `codex mcp add gm-regiment -- /Users/jerson/.nvm/versions/node/v24.18.0/bin/npx -y gm-regiment-mcp` succeeded
- Codex reports the entry as `enabled`
- Auth column shows `Unsupported`, which is expected for a local stdio MCP server with no OAuth flow

Runtime anomaly observed:
- direct invocation of `/Users/jerson/.nvm/versions/node/v24.18.0/bin/npx -y gm-regiment-mcp` returned immediately to the shell
- expected stderr startup banner was not visibly emitted
- therefore MCP runtime health is not yet considered verified
- do not create/fund the Agent wallet until the process behavior is understood

Diagnostic result:
- direct `npx -y gm-regiment-mcp` exits immediately with exit code `0`
- packaged `dist/server.js` contains a direct-invocation guard comparing `import.meta.url` against `pathToFileURL(process.argv[1]).href`
- under npm/npx executable indirection, that comparison can fail, preventing `main()` from running
- manually unpacked tarball cannot be executed directly until dependencies are installed; observed `ERR_MODULE_NOT_FOUND: @modelcontextprotocol/sdk` is consistent with an unpack-only directory

Runtime verification result:
- dedicated install completed successfully under `/Users/jerson/.local/share/gm-regiment-mcp`
- `gm-regiment-mcp@0.1.0` installed with dependencies
- npm audit reported `0 vulnerabilities`
- direct launch with Node succeeded and stayed alive over stdio until manual Ctrl+C
- expected runtime endpoints were displayed:
  - RPC: `https://rpc-gel.inkonchain.com`
  - Identity Registry: `0x7274e874CA62410a93Bd8bf61c69d8045E399c02`
  - DailyAgentGM: `0x2B9DD9Eede2AeCB095455ce45122101109E4AeC7`

Operational decision:
- do not use the npx binary shim for Codex runtime
- install `gm-regiment-mcp@0.1.0` into a dedicated fixed directory
- launch the real file directly with Node:
  `node <fixed-dir>/node_modules/gm-regiment-mcp/dist/server.js`
- then point Codex MCP configuration at that stable path

Status: DIAGNOSED_FIXED_INSTALL_REQUIRED

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
- funded amount observed onchain/RPC balance: `0.000744659857993365 ETH`
- balanceWei: `744659857993365`
- GM Regiment gas gate result: `ok: true`

Status: COMPLETE

### Step 6: register ERC-8004 identity

Call:
- `gm_register_agent`

First execute dry-run.
Confirm destination:
- `0x7274e874CA62410a93Bd8bf61c69d8045E399c02`

Only after checking the prepared transaction, approve the real write with:
- `confirm: true`

Record:
- chosen agent name: `jerson-gm-agent`
- registration tx hash: TBD
- agent ID / NFT ID if returned: TBD

Dry-run verification:
- wallet: `0x87d283153A52333cFc7991f21e9AE0d067Dfa592`
- alreadyRegistered: `false`
- destination: `0x7274e874CA62410a93Bd8bf61c69d8045E399c02`
- value: `0`
- estimatedGas: `128819`
- gasPriceWei: `1000260`
- estimatedFeeWei: `128852492940`
- calldata encodes `register("jerson-gm-agent")`
- broadcast status: NOT SENT

Status: DRY_RUN_VERIFIED

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
- local runtime verified: YES
- npm package availability verified: YES
- npm package contents verified: YES
- Codex MCP capability verified: YES
- Codex MCP entry registered: YES
- Codex MCP fixed-path replacement verified: YES
- MCP runtime health via fixed local install: VERIFIED
- npx entrypoint issue diagnosed: YES
- fixed local install path: `/Users/jerson/.local/share/gm-regiment-mcp/node_modules/gm-regiment-mcp/dist/server.js`
- fixed local package version: `0.1.0`
- npm audit result: `0 vulnerabilities`
- direct Node launch emitted the expected `serving over stdio` banner and stayed alive until manually stopped
- local installation: PENDING
- Agent wallet created: PENDING
- Agent funded: YES
- ERC-8004 dry-run verified: YES
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


## Codex MCP final verification

Observed on 2026-09-27:
- `gm-regiment` command: `/Users/jerson/.nvm/versions/node/v24.18.0/bin/node`
- args: `/Users/jerson/.local/share/gm-regiment-mcp/node_modules/gm-regiment-mcp/dist/server.js`
- status: `enabled`
- auth: `Unsupported` (expected for local stdio MCP)
- existing MCP entries remained intact, including `localGeminiReviewer`, `messages`, `event-stream`, `cua_repl`, and `node_repl`
- no evidence this change modified unrelated project configuration such as web-codex-bridge

The temporary backup file `~/Desktop/codex-mcp-before-gm-regiment.txt` is optional and may be deleted after this verification.


## Local secret storage policy

For the dedicated GM Regiment Agent wallet:

- public wallet address may be recorded in this repository;
- private key must never be committed to Git or stored in project files;
- designated local secret store: macOS Keychain;
- Keychain service name: `gm-regiment-agent-private-key`;
- Keychain account: local macOS user;
- after storing the key, re-read it from Keychain and re-derive the public address to prove the backup is valid before funding;
- only after backup verification may ETH be sent to the Agent wallet.

The MCP package itself does not persist the generated private key.


## Node REPL note

Observed during manual wallet creation:
- `node --input-type=module` cannot be used to start an interactive REPL on the installed Node.js version and returns `Cannot specify --input-type for REPL`.
- Use plain `node` and dynamic `await import("viem/accounts")` inside the REPL instead.
