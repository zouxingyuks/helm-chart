---
name: helm-chart-how-to
description: helm-chart 仓库开发任务的默认入口；针对修改、审查、排错、测试、依赖、文档和发布任务，识别范围并选择本项目 skills，区分职责和组合相关流程；无匹配 skill 时定位已有源码与开发指南。仅调度项目 skills，不提供 Configure 模式。
---

|IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning; 先识别任务，再读取项目规则、资料与匹配 skills。
|Scope:仅本仓库开发维护任务；作为入口调度，不替代具体任务执行；任务讨论也可路由，但不因此启动修改或发布。
|Root:本目录向上三级为仓库根；项目路径相对仓库根，Markdown 链接相对本文件。
|Entry:读取 [根规则](../../../AGENTS.md)，定位目标 chart/文件及局部规则；已加载且未变化的入口不重复读取。
|Discovery:检索本仓库 .agents/skills/*/SKILL.md 的 name/description；只将该目录中实际存在的 skills 纳入候选；下面已知路由用于加速，不替代发现。
|Select:按任务意图和修改对象选择主 skill；有独立辅助职责时同时加载相应项目 skills，不整套加载；不存在匹配项时不虚构 skill、不自动安装或新建。
|Docs Route:知识归属、文档结构、局部规则、工作流沉淀→[helm-chart-information-architecture](../helm-chart-information-architecture/SKILL.md)；目标明确的普通文字修正直接处理目标文件。
|Version Route:chart 版本建议、校验、递增、通道切换与旧格式迁移→[helm-chart-version](../helm-chart-version/SKILL.md)；单纯打包读取发布指南，不因创建版本 skill 扩大为发布授权。
|Fallback:无匹配项目 skill 时，配置/模板/依赖→[开发流程](../../../docs/development/workflow.md)及目标 Chart.yaml、values.yaml、相关模板；测试→[验证指南](../../../docs/development/testing.md)及现有测试；打包/发布→[发布指南](../../../docs/development/releasing.md)及实际脚本；架构理解→[架构资料](../../../docs/architecture/charts.md)及模块 README。
|Review Debug:审查/排错先定位受影响行为，沿上述对象路由，核对源码与现有测试；没有专用 skill 不阻断工作，也不降低验证要求。
|Disambiguate:how-to 负责选流程与入口；information-architecture 负责知识落位与同步；运行语义以实现证据核验，不能仅因任务包含文档二字把所有工作交给文档架构 skill。
|Composition:混合任务按子任务匹配，各 skill 各司其职；主 skill 对应用户核心目标，辅助 skill 对应真实附加职责；若职责冲突则先核对适用规则和证据，只有影响任务且无法消解时询问。
|Local Only:本路由不选择全局 skills、不按名称相似回退全局同名项；外部 skill 不加入项目路由表；用户显式指定或更高层规则要求的 skills 仍按其指令处理。
|No Recursion:不要将本 skill 路由给自己；下游读取 AGENTS 时不重新启动已完成的同一轮路由；仅在任务范围改变或发现新职责时重新选择。
|Maintenance:发现新增项目 skill 后按真实描述选择；仅在入口语义、职责重叠或已有显式引用变化时更新路由；静态分类仍维护在 [文档地图](../../../docs/README.md)，不在此复制。
|Execution:选择后继续完成已授权任务；验证方式从对应指南/脚本读取；路由不扩大部署、联网写入、发布等动作授权；无 Configure 模式，不修改其他工具配置。
|Output:简要说明任务范围、选中的项目 skills 及原因、验证入口；简单任务可融入正常进度说明，无需重复输出固定报告；无匹配时明确使用源码/指南执行。
|Validation:结构校验之外，使用 [路由场景](evals/evals.json)检查项目限定、消歧、无匹配回退和循环防护；未执行的场景不宣称通过。
