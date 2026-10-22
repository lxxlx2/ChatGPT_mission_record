## 2026-10-22 3500 ms 定时器 P1 修复（新的固定 SHA 仍须独立审核）

独立 Mac 审核在旧 SHA `dc2c6cbf2b4e228225d936a278b25dcde2ae1872` 找到等待绝对截止时刻与浮点相减的差异：1.0× × 3500 ms 的两组被错误地报告为只有2次请求和0区块，且等到60s到期。旧24组结果中这两格**无效**，不能视为等待策略真实性能退化。

定向改动仅将最短等待的条件由 `now - head_finished_ms < min_head_refresh_age_ms` 改为 `now < head_finished_ms + min_head_refresh_age_ms`。事件循环已有的 `head_hold_until_ms` 采用相同的绝对截止计算，因此不存在到达截止时却再次判定“尚未到”的矛盾；**HEAD 的 4000 ms 新鲜度门禁不变**。新增包含已报告真实串行耗时样本的 3499/3500/3501 ms 邻界回归，核对 HEAD 到期唤醒、随后派发合成区块、请求和三槽位预算。此分支运行前的新鲜度已审核父代码无需改动。

独立审核与 Mac 重算必须使用**新 SHA**，使用新的私有输出目录，例如 `20261022-f0-head-policy-comparison-r2`；不能复用之前生成的24组 JSONL。旧 SHA `dc2c6cbf2b4e228225d936a278b25dcde2ae1872` 仍保留 `REQUEST_CHANGES`。不得把新版本离线对照说成真实并发供应商测量。

# F0 三槽位离线 HEAD 策略对照：固定检查点 vs 可用高度余量＋延迟刷新

**固定基线:** PR #161 `9f28b741a2e83de0c3b72d2106dba47d4db4f381` 由用户报告独立 Mac 审核 `APPROVE_OFFLINE_CODE`，完整329/329及新增4/4通过；对实际保存在 Mac 私有 Journal 的合成 HEAD 六组诊断：35次刷新中32次主因为 `NO_ELIGIBLE_HEIGHT`、3次为检查点，0次单独因陈旧 TTL；2次检查点/无高度重叠。原始私有 Journal SHA256 `e069b7cd38c2ad3c8a3af3a1b1c220efab1714fe4de0bb7a9e2b814a2302d61a`。真实此前30次网络授权已消耗。

## 为什么要对照而不是继续直接增加并发

三路理想容量上限不等于有可读取的区块；当前短窗口6次HEAD刷新预算先耗尽。等待的成本是更晚发现新HEAD、提高确认延迟；可能换来每次HEAD更多新高度。只能在有**独立来源 HEAD**的后续授权真实试验里评估对交易时效性的影响，不能把模拟积压0当成追上全球最新链头。

本独立实验在新的开发分支扩展`f0_l1_three_slot_offline.simulate()`的可选策略。**默认 `checkpoint` 完全保持已批准 PR160/161 行为**；另一策略`availability_wait`只用**最近已经确认的HEAD、下一个尚未派发高度和虚拟单调时钟**决定是否刷新。绝不能读取模拟器未来HEAD；不能把预估区块成长当成已确认可派发高度。规则：

- `checkpoint`：原策略：高度不足、每4/8个已派发区块、或4000ms HEAD TTL触发刷新。
- `availability_wait`：最后确认 HEAD 的可派发剩余高度 `<=1` 时允许提前刷新，但距离最近HEAD完成不足最短间隔时优先读取已经确认的剩余区块；如果没有可用高度，则**停派发、等待到最短刷新间隔**（1500／2500／3500ms），再刷新。HEAD真实/合成刷新正在执行时即使有可用高度也必须持续遵守4000ms TTL；HEAD已过期则不得派发BLOCK。没有额外的HEAD请求额度；当6次HEAD已耗尽但仍有已确认新鲜区块时，可以用完这些已确认高度，绝不越过确认边界。
- 所有策略共用原模拟器的三个总槽位（包括HEAD）、250ms全局请求起始间隔、32总请求、24块、6个刷新、60s虚拟实验上限、每请求独占先fsync预约及正常结束结算、乱序与父哈希相邻连续提交、失败缺口显示。新代码仍然**只调度合成离线事件，没有HTTP发送器、许可或真正网络请求**。

## 可重复离线复算

六组原始条件：HEAD每4／8块，来源串行时长倍率1.0／1.5／2.0；每组对照4个策略：原固定检查点和三种等待1500／2500／3500ms，合计24组模拟。保持相同从Mac保存的30次真实请求中提取的串行耗时分布；未来HEAD来自模拟模型，**并非独立真实网络最新HEAD**。对每组输出：请求上限和剩余额度、HEAD刷新次数、完整区块尝试和连续提交数、两个吞吐口径、耗时、最后采样HEAD与已提交高度差、已知未尝试高度、P95和缓冲峰值。**选择策略的判断条件不是HEAD请求越少越好，而是同等时长和预算下更高的连续提交吞吐，且更小的积压及不可接受的等待延迟都要权衡。**

在固定本 PR 新 SHA 的 Mac checkout 中，在仓库根目录运行（绝对离线、创建全新目录、不可复写旧证据）：

```zsh
umask 077
mkdir -m 700 "$HOME/Library/Application Support/MissionEvidence/20261022-f0-head-policy-comparison"
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_head_policy_compare.py --journal "$HOME/Library/Application Support/MissionEvidence/20261021-adaptive-sampled-head/archive/journal.json" --expected-sha256 e069b7cd38c2ad3c8a3af3a1b1c220efab1714fe4de0bb7a9e2b814a2302d61a --output-dir "$HOME/Library/Application Support/MissionEvidence/20261022-f0-head-policy-comparison"
```

只发布脱敏的合成对比表，原始Journal/响应/permit/nonce不上传。先独立审核固定新SHA，跑全部旧测试和8个新回归，再实际Mac读取私有日志。若策略改动导致更差积压、更少有效提交或恶化提前发现新币的时效性，则拒绝切换，勿因“节省HEAD”而选择。

**当前：OFFLINE_REVIEW_PENDING；F0_NOT_PASSED / PRODUCTION_NO_GO。** 本PR不创建真实并发传输器，也不授权新RPC/WS、交易、报价、签名、合并或部署。
