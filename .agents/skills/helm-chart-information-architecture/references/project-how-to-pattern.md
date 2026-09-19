# 项目工作流与路由

本项目的技能目录是 `.agents/skills/`，默认任务入口为 [helm-chart-how-to](../../helm-chart-how-to/SKILL.md)，通过根 AGENTS 接入。它仅选择实际存在的项目 skills；无匹配项时读取已有源码与开发指南，不调度全局 skills，也不提供 Configure 模式。修改前仍须检索现有 skills 和实际引用。

新增 skill 需要明确的触发条件、重复流程、预期输出和验证方式。先复用现有文档或技能；文档目录清单、单个配置事实和一次性任务不单独建 skill。

保留本 skill 的名字与目录 `helm-chart-information-architecture`；description 限定 helm-chart 文档架构，主体读取项目文档地图。全局 `agent-information-architecture` 是来源，不是项目分类的同步目标。

how-to 负责选择流程，本 skill 负责文档归属；下游重读根规则时不重复启动同一任务的路由。仅当任务改变技能选择或入口语义时更新路由引用。新增一个 skill 不自动要求新增或同步 `*-how-to`。如果将来需要跨项目复用，应单独决定导出范围，不把本仓库路径变成其他项目的要求。
