# Helm Charts

面向开发维护的 Helm chart 仓库。应用 chart 位于 `charts/`，公共 library 为应用提供模板 helper；各 chart 的配置和运行边界由各自 README 说明。

| Chart | 用途与开发入口 |
| --- | --- |
| [axonhub](charts/axonhub/README.md) | AxonHub 应用及其 PostgreSQL 资源 |
| [deeplx](charts/deeplx/README.md) | DeepLX 翻译 API，依赖 Bitnami common |
| [homelab-common](charts/homelab-common/README.md) | 本地维护的公共模板 library，不单独部署 |
| [lobehub](charts/lobehub/README.md) | LobeHub 应用，可选 PostgreSQL、Redis 子 chart |
| [subconverter](charts/subconverter/README.md) | 独立前后端的订阅转换服务 |
| [tracing-stack](charts/tracing-stack/README.md) | Grafana、Prometheus、Tempo、Loki、OpenTelemetry Gateway |

## 开始开发

先阅读目标 chart 的 `Chart.yaml`、`values.yaml` 和 README。准备 Helm；Python 测试的要求见[验证指南](docs/development/testing.md)。以下是不需要第三方依赖下载的本地示例，从仓库根目录执行：

```sh
helm lint charts/subconverter --strict
helm template demo charts/subconverter > /tmp/subconverter-rendered.yaml
```

渲染通过不代表集群部署成功。有依赖的 chart 先按[开发流程](docs/development/workflow.md)准备依赖，再运行对应检查。

## 开发文档

- [文档地图与归属](docs/README.md)：查找资料及添加新知识。
- [Chart 架构与边界](docs/architecture/charts.md)：理解应用、公共库和第三方依赖的关系。
- [开发流程](docs/development/workflow.md)：修改配置、模板和依赖。
- [验证指南](docs/development/testing.md)：选择本地检查或在线验证。
- [打包与发布](docs/development/releasing.md)：制品、索引和交付边界。
