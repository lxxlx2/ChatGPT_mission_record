# Frank：57条分类缺口与完整历史读取提速（2026-11-15）

产品源码 **ee81a0f44c27eb539c3c874963d311d4e4d5761f**，parent **2471467e53cb772202abcc7415b17c1f33defd59**，PR base **d43878828c86eacee5be9df8a17d16fc63a74bb6**。原PR252继续；复核器和Dashboard局部执行器固定于原PR242 **a594a05c3f873273512fc88c1d4cc573a8f73264**。用户免费、不截断、不加无必要限制、免review、本地直部署与Chrome授权持续；不合并、通知、签名、交易，不启动Loop/新监控或恢复盈利研究。

**当前阶段：分类修复、固定版本回归、本地安装、一次完整实源查询、47811条禁网复放与真实Chrome验收均完成。新查询DONE/error=null，2787.744987秒（46分28秒）；原57中50条分类有据、7条仍UNKNOWN，全部57消歧与完整尽调仍PARTIAL。新查询大量命中既有缓存，不能当作整次冷查询速度证明。** [机器回执](./evidence/frank-gaps-latency-20261115.json)保留分母、实际参数、哈希和阶段状态；新旧原件分列，不改写旧报告。

## 原57条逐项处理

固定旧报告SHA256 1a94b9d6f31cd48498000a0ac178aa0ec142b36abd329b6982679e3ce81cbb79、检查点SHA256 17a9d275966a2ad9e0143d93d42d648926a7cff2e2875d77797eada681f00daf。发布后的脚本重新校验61761条完整哈希链，取得57/57个Owner／签名原始上下文，禁网处理后原件不变：

| 结果 | 数量 | 证据及边界 |
|---|---:|---|
| 被动转入 | 29 | Owner不在消息键中，真实Token Program转入指令、目标Mint、精度和Owner账户余额变化守恒；不伪造Owner原生SOL余额，也不提升为买入或签名授权 |
| 目标Mint的两代币交换 | 21 | 钱包签名、已核实市场指令上下文、两资产相反净流量及原始转账守恒；所有入账须绑定同一市场上下文，额外出账仍保留。非标准币对仅展示账户净交换量，不折成USD或当作精确最终成本 |
| 所得未能在净余额中确定 | 4 | 目标币流出、路线所得随后转交，缺少可用于确定经济对价的保留余额；继续UNKNOWN |
| 未能绑定同一市场路径 | 2 | 不能把不同外层市场指令的流量强行配成单笔报价；继续UNKNOWN |
| 多资产变化 | 1 | 仍有多个可能目标/报价腿；继续UNKNOWN |

共50条得到有证据支持的新解释，7条保持未知；这不是把未知强行归零。默认共享Frank分类器、parser和策略文件字节未改；仅源驱动CA账户历史使用新解释。初始两个正向反例在旧SHA失败，负向反例保持保守；固定新SHA包括授权、金额、Mint/Owner冲突、伪程序、失败交易、无关转入、跨市场路径及回归检查。原298来自另一采集时点，不作为本轮57的修复分母。

已发布的可复核命令（私有路径以变量代称）：

```sh
python -B crypto-300-profit-mission/meme/evidence/frank_history_gap_capture_audit_20261115.py --agent "$FRANK_AGENT" --expected-sha ee81a0f44c27eb539c3c874963d311d4e4d5761f --capture "$FRANK_CAPTURE" --summary "$FRANK_SUMMARY"
```

## 不减少数据的读取优化

旧9h11m查询的实际剖析：48392次资金交易读取耗时27340.34秒，占82.69%；6073次资金签名页耗时2968.95秒，占8.98%。重复的完整交易请求仅10次、合计0.0376秒（已缓存），不是主要瓶颈；读取之间工作合计423.49秒，仅1.28%，因此没有为了速度移除durable reservation、fsync/检查点校验或错误恢复。

新路径只安排当前资金页的交易，按4项JSON-RPC惰性批量读取；响应ID集合、唯一性及类型严格校验，乱序恢复原签名顺序，仍经原逐笔call/checkpoint路径分别落原始响应。无效/部分失败/null回原逐笔读取，不变成空页；崩溃后的已落盘前缀只复放，丢失的易失预取后缀重新读取，旧HTTP预约保留。没有新增并发工作进程、备用任务或定时器。

