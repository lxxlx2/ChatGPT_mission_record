# Monster Stage70：不丢 WATCH 的独立只读事件存储——预先冻结产品及技术方案

日期：2026-10-12 Asia/Bangkok。仅Monster原PR #30。本方案在完成任何新仓储代码前提交；仍处于研究/设计/实现/测试阶段，不含部署授权。

## 设计动机和证据

原V4历史D0早发现已确认；旧P1、D0_FIRST5及半日预留P2三套紧急预算分配策略都不能稳定保留重大机会，不能拿5条紧急配额决定是否让用户在观察列表看到某币。Stage68同源2700历史案例有196个首次D0、56个P1首次资格，研究紧急48、研究延迟8；Stage69另一已曝光5400案例有519个首次D0、166个P1资格，P2研究紧急113、延迟53。两个历史日期群不同，可相加进行技术记录回放：715个不同coin-date第一次WATCH、222个P1升级、共937个真正事件。它们不是900纯meme的现货可买信号，而是USD-M历史研究标的，不得被标为BUY。

## 产品契约，先不改预警模型

- Monster观察列表 READ-ONLY，包含全部真实来源验证的首次D0（即使以后P1被拒绝紧急名额）；显示首次D0 UTC、第一次P1 UTC或未知、阶段WATCH/URGENT_RESEARCH/CAP_DEFERRED_RESEARCH及最近更新时间。
- 永不把研究URGENT=真实BUY，所有未核实Spot/Alpha/DEX交易资格显式UNKNOWN，单笔交易额UNKNOWN；历史窗口数据只能标HISTORICAL_RESEARCH_ONLY，不能标当下LIVE。
- 已审核异常来源未入队的币属于SOURCE_CENSORED，不能把无WATCH误写成被判定不优。
- 只保存 **第一次D0** 和第一次P1升级作为研究证据；重复D0事件保存在既有Stage66原始全市场输入，不在本次有限范围的UI原型中模拟成新入场。后续如要生产重复D0日志须另补真实事件捕获，不得谎称已完成。
- 本原型不提供商品推送、用户实际通知、实时行情刷新、CA买入按钮、资金净利润，只为后续Dashboard可靠信息结构做源证据和SQLite状态隔离。

## 可复现技术方案及验收

- 输入只读固定原始Stage68 252条事件Git blob 8e5d3247aaf04ffd00e44d1ef214e4939d75fa6b，原Stage69 685条事件blob d34ff59b559023af0b0db67c818fb9b2649c0363，两者分支独立且审计源确定。
- 使用Python stdlib sqlite3，只有调用方显式传入新独立数据库路径才写入；无默认Mac目录、LaunchAgent、生产端口/进程、Frank表、外发HTTP或Gmail。
- journal表以event_id唯一，payload SHA256 byte stable；watch_projection表以(date,symbol)唯一，首次WATCH不变，后来的P1可升为URGENT_RESEARCH或CAP_DEFERRED_RESEARCH；状态永不回退WATCH，不因研究超额删除币。每一次导入采用单一ACID事务，完整日志对账后commit，任何坏数据或重复ID内容冲突必rollback并明确错误。
- 按UTC事件时间排序；同分钟先首次WATCH再P1；状态记录必须与原Stage68/69事实吻合。重复导入相同文件无新行也不改变内容，模拟同一数据库多次打开/重启后逐行完全一致。
- 结果导出summary JSON及历史关注池快照JSONL，CI本地临时数据库作为私有测试artifact，不把二进制SQLite发布为Mac生产状态。数据库数据只能来自源真事件，不能用当前时间伪装信号新鲜度。
- 真实验收计数：事件937（715 WATCH+222 P1）、715唯一关注项、161 URGENT_RESEARCH、61 CAP_DEFERRED_RESEARCH、493纯WATCH；输入少任何一条、重复交叉冲突、源Git blob变化、窗口UTC乱序、超额都必须拒绝。
- 有且只有机制验收可能通过；P1/first5/P2策略继续REJECTED。原型通过不等于独立其他AI审查或Mac部署完成。

后续：从该只读模型向真正可用、隔离的Monster Dashboard查询端定义API；为线上成交状态/CA加可信源，完整新日期因果发现/预警及成交回报验证，真实其他AI review、测试/修复过门槛后才考虑本地安装。没有额外用户操作；Monster DEPLOY NO_GO，FRANK UNCHANGED，GMAIL OFF，AUTOTRADE NO_GO。
