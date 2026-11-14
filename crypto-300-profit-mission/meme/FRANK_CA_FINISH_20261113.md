# Frank CA 软件收尾与本地验收（2026-11-13）

后续：本记录保留11:24阶段；原298分类归因、Owner隔离及17:39新验收见[后续结论](./FRANK_CLASSIFICATION_GAPS_20261113.md)。下文不覆盖后续当前状态。

当前源码并已安装 `9677da7d0b429a4a69fd270cd0097231e4713507`，parent `e38d18421b46888a7cf36b4d004f08bc99d4f926`；本轮基线 `aad880991565d148aa6cc2f74fa0de1f5e6c27c7`，源码仍在原PR252，stack在PR220固定 `d43878828c86eacee5be9df8a17d16fc63a74bb6` 上。最新读取main `85fc12b14d65d75d5b2354d4e1bbd42974b1439f`，AGENTS/开发规则与相关Frank门禁无增量。用户明确授权本地调试、直接部署、免独立review；不宣称独立APPROVE，不合并，不恢复MC Loop/盈利研究/通知或交易。

## 已修复的实际缺陷

- **首买完整性**：较早getTransaction异常补holder phase；真实分类器返回UNKNOWN_NEEDS_REVIEW也保留分类缺口，避免已读但未解释交易升级为“完整首买/未见买入”。超时、null、分类异常、缺metadata有/无较晚BUY、游标/空页及重复缓存均有回归。正常成功路径仍只声明当前选中token账户，关闭账户/全Owner历史没有升级。
- **origin接线与恢复**：CheckpointClient仅在底层支持时暴露collect_origin，并经过既有录制/只读重放；legacy能力不伪造。预算及检查点完整性错误在analyzer/JSON读取路径显式传播。另修复来源TimeoutError/OSError被错误归为存储不可用；真正存储错误继续fail closed。错误工件保留安全code，私有URL不入回执。
- **独立复核计时**：旧版在主任务启动时就构造60秒独立RPC，慢主流程会使第二提供方首wire前过期。改为先完成primary读、紧接独立读取前才构造；既有对象不重置deadline，仍最多4wire/60秒，主1200wire/1800秒及最终发布门禁保持。主硬预算/CheckpointError不降级；独立自身预算耗尽仍明确UNAVAILABLE。reason不回显任意异常文本，新增secondary_wire_attempts只读取已有计数，不增加请求。
- **准确展示**：依据supply_bracket描述跨slot供给夹逼及前/账户/后slot；仅真实相等slot使用同slot措辞。后端holder_balances原因按实际方法命名。Pump complete仅表述曲线完成标记，不再据此宣称迁移已验证。
- **安装身份**：完整干净detached checkout替代复制.git的安装；最终501个tracked local-agent文件逐个Git blob校验、Git HEAD与运行目录一致。旧运行目录不reset/clean，完整字节备份保留。

## 实际离线与本机验证

最终固定HEAD在Mac隔离树运行17个相关Python测试文件，446 passed / 1.07秒，审计拒绝全部socket.*且事件0。当前账户/分页/排名/binary/池角色/完整性、RPC预算、真实checkpoint恢复与origin录制/只读重放均覆盖。Node四文件202 passed（运行于e38d，同一app.js与测试blob在最终9677未变），node --check通过。Playwright脚本因本地缺少playwright未启动，不记作PASS；真实Chrome另列。最终HEAD核对未发现GitHub workflow/check runs，不挪用旧CI。

源码变更前，新首买反例5失败/7通过，origin首轮7失败/2通过（后加2存储对照），独立计时/泄漏首轮10失败/4通过（后加2预算对照），三项前端反例均失败；修复后纳入上述通过集。完整实际命令与原件指纹见[机器回执](./evidence/frank-ca-finish-20261113.json)。

原Dashboard8766两次定点切换，最终PID16018；第一阶段旧运行497文件、第二阶段500文件分别完整备份，70报告文件、3 SQLite一致备份/integrity/FK、14保护哈希均验证。旧字节备份和新候选各实际Handler无监听预检：8原任务精确GET/1绑定补证、HTML/JS/CSS、D1/D2、Scanner均通过，socket/POST0。切换后再次8任务GET全文等值、保护文件/报告不变；Scanner2268/1f2c6af仍LIVE/无漂移/0错误，Loop未加载。回滚分支未实操，不把备份可加载当作实际回滚重启。

## 单次真实来源验收

本轮只从Chrome对既有CA发起一次手动查询，复用已配置RPC和已存在的免费来源；无新CA、key、provider、付费、端口、监控、自动任务、通知、签名或交易。主1200wire/1800秒，独立最多4wire/60秒，HTML/metadata/post上限不变。本次已DONE，实际用时357.387秒，数据时间2026-11-13T11:24:34.244167+07:00；主558wire（含23次endpoint失败后恢复）/990缓存，独立另4wire，共562次RPC尝试。1529 checkpoint逻辑读取=1525 RPC逻辑读取+4客户端操作；不能把wire/cache/逻辑读取任意相加。新报告SHA256 `2f1e663f8a47079609ffa1ad61c9dbe2359667aa48ead0706932390b4d8d4825`，1529条逐序哈希链、metadata/head/count、DONE job/Mint/报告hash、timestamped原档及精确job GET均通过。此为档案与证据核对，不冒充完整业务回放或外部真实性认证。

- 全Mint：33633账户、7960非零账户、7951非零Owner，全局Top10 **55.6025%**；排已核验池/前缀策略 **16.8260%**，normalization_complete仍false。slot前468789955 / GPA468789966 / 后468790192，后端holder_balances原因正确为供给夹逼，Chrome同样明确非原子同slot快照。
- origin已真实读取：metadata JSON和2帖API共3读均OK；报告origin与checkpoint原条目全文相同。可追溯引用链起点仅限这条链，官方认领和全网最早起源仍UNVERIFIED。叙事内容及来源链可见，未把帖子引用关系写成作者认可该币。
- 独立PublicNode仍 **UNAVAILABLE / RPC_JOB_WIRE_BUDGET_EXHAUSTED**，实际4次尝试；修复了首wire前过期的软件机制，但未得到可用独立数据。逐次错误体未捕获，不能倒推具体HTTP规则；到限停止，未替换来源或继续查询。
- 新首买结果9个CONFIRMED_BOUNDED / 3个UNRESOLVED / 8个NOT_SCANNED；298条CLASSIFICATION_UNRESOLVED缺口记录（不等于298次RPC失败或298个唯一交易）没有被升级为完整首买。29窗口=16 PAGE_LIMIT/13空页，关闭账户/全Owner完整历史仍缺。
- 208交易证据逐条与捕获成功原交易及真实分类器输出核对，10资金/175归集逐条与原交易提取核对；三组业务键重复0。没有据此声称全部216关系边或所有经济历史完成独立验证。
- 原70文件中68固定文件未变，2 latest/history按新任务预期更新，新增6任务/检查点/时间戳文件，总76；13非缓存保护哈希不变，仅RPC cache按本次查询预期更新。旧任务原件、旧补证不回填。

Chrome实际显示新任务DONE、来源链两帖、供给夹逼/独立失败/有界首买，刷新恢复同一新job通过，页面留开、截图留Git外。本轮软件收尾及干净本地安装PASS；完整CA仍PARTIAL / INCOMPLETE_EVIDENCE。剩余为独立来源、关闭账户历史、全部身份/受控快照及其他代表样本。INVEST_NO_GO / TRADE_NO_GO保持；不因本次有结果恢复盈利研究、Loop、通知或交易。
