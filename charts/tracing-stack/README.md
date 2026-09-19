# tracing-stack

完整的五组件可观测性 Helm Chart：**Grafana + Prometheus + Tempo + Loki + OpenTelemetry Gateway**。
提供 OTLP 数据接收、持久化存储、查询及跨信号关联。各组件使用独立镜像，可通过 Helm 安装包或离线镜像包部署。

```text
应用 OpenTelemetry SDK ── OTLP 4317/4318 ── Gateway
                                          ├─ traces ── Tempo ── span metrics / service graph ─┐
                                          ├─ logs ──── Loki                                 │
                                          └─ metrics ───────────────────────────────────────┤
                                                                                           ▼
Grafana ── Tempo / Loki / Prometheus；日志↔trace、指标 exemplar→trace、服务拓扑     Prometheus
```

## 完整安装

需要 Kubernetes 1.25+、Helm 3.12+ / 4，以及可用的默认 StorageClass。
持久化默认申请：Grafana 2Gi、Prometheus 10Gi、Tempo 10Gi、Loki 10Gi。
这是一套单实例应用可观测性部署，不包含 Prometheus Operator、集群级 node-exporter、Alertmanager 或 HA。

从源码目录：

```bash
/usr/bin/python3 charts/tracing-stack/tests/build_dependencies.py
helm upgrade --install tracing charts/tracing-stack \
  --namespace observability --create-namespace --wait --timeout 10m
```

从安装包目录（包内已包含全部子 Chart，无需访问 Helm 仓库）：

```bash
sha256sum -c SHA256SUMS
helm upgrade --install tracing ./tracing-stack-0.1.0.tgz \
  --namespace observability --create-namespace --wait --timeout 10m
kubectl -n observability port-forward svc/tracing-grafana 3000:80
```

Grafana 初始管理员密码由上游 Chart 随机生成在 `tracing-grafana` Secret 中：

```bash
kubectl -n observability get secret tracing-grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode
```

正式环境建议通过 `grafana.admin.existingSecret` 管理凭据。Chart 不包含固定密码。
Grafana 自动获得 Prometheus、`tracing-Tempo`、`tracing-Loki` 数据源，remote-write 和 exemplar 存储默认开启。

### 自定义存储

无默认 StorageClass 时，创建自己的 values 文件：

```yaml
grafana:
  persistence:
    storageClassName: your-storage-class
prometheus:
  server:
    persistentVolume:
      storageClass: your-storage-class
tempo:
  persistence:
    storageClassName: your-storage-class
loki:
  singleBinary:
    persistence:
      storageClass: your-storage-class
```

安装时用 `-f your-values.yaml`。Tempo 和 Loki 默认使用 PVC 上的本地存储，保留 72 小时；
Prometheus 保留 15 天。磁盘容量应按实际流量配置，时间保留策略不保证磁盘永远足够。

## 应用接入

OTLP HTTP 示例：

```bash
OTEL_SERVICE_NAME=my-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://tracing-gateway.observability.svc:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_TRACES_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
```

OTLP gRPC 地址为 `tracing-gateway.observability.svc:4317`。
SDK 必须真正启用对应 exporter；仅设置环境变量不保证所有语言自动启用日志导出。
跨服务调用须传播 W3C tracecontext；日志在活动 span 上下文内生成，携带原生 `trace_id` / `span_id`。
稳定的 `service.name` 用于服务维度关联，Loki 自动将其映射为 `service_name`。

Gateway 接收三类 OTLP 数据。Pod stdout 日志可使用 Alloy 等采集器，避免同一日志重复入库。
没有额外 tail sampling，上游 SDK 的采样仍影响 trace 完整度。
服务拓扑需要配对的 client/server 或 producer/consumer spans，孤立 span 不会产生服务连线。

### Grafana 关联

- Loki → Tempo：按 OTLP 结构化元数据 `trace_id` 跳转。
- Tempo → Loki：按 `service.name → service_name` 与 trace ID 回查。默认不强制 span ID，避免遗漏父 span 上下文日志。
- Tempo → Prometheus：服务拓扑使用 `traces_service_graph_*`，span metrics 使用 `traces_spanmetrics_*`。
- Prometheus → Tempo：通过 exemplar 中的 `traceID` 跳转。

对于只包含 `trace-id(...)` 文本的日志，需在采集器中规范化元数据或配置文本 derived field。
原生 OTLP 日志使用结构化元数据关联。

## 配置外部服务

将 `global.grafana.install`、`global.prometheus.install` 或 `global.loki.install` 设置为 `false`，
可以连接外部服务。禁用 Prometheus 或 Loki 部署时，必须提供对应的 `global.prometheus.url`
或 `global.loki.url`；`global.prometheus.datasourceUid` 指定 Grafana 中的 Prometheus 数据源 UID。

外部服务要求：

- Grafana datasource sidecar 监听 release namespace 和 `grafana_datasource=1`。
- Prometheus 启用 remote-write receiver 和 exemplar-storage，并配置 exemplar 的 `traceID` 跳转目标。
- Loki 使用 3.x、TSDB schema v13，并允许 structured metadata。

