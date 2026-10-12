# Surf / SurfBoards Genesis NFT 链上候选、发行进度与 Kaito 估值对比（2026-10-12）

更新日期：2026-10-12。独立核查，优先官方与链上；未将历史聊天结论当作证据。区分官方确认、链上事实、推断及情景估值。

## 1. SurfBoards 官方 NFT 站最新状态

官方入口：https://nft.asksurf.ai/
Surf 官方主站：https://asksurf.ai/

- 官方 NFT 站标题 `The Genesis of Surf`，称 `SurfBoards` 是 Surf 生态的 original assets。
- 页面显示 `Trading and member claims open in ...` 的动态倒计时；2026-10-12 查看到约 2 天 13 小时。此数字会变化，不视为保证的铸造/认领时刻。
- 页上写 `Earning` 并展示 SPY、NVDA、SPCX、META、GOOGL；这是项目展示的方向，尚未找到每枚 NFT 可分到多少股票代币、分配周期、来源、领取条件或智能合约保证。不得解读成已经实现收益、持有即自动分红。
- 2026-10-12 尚未从官方公开 NFT 页面查得正式 collection contract、总供应量、真实二级成交价、最终 mint 数量和分配明细。
- Surf 官网将其链接为 `Surf’s Genesis NFT`。

证据：https://nft.asksurf.ai/ ； https://asksurf.ai/

## 2. NFT 在什么链：核查层级

**Robinhood Chain（主网 chain ID 4663）是最有证据的候选链，但没有找到能把合约唯一绑定到 Surf 官方发行的认证映射，严禁宣称已确定官方 NFT 合约。**

链上使用 Blockscout 查询 4663 链上的 `SurfBoard` 名称（2026-10-12）：

| 地址 | 链上名称 / 标准 | 首次部署时间 UTC | 持有地址数（查询时） | 核实结论 |
|---|---|---|---:|---|
| `0x6A044021bb41f4B06193cA9B42946c20918aA4f3` | SurfBoard / SURFBOARD / ERC-721 | 2026-09-30 12:46:45 | 200 | 合约真实存在、未验证源码；**未确认由官方发行** |
| `0xf5a24bd9648f180E306B57bb5B2349bb7908C28` | SurfBoard / SURFBOARD / ERC-721 | 2026-09-29 07:31:15 | 21 | 合约真实存在、未验证源码；**未确认由官方发行** |

两份合约的创建者不同，且搜索结果同时含同名 ERC-20；**仅名称相似不能排除冒牌合约或独立 collection**。任何 mint/买卖/授权都必须待 Surf 官方明确给出 CA 后验证。
- 第一份部署者：`0x110b550faDBe13ceC30f75199e1aad7c3f056A2c`，implementation `0x3cB802dCeDd7A9d016c8b0CeB2a2FFa8a3a93171`，未验证。
- 第二份部署者：`0x56F116c596C5D260cf1A43F61B504BE9CaC9Bf14`，implementation `0xeA9115A1105B9C60710fBF90028Fe1595E7CC025`，未验证。
- Robinhood Chain 官方 https://docs.robinhood.com/chain/ 确认它是 Ethereum L2、gas 为 ETH。
- 一个第三方公开 X 帖子称 Surf NFT 在 Robinhood Chain 发放：https://x.com/LensMoso/status/2107001523733668208 ，这是**第三方口径而不是 Surf 官方证据**。
- 主网 Ethereum 和 Arbitrum 的名称搜索未发现可认证的 AskSurf 官方 NFT；**缺少搜到不能证明不存在**。
- 最终判断所需证据：`nft.asksurf.ai` 的真实 mint chainId / 合约地址或 Surf 官方 X/官网明确公告，配合区块浏览器交叉校验。

## 3. Surf 公司基本面：官方披露

