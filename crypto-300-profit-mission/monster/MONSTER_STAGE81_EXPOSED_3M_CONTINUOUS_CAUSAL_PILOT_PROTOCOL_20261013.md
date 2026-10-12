# Monster Stage81：真实官方分钟数据连续3m回放工程试点预注册

日期：2026-10-13 Asia/Bangkok。范围：仅原 Monster PR #30； Stage79双入口策略参数已在Stage80首次读取事件样本前冻结，不改阈值，不扩研究场所。

## 正式问题

Stage80基于Stage48/64的原WATCH事件时刻获得成功运行的已曝光事件级事实，但它没有观察WATCH之间每一轮3分钟。因此不能把它当真正新D1回测。Stage81先验证**同一 Stage80 核心**与旧 Stage38官方USDM 1m ZIP发布者SHA校验加载器的可重复集成、Stage64已保存的真实信号当时特征一致性与原冻结时钟，随后才能扩大到完整普通分母。

## 价格盲选择协议，先冻结才读取新原始官方分钟ZIP

唯一候选库存是Stage64全519首次D0行（blob `8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a`）；六个冻结市场窗口：2025-01-30、2025-06-02、2025-08-01、2025-10-02、2026-06-21、2026-07-28。每个市场日对所有行按 `SHA256("MONSTER_STAGE81_EXPOSED_ENGINEERING_PILOT_V1|" + date + "|" + symbol)` 升序，选**前2币日期**，合计12个。入选**绝不使用**未来2×标签、当日收益、D1是否通过、币名名气或已有赢家名单。固定选择即使币种取数失败，也必须保留CENSORED，不偷偷换样本。

对每个币：复用已核对的Stage38 `minute_source(symbol,date)`，访问该7日原窗口配套的9天官方 Binance USD-M 每日1m ZIP及发布者 .CHECKSUM；核实完整11520分钟、上游9个官方SHA、首次D0观察分钟数据与Stage64原真实历史特征的报价、笔数、60m收益和归一成交额**逐项同刻吻合**。整个过程**不需要**也不访问未来GT标签即可作出模型判断。

在首次D0之后从第一次tick开始，每3分钟按同一Stage80核心重新评价，直到首次D1达标或48小时/原七日窗口结束。原始首次D0毫秒时刻绝不重写，不能用新增分母优化Stage79参数。源缺失按`SOURCE_CENSORED_UNKNOWN`保留身份并明确记录，不删除。

本试点**仅12个随机化币日期与历史已曝光源**，因此尽管包含全程3m真实行情，也不是全市场，不足以评G1–G4，更不代表样本外预测；此阶段仅对依赖接口、完整分钟、无前视、定时重评和结果快照验收。之后若试点成功，再将相同实现用于完整跨币真实历史回放与真正未来验证。

## 验收与权限

- 12个固定身份（含来源缺失）全部保留、无标签选择、源已知差异必须fail closed、真正第一个3m时间与真实首次 D0 一致。
- 实际归档9天源必须逐ZIP官方checksum验证，Stage64首D0当时已经闭合61m特征一致；未来K线改动不改变以前结果，升级至多一次，正常回撤不会删除D0。
- 审查依赖源码与 source SHA，无其他AI审查前只是 `ENGINEERING_EXPLORATORY`。
- `D0_UNCHANGED`, `MODEL_OOS=NOT_DONE`, `NET_PROFIT=UNKNOWN`, `MONSTER_DEPLOY=NO_GO`, `GMAIL=OFF`, `AUTOTRADE=NO_GO`, `FRANK=UNCHANGED`。
