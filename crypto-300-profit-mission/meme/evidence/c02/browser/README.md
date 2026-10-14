# Browser QA, 2026-10-14

Native Codex in-app browser at temporary `127.0.0.1:18762`, isolated static replay only; no Mission production service, SQLite, Gmail or LaunchAgent used. Actual index.html/styles.css/app.js are rendered with six official-RPC identity results. Automatic Frank refresh disabled in the replay harness. Saved PNGs are real browser screenshots, not generated mockups.

- agency.png: exact saved Agency mint, single Agency label, VERIFIED/EXACT_BASE_MINT_MATCH.
- same-name.png: different actual Agency mint `4cdbUv2X2TUymvdBYSo4DrKXChMVwSnHHZjMyWhBpump`; separate CA and market results.
- missing.png: screenshot-transcription mint `…VXPpump`, official RPC null; no old Agency identity reused, UNCONFIRMED.
- conflict.png: explicitly counterfactual wrong-source label injected into saved real Agency evidence; TOKEN_IDENTITY_CONFLICT visible. Not evidence of a real issuer conflict.

This is C02 rendering QA, not a full holder analysis, deployed Dashboard acceptance or current market-price claim. Input form is blank because the renderer is invoked with saved report evidence, not a production user submission. Source evidence is expandable; detailed provenance remains escaped and includes account/slot/source failures.
