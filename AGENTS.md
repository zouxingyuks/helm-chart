|IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning; 修改前读取目标目录规则、代表实现与对应文档。
|Scope:本仓库 Helm chart 开发维护；子目录 AGENTS 仅补充局部规则；个人工具配置不复制为项目要求。
|Entry:./:{README.md}|docs:{README.md}
|Task Router:.agents/skills/helm-chart-how-to/SKILL.md|本项目修改、审查、排错、测试、依赖、文档和发布任务先使用；仅路由项目 skills；同一任务已完成路由时不因重读规则重复启动。
|Architecture:docs/architecture:{charts.md}|公共库契约:charts/homelab-common:{README.md}
|Development:docs/development:{workflow.md,testing.md,releasing.md}
|Charts:charts:{axonhub,deeplx,homelab-common,lobehub,subconverter,tracing-stack}|先读目标 Chart.yaml、values.yaml、README.md，再读相关 templates 与现有 schema/测试。
|Doc Placement:.agents/skills/helm-chart-information-architecture/SKILL.md|涉及知识归属、文档结构、规则或工作流沉淀时使用；单纯文字修正按目标文档处理。
|Authority:行为约束遵循适用规则；运行语义对照模板、values、schema、锁文件与测试；冲突报告证据，不凭文档新旧裁决或静默修改公开契约。
|Boundaries:各 chart 保留自己的配置与拓扑；公共 helper 接入不自动改变名称、selector、PVC 身份或默认行为。
|Dependencies:按目标 Chart.yaml/Chart.lock 处理；重建与升级分开；不要把某个 chart 的依赖版本或镜像策略推广为全仓要求。
|Validation:按 docs/development/testing.md 选择受影响检查；区分本地渲染、联网构建和在线验证；缺失前置条件应明确报告。
|Artifacts:打包优先写独立临时目录；版本化 tgz 与 index.yaml 属于发布产物，不因文档整理而重建或覆盖。
|Docs Sync:修改行为时核对目标 README、相关 docs、局部规则与实际验证入口；同一事实维护一处，其他位置链接。
|Writing:中文为主，保留英文术语和标识符；AGENTS 使用简洁 pipe-index；README/docs 使用可读 Markdown；临时进度留在任务中。