- 2025-12-11 Surf 正式公告融资 **USD 15 million**，Pantera Capital 领投；Coinbase Ventures、Digital Currency Group 参与。新闻稿并未给出公司估值或 NFT 的利润分配权。
- 2025-12-11 公告称自当年 7 月起有 **80,000+ users**、**1,000,000+ research reports**，属于 Surf 官方口径，不等于订阅付费用户。
- 2026-05 Surf Research 2.0 文章提及其产品覆盖 **500,000+ users**（官方口径，口径不同未独立审计）；业务包括加密数据、金融市场 AI 研究、Studio、API/MCP、企业/机构研究产品。
- 2026 年与机构、交易所存在公开整合报道：2026-07 IOSG 官方案例称研究 Agent 已接入 Surf API；2026-09-01 Bithumb 官方联名案例显示 Surf 在 Bithumb app 为 **450+ KRW 交易对**提供 AI 研究分析。Surf 官方报告提到 500M+ 数据点、2.5M 推理/校验任务、750K+ 结构化输出，这些数字是**项目方生产指标，不是审计过的公司收入**；**Bithumb 的 8M+ 注册用户和 2M 日活并非 Surf 独立用户**。
- 无审计收入/利润、付费转化率、留存和 NFT 资产负债支持数据，不能凭 $15M 融资推算 NFT 权益价值。

证据：https://asksurf.ai/blog/en/surf-raises-15m-to-scale-the-first-ai-model-purpose-built-for-digital-assets
官网：https://asksurf.ai/ ; 近期更新：https://asksurf.ai/blog

## 4. Kaito 同阶段历史演进与 SURF Genesis 峰值情景（2026-10-12 修订）

**估值框架纠错：研究 Surf pre-token / Genesis NFT 时，应将 Kaito 2024-12 发行至 2025-02 TGE 前后的价格形成过程、投机峰值与空投兑现后回撤作为主对照，不应以 2026-10 Kaito 接近 0.1 ETH 的成熟衰退阶段地板作为 Surf 的主要增长空间基准。下述数值是情景模拟，绝非 Surf 的实际报价、保底价值或预言。**

### 历史同阶段事实与强度

- **Kaito Genesis 铸造：** OpenSea 原始 Mint 页面记录 allowlist 2024-12-20、二阶段 12-22、公售 12-24 至 12-25；共 **1,500** 枚，2024-12 阶段 Mint 参考 **0.1 ETH/枚**（Mint UI 当前美元换算是随 ETH 变动的，不应将该页面 USD 值当作 2024-12 实收 USD）。
- **KAITO TGE：** XT 交易所官方公告与 The Block 2025-02-20 报道确认 KAITO 已开始领取/交易。2024-12-20 首轮 Mint 到 2025-02-20 TGE **约 62 天**，这一时间间隔是历史案例，不是对 Surf 的日历预测。
- **Kaito NFT TGE 热度峰值：** DappRadar 2025-03-06 发布的 2025-02 市场复盘记录 Genesis **7.65 ETH 地板历史高点**；此前叙述“一律不应用早期高点”不符合用户希望衡量峰值机会的投资研究目的。其他报道出现 **10.2 ETH、11.6 ETH、11.9399 ETH**，但采样、成交和时点互相冲突，尤其部分 CoinGecko/OpenSea 的 11.9399 ETH 报价源已经陈旧数月；**没有独立成交证据时不将更高报价当成可实现峰值**。
- **权益机制差异：** Kaito 持有人被纳入 2025-02 的 KAITO 空投分配，Kaito NFT 的高价反映当时空投预期、流通性和生态影响力；SURF 的 SPY/NVDA 等股票代币展示属于官方宣传，尚未验证每枚收益承诺，也尚未确认 SURF 代币 TGE。Kaito 的投机价格不能线性视为 Surf 的基本面公允价值。

历史证据：
- https://opensea.io/collection/kaito-genesis/overview?search%5BsortAscending%5D=true&search%5BsortBy%5D=UNIT_PRICE&search%5Btoggles%5D%5B0%5D=BUY_NOW&tab=items
- https://dappradar.com/blog/nft-winter-returns-market-shrinks-50-as-crypto-prices-fall
- https://xtsupport.zendesk.com/hc/en-us/articles/43707220957081-XT-Announcement-on-the-Initial-Listing-of-KAITO-KAITO
- https://www.theblock.co/news/ecosystems/2025-02-20-kaito-token-airdrop-claims-base-342379
- https://www.coingecko.com/en/nft/kaito-genesis

### Kaito 2025-02 高点对应的 NFT 集合估值压力测试

