---
name: helm-chart-information-architecture
description: 为 helm-chart 仓库决定项目知识在 AGENTS.md、chart README、docs 和本地 skills 中的归属，整理开发文档架构并验证同步与包内可读性。用于知识归属、文档结构、局部规则和重复工作流设计；不用于目标明确的普通文字修正。
---

|IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning; 先查项目规则、代表文件与实现，再决定知识归属。
|Scope:仅服务本 helm-chart 仓库的开发维护；保留按职责和变更原因分类的目标；不修改全局来源 skill。
|Root:从本文件向上三级定位仓库；下列项目路径相对于仓库根目录，references/evals 相对于本 skill。
|Entry:读取 AGENTS.md、README.md、docs/README.md；docs/README.md 是文档分类唯一维护位置；再读目标子目录规则、README 和相关实现。
|Discovery:先搜索相同职责的文档/配置/模板，至少检查一个代表；比较适用约束，不凭位置、数量或新旧决定冲突。
|Classification:按内容变更原因分类；规则→作用域 AGENTS；人类入口及模块契约→README；长期设计/开发知识→docs 的既有子类；重复 Agent 流程→本地 skill；临时进度→任务。
|Responsibility:遇到混合内容或冲突时读 [职责判断](references/artifact-responsibility.md)；涉及 docs 归属或迁移时读 [文档落位](references/docs-taxonomy-discovery.md)；设计 skill 或路由时读 [项目工作流](references/project-how-to-pattern.md)。
|Evidence:Helm 行为核对目标 Chart.yaml、Chart.lock（若有）、values.yaml、schema（若有）、相关 templates 与测试；版本/命令不从记忆补全；工具私有 memory 仅作线索。
|Placement Decision:编辑前简要给出目标路径、职责/变更原因、参考证据、未选相邻位置的原因、同步范围、风险和待决问题；机械编辑明确目标时可省略；现有授权内直接执行。
|Approval:既有结构内的普通整理按任务授权执行；公共契约、长期分类/路由或跨组件边界变化未获授权时，只暂停依赖该决定的部分；不把每次文档修改变成审批流程。
|Migration:一项事实维护一处，其他位置链接；迁移时更新原入口/入链并检索旧说法；chart 包或 tracing 交付目录需要的说明保持独立可读，不机械移出 chart。
|Writing:中文为主，保留英文标识符；AGENTS 使用 pipe-index，README/docs 保持可读 Markdown；必需 YAML frontmatter 保留；不批量翻译无关旧文档。
|Project Boundaries:不把公共库接入视为所有应用必须迁移；不把某 chart 的镜像、依赖、测试或发布方式推广为全仓规则；静态架构读取 docs/architecture/charts.md。
|Verification:检查相对链接、索引路径、配置键和命令；变化涉及包内资料时核对打包脚本与可达性；按 docs/development/testing.md 验证必要示例，不自动部署、写遥测或发布。
|Skill Validation:修改本 skill 时核对 frontmatter/name、引用文件与 [行为场景](evals/evals.json)；使用环境中可用的 skill-creator 校验器；场景是验证材料，不代表已自动执行。
|Delivery:报告落位、迁移/同步、实际验证、遗留限制、参考文件和实际使用的 skills；区分源码核验、本地渲染和在线验证。
