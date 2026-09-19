# tracing-stack

单集群、单组织的 Kubernetes 与应用可观测性套件。一个 Helm Chart 组合独立组件镜像，提供集群指标、容器日志、OTLP 三信号、跨信号查询、告警与可选长期指标存储。

| 组件 | 职责 |
| --- | --- |
| kube-prometheus-stack | Prometheus Operator、Prometheus、Alertmanager、node-exporter、kube-state-metrics、集群规则与仪表盘 |
| Grafana | 集群与应用仪表盘、日志/trace/指标关联、服务图 |
| Alloy | 通过 Kubernetes API 采集 Pod stdout/stderr，持久化排队后发送至 Gateway |
| OpenTelemetry Gateway | OTLP HTTP/gRPC，JSON 日志关联转换，导出队列与重试 |
| Loki / Tempo | 日志 / trace 持久化，Tempo 生成 span metrics、service graph 和 exemplars |
| Thanos（可选） | Sidecar 上传、Store 读取、Compactor 保留与降采样、Query 统一近期和历史指标 |
| OTLP Edge（可选） | TLS Ingress 后的 Bearer Token 认证，同步转发至 Gateway |

默认使用 PVC，不依赖对象存储，不提供 HA、多租户、自动埋点注入或 eBPF。应用须配置 SDK 或语言自动埋点。
`1.1.0-alpha.0` 与 `0.1.0` 的 Prometheus 拓扑及 values 不兼容；从旧版采用备份后显式重建，不能直接复用旧 values 执行无感升级。

## 安装

需要 Kubernetes 1.25+、Helm 3.12+ / 4、动态供给的默认 StorageClass，以及创建 CRD 和集群 RBAC 的权限。非默认存储类参考 [storage.yaml](examples/storage.yaml)。

```bash
python3 charts/tracing-stack/tests/build_dependencies.py
python3 charts/tracing-stack/tests/preflight.py --namespace observability --release tracing
helm upgrade --install tracing charts/tracing-stack \
  --namespace observability --create-namespace --wait --timeout 15m
```

默认申请 Grafana 10Gi、Prometheus 50Gi、Alertmanager 10Gi、Loki 10Gi、Tempo 10Gi、Gateway 10Gi、Alloy 10Gi。保留时间为指标 15 天、日志 7 天、trace 3 天；Prometheus 同时设置 40GB 保留上限，可能先于 15 天删除旧指标。实际容量须按流量配置，PVC 大小和时间保留不是容量保障。

默认安装 Operator。已有 Operator 时先确认其版本、CRD 兼容性、namespace 与 instance selectors，再使用 [existing-operator.yaml](examples/existing-operator.yaml)；执行 preflight 时加 `--reuse-operator`。检查脚本通过标准 component label 识别 Operator，不能替代对自定义未标记安装的人工检查。不自动接管其他 release 的资源。

Grafana 默认 ClusterIP，使用 `grafana.ingress` 配置访问入口和 TLS。管理员 Secret 自动生成并由上游 Chart 在正常升级时复用，也可通过 `grafana.admin.existingSecret` 指定已有凭据。

```bash
kubectl -n observability port-forward svc/tracing-grafana 3000:80
kubectl -n observability get secret tracing-grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode
```

## 采集与关联

集群基础监控自动启用。业务 ServiceMonitor、PodMonitor、PrometheusRule、Probe、ScrapeConfig 使用 `observability_stack: tracing` 标签接入；namespace 不限。修改接入标签须同时调整 `monitoring` selectors、公共标签及采集资源。

Alloy 默认采集全 namespace 容器日志。`alloy.excludedNamespaces` 为 namespace 正则列表；`alloy.excludedWorkloads` 匹配 `namespace/app.kubernetes.io/name`。主机系统日志和自定义文件不在默认范围内。通过 API 采集避免挂载宿主机日志目录，但重启期间与日志轮转可能导致缺口或重复；发送队列不能弥补日志尚未被读取时的损失。

```yaml
alloy:
  excludedNamespaces: ["sandbox-.*"]
  excludedWorkloads: ["payments/load-generator"]
```

应用 OTLP HTTP 地址为 `http://tracing-gateway.observability.svc:4318`，gRPC 为 `tracing-gateway.observability.svc:4317`。

```bash
OTEL_SERVICE_NAME=my-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://tracing-gateway.observability.svc:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_TRACES_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
```

Gateway 不额外采样；应用自身采样仍影响完整性。服务图需要配对 client/server 或 producer/consumer spans，应用须传播 W3C tracecontext。

- 原生 OTLP 日志使用携带的 trace/span 上下文。
- JSON 日志识别 32 位十六进制 `trace_id`、16 位 `span_id`，可用 `service_name` 对齐应用服务名。普通文本照常采集，其他格式可覆盖 transform 配置。
- Kubernetes 日志补充 namespace、pod、container 属性；服务名优先来自应用标签或 JSON。
- trace ID 保存在 Loki structured metadata，不作为索引标签。
- Tempo → Loki 按服务名及 trace ID 回查；Loki → Tempo 使用 trace ID；Prometheus exemplar 使用 `traceID`。
- 避免同一条日志同时通过 stdout 采集与 SDK 日志 exporter 重复发送。

## 持久化缓冲

Gateway 的 trace/log exporter 使用 `file_storage` 持久队列，指标 remote-write 使用 WAL。Alloy 使用 OTLP exporter 文件队列；其 `otelcol.storage.file` 在固定的 Alloy 1.17.1 中属于 **public-preview**，默认显式启用此稳定性等级。