参考 **7.65 ETH × 1,500 = 11,475 ETH** 的 Kaito 峰值名义地板总额。换美元时**假设当时每 ETH = $2,700**（仅供同口径情景计算，未确认这一假定汇率就是 7.65 ETH 高点当天的同步成交汇率），得到 **约 $30,982,500** 的 Kaito 高点名义地板总价值。该口径是“全部供应乘最便宜挂牌价”，不代表可同时出售所得资金。

假设未来 SurfBoards 整体系列的**名义地板总额**仅达到该 Kaito 同阶段高点的 **10% / 25% / 50% / 100%**，按不同可能供给量折算。SurfBoards **正式总供应量仍未核实**，下表仅为假设：

| SurfBoards 假设总量 | Kaito 高点总额的 10% | 25% | 50% | 100% 极强行情 |
|---:|---:|---:|---:|---:|
| 1,000 | $3,098 | $7,746 | $15,491 | $30,983 |
| 1,500 | $2,065 | $5,164 | $10,328 | $20,655 |
| 3,000 | $1,033 | $2,582 | $5,164 | $10,328 |
| 5,000 | $620 | $1,549 | $3,098 | $6,197 |
| 10,000 | $310 | $775 | $1,549 | $3,098 |

从用户的 **$228 历史支付成本**计算：假设 **3,000 枚总量**，上述 10% / 25% / 50% / 100% 情景对应约 **4.5× / 11.3× / 22.6× / 45.3× 的毛价值/成本倍数**，**未扣 gas、交易费、版税、卖出滑点、税，也未考虑#691实际可交易前置条件**。这是反事实情景比率，不能解释成发生概率。若 Surf 根本无二级流动性或不能交付，实际可执行价值可远低于所有列值。

**研究分层**：
1. **筹备/初上市阶段：** 优先关注已确认交付、总量、官方成交和 bid 深度，市场价格尚未形成时只列成本和候选定价；Kaito 2024-12 的 0.1 ETH Mint 是历史起点。
2. **权益披露/上市后的早期发现：** 比较官方 NFT utility 和真实买盘、稀缺性，以 Kaito 从 0.1 ETH 起步并随热度上行的历史路径描述潜在重新定价，而不预设 Surf 一定复制。
3. **可能的代币/分发催化剂：** 仅在 SURF 正式确认 TGE、快照、allocation 和 claim 后才模拟空投贴现价值；Kaito 2025-02 的 7.65 ETH 是强行情**峰值压力测试**。
4. **权益兑现或失败后的回撤：** Kaito 2026-10 约 $240-$270 旧市场价属于这层的回撤尾部参照，应保留为极端下行情景，而非早期公平价锚。

**不可解答的核心缺口：** SurfBoards 真实总量、团队/保留配额、每个 #691 的兑现条款、二级出价/成交、股票代币池的法律与实际资金来源、SURF 代币存在性及分配比例。融资 $15M 与公司用户数据能支持公司基础真实性，不能推算上述未知变量。

## 5. 来源和证据限制

- Surf NFT 官网：https://nft.asksurf.ai/
- Surf 官网：https://asksurf.ai/
- Surf 官方融资公告：https://asksurf.ai/blog/en/surf-raises-15m-to-scale-the-first-ai-model-purpose-built-for-digital-assets
- Surf × Bithumb 官方案例：https://asksurf.ai/blog/en/how-surf-built-korea-s-first-ai-centric-trading-experience-with-bithumb
- Surf × IOSG 官方案例：https://asksurf.ai/blog/en/announcing-our-system-design-partnership-with-iosg-ai-native-venture-capital-connecting-western-technology-and-asian-finance
- Kaito NFT OpenSea：https://opensea.io/collection/kaito-genesis/overview
- Robinhood Chain 官方文档：https://docs.robinhood.com/chain/
- 第三方 Surf NFT 链声明：https://x.com/LensMoso/status/2107001523733668208
- Blockscout 4663 candidate A: https://robinhoodchain.blockscout.com/address/0x6A044021bb41f4B06193cA9B42946c20918aA4f3 （Blockscout 官方 Robinhood Chain 主网浏览器）
- Blockscout 4663 candidate B: https://robinhoodchain.blockscout.com/address/0xf5a24bd9648f180E306B57bb5B2349bb7908C28 （Blockscout 官方 Robinhood Chain 主网浏览器）
- Kaito collection：在 OpenSea 官方 collection 页面核价（流动性、真实成交与挂单须区分）。

