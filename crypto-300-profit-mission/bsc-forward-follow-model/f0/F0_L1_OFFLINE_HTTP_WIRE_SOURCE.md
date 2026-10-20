# BSC F0 L1 — 官方 HTTP JSON-RPC 报文适配与未来高度规划（离线）

**Status:** `SOURCE_WIRE_CODED_OFFLINE_ONLY / COMPLETE_STACK_REVIEW_PENDING / NO_RPC / NO_RUN`.

这是已离线独立审核 #145 的下一层 **HTTP 接口**，而不是第二个监听程序、不是真实采集器，更不是 24–48 小时 F0。#145 固定审核 SHA `cea094f38d72f85e71ca63f0aa3837532de3b205` 在完整 checkout 获独立 `230/230 PASS, ZERO SKIP`；本分支未更改其已经审核通过的 `f0_l1_injected_capture.py` 源码或测试。#144 组合 SHA `6c998d7b4c5d0056d675daf0ae70f4e63837c259` 曾独立 `224/224 PASS, ZERO SKIP`，两项结论已经分别写入 GitHub PR 评论。

## 功能交付（两个新增文件）

`f0_l1_http_wire.py`：

1. 只接受 `eth_chainId`、`eth_blockNumber` 和 `eth_getBlockByNumber([0xheight, true])`，拒绝 `eth_getLogs`、写交易请求、`latest` 以及 `fullTransactions=false`；所有标准请求指定固定、唯一正整数 ID。
2. 统一官方免费 BSC 主网端点 `https://bsc-dataseed.bnbchain.org`，严格要求 JSON-RPC 2.0 格式，HTTP 200、`application/json`、无压缩响应、响应 ID 与请求一致、不能同时含 `result` 与 `error`。HTTP redirect/非 JSON/过大正文/错误 ID 失败关闭。**这是从假传输回调返回的 HTTP 字节进行验证，并没有真实 socket/TLS 或重定向链的实现。** 将来真实传输实现必须在网络层自己禁用代理/重定向、强制 TLS 及原始响应字节数上限，而不能把本解析函数当成传输安全门禁。
3. `make_injected_http_sender(post_bytes)` 将 **外部注入** 的 `(endpoint, request_bytes, timeout, cap) -> (status, headers, response_bytes)` 转成与已审核 #145 区块采集核心一致的 `sender(payload)` 接口。仅使用假回调可称为完全离线；真实 HTTP 回调可能联网，**没有自动获得许可**。
4. `plan_prospective_heights(chain_rpc, head_rpc, ...)` 对假 `eth_chainId=56`、有效 `eth_blockNumber >0` 做纯数据验证，输出 `head+1` 到 `head+n` 的**未来高度**和预算。绝不把回溯 `head-n` 的历史扫描伪称为首次捕获，或者把这一步当作真实链头已确认。

新增 `tests/test_f0_l1_http_wire.py` 共 11 项定向测试，包括请求白名单、真实 JSON-RPC 编码、注入 HTTP 字节回放、HTTP redirect/Content-Type/压缩/体积/ID/JSON/歧义错误响应、无自动重试及未来高度规划。

## 已运行证据

本地隔离目录使用 **确切提交的源码与测试**（Git blobs 均与远端一致），运行：

```zsh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

**实际 Ran 11 tests, OK，无 skipped。** 测试日期 2026-10-20；所在本地隔离目录只有新 HTTP wire 模块和测试，不包含 Mission 其他 230 个测试，不允许用它宣称整个 F0 全通过。真实日志仅保存在本次作者的隔离运行环境，并未上传 Git；SHA256 `bc39d3043c02b16c8d31243b83b99fd6ece068c5d541dd0d6b7955a81a79d575` 仅作本地日志识别，不能当作 GitHub 附件。

| 验证文件 | 已验证 Git blob | 实际本地 SHA256 |
| --- | --- | --- |
| `f0_l1_http_wire.py` | `535c0e012b9d301c1bbebc25004c906e648ac15d` | `9eeeffc3c5b6adab7beeec8cdf0ea81d5117f2aca1647224e264abd8df69ebda` |
| `tests/test_f0_l1_http_wire.py` | `e4a1a2fb6fe703903347b9028cac308898d7390b` | `b03208c6f09d1f970a1e6078c6fb83196afea0f7156f5b4c49639b5c6e6e75c0` |

现有批准基线 230 + 新增 11 = **完整 checkout 预计 241 项测试**（`241/241 PASS, ZERO SKIP` 是下一次独立审核要求，不是作者本地已运行结果）。需审核新代码/PR SHA 是否仍不包含网络实现、是否可直接以假 HTTP 回调连接到 #145 的采集核心、是否影响已有日志/账本/种子/20 PRIMARY/Router 选择/旧许可门禁。旧的真实四次烟雾测试和单高度 24 次资格检查授权**都已经消耗，不可重复使用**。

## 真正实现短窗口主线还缺什么

接下来应**直接开发一个独立审查的、本机用户可运行的、有硬性界限的只读 HTTPS 驱动**，接入已批准采集核心，先确认链 ID 56 和当前 head，再观察未来块；它必须在每个真实请求发出前持久记账（包括 chain/head 的两次请求），强制总调用预算、速率、窗口、响应字节上限、TLS/禁止代理与重定向、过期停止、重复运行 nonce、原始数据可验证性/脱敏和失败分母。推荐先在真实 30～60 个区块的**短样本**上衡量成功率/延迟与手续费为零的公共端点性能，而非直接宣称 120 秒约 267 块全部可覆盖。

真实 RPC、WS、生产部署和控制对照资格都**不包含本 PR 权限**。另须**用户新授权**以及绑定真实运行 SHA、非复用 nonce、UTC 窗口与预算的具体 permit 经独立审查；批准的是一次试验，不是长期监听。真实首见延迟、Router swap 因果、E1/E2/E3、+60/+300/+900 秒价格及规则收益仍未建立。

官方资料： https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/ （BSC chain ID 56、官方 HTTP 节点、公开列出的 10K/5min 限制以及部分主网节点禁用 eth_getLogs；均为文档声明，不保证本次用户客户端实际服务能力）。
