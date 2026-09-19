# 开发流程

以下路径与命令均相对于仓库根目录。先确定目标 chart；模块 README 负责参数和模块行为，本页负责共用开发步骤。

## 修改配置或模板

1. 阅读目标 `Chart.yaml`、`values.yaml`、README 和相关模板；存在 `AGENTS.md`、`values.schema.json`、测试时一并核对。
2. 找一个职责和约束相同的本地实现作为参考。跨 chart 的类似片段只作为线索，不能据此改变当前 chart 的默认值或公开契约。
3. 修改必要文件；配置键变化同时核对 schema（若存在）、默认值、模板引用和 README 示例。名称、selector、PVC 变化需要单独审查升级影响。
4. 按[验证指南](testing.md)选择覆盖变更的检查，说明未验证的条件。
5. 对照[文档地图](../README.md)同步知识入口；临时计划不写进长期指南。

## 依赖管理

`Chart.yaml` 表达依赖要求，`Chart.lock` 记录解析结果，chart 内的 `charts/` 保存实际依赖。先检查它们再选择命令。

- **重建已有锁定依赖**：`helm dependency build charts/<name>`。缺少锁文件时它会按 update 的方式解析，不能把它当作固定版本重建。
- **有意更新依赖**：修改声明后执行 `helm dependency update charts/<name>`，审查锁文件和渲染差异。不要为了修复文档而更新依赖。
- **tracing-stack**：使用 `python3 charts/tracing-stack/tests/build_dependencies.py`。它从锁文件读取仓库，用临时 Helm 仓库配置和缓存构建；仍会联网，并写入该 chart 的依赖目录。
- **本地 library**：`file://../homelab-common` 按消费 chart 目录解析。接入与兼容性要求见[公共库 README](../../charts/homelab-common/README.md)。

DeepLX 和 LobeHub 的第三方仓库与版本由各自声明和锁文件确定，不能套用 tracing-stack 的脚本。`--skip-refresh` 仅跳过仓库索引刷新，不等于整个流程离线。

官方命令语义：[dependency build](https://helm.sh/docs/helm/helm_dependency_build/)、[dependency update](https://helm.sh/docs/helm/helm_dependency_update/)。

## 提交前

查看差异是否包含意外依赖包、临时渲染结果或凭据；仓库已有发布制品按[发布流程](releasing.md)单独维护。只报告实际运行过的检查，区分本地渲染和在线验证。
