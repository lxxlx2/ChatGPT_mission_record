# Airdrop / TGE Monitor

记录每小时后台检索。无新事件时只写 GitHub 记录，对 ChatGPT 和 Gmail 保持静默。

额外规则：官方 X 帖文中包含的 t.co、官网、claim/checker/allocation 链接必须继续打开核验，不能只读帖文文本。继续监控 Clay Shares 的 allocation、法律文件、分发、签署、KYC、领取或交付进度。

## 项目身份锁定与同名冲突 Hard Fail

每个白名单项目必须先建立并使用 canonical identity tuple：

`project_id + canonical_name + official_x_handles + official_root_domains + known_tickers + known_chains + known_collision_names`

候选事件必须从白名单项目自身的官方账号或官方根域名进入。相似名称、相同 ticker、同链、同生态、合作关系、迁移历史、第三方搜索摘要均不能替代项目身份锚点。

对每个候选事件及所有跳转链接必须持续记录：

`candidate_source_account`
`candidate_source_url`
`candidate_project_name`
`final_domain`
`identity_match`
`identity_conflicts`
`same_name_collision_checked`
`hard_fail_triggered`

以下任一项存在未解决冲突时，禁止触发 ChatGPT、Gmail 或 official event：

1）官方 X handle 不匹配。
2）根域名不匹配。
3）ticker 冲突。
4）chain / contract 冲突。
5）存在同名项目且来源账号无法唯一归属。
6）公告来源属于非白名单项目。

发现冲突后禁止通过“正文里不写 ticker / chain / contract”等方式绕过。必须停止正式提醒，重新做项目身份核验。

Claim / Checker / Allocation / Rewards / KYC / Wallet 页面采用 two-anchor rule：至少需要两个直接身份锚点，其中至少一个必须来自被监控项目的 canonical 官方 X 或 canonical 官方根域名。第三方结果加一个同名操作页面不构成证据链。

已知回归案例：白名单 `Space (@intodotspace)` 与 `Spacecoin (@spacecoin)` 必须视为两个独立项目。任何来自 `@spacecoin` 的 `$SPACE` airdrop/claim 信息不得归入 `Space (@intodotspace)`，即使另有 `into.space` 页面存在 claim 或 migration 流程。对应事故记录：`airdrop-tge-monitor/incidents/2026-09-14-space-cross-project-misattribution.md`。
