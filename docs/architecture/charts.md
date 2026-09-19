# Chart 架构与边界

本仓库同时包含应用 chart 和一个 library chart。应用负责 Kubernetes 资源、组件拓扑和配置；library 负责显式调用的模板 helper，不生成工作负载。

## 依赖关系

下表概括职责，具体版本及条件以各 chart 的 `Chart.yaml` 和已有 `Chart.lock` 为准。

| Chart | 实现与依赖 |
| --- | --- |
| [AxonHub](../../charts/axonhub/Chart.yaml) | 本地应用模板及 PostgreSQL 模板，无声明的子 chart 依赖 |
| [DeepLX](../../charts/deeplx/Chart.yaml) | 本地应用模板，依赖第三方 Bitnami common |
| [LobeHub](../../charts/lobehub/Chart.yaml) | 本地应用模板，按配置启用 PostgreSQL、Redis 子 chart |
| [Subconverter](../../charts/subconverter/Chart.yaml) | 独立前后端 Deployment 与 Service，无声明的子 chart 依赖 |
| [tracing-stack](../../charts/tracing-stack/Chart.yaml) | 组合 kube-prometheus-stack、Grafana、Alloy、Loki、Tempo 和 Collector，提供可选 Thanos 模板；本地 helper 消费 homelab-common |
| [homelab-common](../../charts/homelab-common/Chart.yaml) | library，无运行时子 chart 依赖 |

## 公共库边界

`homelab-common` 维护来自 Bitnami common 的必要源码子集，使用 `homelab.common.*` 命名空间，避免与第三方 `common.*` 直接重名。Dependency alias 不会重命名 Helm named templates。

库不负责应用端口、数据库连接、组件启停或存储拓扑。接入时由应用保留自己的 helper 入口和资源身份，不能假设相似 helper 具有相同默认行为。当前关系不意味着其他 chart 已迁移或必须迁移。

Helper API、兼容性政策、来源许可证和接入检查只维护在[公共库 README](../../charts/homelab-common/README.md)。其中的名称、selector 和 PVC 约束应在消费应用的回归验证中检查，公共库契约测试不能代替应用测试。

## 模块设计与知识入口

- [Subconverter](../../charts/subconverter/README.md) 维护前后端资源、路由和配置模式说明；局部修改规则见其 [AGENTS](../../charts/subconverter/AGENTS.md)。
- [tracing-stack](../../charts/tracing-stack/README.md) 维护数据流、外部服务条件、存储和运行边界；交付说明随安装包分发，因此保留在 chart 内。
- 同一种 Kubernetes 资源在不同 chart 中可能有不同约束。修改时比较相同职责和语义，不把一处实现无条件推广到其他 chart。

仓库根的版本化 tgz 和 `index.yaml` 是发布制品与索引；源码存在不代表对应版本已远程发布。发布维护见[打包与发布](../development/releasing.md)。
