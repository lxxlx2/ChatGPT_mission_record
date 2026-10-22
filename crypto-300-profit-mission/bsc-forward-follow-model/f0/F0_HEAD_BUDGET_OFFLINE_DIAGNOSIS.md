# F0 HEAD 高度和有限刷新预算：纯离线因果诊断

**前置审核通过的固定基线：** PR #160 SHA `20c1df5ed69200ff24fbd60084c5553111d1eded`，独立 Mac 报告 325/325 PASS，13/13 单独 PASS、HEAD 新鲜度原 P1 关闭。六组 Mac 私有 Journal 时长复放见用户报告，**都是模拟**；不代表并发 HTTP 实测。

## 先回答主线疑问

PR #159 的理想三槽位吞吐 2.753–2.976 blocks/s **假设所有 24 个区块任务立即可派发**。PR #160 在当前工作流中必须遵守：
- 只有 HEAD 确认过的高度可以派发；
- 到达已确认 HEAD 之后，即使另外两个槽位空闲，也必须刷新 HEAD；
- HEAD 与 BLOCK 共用总共三个槽位、250 ms 全局请求起始间隔以及最多 32 次总请求；
- 每次源头 HEAD 刷新（最多六次）都消耗真实的一次性预算；真实头同步和按序父哈希验证必须与响应吞吐区分；
- 最新 HEAD 过期时即使刷新在途，也不能继续派发区块。

所以当采集器接近最新链头，*越快完成已知区块，不一定代表越多有效区块会完成*：它可能过早触及 HEAD 刷新上限并终止。这是有限实验预算导致的窗口截断和源头可用性限制，而不是真实服务商三路限流的证据。

六个已公开的合成场景（HEAD 间隔 4/8 × 假设耗时倍率 1/1.5/2）分别只得到 11/19/21/11/20/24 块。五组在 HEAD 刷新六次用尽后退出，第六组恰好达到 24 块上限；六组最大连续吞吐仅 1.644 blocks/s，低于用于模拟的来源增长率 2.178。这些数字不能与未来 24 小时真实运行能力相提并论。

## 这次实现范围

新增独立 `f0_l1_head_budget_diagnosis.py`，只读此前 PR160 **已批准、纯离线模拟器返回的事件 trace**，逐次复盘 HEAD_REFRESH 的直接触发条件：
1. `NO_ELIGIBLE_HEIGHT`：下一个高度大于最近已确认 HEAD；
2. `DISPATCH_CHECKPOINT`：达到每4/8块检查点；
3. `HEAD_STALE`：超过新鲜度 TTL。

会同时保留每个 HEAD 的多重触发原因，避免因原因重叠而错误归因。还输出每次刷新确认了多少新高度、刷新前后可派发高度数量、已耗刷新预算、剩余区块预算、HEAD 虚拟工作时长占比、三个共享槽位的虚拟占用率、已知未尝试区块数，以及响应和连续提交吞吐。**不修改 PR160 调度规则、不合成额外链上事实、不推定真实网络最新高度。**

输入仍是 Mac 私有的旧 `journal.json` 逐字节 SHA256 验证，仅借用其中已观察的串行请求耗时。CLI 只运行 PR160 的六组合成场景并保留独占的 0600 JSONL 假账本；不能联网、不能调用 live sender、没有 permit 参数。

### Mac 实际旧 Journal 回放（绝对离线）

从**本 PR 固定 SHA 的独立 checkout**执行；建立**全新**私有输出目录（不能复用旧模拟输出）：

```zsh
umask 077
mkdir -m 700 "$HOME/Library/Application Support/MissionEvidence/20261022-f0-head-budget-diagnosis"
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_head_budget_diagnosis.py --journal "$HOME/Library/Application Support/MissionEvidence/20261021-adaptive-sampled-head/archive/journal.json" --expected-sha256 e069b7cd38c2ad3c8a3af3a1b1c220efab1714fe4de0bb7a9e2b814a2302d61a --output-dir "$HOME/Library/Application Support/MissionEvidence/20261022-f0-head-budget-diagnosis"
```

仅把脱敏后的 6 组指标和每次刷新类别同步到 PR，原始 JSONL、旧 journal、钱包信息、许可、nonce 等一律不上传。

## 决策标准

- 若六组多数 HEAD 刷新是 `NO_ELIGIBLE_HEIGHT`，且每次刷新能释放的高度数较小：当前主要是高度可用性与刷新次数的数学限制，**先研究源头 HEAD 可用性/刷新频率与预算的关系**，不要宣称增加三路线程可以解决。
- 若多数是 `DISPATCH_CHECKPOINT` 而还有大量已确认高度：检查是否可以在**明确新鲜度边界**内减少不必要的检查点；这仍需离线对照及新 SHA 独立审核，不得自动扩大预算。
- 若大量是 `HEAD_STALE`：不能简单放宽 TTL；需要对新鲜度、在途 HEAD 延迟和完整块获取速度做联合模拟，不把延迟容忍换成虚假的实时性。
- 即使诊断能解释离线 1.644 bps 上限，也不能把并发供应商吞吐标为验证通过；只有以后获得新的用户授权、独立审过真实并发代码和逐字节许可，才允许有限真实实验。

`F0_NOT_PASSED / PRODUCTION_NO_GO`，历史 30 次真实请求许可已经消耗，零新增 RPC/WS、签名、交易或部署。
