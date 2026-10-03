# US Stock Daily Report Spec

Updated: 2026-10-01 Asia/Bangkok
Status: canonical content contract

The official morning email is a complete decision-oriented report, not a recovery digest.

## Fixed 12-section structure

The exact first-level sections and order are:

一、市场总览
二、正常时段、盘后与异动原因
三、行业级异动与结构性主题
四、重大主题专题分析
五、AI、科技与一级市场
六、机构资金与市场观点
七、政策、监管与全球局势
八、风险雷达
九、未来24至72小时事件日历
十、今日买入观察
十一、漏检复盘与监控修正
十二、结论

A section may be concise when there is genuinely no material update, but the report cannot collapse into a short digest merely because one source failed or a recovery path is used.

## Required factual coverage

The report must cover, when market/source data exists:
- latest completed US session: Dow, S&P 500, Nasdaq; breadth/volume when reliable;
- current global/premarket context;
- US rates, oil and USD/macro risk;
- major stock and sector moves with drivers;
- at least one deep thematic analysis connecting market variables;
- material AI/technology/IPO/private-market developments;
- institutional flow/positioning or clearly state no high-confidence new item;
- policy/regulatory/global developments relevant to markets;
- explicit risk radar;
- dated 24-72h catalysts;
- buy-watch candidates only when evidence exists, with catalyst/risk/invalidation;
- user-specific private-market rights only for active exposure.

## Source quality

Use company IR/SEC/regulators/official sources and high-quality English news/data sources.
Do not use Chinese-language websites as evidence.
Facts, attributed claims and analysis must be distinguishable.

## User-visible quality

The email body must not be dominated by monitoring plumbing, tool failures or QA mechanics.
Operational failures belong in run audits.

## Canonical body

One QA-approved body becomes the daily canonical body.
All delivery/recovery paths must use that body.
Gmail readback body and GitHub canonical report body must be identical.

## Monthly long-term investment report

On the first Asia/Bangkok calendar day of each month, the same existing `美股每日晨报` automation must also prepare and deliver the previous natural month's monthly report. This is an existing capability and must not be implemented as a separate automation.

Archive path:
`us-stock-daily/reports/monthly/YYYY/YYYY-MM.md`

Subject convention:
`月度长期投资报告｜YYYY-MM｜长期股票、IPO与项目机会`

### Monthly source-completeness gate

Before monthly synthesis, build a manifest for every calendar date in the previous month because this automation publishes every day, including weekends/holidays.

For every expected date:
1. locate the final/canonical daily Git report;
2. if Git is missing, search Gmail Sent for that report date;
3. when one authoritative final/corrected/formal-resend message can be identified, backfill the Git archive from Gmail readback before continuing;
4. if the authoritative version cannot be resolved, mark `MONTHLY_SOURCE_GAP` and do not send the monthly report until repaired.

Superseded emails must not be treated as separate daily observations.
Historical Gmail/Git daily bodies remain immutable audit records even when they contain old formatting or operational text. Monthly synthesis must ignore monitoring plumbing, scheduler/Gmail/GitHub/recovery prose, QA explanations, empty-section explanations and other non-market meta text.

### Monthly report purpose

The monthly report is not a concatenation of daily emails. It must aggregate repeated evidence across the month and answer:
- what market regime actually dominated the month;
- which themes strengthened or weakened across multiple daily reports;
- which macro/rate/oil/USD variables drove returns;
- which sectors and companies showed durable relative strength/weakness;
- what changed in AI/technology, IPO/private markets and regulation;
- what the next 1 to 3 months most likely hinge on;
- which stocks are attractive to buy/accumulate, which require a better entry, and which should be avoided or downgraded.

For every recommended stock include:
- recommendation tier: `长期核心 / 分批买入 / 成长卫星 / 观察等待 / 回避`;
- month-end/current price or valuation context when reliably available;
- 1 to 5 year thesis;
- 6 to 12 month catalysts;
- key risks;
- explicit invalidation conditions;
- preferred entry conditions;
- portfolio role.

The report must also include IPO/private-market opportunities only when there is enough verified pricing, rights, valuation or filing information to support a decision.

### Monthly idempotency and delivery

On day 1, after the normal daily report is delivered, check Gmail Sent for the exact previous-month monthly subject. If already delivered, do not resend. If absent and the monthly source manifest passes, send exactly one monthly report, read it back, then archive the exact Gmail body to GitHub and verify the archive. Recovery windows may deliver a missing monthly report, but must perform the same source-completeness and quality gates first.
