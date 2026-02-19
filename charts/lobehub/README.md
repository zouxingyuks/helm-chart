# LobeHub Helm Chart

[LobeHub](https://github.com/lobehub/lobe-chat) 是一个现代化的开源 AI 聊天框架，支持多模型对话、插件扩展和知识库。本 Chart 用于在 Kubernetes 集群上部署 LobeHub 实例。

## 前置要求

- Kubernetes 1.20+
- Helm 3.2+
- （可选）Ingress Controller（如 ingress-nginx）

---

## 快速开始

### External 模式（推荐生产使用）

自行提供 PostgreSQL 和 Redis，Chart 只部署应用本身。

```bash
helm install lobehub charts/lobehub \
  --set auth.authSecret="$(openssl rand -hex 32)" \
  --set auth.keyVaultsSecret="$(openssl rand -hex 32)" \
  --set database.url="postgresql://lobechat:password@pg-host:5432/lobechat" \
  --set redis.url="redis://:password@redis-host:6379/0" \
  --set ingress.enabled=true \
  --set ingress.hostname="lobehub.example.com" \
  --set config.appUrl="https://lobehub.example.com"
```

### Internal 模式（快速体验）

让 Chart 自动部署内置 PostgreSQL 和 Redis 子 Chart。

> ⚠ Internal 模式不会自动注入连接串，仍需显式提供 `database.url` 和 `redis.url` 指向内置服务。

```bash
helm install lobehub charts/lobehub \
  --set auth.authSecret="$(openssl rand -hex 32)" \
  --set auth.keyVaultsSecret="$(openssl rand -hex 32)" \
  --set database.internal.enabled=true \
  --set database.url="postgresql://lobechat:pg-app-pass@lobehub-postgresql:5432/lobechat" \
  --set postgresql.auth.postgresPassword="pg-admin-pass" \
  --set postgresql.auth.password="pg-app-pass" \
  --set redis.internal.enabled=true \
  --set redis.url="redis://:redis-pass@lobehub-redis-master:6379/0" \
  --set ingress.enabled=true \
  --set ingress.hostname="lobehub.example.com" \
  --set config.appUrl="https://lobehub.example.com"
```

---

## 必需变量与 Secret 管理

### 必需字段

未使用 `auth.existingSecret` 时，以下两个字段**必须**提供：

| 字段 | 环境变量 | 说明 |
|------|----------|------|
| `auth.authSecret` | `AUTH_SECRET` | NextAuth 签名密钥，建议 32 字节随机值 |
| `auth.keyVaultsSecret` | `KEY_VAULTS_SECRET` | 密钥保险库加密密钥，建议 32 字节随机值 |

生成随机值：

```bash
openssl rand -hex 32
```

### existingSecret 模式（推荐）

将敏感值预先存入 Kubernetes Secret，Chart 直接引用，避免明文出现在命令行历史中。

**创建 Secret：**

```bash
kubectl create secret generic lobehub-secrets \
  --from-literal=AUTH_SECRET="your-auth-secret" \
  --from-literal=KEY_VAULTS_SECRET="your-key-vaults-secret" \
  --from-literal=ACCESS_CODE="optional-access-code"
```

Secret 中的 key 名称必须与环境变量名完全一致（`AUTH_SECRET`、`KEY_VAULTS_SECRET`、`ACCESS_CODE`）。

**引用 Secret：**

```bash
helm install lobehub charts/lobehub \
  --set auth.existingSecret="lobehub-secrets" \
  --set database.url="postgresql://..." \
  --set redis.url="redis://..." \
  --set ingress.enabled=true \
  --set ingress.hostname="lobehub.example.com"
```

设置 `auth.existingSecret` 后，`auth.authSecret`、`auth.keyVaultsSecret`、`auth.accessCode` 字段会被忽略，Chart 不再自动创建 Secret。

---

## Internal / External 模式与 URL 配置

数据库和 Redis 各有两种接入方式：

| 组件 | Internal 模式 | External 模式 |
|------|--------------|--------------|
| PostgreSQL | `database.internal.enabled=true` + `database.url` 指向内置服务 | `database.url="postgresql://..."` |
| Redis | `redis.internal.enabled=true` + `redis.url` 指向内置服务 | `redis.url="redis://..."` |

> ⚠ 无论 Internal 还是 External 模式，`database.url` 和 `redis.url` 都是必需的。Internal 模式下 Chart 不会自动拼接连接串，需用户显式提供指向内置服务的 URL。缺失时渲染会 `fail` 报错。

### Internal 模式配置示例

```yaml
database:
  internal:
    enabled: true
  url: "postgresql://lobechat:app-password@<release>-postgresql:5432/lobechat"

postgresql:
  auth:
    postgresPassword: "admin-password"   # 必填
    password: "app-password"             # 必填，需与 database.url 中的密码一致
    database: lobechat
    username: lobechat
  primary:
    persistence:
      size: 8Gi

redis:
  internal:
    enabled: true
  url: "redis://:redis-password@<release>-redis-master:6379/0"
```

### External 模式配置示例

```yaml
database:
  internal:
    enabled: false
  url: "postgresql://lobechat:password@pg-host:5432/lobechat"

redis:
  internal:
    enabled: false
  url: "redis://:password@redis-host:6379/0"
```

---

## 完整配置参考

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `replicaCount` | 副本数（`autoscaling.enabled=true` 时由 HPA 管理，此值被忽略） | `1` |
| `autoscaling.enabled` | 启用 HorizontalPodAutoscaler | `false` |
| `autoscaling.minReplicas` | HPA 最小副本数 | `1` |
| `autoscaling.maxReplicas` | HPA 最大副本数 | `100` |
| `autoscaling.targetCPUUtilizationPercentage` | CPU 目标利用率（%） | `80` |
| `autoscaling.targetMemoryUtilizationPercentage` | Memory 目标利用率（%），未设置则不渲染 | — |
| `image.repository` | 镜像仓库 | `lobehub/lobe-chat` |
| `image.tag` | 镜像标签，空则使用 appVersion | `""` |
| `image.pullPolicy` | 镜像拉取策略 | `IfNotPresent` |
| `service.type` | Service 类型 | `ClusterIP` |
| `service.port` | Service 端口 | `3210` |
| `ingress.enabled` | 启用 Ingress | `false` |
| `ingress.className` | Ingress Class | `nginx` |
| `ingress.hostname` | 访问域名（启用 Ingress 时必填） | `lobehub.example.com` |
| `ingress.tls` | TLS 配置列表 | `[]` |
| `auth.existingSecret` | 引用已有 Secret 名称 | `""` |
| `auth.authSecret` | NextAuth 签名密钥（必填） | `""` |
| `auth.keyVaultsSecret` | 密钥保险库加密密钥（必填） | `""` |
| `auth.accessCode` | 访问码，多个用逗号分隔 | `""` |
| `database.internal.enabled` | 启用内置 PostgreSQL | `false` |
| `database.url` | PostgreSQL 连接串（internal/external 均需提供） | `""` |
| `redis.internal.enabled` | 启用内置 Redis | `false` |
| `redis.url` | Redis 连接串（internal/external 均需提供） | `""` |
| `config.appUrl` | 应用公开 URL | `""` |
| `config.nextAuthUrl` | NextAuth URL，空则使用 appUrl | `""` |
| `s3.accessKeyId` | S3 Access Key ID | `""` |
| `s3.secretAccessKey` | S3 Secret Access Key | `""` |
| `s3.bucket` | S3 Bucket 名称 | `""` |
| `s3.endpoint` | S3 Endpoint URL | `""` |
| `s3.region` | S3 Region | `""` |
| `s3.publicDomain` | S3 公开访问域名 | `""` |
| `extraEnv` | 额外环境变量列表 | `[]` |
| `extraEnvFrom` | 额外 envFrom 引用列表 | `[]` |

完整配置项见 [values.yaml](./values.yaml)。

---

## 验证命令

```bash
# Lint 检查（需提供必填字段）
helm lint charts/lobehub \
  --set auth.authSecret=foo \
  --set auth.keyVaultsSecret=bar

# 渲染模板预览
helm template test charts/lobehub \
  --set auth.authSecret=foo \
  --set auth.keyVaultsSecret=bar

# 模拟安装（不实际部署）
helm install lobehub charts/lobehub \
  --dry-run --debug \
  --set auth.authSecret=foo \
  --set auth.keyVaultsSecret=bar
```

---

## 常见故障排查

### auth.authSecret 缺失

**错误信息：**

```text
Error: INSTALLATION FAILED: execution error at (lobehub/templates/deployment.yaml):
ERROR: auth.authSecret is required. LobeHub needs AUTH_SECRET for NextAuth signing.
Please provide it using --set auth.authSecret=<your-secret>
or use --set auth.existingSecret=<secret-name> to reference an existing Secret.
```

**修复方式（二选一）：**

```bash
# 方式 1：直接提供明文值
--set auth.authSecret="$(openssl rand -hex 32)"

# 方式 2：引用已有 Secret（Secret 中需包含 AUTH_SECRET key）
--set auth.existingSecret="lobehub-secrets"
```

---

### auth.keyVaultsSecret 缺失

**错误信息：**

```text
Error: INSTALLATION FAILED: execution error at (lobehub/templates/deployment.yaml):
ERROR: auth.keyVaultsSecret is required. LobeHub needs KEY_VAULTS_SECRET for encrypting key vaults.
Please provide it using --set auth.keyVaultsSecret=<your-secret>
or use --set auth.existingSecret=<secret-name> to reference an existing Secret.
```

**修复方式（二选一）：**

```bash
# 方式 1：直接提供明文值
--set auth.keyVaultsSecret="$(openssl rand -hex 32)"

# 方式 2：引用已有 Secret（Secret 中需包含 KEY_VAULTS_SECRET key）
--set auth.existingSecret="lobehub-secrets"
```

---

### ingress.enabled=true 但 hostname 为空

**错误信息：**

```text
Error: INSTALLATION FAILED: execution error at (lobehub/templates/deployment.yaml):
ERROR: ingress.hostname is required when ingress.enabled is true.
Please provide it using --set ingress.hostname=<your-domain>.
```

**修复方式：**

```bash
--set ingress.hostname="lobehub.example.com"
```

---

### database.internal.enabled=true 但缺少 database.url

**错误信息：**

```text
ERROR: database.url is required even when database.internal.enabled=true.
The internal PostgreSQL sub-chart does not auto-inject DATABASE_URL.
Please provide the connection string pointing to the internal service,
e.g. --set database.url="postgresql://lobechat:password@<release>-postgresql:5432/lobechat".
```

**修复方式：**

```bash
--set database.url="postgresql://lobechat:password@<release>-postgresql:5432/lobechat"
```

---

### redis.internal.enabled=true 但缺少 redis.url

**错误信息：**

```text
ERROR: redis.url is required even when redis.internal.enabled=true.
The internal Redis sub-chart does not auto-inject REDIS_URL.
Please provide the connection string pointing to the internal service,
e.g. --set redis.url="redis://:password@<release>-redis-master:6379/0".
```

**修复方式：**

```bash
--set redis.url="redis://:password@<release>-redis-master:6379/0"
```

---

### Pod 无法启动

```bash
# 查看 Pod 状态
kubectl get pods -l app.kubernetes.io/name=lobehub

# 查看事件
kubectl describe pod -l app.kubernetes.io/name=lobehub

# 查看日志
kubectl logs -l app.kubernetes.io/name=lobehub
```

---

## 卸载

```bash
helm uninstall lobehub
```

内置 PostgreSQL/Redis 的 PVC 不会自动删除，需手动清理：

```bash
kubectl get pvc
kubectl delete pvc <pvc-name>
```
