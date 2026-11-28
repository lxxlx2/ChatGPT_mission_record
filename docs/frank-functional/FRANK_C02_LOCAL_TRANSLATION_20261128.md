# C02 浏览器本机翻译

- 已就绪的 Chrome 模型保留自动翻译。缺少检测器或语言包时，在 CA 报告选择原文语言并点「在本机翻译」。首次使用可能需要下载 Chrome 语言包，页面显示准备、下载、完成或失败。没有原生接口时不走外部翻译。
- 译文标注为机器翻译，原文入口和 CA 认领证据保持不变。更换报告后不会写入旧译文或旧进度。
- 隔离 Mac Chrome 实测：原生英译中把公开句子 “This public park opens at nine in the morning.” 译成“这个公园在早上九点开放。”，保留来源链接。另以替身模型核实点击激活和下载状态。只验收这条短句，不代表真实 CA 多语种长文摘要已经验收。
- 固定暂存代码的统一入口通过 577 项 Python、227 项 Node；扩展 Node 280 项通过。原生 Chrome 为独立人工验收，未重跑统一入口的全部浏览器阶段。未切换生产，发布仍为 NO_GO。

[Chrome Translator API](https://developer.chrome.com/docs/ai/translator-api)
