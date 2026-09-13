---
incident_date: 2026-09-14
timezone: Asia/Bangkok
automation_id: "6a85fff710e0819190ffcf8c1145a170"
severity: high
status: corrected
category: cross_project_misattribution
affected_project: "Space (@intodotspace)"
conflicting_project: "Spacecoin (@spacecoin)"
affected_event: "airdrop-tge-monitor/reports/events/2026/2026-09/2026-09-14/045127-space-final-claim-deadline.md"
affected_gmail_message_id: "1a09cc0fb4edb6f0"
---

# Incident: Space / Spacecoin cross-project misattribution

## 1. Impact
A formal alert was incorrectly sent for the whitelist project `Space (@intodotspace)`. The candidate deadline information belonged to a different project, Spacecoin `@spacecoin`. The alert then combined that candidate with `into.space` / UFO migration pages, creating a false evidence chain.

The archived event has been retracted and must not be used as a future deduplication baseline or as historical evidence that `@intodotspace` announced that claim deadline.

## 2. Canonical whitelist identity
Monitored project: Space

Canonical official X: `@intodotspace`

Canonical root domain: `into.space`

Known collision to reject unless independently whitelisted: Spacecoin `@spacecoin`

## 3. Root cause
1）Candidate discovery relied on a search result that was interpreted inside the current `Space` context without preserving the source account as a mandatory identity field.

2）The evidence pipeline verified the destination claim domain separately from the announcement identity, then joined those two pieces because their names/tickers appeared related.

3）QA detected a `$SPACE` versus `$SPC` inconsistency but treated it as a display ambiguity. That should have been a blocking identity conflict.

4）The existing monitor rules required direct evidence chains, but did not define a machine-checkable identity gate before following claim/checker links.

## 4. Corrective controls
### A. Identity lock before evidence expansion
Every whitelist entry must be represented as a canonical tuple:

`project_id + canonical_name + official_x_handles + official_root_domains + known_tickers + known_chains + known_collision_names`

A candidate may advance only when its originating official source matches the whitelist tuple. Similar name, ticker, ecosystem, migration history or partner relationship cannot satisfy this gate.

### B. Preserve source identity through every hop
For every candidate and every followed link, record:

`candidate_source_account`
`candidate_source_url`
`candidate_project_name`
`final_domain`
`identity_match`
`identity_conflicts`

The originating account/domain must stay attached to the candidate through redirects and link expansion.

### C. Hard-fail conflicts
Before any ChatGPT/Gmail/GitHub alert, stop the event when any of these is unresolved:

1）official X handle mismatch
2）root-domain mismatch
3）ticker conflict
4）chain/contract conflict
5）project-name collision with another known project
6）announcement source belongs to a non-whitelisted project

A conflict cannot be bypassed by omitting the conflicting field from the final message.

### D. Two-anchor rule for action pages
A claim/checker/KYC/wallet page can be assigned to a whitelist project only when at least two direct identity anchors exist, with one anchor required to be the monitored project's official account or official root domain. Examples:

1）official X post from the canonical handle → action page
2）official root domain → docs/blog → action page
3）official root domain explicitly names the exact subdomain/action page and the page itself identifies the same project

A third-party search result plus a separately discovered same-name domain is invalid.

### E. Same-name collision check
Before triggering, explicitly search for other projects using the same or similar name/ticker. If a collision exists, compare official handles and root domains. Any ambiguity forces `identity_match: false` or `identity_match: unresolved`, and the alert remains silent.

## 5. Audit changes
Future run files must include:

`identity_registry_checked`
`candidate_source_account`
`candidate_source_url`
`identity_match`
`identity_conflicts`
`same_name_collision_checked`
`hard_fail_triggered`

For triggered events, `identity_match` must equal `true`, `identity_conflicts` must be empty, and `hard_fail_triggered` must be `false`.

## 6. Regression test for Space
A candidate mentioning `$SPACE`, airdrop or claim must be rejected for `Space (@intodotspace)` when its originating account is `@spacecoin`, even if another page under `into.space` contains a claim flow or migration history.

Expected result: no user notification, no Gmail, no official event archive. Record only the rejected candidate in the run audit.