源驱动资金签名请求按每页1000条读取，继续到来源结束。固定旧原件的16个资金窗口重新分组后，6073个请求可合成76个请求；48392条签名、顺序、全部原始元数据及最后空页均逐项相同，来源调用0。另有实际既有私有RPC的1000签名页200对照：返回1000，锚定最新slot一致。每页请求容量不是总历史截断。

同一既有私有RPC、同4笔完整交易实测：串行1.9763秒/4wire，批量0.58747秒/1wire，完整返回值相同；样本比值3.364。测试顺序为先串行后批量，未隔离提供方内部缓存效应，不是完整冷CA时延证明。批量方法的CU仍按内部方法次数计算，不能把HTTP减少写成CU同倍率减少。[Alchemy批量规范](https://www.alchemy.com/docs/reference/batch-requests)、[方法CU及batch计费单位](https://www.alchemy.com/docs/reference/compute-unit-costs)仅作技术依据；本轮没有付费升级、新key或新提供方。

本轮额外来源诊断共7个HTTP wire：12个getTransaction子请求和1个getSignaturesForAddress请求，与正式新CA查询分列。旧正式采集、旧18次诊断继续保留各自时点和范围，不合并成缺失的历史总数。

## 固定版本测试、本机安装与已完成验收

固定ee81实际1070 Python通过，7.67秒，socket事件0；212 Node通过，无失败/跳过；JS语法通过。完整pytest实际参数和日志哈希见机器回执，实际Node命令：

```sh
node --test tests/test_frank_ca_get_resume.mjs tests/test_frank_ca_report_render.mjs tests/test_frank_d2_ingress_ui.mjs tests/test_frank_ca_rpc_budget_ui.mjs
node --check mission_agent/mission_control/static/app.js
```

批量恢复测试包含乱序ID、重复/错误ID、部分错误/null、4条独立哈希链记录、崩溃后只重读易失后缀、错误读取序列/预约失败不得发请求，以及1500条签名1000/500/空页完整读取。本SHA PR workflow列表为空，不用CI替代本机或实源。

511个tracked agent文件真实干净detached版本已安装原8766，Dashboard PID53830。更新前保留507旧源文件、90报告、3 SQLite一致备份和14保护哈希；旧新实际Handler无监听各11精确任务/1绑定补证、HTML/JS/CSS/D1/D2通过，切换后再次HTTP验证。Scanner2268/1f2c6afc28b9988eaacdc896562ff9a71b78f801仍LIVE、无漂移/连续错误0，Loop未加载，回滚未实操。

Chrome对既有CA手动提交一次新查询，已DONE/error=null。实际总耗时2787.744987秒（46分28秒），逻辑读取47811，主RPC预约wire 3609、第二提供方wire 3360、缓存命中40860；wire/seconds/deadline均无总配额。新报告33593账户/7914非零Owner，主来源地址集合及Mint共33594项在第二提供方数值全部一致；仍是NEAR_TIME_ALL_MATCH，不是独立枚举或原子同slot快照。19个所选目标币账户窗口及15个建仓前资金窗口全部PROVIDER_EMPTY_PAGE，page_limit均null；目标币历史404条/63页，资金历史40460条/67页。首买状态13账户历史完整、3当前账户完整但未见市场买入、2有界、1未知、1协议池N/A。来源结束不证明闭户全集或钱包终身首买。

新报告29+21条补充分类的Owner/签名集合与原57中50条已解释集合完全相同。新10条UNKNOWN由原7条全部保留，加本次新进入Top20的同一Owner的3条交换证据不足组成；不是原57复发或将跨时点缺口相减。新Top20有19 Owner与旧相同，1进1出：退出者原资金窗口7831条不在新Top20；另1个Owner因正确识别更早买入，资金初始before前移，384条变283条。两者合计解释旧48392到新40460的7932条差额；这属于所选对象/首买边界改变，不能写成相同输入下靠提速少读了7932条。固定旧窗口6073→76的无损页合并证据单独保留。

此次完整查询的资金交易均复用了既有缓存，实际HTTP批量计数为0，不能据此宣称批量路径已在该次全程实际发出。当前4笔实源微基准与崩溃/检查点回归单独证明批量能力。46分28秒相对旧9h11m是观测耗时差，混有缓存、所选Owner及首买窗口变化，**未证明同输入冷查询11.86倍提速**。原有每请求超时、服务限流和已实测免费第二提供方每请求10地址容量继续有效，不是总数据截断。

新报告SHA256 **3bbf693879c7f98bbd856cc0fb0d3197b72e49c8f3cf4444a7fe7c5d2362588a**，检查点1013469184字节/SHA256 **a04b5405ebf2a089b8f812b25c2bf1507ed721a14915253995c528fad85439fb**。DONE绑定及精确job GET值与盘上报告一致；HTTP序列化字节不相同，不把值相同写成原件字节相同。工作线程关闭缓存后才复制检查点，完整47811行哈希链及双来源原响应重算通过，未冻结独立对照结论，业务差异0/socket0/原件哈希不变；仅允许既已发布复放器中列明的本地读取时间、间隔和端点/调用计数口径字段归一化。265边（243直接原始指令、22多证据派生）、87归集及另13资金来源指令/成功状态/签名/金额/时间核对通过；不把关系写成共同控制。新10未知亦逐条从原始捕获重新核对。

可复核命令（私有路径用变量代称，脚本均来自上述固定tools SHA）：

```sh
python -B crypto-300-profit-mission/meme/evidence/frank_source_end_capture_audit_20261114.py --agent "$FRANK_AGENT" --expected-sha ee81a0f44c27eb539c3c874963d311d4e4d5761f --capture "$FRANK_NEW_CAPTURE" --summary "$FRANK_REPLAY_SUMMARY"
python -B crypto-300-profit-mission/meme/evidence/frank_captured_edges_audit_20261113.py --agent "$FRANK_AGENT" --expected-sha ee81a0f44c27eb539c3c874963d311d4e4d5761f --capture "$FRANK_NEW_CAPTURE" --output "$FRANK_EDGES_SUMMARY"
python -B crypto-300-profit-mission/meme/evidence/frank_history_gap_capture_audit_20261115.py --agent "$FRANK_AGENT" --expected-sha ee81a0f44c27eb539c3c874963d311d4e4d5761f --capture "$FRANK_NEW_CAPTURE" --summary "$FRANK_GAPS_SUMMARY"
```

Chrome实际打开原8766并GET最新保存报告，确认29被动转入/21币对交换、10未知、40860缓存、3609主wire、34来源结束窗口、非标准报价警示及叙事/认领分列均可见，页面留开。最终读取未再提交查询。应用错误未见；浏览器钱包扩展有与本应用无关的注入错误，未接钱包或签名。截图SHA256 5b6d11c1146e3cada1c91faf1984c6bb3efeb652c8fb7ef9b62c05c9e9563bd1；原件留私有证据目录。安装后再次逐Git blob核对511文件/干净ee81/served JS相符；Dashboard仍同一PID53830、唯一监听原127.0.0.1:8766。Scanner2268/1f2c6af仍LIVE/0漂移/连续错误0；Loop launchctl只读查验未加载。

查询后旧90文件88字节不变，另2为授权查询正常更新的当前CA latest/assessment-history；无文件缺失，旧精确job原件及既有叙事补证不变。13个非缓存保护项全部不变，仅既有RPC缓存按预期变化。实际配置中的私有RPC URL和不透明key片段均未出现在新报告；公开回执只保留案例哈希和安全汇总。原件、完整URL与私有路径均留Git外。

本轮结论：固定源码/离线回归/已选窗口来源结束/本机Chrome **PASS**；原57全部消歧、完整冷查询耗时与全部尽调 **PARTIAL/未证明**。剩余7不能由重复读取同一余额结果确定经济含义，需要可验证的路径与对价归属证据；新Owner3条同样保留未知。闭户全集、完整身份、受控独立快照及官方认领边界没有被本轮测试自动证明。当前没有权限、付费或review阻断；INVEST_NO_GO / TRADE_NO_GO保持。
