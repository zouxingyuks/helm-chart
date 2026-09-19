# Subconverter Helm Chart

部署订阅转换后端 [subconverter](https://github.com/tindy2013/subconverter) 和前端
[sub-web](https://github.com/CareyWang/sub-web)。默认启用两个独立的 Deployment 和 Service。
完整配置入口为 [values.yaml](values.yaml)，资源定义为 [templates](templates/)。

## 安装与访问

以下命令在仓库根目录执行，需要 Helm 和可访问的 Kubernetes 集群；安装命令会写入集群。
Chart 没有外部 Chart 依赖。使用默认 release 名时：

```sh
helm install subconverter charts/subconverter
kubectl port-forward svc/subconverter-frontend 8080:80
```

浏览器访问 `http://localhost:8080`。后端 Service 为 `subconverter-backend:25500`，
前端 Service 为 `subconverter-frontend:80`；它们有独立 selector，不共享 Pod 网络。
更换 release 名或 name overrides 后，应以渲染结果中的 Service 名称为准。

`frontend.apiURL` 对应 `VUE_APP_SUBCONVERTER_DEFAULT_BACKEND`。留空时模板生成后端
Service 地址，而非 `localhost`。此处只说明 Chart 注入的环境变量；浏览器通常无法解析
集群 Service DNS，且具体镜像是否在启动时将变量写入前端静态配置需要运行验证。
对外使用应设置浏览器可访问的后端 URL，并检查浏览器请求、HTTPS 和跨域配置。

本机访问前后端时，可在两个终端分别运行上述前端转发和：

```sh
kubectl port-forward svc/subconverter-backend 25500:25500
curl http://localhost:25500/version
```

## 配置入口

以下为常用配置；完整默认值以 values.yaml 为准，不使用旧的顶层 `image`、`service`、
`replicaCount`、`resources` 作为后端配置。

| 配置 | 默认值或行为 |
| --- | --- |
| `backend.enabled` / `frontend.enabled` | 均为 `true`，独立控制组件 |
| `backend.replicaCount` / `frontend.replicaCount` | 均为 `1`，对应 HPA 启用时忽略 |
| `backend.image.repository` / `backend.image.tag` | `asdlokj1qpi23/subconverter` / `0.9.0` |
| `frontend.image.repository` / `frontend.image.tag` | `careywong/subweb` / `latest` |
| `backend.service.type` / `backend.service.port` | `ClusterIP` / `25500`；前端 Service 固定为 ClusterIP、80 |
| `backend.configMode` | `default`；其他模式见下方限制 |
| `backend.persistence.enabled` | `false`；启用后挂载 `/base/` |
| `backend.persistence.existingClaim` | 可指定已有 PVC，否则创建 PVC |
| `backend.persistence.storageClass` | 空值省略 storageClassName；`-` 显式设为空字符串 |
| `backend.resources` / `frontend.resources` | 分别配置 requests/limits |
| `backend.autoscaling` / `frontend.autoscaling` | 独立 HPA，默认关闭 |
| `backend.podDisruptionBudget` / `frontend.podDisruptionBudget` | 独立 PDB，默认关闭 |
| `serviceAccount` | 两个组件使用同一 ServiceAccount 配置 |
| `frontend.apiURL` | 空值生成集群内后端 Service URL |
| `frontend.env` | 额外容器环境变量，按原样注入 |

前端还支持 `projectUrl`、`botLink`、`useStorage`、`cacheTTL`、`backendRelease`、
`remoteConfig`、`advancedDoc`、`myurlsApi` 和 `configUploadApi`。对应的 `VUE_APP_*`
变量映射见 [deployment-frontend.yaml](templates/deployment-frontend.yaml)。环境变量注入
不等于已验证前端镜像支持运行时配置；普通容器变量也不必都使用 `VUE_APP_` 前缀。

两个组件的调度、探针和安全上下文分别在 `backend.*` / `frontend.*` 配置。
PDB 的 `minAvailable` 与 `maxUnavailable` 不应同时设置；使用后者时清除默认的前者。

## 常用部署方式

仅部署后端：

```sh
helm install subconverter charts/subconverter --set frontend.enabled=false
```

仅部署前端，连接已有的后端：

```sh
helm install subconverter charts/subconverter \
  --set backend.enabled=false \
  --set frontend.apiURL=https://api.example.com
```

其他配置写入自己创建的 values 文件，再通过 `-f your-values.yaml` 传入；仓库没有
`values-no-frontend.yaml`、`values-external-api.yaml` 或 `values-multi-domain.yaml` 示例文件。

## Ingress

默认关闭。`ingress.hosts` 非空时使用多域名模式并忽略 `ingress.hostname`；二者不是
模板强制互斥的配置。单域名模式在前端启用时指向前端，否则指向后端。

多域名模式为每个 host 创建一个 Ingress，支持各自的 annotations/TLS。
`serviceName` 默认指向前端；**仅将 servicePort 改为 25500 不会切换到后端 Service**。
以下配置适用于 release 名 `subconverter` 且未设置 name overrides：

```yaml
frontend:
  apiURL: https://api.example.com
ingress:
  enabled: true
  className: nginx
  hosts:
    - name: frontend.example.com
      serviceName: subconverter-frontend
      servicePort: 80
      tls:
        - secretName: frontend-tls
          hosts: [frontend.example.com]
    - name: api.example.com
      serviceName: subconverter-backend
      servicePort: 25500
      tls:
        - secretName: backend-tls
          hosts: [api.example.com]
```

TLS Secret、域名解析、Ingress Controller 和跨域策略由部署环境提供。
自定义 release 名或 overrides 时，相应调整 `serviceName`。组件禁用后也应移除指向它的路由。

## 配置文件与存储限制

`default` 使用后端镜像内置配置；`customImage` 表示选择内嵌配置的自定义后端镜像，
Chart 不负责构建镜像。持久化启用时挂载 `/base/`，镜像需兼容该目录被覆盖的行为。

当前实现存在键位不一致：后端 Deployment 使用 `backend.configMode`，而
[configmap.yaml](templates/configmap.yaml) 仍读取顶层 `configMode` / `configFiles`。
因此仅设置 `backend.configMode: configmap` 和 `backend.configFiles` 不会生成所需
ConfigMap，不能将其视为完整可用的配置方式。修复该行为前须同时核对 ConfigMap、挂载
和 checksum 渲染。`backend.configMode: configmap` 与
`backend.persistence.enabled: true` 同时启用会触发模板错误。

## 开发验证

本地命令不访问集群、不下载依赖：

```sh
helm lint charts/subconverter --strict
helm template subconverter charts/subconverter
helm template subconverter charts/subconverter --set frontend.enabled=false
helm template subconverter charts/subconverter --set backend.enabled=false
```

修改路由需核对 Ingress 的 Service 名和端口；修改配置需核对引用的 ConfigMap/PVC 是否
实际存在；修改组件开关需同时检查 Deployment、Service、HPA/PDB 和 Ingress。
本地渲染通过不能证明前端镜像的运行时变量处理、浏览器连通性或生产部署健康。
