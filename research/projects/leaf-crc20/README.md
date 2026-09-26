# Bitcoin L1 CRC-20 LEAF 项目研究索引与链上验证记录

Updated: 2026-09-26
Status: ACTIVE_RESEARCH

## 项目对象

- Project / protocol: CRC-20 / leaf (🌱)
- Network: Bitcoin L1
- Official site: https://crc.garden/
- Activity: https://crc.garden/activity
- Research scope: Golden Curve allocation、CRC indexer、Taproot/CSV 锁仓、实际解锁供给、大户吸筹与卖方地址集群

## 当前研究文件

1. `leaf-crc20-golden-curve-indexer-research.md`
   - Golden Curve / quote / allocation / indexer
   - 144 / 1000 / 2100 / 6767 四档锁
   - 已解锁 CRC-20 LEAF 数量
   - 后续精确 unlock supply 所需数据

2. `leaf-crc20-whale-accumulation-cluster-analysis.md`
   - 鲸鱼地址 `bc1pa8vrkzs2wrrh6nsu862vj50vgmsajtju5yv52atlm6xdf0nmaesqrffjrs`
   - ICO-20 LEAF 买入历史
   - 107.813M 迁移交易
   - 卖方地址与资金来源集群调查

## 只读研究脚本

- `scripts/leaf-crc20-golden-curve-probe.py`
  - 枚举 crc.garden public pages、JS bundles、只读 network requests 与 endpoint candidates。
  - 不连接钱包、不签名、不 POST、不广播交易。

- `scripts/leaf-crc20-whale-audit.py`
  - 全量读取目标 whale 的 mempool.space 地址历史。
  - 复算 acquisition tx count、unique sellers、ICO-20 LEAF、BTC cost 口径。
  - 追踪 seller UTXO immediate parent 与共同 upstream funding evidence。

## 证据规则

遵循：
- `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`
- `crypto-300-profit-mission/token_trading_principles.md`
- `docs/REPOSITORY_STRUCTURE.md`

链上原始交易优先于社交媒体描述。任何尚未完成全量复算的统计值标记为 UNRESOLVED，不用二手帖子覆盖链上结果。

## 当前状态

- Taproot/CSV 锁仓机制：高置信度链上验证完成。
- 144 block：实际 spend witness 已验证。
- 1000 block：实际 spend witness 已验证。
- 2100 block：Taproot commitment 已验证，尚未进入首批成熟期。
- 6767 block：Taproot commitment 已验证，289 个样本全部成功分类。
- Golden Curve 精确分配函数：ACTIVE_RESEARCH。
- 鲸鱼 149 笔 / 120 卖方 / 107.813M old ICO-20 LEAF：全量复算 CONFIRMED；0.605 BTC cost 口径仍为 UNRESOLVED。
- 鲸鱼卖方共同资金源 / 项目方关联：当前一跳 funding graph 未发现 multi-seller cluster、common parent 或 common upstream，分类为 INFERRED independent whale accumulation；更深层 ancestry 仍可继续验证。

本目录只保存项目研究。若未来需要加入 Mission 自动监控，应另行写入已有 operational watchlist / position 体系并保持现有自动任务路径兼容。
