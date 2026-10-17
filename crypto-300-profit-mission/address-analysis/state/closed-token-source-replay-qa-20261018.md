# 已保存单币证据交叉复算及离线测试记录

日期：2026-10-18
范围：新独立地址分析模块，原始源 Blob `954f3aba66be21911dd627fa40dd3dd0a9fd1d26`

## 已完成：标准化复算工具

- 新增 `tools/closed_token_index.py`，源代码 Git blob `e2366dccf09561849a7b72d8a8ce08c2ddad1caa`；测试 Git blob `b8832281176fbfce486cc96726a614253a7202fb`。
- 隔离 Linux/Python 3.13 工作区中按照最终 `tools/`、`tests/` 目录结构，运行 `python -m unittest discover -s tests -p test_closed_token_index.py -v`，5个测试全部通过，退出码0。测试含**人工构造**三笔亏损样例、错误成本、钱包地址与源清单不匹配、未闭合库存，以及非法数值的拒绝行为。测试中制造的亏损钱包不代表链上事实。
- 复算器要求严格对应冻结449地址源中的源行和钱包地址；sauce 使用整数 Wei 检查每个买入负现金流、总成本、实际出售价款、净收益以及前后持仓为零；RTX 旧来源为浮点，复算允许明确的微小容差，**不声称 RTX 精确到 Wei**。
- 本轮还通过 GitHub API 读取 RTX/sauce 原始证据并在独立 JavaScript 逻辑中逐项重算，所得三个原单币记录均匹配；参见 [只读已保存来源算术核对 JSON](../evidence/closed-token-replay-source-check-20261018.json)。

## 尚未通过或未做

- 未将 CLI 与 Alchemy 主网 RPC 实际连接来独立重取全部交易收据。
- 未在用户 Mac 环境实测。
- 未证明所有钱包历史买卖、桥接、矿池、铸造、代币税、手续费和转入库存成本均完整。
- 未得到独立外部 AI 审核或合并权限。**不存在完整已核实亏损代币闭环**；不能将 `negative_positions=0` 转化为「钱包亏损为0」。
- 目前该 CLI 是保存的特定三笔轮次的读入适配器，未来需要替换为通用的多 Token/多链交易账本，不能将该原型描述为生产盈利模型。

## 手动使用示例

在新模块目录下：

```zsh
python3 -m unittest discover -s tests -p test_closed_token_index.py -v
python3 tools/closed_token_index.py --manifest sources/oooooyoung-evm-449-source-snapshot.json --rtx evidence/batch-001-row-016-rtx5090-roundtrip.json --sauce evidence/batch-001-rows-002-004-sauce-roundtrips.json
```

以上命令是读取 Git 中的静态只读证据。原始 Python CLI 对实际 Git 证据的运行在本轮**尚未确认成功**，本报告不虚构该运行结果。
