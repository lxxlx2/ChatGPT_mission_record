# Monster 原官方Publisher采集器 — 阻断P2定向修复、真实HTTP反例与单次复审包（2026-10-19）

## 一、审核结论和问题边界

**原Codex审查结论为 `REQUEST_CHANGES`**，固定代码SHA `e6fb680b868d52a9a0d77d80920b6049fa36252d`、比较基线`f557780d9ad4ea27a69b1bebe7c9c67065790b5d`。Codex独立读取全部3个Actions artifacts的真实**1533个官方ZIP+.CHECKSUM及2,207,520根完整1m**，每个issuer哈希/时间网格/OHLC/原511人口匹配均通过；**独立审核P2=1**：`urllib.request.urlopen(request)`默认自动跟HTTP 302请求到目标地址，调用`response.geturl()`检查时，目标服务器已收到GET。HTTP来源只读限域承诺错误，但**不否认**已通过真实哈希校验的市场档案，也不代表后续可交易盈利。

**冻结限定修复**：[原P2预冻结修复说明](MONSTER_PUBLISHER_REDIRECT_PRE_REQUEST_P2_FROZEN_FIX_20261019.md)（freeze commit `99e621503797cfa3cff6e72a1cfd11a748b108a0`）：只在原`crypto-300-profit-mission/local-agent/scripts/monster_v4_forward_spot511_official_publisher_acquire.py`中改用自定义`HTTPRedirectHandler.redirect_request(...)`，对于301/302/303/307/308在发送任何target第二次请求前抛出明确`ValueError("PUBLISHER_REDIRECT_BLOCKED_BEFORE_FOLLOW")`；由`build_opener(_RejectPublisherRedirect()).open(request,timeout=...)`替代自动follow`urlopen(request)`。原`response.geturl()==url`二次保险继续保留，且原BASE、来源名录、Unicode编码、CHECKSUM/发行方SHA、归档写保护、大小/并发/重试限制完全不变。没有改Stage165/166、原获Codex批准的300U资金账本、主D0/D1、Frank/Mac/Gmail或定时采集/下单。

### 固定版本

- **唯一实际代码+定向CI审核SHA：`18ec436d04fb2c121a62a46311e56d15d4dc2606`**。定向对照旧REQUEST_CHANGES SHA `e6fb680b868d52a9a0d77d80920b6049fa36252d`。二者之间不仅有此次三个执行文件，还含之前原真实Oct18 source proof与回顾文档；Codex复审**只审新增P2被报告项及明确修复**，不要因宽泛diff去无休止重审已独立验证真实数据/旧模型。
- 代码文件`crypto-300-profit-mission/local-agent/scripts/monster_v4_forward_spot511_official_publisher_acquire.py`，相对旧审SHA仅**11行**变动；测试`.../tests/test_monster_v4_forward_spot511_official_publisher_acquire.py`新增2个真实HTTP服务相关回归（92行）；一次性**不下载任何官方市场行情**工作流`.github/workflows/monster-v4-publisher-redirect-pre-request-p2-offline-once.yml`（仅该新workflow文件首次push触发、无schedule、只读Git权限）。
- 主冻结原T0完整511名单、真实三日1533档原始证据与发行方ZIP SHA不改；原Git三日核对`evidence/monster_forward_spot511_oct16_18_1533_actual_issuer_source_reconciled_v1.json`仍记录2026-10-16/17/18各511、每文件1440根，总2207520根已校验1m。**不要为修复P2重新下载1533原ZIP，不把历史行情做BUY**。

### 实际测试与CI证据（已执行，不是计划）

