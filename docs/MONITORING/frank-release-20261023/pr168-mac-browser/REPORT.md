# PR #168 Mac 隔离浏览器验收

结论：**MAC_ISOLATED_BROWSER_FAIL**。真实浏览器验收发现报告渲染阻断；本轮未修改产品源码，没有部署或生产操作。

- 固定产品 SHA：`cfa789fa23c9c331f0d3015d188c77ec5a923a33`；GitHub PR HEAD 当场读回一致。
- 产品基线：`31dd598df248ca15f731913a5cbf82e88b981874`。
- 平台：真实 macOS / `darwin`；已有 Google Chrome `155.0.8059.86`，Playwright headful 独立临时 profile；未安装依赖。
- 随机 fixture：`http://127.0.0.1:54929`，不是正式 Dashboard。
- 执行：`/Users/jerson/.nvm/versions/node/v24.18.0/bin/node /tmp/frank-pr168-mac-browser-acceptance.cjs`。附 runner 为本次原始脚本（其临时路径仅用于重现说明）。
- 时间：结束于 `2026-10-23T04:50:43.474Z`。
- 原始 index.html/app.js/styles.css 字节未修改；各 SHA256 在 setup.json，执行前后完全一致。

## 实测结果

|项|结果|实际证据与限制|
|---|---|---|
|A 读取中断恢复|PASS|初始失败 + 3 次自动 GET；实测间隔 1515/3005/6003ms；停止后等待 1.6 秒没有额外重试；按钮只 GET 同一任务，未 POST。|
|B 页面刷新|PASS|真实 page.reload；只 GET 原任务 B；保留 B Mint，未读取此前 A 缓存，未 POST。|
|C 迟到响应隔离|未完成，验收 FAIL|A 历史 GET 延迟挂起；用户明确 fixture POST B，B DONE、报告 GET 200，但渲染异常使状态停在“任务已结束，报告读取中断”。未到释放 A 的步骤，不能宣称迟到覆盖保护通过，也不能宣称已复现跨任务覆盖。|
|D DONE 报告恢复|FAIL|第一次报告 GET 按设计断线；身份保留、“重试读取报告”出现；点击后只发第二次报告 GET，HTTP 200，未再 poll/POST；但页面仍显示“报告读取仍然中断”，pending 未清除，提交按钮持续禁用。|
|E 新提交不确定|PASS|仅 fixture 内明确 POST B，模拟连接失败；旧 A pending 清除；真实刷新后没有恢复 A、没有自动重新 POST B。|
|F 失败和完整性|部分通过，验收 FAIL|404 在 C/E 正确停止；F 的任务编号不匹配正确拒绝且只 poll 一次；同 CA incomplete 历史报告 GET 200 后渲染抛错，显示“历史缓存读取失败”，未完成正常的不完整/关联未核实提示；没有错误标为完整成功。|

完整案例计数：3 PASS / 3 FAIL（C、F 含被阻断的子项，非全部子项已验证）。未重跑历史交易或 11 项离线测试。

## P1：报告渲染调用不存在的函数，成功 GET 被误报成读取中断

固定 SHA 文件 `crypto-300-profit-mission/local-agent/mission_agent/mission_control/static/app.js` 第 1488 行：

```js
caScheduleQuoteExpiry(quote, 'cluster-final-quote');
```

完整静态文件内没有 `caScheduleQuoteExpiry` 或 `quote` 定义；index.html 加载的是该原始 app.js。执行到该行会产生 ReferenceError。此调用也存在于产品基线（第 1472 行），因此是本次真实验收暴露的既存阻断，不应写成三项 P2 增量修复引入。

最小复现：恢复一个 fixture DONE 任务 → 首次报告 GET 模拟断线 → 点击“重试读取报告” → GET 200 返回同 Mint 合法报告 → summary 已写入 FIXTURE_A，但状态仍为“报告读取仍然中断”、任务保留、提交禁用（D-FAIL.dom.json / D-FAIL.png）。

原因链：renderClusterReport 先写 summary/部分 DOM，随后第 1488 行抛错；loadLatestCluster 第 1122 行 catch 将渲染异常吞为 false；DONE/重试分支误报网络读取失败。历史缓存分支也捕获同一异常并显示不存在可核对报告。因此不限于 fixture 缺少可选字段；调用本身无定义且无条件执行。

最小修复方向：在独立开发分支移除/修复这条孤立调用，保持本 PR GET-only 恢复范围；明确区分报告获取失败与渲染失败。补一项使用原始完整 app.js 和浏览器 DOM 的 DONE→报告成功渲染/清理 pending 定向测试，然后独立审核新 SHA。此轮不直接修源码，不授权外部报价或 RPC。修复后仅重测被阻断 C/D/F，不重跑无关页面/历史样本。

## 请求、控制台和隔离

`http-audit.json` 为脱敏请求日志；测试 Mint/任务编号全部为合成重复字符，不是真实地址。C、E 共 2 次 POST 全部由同源 fixture 拦截，未启动后端或扫描器。所有 API 由路由 fulfill/abort；只允许本地三份静态文件，其余页面请求拒绝。

Chrome 自身有 43 次后台连接意图，全部进入本地 deny-only proxy 后拒绝，未转发到外网；没有真实 RPC 或生产接口请求。背景查询串已脱敏。浏览器路由和代理的拒绝记录保留，不能将“无外部请求成功”写成“浏览器从未尝试后台请求”。

- `REAL_RPC=0`
- `PRODUCTION_8766_REQUESTS=0`
- `REAL_CA_POST=0`
- `REAL_NOTIFICATIONS=0`
- `REAL_TRADES=0`

控制台有 6 次预期 connection reset（A 四次，D 一次，E 一次）及 2 次模拟 404（C/E），属于测试注入。原始 result.json 的通用分类器将 404 列入 unexpectedErrors；经 HTTP 日志人工核对，它们是预期 fixture 错误，不能作为另一个产品缺陷。pageerror 为 0：渲染异常由产品 catch 吞掉，不代表没有异常。产品警告和浏览器错误原始记录在 console.json。

清理：本次 context/browser 已关闭，fixture 与拒绝代理关闭，临时 profile 删除；独立读回 lsof 确认 54929 无监听者，pgrep 未找到本次 profile 的 Chrome。未访问正式 8766，未运行 Mission 后端、worker、launchctl、通知或交易。未修改生产 DB、正式文件或原主工作区。

## 证据

- setup.json：浏览器、平台、端口、源码文件哈希。
- result.json：原始自动断言结果（包括超时原文）。
- http-audit.json / console.json：脱敏请求与控制台。
- *.dom.json / *.png：真实 DOM 和截图；D-FAIL.png 明确展示成功收到的合成报告片段和仍然中断的状态。
- acceptance-runner.cjs：本轮完整 fixture/浏览器测试脚本，无产品行为替换或计时器修改。

停止：不建议部署或合并。先修复上述报告渲染阻断并审核新 SHA，再完成被阻断的有界浏览器用例。本结论仅针对上述固定源码和隔离 fixture，不是生产上线或真实链上数据验收。
