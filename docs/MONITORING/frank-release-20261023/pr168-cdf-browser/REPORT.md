# PR #168 C/D/F Mac 浏览器补测

**MAC_ISOLATED_BROWSER_PASS**

固定产品 SHA `656ed2c96f4210d106d7b1129ec6cf8d7c4586f3`；开始/结束 GitHub HEAD 均一致。独立 detached checkout，macOS darwin，既有 Chrome 155.0.8059.86 / Playwright headful，独立临时 profile。未安装依赖、未改产品代码、未替换 renderClusterReport、未修改计时器。只运行 C/D/F，没有 A/B/E 或历史交易回放。

|用例|结果|真实浏览器观察|
|---|---|---|
|C|PASS|A 历史报告 GET 挂起；明确点击表单仅发送 fixture POST B（202）；B 状态 GET DONE、报告 GET 200，原始 renderer 成功显示 FIXTURE_B 与 DONE 后归属未证实提示；随后释放 A GET 200，B Mint、summary、status、恢复控件均未变化。|
|D|PASS|DONE GET 200，首次报告 GET connection reset；session 身份保留并出现“重试读取报告”。点击后第二次报告 GET 200，真实 report/metrics 渲染成功、pending 清除、提交按钮恢复、恢复控件隐藏；只 poll 一次、报告 GET 两次、POST 零。|
|F|PASS|使用同 Mint 历史 incomplete 报告，GET 200 后可用内容正常渲染，状态显示“覆盖仍不完整”“与当前任务的关联未经核实”，无 done 类。正常点击展开技术细节，覆盖区域明确显示归一化尚未完成。未标为完整 CA 验收成功。|

## 有界 fixture 调整与原始记录

第一次运行 C/D/F（端口 64470）：C、D 通过。F fixture 设为 RUNNING，产品正确隐藏历史恢复按钮，测试点击超时。因此原始自动结果为 FAIL；这是 fixture 前置条件错误，不是报告渲染缺陷，不能删除或改写原始结果。

仅补跑 F（64577）：按本轮规则允许的必要设置，GET 404 显示历史读取入口；实际报告渲染成功且状态准确。但额外覆盖区域断言读取 innerText 为空，原因是原页面技术细节 details 正常折叠。保留此失败记录。

仅调整 F 用户操作：正常点击“展开完整链上证据和技术细节”，保留覆盖文字断言，再仅执行 F（64600）：PASS。没有强制点击隐藏按钮、改 DOM、改产品源码、删除失败断言或重复 C/D。三次脚本与全部结果分别保存在 cdf-initial、f-setup-adjusted、f-expanded-pass，SUMMARY.json 为经核实的最终组合结果，未将原始 FAIL 改成 PASS。

## 隔离与完整性

原始 index.html、app.js、styles.css 的 SHA256 见各 setup.json 和 SUMMARY.json；每次执行前后完全一致。仅静态文件由本地 HTTP 读取，同源 API 由 fixture fulfill/abort；不存在正式 Mission 后端、worker 或链上扫描器。路由阻止其他 origin，Chrome 背景连接通过本地 deny-only proxy 拒绝，52 次意图均没有转发到外部。背景查询串已脱敏。

```text
REAL_RPC=0
PRODUCTION_8766_REQUESTS=0
REAL_CA_POST=0
REAL_NOTIFICATIONS=0
REAL_TRADES=0
FIXTURE_ONLY_POST=1
```

端口 64470 / 64577 / 64600 均为随机 127.0.0.1 端口，不访问 8766 或其他生产端口。唯一 POST 为 C 用户明确提交到 fixture，无真实扫描。C 的 404 为必要入口；D 的 connection reset 为故意注入；两次 F 的 404 为必要前置。console.json 均无意外 console error，pageerror 均为 0。预期网络/404 错误完整保留。

测试后每个浏览器 context/process、fixture、deny proxy 已关闭、临时 profile 删除。独立执行 lsof 对三个端口读回均无监听者，pgrep 本次 profile 无进程。未修改生产 DB、控制文件、Dashboard/V1/MC Loop、launchd、策略、通知或交易；未部署、合并。

## 证据与边界

各子目录包含原始 setup/result、脱敏 HTTP 序列、console、DOM、真实截图和执行 runner。C、D 的通过证据在 cdf-initial；F 最终通过证据在 f-expanded-pass。fixture 地址/任务号均为合成数据，没有真实钱包或密钥。

执行命令：既有 Node `/Users/jerson/.nvm/versions/node/v24.18.0/bin/node` 分别运行附录三个 runner。开始执行于 2026-10-23；最终完成 2026-10-23T09:50:05.986Z（曼谷 16:50:05）。

**BROWSER_RELEASE_GATE_PASS / DASHBOARD_PRODUCTION_AUTHORIZATION_STILL_REQUIRED**。

已满足申请单独 Dashboard-only 上线授权的浏览器条件。该结论不是完整 CA 数据/链上分析 Gate A-D 通过，不是生产验收或发布授权。本轮结束，不执行生产切换。
