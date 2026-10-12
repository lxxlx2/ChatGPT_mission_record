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

## 4. Kaito 横向对比与 NFT 情景估值

- Kaito 披露累计融资约 **USD 10.8M**，早期投资人包括 Dragonfly、Sequoia China、Jane Street 等。融资规模和时间不同，**不能据此认定 Surf 的 NFT 必然更贵**。
- Kaito Yapybaras Genesis NFT：总量 **1,500**，2026-10 公开市场地板参考约 **0.10 ETH（$240–270）**；不同时间点挂单与已成交价格应独立记录，历史数 ETH 甚至更高的峰值不应作为当前合理地板。
- 用 $240 × 1,500 ≈ **$360,000 地板隐含总价值**作最简单可比锚，**这只是挂单市值估算，并非实际清算价值**。
- Surf 的总量 **未确认**。因此不能给单一的公平价格。下表只模拟在三个 NFT 总市值情景下各 supply 对应的均价（USD/NFT），不是 Surf 报价：

| Surf NFT 总供应 | $180K 情景 | $360K（近似 Kaito 当前地板总价值） | $900K 强权益情景 |
|---:|---:|---:|---:|
| 1,000 | $180 | $360 | $900 |
| 1,500 | $120 | $240 | $600 |
| 3,000 | $60 | $120 | $300 |
| 5,000 | $36 | $72 | $180 |
| 10,000 | $18 | $36 | $90 |

**估值判断**：如无可核实、可持续的真实股票代币收益和用户权益，不能用未来收入定价，应倾向 NFT 社区/品牌权益折价；若未来披露可兑付 stock token 分配，可对单枚 NFT 计算：已承诺可领取价值 + 风险折现的未来预计分配 + 会员权益价值 + 投机溢价，避免把未发生的收益和企业估值混同。避免用早期 Kaito NFT 巅峰价格锚定 Surf。

需追踪但**不主动新增监控**：官方 chain ID + CA；最终 NFT supply；claims/交易开放时刻；Waves 与年度会员数量与分配规则；SPY/NVDA 等实际单枚额度、领取路径、可转让性；OpenSea 实际成交/最高有效 bid；Surf 公司真实用户与收入指标。

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