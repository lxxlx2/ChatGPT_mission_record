# User-run Gmail OAuth setup

The Frank scanner and frozen V1 policy are unchanged. Provisioning runs outside
`mission_agent.signals`, and does not write the live delivery configuration.
The existing adapter has file credentials, not a Keychain abstraction. This
bootstrap therefore uses the supported LOCAL_FILE fallback: directory 0700,
files 0600, outside both Git and evidence at ~/.config/frank-local-gmail.
No connector credentials are accessed. No secrets or HTTP exception payloads
are printed. OAuth uses Desktop loopback, random state, PKCE S256, and exactly
Gmail send plus Gmail readonly (required for Sent search and full MIME readback).

Download a project-specific Google OAuth Desktop client to
~/.config/frank-local-gmail/oauth-desktop-client.json and chmod it 600. Enable
Gmail API and configure the account as an allowed consent test user if needed.
Run from this local-agent directory:

    python -m mission_agent.gmail_setup

The command opens the system browser for explicit user consent. It stores only
the refreshable authorized-user credential, not the transient access token.
It uses one durable lowercase test-UUID identity compatible with the existing
TEST outbox contract. Rerunning reuses this identity. An ambiguous send is never
blindly retried. TEST state/receipt are private and separate from the live DB.
After Sent search and exact MIME verification, the isolated TEST row loses its
local SENT metadata; a reopened ledger and fresh real adapter must recover the
same Gmail message ID with zero send calls. A further drain verifies dedupe.
The receipt explicitly says production_activated=false.

Return to the same Codex chat after success. Remaining activation gates:
- inspect any preexisting true LIVE outbox individually, preserving identities;
- verify this credential through the actual LaunchAgent adapter environment;
- only after TEST and daemon verification, install the private live credential
  pointer and activate Gmail; never replay historical, dry, or synthetic rows;
- retain frozen predicates/local notifications and reconcile cursors if one
  controlled service reload is required.

Neither this CLI nor a passing mock test establishes Gmail LIVE. Missing client,
consent, real TEST receipt, or launchd access remains blocked.

Provider RFC822 Message-ID rewriting is allowed only with exact Frank signal ID,
subject, mode, content hash and complete body equality, plus SENT label and a
valid observed RFC822 ID. Both submitted and observed IDs enter the receipt.
Delivery can require a one-time capability probe executed inside the actual
existing daemon worker; probe_only blocks all production sends until verified.
