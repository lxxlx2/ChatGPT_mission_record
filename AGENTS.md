# Repository Development Instructions (AGENTS.md)

本文件适用于整个 `lxxlx2/ChatGPT_mission_record` 仓库及所有子目录中的开发、审核、Mac 执行交接（包括 Frank、Monster、地址分析和监控项目）。执行前阅读本文件及 [docs/DEVELOPMENT_RULES.md](docs/DEVELOPMENT_RULES.md)。它们是正式开发流程规范，不是 Issue/PR 评论或临时聊天约定。

## 强制规则：GitHub-first，禁止反复交付 ZIP

- **GitHub 是开发产物及交接的唯一常规入口。** 开发或修复源代码、测试、工作流、门禁文档时，直接提交到相应 GitHub 分支／现有 PR；适合主分支的仓库规则则提交到主分支。不得只放在聊天、Issue 评论、临时文件、sandbox 或 Mac 本地目录而当作已经交付。
- **默认禁止向用户发送 ZIP/压缩包，让用户下载、解压，再手工交给 Mac Codex 或另一 AI。** 不要因工具可生成 ZIP 就生成它。用户明确要求离线包，或 GitHub 客观不可用且用户明确同意例外时，才可提供包；例外不改变 GitHub 作为长期规范和源码的权威。
- 正常交付给用户的是 **GitHub PR/commit URL、固定完整 SHA、准确基线、测试结果及可直接复制到 Mac Codex 的提示词／zsh 兼容命令**。Mac 代理直接从 GitHub 读取指定固定 SHA，在独立 detached checkout 中验证。用户不承担下载、解压、上传和文件转运。
- 在现有 PR 上修复既有问题；只有确有独立工程范围时才创建最小 Draft PR。**不得为交接压缩包、重复测试或更新记录而机械地增加 PR。**
- 任何固定 SHA 的 `APPROVE` 只适用于该提交；新 HEAD 必须重新核查。区分 **代码／离线测试通过** 与 **Mac 实测、生产发布通过**，不夸大验证范围。
- **严守用户授权边界**：未明确单独授权前，不得部署、重启、运行生产 launchctl、真实 RPC/CA POST、发送邮件/通知、交易、合并、改变生产规则或数据。Mac 本地执行提示词应默认只读或隔离。
- 所有改变须保留 Git 可审计证据：固定 SHA、diff、运行的具体测试、实际结果、限制及 GitHub 回执；避免提交私钥、RPC token、钱包私有数据、未脱敏日志与生产环境信息到公共仓库。
- 不重复已经关闭的验收，也不将缺失证据伪装为通过；主线优先解决真实业务阻断，而非不断延伸模拟器或增加交接环节。

详细操作、例外与检查表以 [docs/DEVELOPMENT_RULES.md](docs/DEVELOPMENT_RULES.md) 为准。其他模块特定操作规程不得放松以上交付和生产保护约束。
