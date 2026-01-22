# BookLore Helm Chart

[BookLore](https://booklore.org) 是一个功能强大的自托管数字图书馆应用,支持多用户、智能书架、自动元数据管理、Kobo/KOReader 同步、OPDS 支持等功能。

## 简介

本 Chart 为 BookLore 提供了生产就绪的 Kubernetes 部署方案,包含:

- **一键部署**: 简单的命令即可完成 BookLore 及其依赖的部署
- **灵活配置**: 通过 values.yaml 统一管理所有配置项
- **双数据库支持**: 内置 MariaDB 或外部数据库
- **持久化存储**: 自动配置��据、书籍和 BookDrop 存储
- **生产级特性**: 健康检查、资源限制、自动扩缩容等

## 前置要求

- Kubernetes 1.20+
- Helm 3.5+ (支持 schema validation)
- PV 动态供应提供程序 (StorageClass)

## 依赖管理

本 Chart 使用 Helm 官方推荐的依赖管理方式：
- `Chart.yaml` 声明依赖关系和版本范围
- `Chart.lock` 锁定精确版本
- `helm dependency update` 自动下载依赖

### 安装前准备

如果您从源码安装，请先更新依赖：

```bash
cd charts/booklore
helm dependency update
```

### 当前依赖

| 依赖 | 版本范围 | 锁定版本 | 用途 |
|-----|---------|---------|------|
| common | ~2.31.0 | 2.31.4 | Bitnami 公共库 |
| mariadb | ~23.2.0 | 23.2.4 | MariaDB 数据库（可选） |

**版本范围说明**：
- `~2.31.0` 表示允许 >=2.31.0 且 < 2.32.0 的版本（允许补丁更新）
- `~23.2.0` 表示允许 >=23.2.0 且 < 23.3.0 的版本（允许补丁更新）

这种版本管理方式确保了：
- 锁定次版本，避免破坏性变更
- 允许补丁更新，获取安全修复和 bug 修复
- Chart.lock 记录实际使用的精确版本

## 安装

### 快速开始 (使用内置数据库)

```bash
# 添加 Helm 仓库
helm repo add booklore https://your-helm-repo-url
helm repo update

# 安装 BookLore
helm install my-library booklore/booklore
```

### 使用外部数据库

```bash
helm install my-library booklore/booklore \
  --set mariadb.enabled=false \
  --set externalDatabase.host=external-mariadb.example.com \
  --set externalDatabase.password=your-secret-password \
  --set externalDatabase.user=booklore \
  --set externalDatabase.database=booklore
```

### 启用 Ingress

```bash
helm install my-library booklore/booklore \
  --set ingress.enabled=true \
  --set ingress.hostname=library.example.com
```

### 使用内置 MariaDB 数据库

**重要**: 出于安全考虑,BookLore Chart **要求您在安装时提供 MariaDB 密码**:

```bash
# 使用 --set 提供密码
helm install my-library booklore/booklore \
  --set mariadb.auth.rootPassword=YOUR_ROOT_PASSWORD \
  --set mariadb.auth.password=YOUR_PASSWORD

# 或使用 --set-file 从文件读取(推荐,避免密码出现在 shell 历史中)
helm install my-library booklore/booklore \
  --set-file mariadb.auth.rootPassword=./root-password.txt \
  --set-file mariadb.auth.password=./password.txt

# 或使用现有 Secret
helm install my-library booklore/booklore \
  --set mariadb.auth.existingSecret=my-mariadb-secret
```

## 配置验证 (Schema Validation)

BookLore Chart 提供了 `values.schema.json` 来验证配置参数的正确性。Helm 会在安装和升级时自动验证您的配置。

### 验证内容

- **必填字段检查**: 确保 image.repository 等关键字段已提供
- **类型验证**: 验证参数类型 (string, number, boolean 等)
- **枚举值验证**: 如 image.pullPolicy (Always/IfNotPresent/Never)、service.type 等
- **数值范围验证**: 如端口号 (1-65535)、副本数量等
- **格式验证**: 确保配置值符合预期格式

### 验证时机

Helm 会在以下时机自动验证:
- `helm install` - 安装时
- `helm upgrade` - 升级时
- `helm lint` - Lint 时
- `helm template` - 渲染模板时

### 常见验证错误

#### 错误 1: MariaDB 密码未提供

```
Error: values don't meet the specifications of the schema(s) in the following chart(s):
booklore:
- mariadb.auth.password is required when mariadb.enabled is true
```

**解决方案**: 使用 `--set` �� `--set-file` 提供密码:

```bash
helm install my-library booklore/booklore \
  --set mariadb.auth.password=YOUR_PASSWORD \
  --set mariadb.auth.rootPassword=YOUR_ROOT_PASSWORD
```

#### 错误 2: 无效的 Service 类型

```
Error: - at '/service/type': value must be one of 'ClusterIP', 'NodePort', 'LoadBalancer', 'ExternalName'
```

**解决方案**: 使用有效的 Service 类型:

```bash
helm install my-library booklore/booklore \
  --set service.type=ClusterIP  # 或 NodePort, LoadBalancer
```

#### 错误 3: 端口号超出范围

```
Error: - at '/service/port': maximum: got 70,000, want 65,535
```

**解决方案**: 使用有效的端口号 (1-65535):

```bash
helm install my-library booklore/booklore \
  --set service.port=6060
```

### 手动验证

您可以在安装前手动验证配置:

```bash
# 验证默认配置
helm lint charts/booklore

# 验证自定义配置文件
helm lint charts/booklore -f my-values.yaml

# 验证命令行参数
helm lint charts/booklore \
  --set mariadb.auth.password=test \
  --set mariadb.auth.rootPassword=test
```

### 禁用验证 (不推荐)

如果需要临时禁用验证 (不推荐,除非您完全了解后果):

```bash
helm install my-library booklore/booklore \
  --set mariadb.auth.password=YOUR_PASSWORD \
  --disable-openapi-validation
```

**警告**: 禁用验证可能导致配置错误或安装失败。

## 安全配置

### 密码要求

BookLore Chart 遵循安全最佳实践,**不提供默认密码**。您必须在安装时提供 MariaDB 密码,否则安装会失败并提示:

```
Error: mariadb.auth.password is required when mariadb.enabled is true.
Please provide it using --set mariadb.auth.password=<your-password>
```

### 容器安全上下文

BookLore Chart 默认启用以下安全配置:

- `allowPrivilegeEscalation: false` - 防止权限提升
- `capabilities.drop[ALL]` - 移除所有特权 capabilities

这些设置降低了容器被攻破时的风险。

如果您的 BookLore 镜像支持非 root 运行(UID 1000),可以在 values.yaml 中启用额外的安全配置:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
```

**注意**: BookLore 使用 nginx,监听端口 6060(>1024,不需要特权端口)。如果启用 `runAsNonRoot` 后应用无法正常工作,请保持注释状态。

### PodDisruptionBudget

如果启用 PodDisruptionBudget,必须设置 `minAvailable` 或 `maxUnavailable` 之一:

```bash
# 正确: 设置 minAvailable
helm install my-library booklore/booklore \
  --set podDisruptionBudget.enabled=true \
  --set podDisruptionBudget.minAvailable=1 \
  --set mariadb.auth.password=YOUR_PASSWORD

# 正确: 设置 maxUnavailable
helm install my-library booklore/booklore \
  --set podDisruptionBudget.enabled=true \
  --set podDisruptionBudget.maxUnavailable=1 \
  --set mariadb.auth.password=YOUR_PASSWORD

# 错误: 未设置任何值会失败
helm install my-library booklore/booklore \
  --set podDisruptionBudget.enabled=true \
  --set mariadb.auth.password=YOUR_PASSWORD
# Error: podDisruptionBudget: Either minAvailable or maxUnavailable must be set...
```

## 配置参数

### 全局配置

| 参数 | 描述 | 默认值 |
|-----|------|--------|
| `global.imagePullSecrets` | 全局镜像拉取密钥 | `[]` |
| `replicaCount` | 副本数量 | `1` |

### 镜像配置

| 参数 | 描述 | 默认值 |
|-----|------|--------|
| `image.repository` | 镜像仓库 | `ghcr.io/booklore-app/booklore` |
| `image.pullPolicy` | 镜像拉取策略 | `IfNotPresent` |
| `image.tag` | 镜像标签 | `""` (使用 appVersion) |

### 持久化存储

| 参数 | 描述 | 默认值 |
|-----|------|--------|
| `persistence.data.enabled` | 启用数据持久化 | `true` |
| `persistence.data.size` | 数据存储大小 | `10Gi` |
| `persistence.books.enabled` | 启用书籍持久化 | `true` |
| `persistence.books.size` | 书籍存储大小 | `20Gi` |
| `persistence.bookdrop.enabled` | 启用 BookDrop | `false` |
| `persistence.bookdrop.size` | BookDrop 存储大小 | `5Gi` |

### 数据库配置

**内置 MariaDB:**

| 参数 | 描述 | 默认值 |
|-----|------|--------|
| `mariadb.enabled` | 启用内置 MariaDB | `true` |
| `mariadb.auth.rootPassword` | Root 密码 | `change-me` |
| `mariadb.auth.password` | 数据库密码 | `change-me` |
| `mariadb.primary.persistence.size` | 数据库存储大小 | `8Gi` |

**外部数据库:**

| 参数 | 描述 | 默认值 |
|-----|------|--------|
| `externalDatabase.host` | 数据库主机 | `""` |
| `externalDatabase.port` | 数据库端口 | `3306` |
| `externalDatabase.user` | 数据库用户 | `booklore` |
| `externalDatabase.password` | 数据库密码 | `""` |
| `externalDatabase.database` | 数据库名称 | `booklore` |

### 资源配置

| 参数 | 描述 | 默认值 |
|-----|------|--------|
| `resources.limits.cpu` | CPU 限制 | `1000m` |
| `resources.limits.memory` | 内存限制 | `1Gi` |
| `resources.requests.cpu` | CPU 请求 | `500m` |
| `resources.requests.memory` | 内存请求 | `512Mi` |

### 健康检查

| 参数 | 描述 | 默认值 |
|-----|------|--------|
| `healthCheck.enabled` | 启用健康检查 | `true` |
| `healthCheck.path` | 健康检查路径 | `/api/v1/healthcheck` |
| `healthCheck.initialDelaySeconds` | 初始延迟 | `60` |

### Ingress 配置

| 参数 | 描述 | 默认值 |
|-----|------|--------|
| `ingress.enabled` | 启用 Ingress | `false` |
| `ingress.className` | Ingress 类名 | `"nginx"` |
| `ingress.hostname` | 主机名 | `"booklore.example.com"` |
| `ingress.tls.enabled` | 启用 TLS | `false` |

## 升级

```bash
# 升级到新版本
helm upgrade my-library booklore/booklore

# 升级时修改配置
helm upgrade my-library booklore/booklore \
  --set persistence.books.size=50Gi
```

## 卸载

```bash
# 卸载 BookLore (保留 PVC 数据)
helm uninstall my-library

# 卸载 BookLore 并删除所有数据
helm uninstall my-library
kubectl delete pvc -l app.kubernetes.io/instance=my-library
```

## 故障排查

### Pod 无法启动

```bash
# 查看 Pod 状态
kubectl get pods -l app.kubernetes.io/name=booklore

# 查看 Pod 日志
kubectl logs -l app.kubernetes.io/name=booklore

# 查看 Pod 事件
kubectl describe pod -l app.kubernetes.io/name=booklore
```

### 数据库连接失败

```bash
# 检查数据库密码
kubectl get secret -l app.kubernetes.io/name=booklore

# 检查数据库连接
kubectl exec -it my-library-booklore-0 -- env | grep DATABASE
```

**重要**: 如果遇到数据库认证错误 ("Access denied for user 'root'"),需要在 `values.yaml` 中添加 Spring Boot 数据源环境变量:

```yaml
extraEnv:
  - name: SPRING_DATASOURCE_USERNAME
    value: "booklore"  # 应该与 mariadb.auth.username 一致
  - name: SPRING_DATASOURCE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: my-library-mariadb  # 替换为实际的 release 名称
        key: mariadb-password
```

### 容器端口架构说明

BookLore 容器内部使用双层架构:
- **nginx** 监听 **6060** 端口 (对外入口)
- **Java 应用** 监听 **8080** 端口 (内部)
- nginx 将 6060 端口的请求反向代理到 8080

因此:
- `service.port` 默认为 **6060** (连接到 nginx)
- `containerPort` 设置为 **6060** (声明容器暴露的端口)
- `env.BOOKLORE_PORT` 应设置为 **"6060"** (配置应用监听端口)

### 持久化存储问题

```bash
# 查看 PVC 状态
kubectl get pvc -l app.kubernetes.io/name=booklore

# 查看 PV 绑定情况
kubectl get pv
```

## 更多信息

- [BookLore 官方文档](https://booklore.org/docs)
- [BookLore GitHub](https://github.com/booklore-app/booklore)
- [BookLore 社区讨论](https://github.com/booklore-app/booklore/discussions)

## 许可证

BookLore 使用 [GPL-3.0](https://github.com/booklore-app/booklore/blob/develop/LICENSE) 许可证。

---

**注意**: 本 Chart 由社区维护,不是 BookLore 官方项目的一部分。