- [成功CI #39216876277](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39216876277)；真实trigger SHA精确为`18ec436d04fb2c121a62a46311e56d15d4dc2606`；Job ID `117942686055`；原始日志**12/12 unittest通过、10/10工作流步骤成功**；`py_compile` PASS；Git工作树无未提交修改。
- 真正两个本地`ThreadingHTTPServer`，没有把HTTP入口替换成synthetic `getter`，对`301/302/303/307/308`逐个回应`Location: http://127.0.0.1:<另一个监听端口>/non-publisher.zip`。真实`fetch_one_url`每次明确抛`PUBLISHER_REDIRECT_BLOCKED_BEFORE_FOLLOW`，源服务器累计5次GET、**被拒绝目标服务器实际GET数恒为0**。此处真实局域socket可复现，不只是检查异常文本。
- 正常真实本地HTTP直接`200`继续能获取来源字节并返回`http_status=200`；原错误SHA、不完整1439行、真实512人口来源拒绝、Unicode percent encoding、旧档不可覆写、HTTP404不算0 WATCH等既有测试均PASS。不得使用原仅模拟`getter`测试冒充双服务器反例。
- CI原始保全证据关口打印`MONSTER_1533_ORIGINAL_SOURCE_PROOF_UNCHANGED_NO_REDOWNLOAD`及`MONSTER_REDIRECT_P2_ONLY_NO_ARCHIVE_DOWNLOAD_NO_GIT_WRITE_NO_DEPLOY`，并实测原1533来源Git机读SHA所代表覆盖计数及G4/G6无变。新增定向CI没有官方ZIP网络采集、Mac部署、Frank、Gmail、真实交易；无自动schedule/cron。

## 二、独立其他AI定向复审完整任务（供Claude网页或Codex原对话直接复制）

**审核目标**：独立复核Mission仓库`lxxlx2/ChatGPT_mission_record` Draft PR#30分支`research/monster-v4-local-discovery-20261010`，固定SHA `18ec436d04fb2c121a62a46311e56d15d4dc2606`，唯一对照Codex上一轮REQUEST_CHANGES的SHA `e6fb680b868d52a9a0d77d80920b6049fa36252d`。在隔离detached checkout审核固定SHA，禁以最新PR HEAD替代。原审唯一阻断项P2：官方发行方HTTP反向302时，`urllib.request.urlopen`默认先访问跳转的非官方服务器，旧`geturl()`防护后置而无效。独立核查新`_RejectPublisherRedirect(HTTPRedirectHandler).redirect_request`在urllib发起目标请求**之前**阻断301/302/303/307/308，`build_opener(...).open`未自动跟随，初始只能请求`BASE`官方路径，原正常HTTP 200不受影响。

**重点复现**：使用真实两台本地`ThreadingHTTPServer`、允许源发302 Location至第二台服务；运行新真实HTTP `fetch_one_url`，断言第二台`GET == 0`，不能仅凭`ValueError`或简单`getter` stub就宣称解决。另核对301/303/307/308与正常HTTP 200。检查原网络错误统计、重试、SHA校验、数据保护无回退。原始数据真实来源完整性上一轮Codex已独立从原三个Actions artifact验证原511人口2026-10-16..18日1533个ZIP/CHECKSUM和2207520个1m；这次**不需要重复1533全下载**，仅核对Git原SHA证据未被P2修复变更。无需重审Stage165/166/已审300U账本或原2月历史经济模型。

**独立执行**：运行`python3 -B -m unittest discover -v -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_forward_spot511_official_publisher_acquire.py`（期望**12/12**）；`python3 -B -m py_compile crypto-300-profit-mission/local-agent/scripts/monster_v4_forward_spot511_official_publisher_acquire.py crypto-300-profit-mission/local-agent/tests/test_monster_v4_forward_spot511_official_publisher_acquire.py`；核查真实[CI #39216876277](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39216876277)触发SHA、原Job日志、10/10步骤、双服务GET=0的可证伪反例及Git工作区无修改。

**结论规范**：`APPROVE / REQUEST_CHANGES / BLOCKED`，固定唯一SHA、审查者身份与准确模型名或`UNVERIFIED`、实际源码与CI及反例、P0/P1/P2和阻断原因。只有P2真正闭合才准`APPROVE`**采集器网络安全的这一局部代码范围**，不能将用户现场原三日行情、未完整OOS、真正PIT上市、同时刻ask/bid、手续费/滑点或执行净收益升级通过，不能将其他模块旧代码自动再批准。PR仍Draft，继续`G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。

## 三、后续主线

此P2定向修复作者CI成功但**独立第二轮复审尚`NOT_DONE`**。正式其它AI重审回复前，仍应记录为`REQUEST_CHANGES_P2_REMEDIATED_PENDING_INDEPENDENT_REVIEW`；成功后才升级固定SHA的Publisher Collector `APPROVE`。2026-10-19原冻结7日新Spot窗口未完成，后续继续按完整官方source/population、真实3分钟T因果队列、上市PIT及执行L2/费率推进，而非旧2月历史回调上拟合“正盈利”。

`G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。
