# Monster Stage32：原V4每1分钟 vs 每3分钟扫描，六个新日期、全758币历史对照

本轮研究日期：2026-10-12。原PR #30研究分支。本文件记录已冻结的设计和真实执行状态，并非结果报告；历史价格全部回放完成前不得宣称1分钟模式有盈利能力。

## 研究依据与真实目标

Stage30在六个此前未使用的日期得到33个随后达到历史06:00 UTC基准价2×的币次，原3分钟V4提前WATCH30个，但30/300U资金严格回放时300U乐观20bps滑点情景仍净亏79.489406U。Stage31在原历史分钟SHA上复现VTHO爆发过快导致晚3分钟报警、PENGU/CETUS平缓趋势未达到短线动量阈值；两个5×赢家ALPACA和SPK确实已有提前WATCH。

这一轮只改变观察频率，比较真正V4原函数每1分钟运行和原生产每3分钟运行；不修改3m+5%、15m+8%、60m+15%、过去24h成交额≥10万U、6小时冷却、5分钟D1评价、WATCH+3分钟入场与固定24小时退出等冻结条件。

## 未读取新行情前冻结的数据与闸门

[Stage32事前冻结的日历、758币集合、所有真实源码SHA和30/300U决策门槛](evidence/monster_stage32_6newdate_1m_vs3m_full758_prereg_20261012.json)，注册提交 ea680fb778cd5f625674f1725a31d5caedd78252。

固定六个UTC 06:00开始的168h自然日：2025-03-19、2025-06-19、2025-09-19、2025-12-19、2026-01-19、2026-03-19。此前Stage26和Stage30未使用这些日历日；不改变原758个曾现存及归档Binance Spot USDT交易对名单。历史实时交易许可未认证，历史币种集合仍有幸存者偏差，两个非ASCII归档币未覆盖。

每个币日期共同采用一次Binance官方发行方CHECKSUM SHA认证的月度1h历史价真实GT、10个日度1m档案216h的同一原始分钟条目，再独立以原版3m3360轮（从06:03开始）和候选1m10080轮（从06:01开始）运行真实原V4 observe_snapshot/process_queue。单币每臂SQLite贯穿七天，不日切重置；真实1m HIGH只在事后打2×/5×/10×标签，绝不输入原D0决策。来源缺档删失，网络/校验错误失败，不得冒充普通无信号。

新方案必须报告2×/5×首次1m HIGH越线之前的WATCH、近越线可用WATCH领先分钟、额外通知和D1负载、24h真实分钟退出的删失比率、每边10bps手续费与20/100bps滑点。旧原Stage27资金账本按全部UTC时间顺序模拟30U单仓和300U十仓，每笔固定30U、24h锁定、不透支现金，退出未知本金100%回收的乐观情景和0%回收压力情景均报告。300U两档成本都不正收益或原本2×漏报无改善则不得放行，更不能声称历史1m HIGH等于可成交。

## 已实际完成的研发与测试、仍未完成的验证

[Stage32真实双频V4回放器](../local-agent/scripts/monster_v4_stage32_paired_1m_vs3m.py)、[V4一分/三分真实源码与来源故障测试](../local-agent/tests/test_monster_v4_stage32_paired_1m_vs3m.py)、[六日期36原始SHA聚合与现金模拟](../local-agent/scripts/monster_v4_stage32_aggregate.py)、[资金及完整性测试](../local-agent/tests/test_monster_v4_stage32_aggregate.py)、[原始36份官方来源身份确认脚本](../local-agent/scripts/monster_v4_stage32_make_real_source_proof.py)均已提交。

[真实36片新市场回放CI #38158924838](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38158924838)在启动后仍处于运行/等待分片。首次CI #38158711203发现单测以为替换了Python函数却没替换被默认参数预绑定的来源函数，导致三个测试检查失败，已用明确传入假的hourly_get修复，未修改模型规则。[单测与源验证准备CI #38159126425](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38159126425)已经真实通过，但原36行情产物未集齐，所以其全市场验收分支明确跳过，不可写成行情结果通过。

[Stage32a五个已知币事后配对因果诊断代码](../local-agent/scripts/monster_v4_stage32a_known5_1m_cadence_diagnosis.py)与[真实CI #38159292959](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38159292959)仅用于复核PENGU、CETUS、VTHO、ALPACA、SPK；不得混入六个新日期作为所谓独立策略验证。

真实来源36/36分片完成、逐ZIP/解压JSON SHA重新审计、严格30/300U比较及确切盈利门槛，仍需独立实测结果。其他AI独立Review依旧NOT_DONE。历史真实L2盘口、CEX实际成交、全市场Spot/Futures共享D1队列和用户Mac网络邮箱真实运行均NOT_DONE。原V4生产、Frank与真实Gmail均未触碰；Monster自动交易和部署持续NO_GO，PR #30仍保留Draft。不修改用户现有对话标题。
