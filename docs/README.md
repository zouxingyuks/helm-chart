# 开发文档地图

这里维护跨 chart 的长期知识，面向开发者。单个 chart 的配置、安装与公开契约留在对应 README，使安装包离开源码仓库后仍可阅读。

| 资料 | 负责的内容 |
| --- | --- |
| [根 README](../README.md) | 项目概览、chart 清单和开发入口 |
| [根 AGENTS](../AGENTS.md) | Agent 行为规则、查找路径与验证导航 |
| [架构](architecture/charts.md) | Chart 关系、公共库和应用的职责边界 |
| [开发流程](development/workflow.md) | 配置、模板、依赖的修改方式 |
| [验证指南](development/testing.md) | 各测试入口、前置条件、覆盖范围和副作用 |
| [打包与发布](development/releasing.md) | 跨 chart 的制品与索引维护流程 |
| [Chart 版本规则](development/versioning.md) | 版本语法、变更级别、发布通道及迁移基准 |
| [公共库 README](../charts/homelab-common/README.md) | Helper API、兼容性、命名空间及接入约定 |
| [公共库测试说明](../tests/homelab-common/README.md) | 契约测试的准确参数与参考制品要求 |
| [项目任务入口 skill](../.agents/skills/helm-chart-how-to/SKILL.md) | 选择项目 skills、区分职责；无匹配项时定位源码与开发指南 |
| [Chart 版本 skill](../.agents/skills/helm-chart-version/SKILL.md) | 依据已发布制品建议、校验或按指令更新 chart 版本 |
| [项目文档架构 skill](../.agents/skills/helm-chart-information-architecture/SKILL.md) | Agent 判断知识归属、整理和验证的可复用流程 |

## 放置规则

- 必须执行的规则放适用范围的 AGENTS；模块说明放模块 README。只有存在独立局部规则才增加子目录 AGENTS。
- 跨 chart 的设计解释放 `architecture/`；开发、测试、依赖和发布流程放 `development/`。不为尚无内容的分类建空目录。
- 单个 chart 的参数与使用示例放其 README；较长模块资料确需拆分时，保持 chart 包内可达，并检查打包结果。
- 重复的 Agent 工作流只有具备触发条件、步骤、输出和验证方式才放 `.agents/skills/`；静态项目事实通过链接读取。
- 一次性计划、未完成事项和过程记录留在任务或 issue，不写成长期文档事实。工具私有 memory 可作线索，不能替代版本控制中的项目文档。

## 维护与冲突处理

一项事实只设一个主要维护位置。其他入口链接它；必要的简短概述应随来源一同核对。变更模板、values、schema、依赖或测试入口时，检查相关 README、docs 和 AGENTS 是否受影响。

运行语义需要对照实现与测试核实。若文档与源码冲突，记录具体证据；明确过时的说明按现状修正，涉及预期公开契约或长期架构的取舍应先确认。不得为使文字成立而顺手改变 chart 行为。

迁移文档时更新原入口和引用，检查相对链接与包内可读性。本文维护分类约定；skill 引用本文，不另存一份分类事实。
