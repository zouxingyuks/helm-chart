# DeepLX Helm Chart

本 Chart 在 Kubernetes 上部署 [DeepLX](https://github.com/OwO-Network/DeepLX) `1.2.2`，提供 DeepL-compatible translation
API。Chart 默认不配置认证信息、不创建持久卷，也不创建 RBAC。

## 前置要求

- Kubernetes 1.20+
- Helm 3.2+
- 可选的 Ingress Controller

## 快速开始

```bash
helm dependency build charts/deeplx
helm install deeplx charts/deeplx
```

默认创建 `Deployment`、`Service`、`ServiceAccount` 和 Helm test hook。Service 为 `ClusterIP`，端口 `1188`。

## 镜像

默认镜像为 `docker.io/missuo/deeplx:v1.2.2`，不会使用 `latest`。设置 `image.digest` 后 digest 优先于 tag，例如：

```yaml
image:
  digest: sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

## 认证与代理

三项 inline 值分别映射为 `TOKEN`、`DL_SESSION` 和 `PROXY`。只要任一 inline 值非空，Chart 就创建 Secret；三项均为空时不会创建
Secret。

```yaml
auth:
  token: "replace-me"
  dlSession: ""
  proxy: "http://proxy.example.com:8080"
```

生产环境建议引用已有 Secret：

```yaml
auth:
  existingSecret:
    name: deeplx-credentials
    keyMapping:
      token: TOKEN
      dlSession: DL_SESSION
      proxy: PROXY
```

`auth.existingSecret.name` 与任一 inline 值互斥，混用会在渲染期报错。三个凭据彼此独立可选；existing Secret 只需包含实际使用的映射 key；缺失的可选 key 不会阻止 Pod 启动，对应环境变量也不会被设置。

Chart 始终注入 `IP=0.0.0.0` 与 `PORT=1188`，以固定 DeepLX 的监听地址和端口。`IP`、`PORT`、`TOKEN`、`DL_SESSION`、`PROXY`
均由 Chart 管理，不能在 `extraEnvVars` 中重复定义；冲突配置会在渲染期失败。

## Ingress

`ingress.hosts[]` 中每个 host 创建一个独立 Ingress，可分别设置 annotations、TLS、path 和 pathType；`className` 为全局配置。

```yaml
ingress:
  enabled: true
  className: nginx
  hosts:
    - hostname: api.example.com
      path: /
      pathType: Prefix
      annotations:
        cert-manager.io/cluster-issuer: letsencrypt-prod
      tls:
        - secretName: api-example-com-tls
          hosts:
            - api.example.com
    - hostname: translate.example.com
      path: /deeplx
      pathType: Prefix
      annotations: {}
      tls: []
```

启用 Ingress 时 `hosts` 不得为空，且每项 `hostname` 必须非空并保持唯一。资源名包含 hostname 的稳定短哈希，避免不同 hostname 清理为相同 DNS 名称时发生冲突。

## 健康检查与 Helm test

默认 readiness/liveness probes 都使用命名端口 `http` 的 `tcpSocket`，不把 `GET /` 当作语义健康检查。`customReadinessProbe`
或 `customLivenessProbe` 非空时会完整覆盖对应默认探针，因此必须提供完整的 `exec`、`httpGet` 或 `tcpSocket` handler。

Helm test 使用固定非 latest 镜像 `docker.io/curlimages/curl:8.14.1` 请求 Service 根路径。该请求仅验证 Pod 到 Service 的
HTTP 连通性，是 smoke test，不代表翻译功能或上游 DeepL 可用性。

## HPA 与 PDB

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: null

podDisruptionBudget:
  enabled: true
  minAvailable: 1
  maxUnavailable: null
```

HPA 启用时 Deployment 不渲染 `replicas`。`maxReplicas` 必须大于或等于 `minReplicas`，且 CPU/Memory target 至少设置一个。PDB
启用时必须且只能设置 `minAvailable` 或 `maxUnavailable` 中一个，值不能为零。

## 调度与安全

支持 `nodeSelector`、`tolerations`、Common affinity presets、完整 `affinity`、`topologySpreadConstraints`、
`priorityClassName` 和 `schedulerName`。默认不添加任何 affinity 或其他调度约束；完整 `affinity` 非空时优先于所有 presets。

默认 Pod 与容器以 UID/GID `1001` 非 root 运行，使用 `RuntimeDefault` seccomp、只读根文件系统、禁止权限提升并 drop `ALL`
capabilities。可通过 `podSecurityContext.enabled`、`containerSecurityContext.enabled` 关闭对应上下文，或覆盖其字段。

OpenShift 的随机 UID 策略可能与固定 UID/GID `1001` 冲突；在受限 SCC 下请关闭固定上下文或按集群分配范围覆盖 UID/GID，同时保留
`runAsNonRoot`、seccomp 和 capabilities 限制。

## 主要参数

| 参数                                          | 说明                               | 默认值          |
| --------------------------------------------- | ---------------------------------- | --------------- |
| `replicaCount`                                | Deployment 副本数                  | `1`             |
| `image.repository`                            | 应用镜像仓库                       | `missuo/deeplx` |
| `image.tag`                                   | 应用镜像 tag                       | `v1.2.2`        |
| `image.digest`                                | 可选 sha256 digest，设置后覆盖 tag | `""`            |
| `service.port`                                | Service 端口                       | `1188`          |
| `serviceAccount.create`                       | 创建 ServiceAccount                | `true`          |
| `serviceAccount.automountServiceAccountToken` | 自动挂载 token                     | `false`         |
| `auth.existingSecret.name`                    | 已有 Secret 名称                   | `""`            |
| `extraEnvVars`                                | 额外环境变量                       | `[]`            |
| `extraEnvVarsCM`                              | 额外 envFrom ConfigMap             | `""`            |
| `extraEnvVarsSecret`                          | 额外 envFrom Secret                | `""`            |
| `resources`                                   | 容器 resources                     | `{}`            |
| `autoscaling.enabled`                         | 启用 HPA                           | `false`         |
| `podDisruptionBudget.enabled`                 | 启用 PDB                           | `false`         |
| `terminationGracePeriodSeconds`               | Pod 终止等待秒数                   | `30`            |
| `extraVolumes` / `extraVolumeMounts`          | 附加卷与挂载                       | `[]` / `[]`     |

全部配置及中文注释见 [values.yaml](./values.yaml)。

## v1 范围边界

本 Chart v1 不提供 PVC/持久化、NetworkPolicy、metrics/ServiceMonitor、RBAC、sidecars/initContainers、`diagnosticMode`、
`hostAliases`、`lifecycle` 或 `extraDeploy`。如需这些能力，应由平台层或后续明确合同单独设计，不通过未声明 values 隐式扩展。

## 本地验证

```bash
helm dependency build charts/deeplx
helm lint charts/deeplx --strict
helm template deeplx charts/deeplx
helm template deeplx charts/deeplx --kube-version 1.20.0
helm test deeplx --logs
```

关键失败示例：

```bash
# 已有 Secret 与 inline 凭据互斥
helm template deeplx charts/deeplx \
  --set auth.existingSecret.name=credentials \
  --set auth.token=inline

# Ingress 启用时必须提供唯一 hostname
helm template deeplx charts/deeplx --set ingress.enabled=true

# HPA 必须有指标且 maxReplicas >= minReplicas
helm template deeplx charts/deeplx \
  --set autoscaling.enabled=true \
  --set autoscaling.targetCPUUtilizationPercentage=null

# Chart 管理的环境变量不可由 extraEnvVars 覆盖
helm template deeplx charts/deeplx --set 'extraEnvVars[0].name=PORT' --set 'extraEnvVars[0].value=9999'
```
