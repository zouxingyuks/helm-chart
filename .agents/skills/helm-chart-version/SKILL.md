---
name: helm-chart-version
description: 为本 helm-chart 仓库分析、建议、校验或按指令更新 chart 版本；根据已发布制品和目标维护线判断变更级别，处理 alpha、beta、lts、临时 Mark 及旧格式迁移。不自动发布或升级 appVersion。
---

|IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning; 以已发布制品和真实差异判断版本，不从工作区版本或 commit 数量推断。
|Scope:仅本仓库 chart 版本工作流；默认给出建议，收到更新指令才修改必要文件；远端发布和临时制品清理分别需要明确指令。
|Root:从本文件向上三级定位仓库；开始先读 [版本契约](../../../docs/development/versioning.md)，字段、通道、初始化、迁移和语法只在该文档维护。
|Discovery:读取目标目录适用 AGENTS、Chart.yaml、values.yaml、README、相关模板、schema、Chart.lock 与测试；检索代表版本引用和发布方式，保留 chart 自身结构，不扩展成全仓迁移。
|Inputs:优先使用用户明确提供的目标 chart、发布渠道、基准版本、目标通道和维护线；上下文唯一时自动确定，否则只询问缺失项；指定基准仍须核实 chart、通道、维护线和已发布状态。
|Baseline:按版本契约选择对应通道中最近的正常已发布版本；排除 Mark；不要将全仓最大版本、本地 index、Git tag 或工作区版本当作发布证明。Git 记录只作辅助，不强制 tag。
|Retrieve:从目标发布渠道下载基准 tgz 到独立临时目录，核对包内 name/version 与发布元数据、摘要（若提供）；依据现有发布环境选择命令。无法获取或唯一确认基准时报告缺失证据，不伪造已验证的版本建议。
|Compare:比较已发布包与待发布的有效 chart 内容；按 .helmignore 和实际依赖范围识别包内变化，必要时在临时目录本地打包。排除 tgz 容器时间戳等打包噪声和纯版本字段变化；嵌套依赖不能只比较压缩字节，需检查内容和上游变更证据。
|Classify:依据版本契约评估最高变更级别，列出具体文件和兼容性影响；镜像或依赖升级无法仅从包差异判定兼容性时继续查证，证据不足则说明待确认项。ArchVer 递增须有明确产品代际批准。
|Calculate:按目标通道重选基准并计算；beta 必须与前个 beta 比较全部累计变化；不直接改 alpha 的 Tag。旧格式迁移和缺失历史按契约处理，不静默初始化；同一通道没有制品内容变化不制造新版本；首次获准 LTS 按版本契约的通道建立例外处理。
|Output:报告 chart、渠道、维护线、基准版本及制品证据、差异摘要、最高变更级别与理由、目标版本、语法校验结果及未确认事项；明确建议与已执行动作。
|Update:收到更新指令后修改目标 Chart.yaml 的 version 及确有必要的版本引用；appVersion 独立，不自动改镜像或依赖版本，不重建发布 index/tgz。需要修改依赖锁时遵循 [开发流程](../../../docs/development/workflow.md)，不把版本工作变成依赖升级。
|Validate:用版本契约的完整语法检查目标值，并按 [验证指南](../../../docs/development/testing.md)执行受影响检查；检查相对基准的数字变化和通道，必要时用临时 tgz 核验元数据。说明本地验证与远程发布验证的区别。
|Publish:明确发布指令交给 [发布指南](../../../docs/development/releasing.md)及目标 chart 流程；本 skill 不创造统一上传方式，不覆盖已发布正常版本，不自动删除带 Mark 产物。
|Skill Checks:维护本 skill 时检查 frontmatter、相对链接及 [行为场景](evals/evals.json)；场景材料不等于已执行测试，交付时说明实际验证范围。