队列默认 1,000 个请求，受请求大小、内存与 10Gi PVC 容量共同限制。后端暂时不可用时重试，重启后重放未完成记录。队列满、磁盘满、不可重试错误、上游已确认但尚未持久化的数据、节点/PV 永久损坏都可能导致数据丢失；不承诺 exactly-once 或零丢失。失败重试可能产生重复数据。

PodMonitor 采集 Gateway、Alloy、Tempo、Loki；提供队列积压、入队失败、导出失败规则及应用/发送概览仪表盘。Kubernetes 默认规则覆盖组件不可用和卷空间不足。

## 告警

默认启用 Alertmanager 和规则，支持查询、分组、抑制、静默。未配置外部通知时，`ObservabilityNotificationsNotConfigured` 告警明确提示状态，不自动发送消息。

使用 `monitoring.alertmanager` 的上游配置接口管理 receivers、routes 和 Secret 引用。通知凭据放在 Secret；完成渠道配置和测试后设置 `notifications.configured: true`。此开关仅表示用户确认配置完成，不会自动验证渠道。

## 对象存储与长期查询

三个组件独立启用 S3，可共享服务但使用独立 bucket。启用 Thanos 不改变 Loki/Tempo 存储，不自动搬迁已有 PVC 数据。

- [loki-s3.yaml](examples/loki-s3.yaml)：引用 `loki-s3-credentials` Secret，包含 `S3_ACCESS_KEY_ID`、`S3_SECRET_ACCESS_KEY`。
- [tempo-s3.yaml](examples/tempo-s3.yaml)：引用 `tempo-s3-credentials` Secret，使用同名两个键。
- [thanos.yaml](examples/thanos.yaml)：Secret `thanos-objstore` 的 `objstore.yml` 键保存 Thanos S3 配置；sidecar 与 Store/Compactor 必须引用相同 Secret/key。

Thanos 启用时 Grafana 保持 Prometheus datasource UID，查询地址改为 Thanos Query。Gateway 和 Tempo 仍写入 Prometheus，规则仍由 Prometheus 计算。默认原始指标保留 30 天、5 分钟降采样保留 90 天、1 小时降采样保留 180 天。

对象存储需预先创建 bucket、配置访问权限及 Secret。运行时配置中的环境变量占位符通过 Secret 注入，默认 values 不包含凭据。存储切换须停写并另行制定数据迁移或重建流程，不能直接覆盖已有 Loki schema 历史。

## 外部 OTLP

参考 [otlp-ingress.yaml](examples/otlp-ingress.yaml)，以 nginx Ingress 分别暴露 HTTP 和 gRPC。TLS Secret 和 Token Secret 由用户创建；`otlp-edge.extraEnvs` 中的 `OTLP_TOKEN.valueFrom.secretKeyRef` 指定 Token Secret/key。

请求必须携带 `Authorization: Bearer <token>`。两个外部入口均要求 TLS；后端默认不对外暴露。接入层不使用异步队列，Gateway 不可用时返回失败，由客户端重试。Secret 通过环境变量注入，Token 轮换后须滚动重启接入层。

集群内部 OTLP 和查询接口默认没有 TLS/认证，适用于已约定的单组织可信集群；外部入口的认证不等于集群内网络隔离。

## 保留、备份与卸载

StatefulSet PVC 默认 Retain；Grafana 独立 PVC 使用 `helm.sh/resource-policy: keep`。正常卸载不清理 S3 bucket。卸载后保留卷不代表自动恢复：重装前需确认卷的绑定关系、Secret 和数据格式。

备份应覆盖 Grafana 数据和管理员 Secret、Prometheus/Alertmanager/Tempo/Loki 数据卷、队列卷、环境 values、S3 bucket 及外部 Secret。恢复须验证查询和写入，不能把 `helm rollback` 当作数据备份。删除 PVC 或 bucket 是单独的显式清理操作。

## 打包与验证

消费 `homelab-common` 命名与标签 helper；第三方组件保持上游模板。依赖版本在 `Chart.yaml` / `Chart.lock` 固定，镜像清单从默认及可选配置渲染，包括 Operator 管理的容器、config-reloader、hook、Thanos 和 OTLP Edge。

```bash
helm lint charts/tracing-stack --strict
python3 charts/tracing-stack/tests/check_render.py
python3 charts/tracing-stack/tests/package_release.py /tmp/tracing-online
python3 charts/tracing-stack/tests/package_release.py /tmp/tracing-offline --offline --platform linux/amd64
```

离线包包含携带依赖的 tgz、`images.tar`、镜像 ID/digest、README、示例、验证脚本与 SHA256SUMS。当前交付目标为 `linux/amd64`。客户需将镜像导入每个可调度节点或私有 registry，且使用完整 values 配置所有应用、Operator 和辅助镜像地址。在线包没有运行时镜像。

运行 smoke 前分别转发 Gateway 4318、Tempo 3200、Loki 3100、Prometheus 9090 到本地 14318、13200、13100、19090，再执行 `tests/smoke.py`。Grafana 验证使用 `tests/check_grafana.py --url <url> --password-file <protected-file>`。

静态渲染通过不代表在线验收完成。发布验证还应覆盖 Pod 日志采集、业务 Monitor 标签、告警触发/静默、TLS/Token 拒绝、持久化队列恢复、S3 历史查询、PVC 保留与离线安装。
