# Frank 主线本地验收

现有 [PR #253](https://github.com/lxxlx2/ChatGPT_mission_record/pull/253) 对应 `codex/frank-functional-completion-20261115`。安装源码为 `2c84dbb16028d1a9259a3155fdb89ebaa6b85546`。父提交为 `a84a2cf509820cb016afaebd2932e95168238281`。W10–W14 本地功能和隔离验收通过。W09–W14 的真实来源或真实运行覆盖另见下表。生产和交易保持 **NO_GO**。

| 工作包 | 结果依据 | 真实证据范围 |
| --- | --- | --- |
| W10 历史、资金和关系 | 重要 Owner 的多个小账户不再因单账户未进入 Top20 而漏查。使用链上 slot 排序首买，保留同槽顺序未知。对原币资金按资产与来源记录，同一个资金机制只算一类控制证据。 | 三份不同 Mint 的真实归档都有既有交易和关系记录。其中一份有历史与控制归因完整性条目，状态为部分覆盖。关闭账户全集和终身首买仍未证明。 |
| W11 可信叙事 | 合并已有来源的页面、链上元数据和帖子线索。原帖 ID、作者和来源响应摘要须匹配。引用和回复分列，遍历去重。叙事内容、人物互动、确切 CA 认领和最早可追溯出处分别保留。 | 三份归档中一份有可展示叙事和帖子链。不同合成 Mint 覆盖发帖者明示认领、别名、错 CA、只有链接及来源拒绝。真实三类典型叙事与全网起源未验收。 |
| W12 两源和性能 | 独立 Mint 枚举与逐地址数值复核分列。相同主源主机不能充作第二源。实际同槽集合冲突时撤下精确排名。队列、恢复和失败测试保留已提交结果。 | 一份历史归档有逐地址对照。当前缺少真实独立集合、原始池和持有人同槽对账。合成冷暖结果仅说明运输层减少往返，真实完整查询耗时仍待测量。 |
| W13 通知 | 本地审计可查原信号、策略、渠道、outbox、回执证明和分段延迟。归档只写独立注解库。合成 Gmail 结果不明时重读 Sent，原信号和出站台账核对后保持原状。Option3 用独立策略摘要、通知身份和持久队列完成合成演练。 | 本地回执日志证据单列。Gmail Sent 回执可证明发送台账核对，收件时间证据仍缺。Option3 真实发送未接入，本轮没有新的投递或策略签发。 |
| W14 集成升级 | 固定 SHA 完成 Mac 回归、Chrome 预览、旧版回滚与读取、同端口安装及安装后验证。 | 本轮未发真实 CA 作业。真实 5 类 CA、代表协议原件和跨源性能仍为 PARTIAL。 |

## Mac 测试

在固定源码的 detached checkout 进入 `crypto-300-profit-mission/local-agent`。使用已安装的 pytest 环境。下面的 Python 运行器拒绝网络连接及新端口绑定。已有随机端口 HTTP 压测、旧部署 HTTP 测试和 OAuth 本机回调测试另列。Chrome 预览和安装使用固定端口 8766。

```sh
PYTHONDONTWRITEBYTECODE=1 python - -q -p no:cacheprovider --tb=short tests \
  --ignore=tests/test_dashboard_http_burst.py \
  --ignore=tests/research/test_frank_dashboard_deploy.py \
  --deselect=tests/research/test_reauthorize_existing_gmail.py::SafeReauthTests::test_browser_callback_uses_loopback_server <<'PY'
import sys
blocked = []
def guard(event, args):
    if event in {'socket.bind','socket.connect','socket.getaddrinfo','socket.gethostbyname','socket.sendto'}:
        blocked.append(event)
        raise AssertionError('isolated test attempted network or port bind')
sys.addaudithook(guard)
import pytest
result = pytest.main(sys.argv[1:])
print('Guarded network/bind events:', len(blocked))
raise SystemExit(result or bool(blocked))
PY

rg --files tests -g 'test_*.mjs' -g 'test_*.cjs' \
  | rg -v 'test_frank_ca(_checkpoint)?_browser\.mjs$' \
  | sort | xargs node --test --test-reporter=tap
```

- 合成交易 5、29、109 笔分别验证冷缓存的 2、8、28 次传输，以及重开持久缓存后的零传输。逐笔结果与原单请求读取一致。1500 条分页和空页结束另有回归。
- 通知隔离正例包括本机和 Gmail 两类记录。模拟送达结果未知时，重启后只查相同 ID 的回执，无再次发送。错误回执继续保持未知。过期和策略更换不会恢复待发送条目。原风险库的摘要未变化。
- 两个合成 CA 在 Chrome 使用同一历史报告入口分别验证认领与仅链接场景。额外重要 Owner 的同槽首买歧义可见，独立同槽冲突下全局 Top10 未确认。五条合成通知分别显示已绑定回执、未核实或无回执。在隔离库归档一条未知结果后重载，归档标记与未知状态都保留。
- 固定安装源码的 Mac detached checkout 通过 **2,804 项 Python**及 **270 项 Node**。Python 审计事件为 0。Python 输出 14 个历史回退测试的 fork 弃用警告。两份需要随机端口的自动浏览器脚本与上述 Python 排除项未运行，另有原端口的人工 Chrome 验收。GitHub 查询没有返回该安装源码 SHA 的 PR 工作流记录。

## 部署与余项

653 个安装跟踪文件逐一核对 Git blob。恢复旧版后验证原 8766 和成本账本，再升级到固定候选。Scanner PID 及受保护控制文件摘要一致。Chrome 安装后读到真实本机通知台账的第一页 20 条记录，并将标签保留。安装与 Chrome 原始记录保存在本机。没有实际通知、RPC、CA POST、签名、交易或生产账本写入。W09 已观察候选核对通过，完整真实池与身份矩阵仍开放。 [W09 证据](W09_HOLDER_POOL_ACCEPTANCE_20261119.md)