以上只包含公开资料，未包括用户钱包和私密信息。

## 6. 2026-10-12 #691 SurfBoards 已购买权益与链上交付状态（用户确认修正）

资料口径：Git `crypto-300-profit-mission/portfolio/current.md` 的 2026-10-12 状态，官方 Surf 页面及上述公开证据；这是一项**研究口径纠偏**，未操作钱包、监控、交易或自动化。

- Git 原始资产提交 [14ed597c8afcd2758b2766ea00991313dd7042e2](https://github.com/lxxlx2/ChatGPT_mission_record/commit/14ed597c8afcd2758b2766ea00991313dd7042e2) 记录：**2025-08-31 13:38** 通过 **DaimoPay** 支付 **USD 228**，购买 **Surf Limited Edition NFT #691** 一枚，2026-10-05 在途/待 airdrop 到用户主钱包，预期 RB 链。**2026-10-12 用户明确确认该已购买权益就是官方新公布的 SurfBoards / The Genesis of Surf NFT**，故以 `USER_CONFIRMED` 认定为同一个项目发行权益，不再把二者作为互不相关资产假设。官方尚未核实的只是具体链上交付、CA、token ID、转让与兑付条件。另有 **Surf 28,600 Points** 独立记录，不可自动转换为 NFT 份额或已兑现现金收益。
- 新的 **SurfBoards / The Genesis of Surf** 官网明确写有 `Trading and member claims open in ...`，Surf 主站也直接链接至这个入口。这仅确认项目页面与官方关联、领取/交易倒计时宣传存在，**用户已确认 #691 与 SurfBoards 属同一发行权益，但 #691 是否就是链上 ERC-721 token ID、是否已铸造、到账以及股票代币的具体分配权仍待官方/链上核验**。
- 官方公开网页中仍缺少：SurfBoards 的 canonical chain/contract、总量、#691 的发行/交付映射、会员权益与股票代币分配的法定和合约条款、实际可执行卖出报价。前述 Robinhood Chain 两份同名合约只属于**未确认官方身份的链上候选**。在本次接手时使用 Blockscout 连接器重查遭遇 session authorization 错误，因而本条**未声称重新得到直接链上确认**。
- 2026-10-12 重新查阅 Surf 的 2025-12-11 融资公告，确认公告称募资 USD 15M、Pantera 领投、Coinbase Ventures 与 DCG 参与；2026-09-01 Bithumb 产品材料所列活跃用户和生产指标均为项目/合作方披露，**不能推导 Surf NFT 的利润分配、公司股权或保底回报**。
- Kaito Yapybaras 的 1,500 总量及约 USD 240 至 270 地板参考为历史公开页面快照；历史页面还展示真实成交和 top offer，随时会变化。对 Surf 的比较必须按同时间点的**最高真实买单、实际成交、挂牌地板**三种不同口径，不把挂牌总估值当作可清算市值。
- 研究状态：**Surf 公司产品/融资披露有据、用户的 #691 对应 SurfBoards 已获用户确认；官方链上 CA、交付和兑付条款仍未验证，故投机价值研究为 `WATCH / ONCHAIN_DELIVERY_UNRESOLVED`。用户 #691 仍是待交付历史成本权益，不能计入有可执行报价的 NFT 流动 NAV。** `ACTIVE` 仅可描述用户已有经济敞口，绝不授予任何交易或授权权限。
- 相关历史状态纠正：`research/nfts/jack-credits/jack-credits-nft-position.md` 是 2026-09-27 快照，其中写的“2 active”已经被 2026-10-10 直接链上核查的 **Credits 0 枚持有**覆盖；UNICRED #230 也已在 2026-10-10 标记 `CLOSED / NOT_OWNED`。此处不修改历史成交和当时报告。

后续研究核验顺序：**官方 SurfBoards chainId 和 contract → #691 交付凭据及链上 token ID → 总供应和领取资格 → 股票代币的每枚金额、法律属性、领取与锁定条款 → 真实订单簿和成交 → 按用户的 USD 228 成本计算可执行净回款**。不据此开启 NFT 监控任务。
