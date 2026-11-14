# 地址分析 / 只读 CLI unittest 导入失败复现与修复（2026-10-18）

## 被检验版本与环境

- 原 Git 分支 HEAD：`bf86cb8a6df1ba2d07ce4ec8117c99952beb797f`。
- Python 程序原 blob：`4a1191c604c2408f1aa295ce55fa0935b7291c5e`；隔离环境的 `git hash-object` 完全一致。
- 测试文件原 blob：`628896df6c4b3640243167c57365edcc661e5310`；隔离环境的 `git hash-object` 完全一致。
- 执行：Linux Python 3.13，工作目录为模块根，`python3 -m unittest discover -s tests -v`。网络隔离，本轮未进行 Mac/真实 RPC CLI E2E 验收。

## 原版真实失败

执行退出码 **1**，实际 Python 错误：

```text
File ".../tests/test_address_analysis.py", line 6, in <module>
  from address_analysis import assert_source, nonce_pair, screen, replay_closed_token
ModuleNotFoundError: No module named 'address_analysis'

Ran 1 test in 0.000s
FAILED (errors=1)
```

原脚本在 `tools/address_analysis.py`，而测试旧代码只把**模块根**加到 `sys.path`。此前 README 所写的「6/6 passed」在原始 SHA 下不可重现，已纠正。

## 唯一修复与复测

仅替换 tests 内一行：

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
```

修复后测试 Git blob：`d6b7b8f912846f24d1a88e4168fda7a204553d86`，GitHub 提交时须与此精确一致。程序主体 SHA **不变**。相同隔离环境运行结果：

```text
test_bad_block_hash_rejected ... ok
test_census_partial_never_zero_on_failure ... ok
test_known_sauce_values ... ok
test_loss_no_cherrypicking ... ok
test_nonce_exact_and_regression ... ok
test_source_pin_and_order ... ok

Ran 6 tests in 0.005s
OK
```

修复版真实退出码 **0**。覆盖纯离线、合成 RPC 与历史已存 sauce wei 数字重放；它只能证明导入和现有单元测试通过，**未证明**真实 RPC CLI 端到端运行、收益模型准确、全部交易成本/亏损完整、Mac 实测或生产可用性。