## 升级

升级前备份持久化数据和 Grafana Secret。使用完整环境配置升级同一个 release：

```bash
helm upgrade tracing ./tracing-stack-0.1.0.tgz \
  --namespace observability --reset-values -f values.yaml --wait --timeout 10m
```

`helm rollback` 恢复 Kubernetes 资源配置；涉及应用版本降级时，需要确认持久化数据格式兼容性。

## 构建安装包

公共命名和资源标签使用 `homelab-common 0.1.0` library chart。源码构建通过
`file://../homelab-common` 引用同仓库公共库；安装包包含公共库模板和许可证，
安装时无需访问源码目录。第三方子 Chart 保留各自的资源模板。

依赖固定在 `Chart.yaml` / `Chart.lock`。五个应用分别为 Grafana 13.0.1、Prometheus 3.14.0、
Tempo 2.9.0、Loki 3.6.5、Collector contrib 0.145.0。辅助镜像由固定依赖版本确定。
完整清单从实际渲染结果生成，包含 Grafana 初始化容器、datasource sidecar、Prometheus config reloader。
不使用 `latest`。版本标签仍可能被上游重推，离线包另外记录实际镜像 ID 和仓库 digest。

构建机需要 Helm、Python 3 + PyYAML；离线打包还需要 Docker 和 registry 网络访问。
输出目录必须尚不存在：

```bash
# 在线安装包：包含所有 Chart 依赖、镜像清单、文档、测试、校验和。
/usr/bin/python3 charts/tracing-stack/tests/package_release.py /tmp/tracing-online

# 离线完整包：额外包含全部镜像的 images.tar，以及实际镜像 ID / digest。
/usr/bin/python3 charts/tracing-stack/tests/package_release.py /tmp/tracing-offline \
  --offline --platform linux/amd64
```

输出内容：

- `tracing-stack-0.1.0.tgz`：携带全部依赖的 Chart。
- `images.txt`：主容器、sidecar、init container 的完整镜像引用。
- `images.tar`：仅离线模式，指定架构的全部镜像。
- `release-manifest.json`：交付模式、架构、实际离线镜像 ID / digest。
- `Chart.lock`、`README.md`、`examples/`、`tests/`、`SHA256SUMS`。

没有 `images.tar` 的在线包需要客户节点访问相应镜像仓库；它不是离线镜像包。
离线交付方在每个可调度节点按实际 CRI 导入镜像，例如 containerd：

```bash
sha256sum -c SHA256SUMS
sudo ctr -n k8s.io images import images.tar
```

Docker 的 `docker load -i images.tar` 只用于实际使用该镜像存储的环境；加载到构建机 Docker
不会自动使 Kubernetes 节点可用。保持默认 `IfNotPresent` 拉取策略，核对节点上的镜像引用。
也可按镜像清单推送到客户私有 registry，并在完整 values 中逐一设置各组件及辅助镜像的 repository。
镜像仓库、TLS 与 imagePullSecrets 由部署环境配置。离线镜像包的架构必须与目标节点一致。

## 验证

在源码目录：

```bash
helm lint charts/tracing-stack --strict
/usr/bin/python3 charts/tracing-stack/tests/check_render.py
```

部署后分别 port-forward（完整安装示例）：

```bash
kubectl -n observability port-forward svc/tracing-gateway 14318:4318
kubectl -n observability port-forward svc/tracing-tempo 13200:3200
kubectl -n observability port-forward svc/tracing-loki 13100:3100
kubectl -n observability port-forward svc/tracing-prometheus-server 19090:80
kubectl -n observability port-forward svc/tracing-grafana 13000:80
```

在安装包目录执行：

```bash
python3 tests/smoke.py
python3 tests/check_grafana.py --password-file /secure/path/grafana-admin-password
/usr/bin/python3 tests/check_render.py
```

smoke 会发送带统一 trace ID 的日志、指标、配对跨服务 spans，核验三类数据、span metrics、
service graph 和 exemplar。Grafana 检查核验真实 datasource 健康及关联配置；仍需人工点击 UI 验证跳转。

## 运行边界

默认内部通信为 ClusterIP、无后端 TLS/多租户鉴权，Grafana 不开放匿名访问。
Gateway 的发送队列在内存中，重启或超过重试窗口可能丢失未导出数据；严格耐久性需求应另行配置持久化队列。
单实例后端不提供 HA。Tempo 子 Chart 的 ConfigMap 名固定为 `tempo`，同一 namespace 安装一套。
本地存储限制 Tempo/Loki 为一副本，不支持直接调大副本数变为分布式部署。

Tempo/Loki/Prometheus 的 StatefulSet PVC 默认保留；Grafana PVC 是 Helm 管理的独立资源，
卸载前应按环境备份或设置明确的保留策略。不要用卸载再安装代替升级。
外部 Grafana 未启用 datasource prune，卸载集成 Chart 后新增数据源可能保留，需按原管理流程清理。
