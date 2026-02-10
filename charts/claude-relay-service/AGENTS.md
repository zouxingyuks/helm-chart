# CLAUDE-RELAY-SERVICE CHART

Claude API 中继服务 Chart（v0.1.0），带 Redis 依赖和 Init Container 启动依赖。

## WHERE TO LOOK

| 任务 | 文件 | 备注 |
|------|------|------|
| 部署逻辑 | `templates/deployment.yaml` | Init Container 等待 Redis |
| 持久化 | `templates/pvc-data.yaml` + `pvc-logs.yaml` | 双 PVC |
| 密钥管理 | `templates/secret.yaml` | env 字段直接映射为 Secret data |
| PVC 名称 | `templates/_helpers.tpl` | `existingClaim` 覆盖逻辑 |
| Redis 配置 | `values.yaml` → `redis.*` | Bitnami Redis 子 Chart |

## UNIQUE PATTERNS

### Init Container 启动依赖

当 `redis.enabled` + `startup.waitForRedis.enabled` 时，部署包含 `wait-for-redis` Init Container，用 `nc -z` 轮询 Redis master 端口直到就绪。

### checksum 双注解

同时计算 ConfigMap 和 Secret 的 sha256sum，任一变更触发 Pod 重启：
```yaml
checksum/config: {{ include ... "/configmap.yaml" | sha256sum }}
checksum/secret: {{ include ... "/secret.yaml" | sha256sum }}
```

### PVC Helper 函数

`_helpers.tpl` 定义了 `dataPersistentVolumeClaimName` 和 `logsPersistentVolumeClaimName`，支持 `existingClaim` 覆盖。

### 环境变量驱动

所有应用配置通过 `env.*` 传入（JWT_SECRET、ENCRYPTION_KEY、ADMIN_USERNAME 等），映射为 Kubernetes Secret。

## DEPENDENCIES

| 依赖 | 版本范围 | 用途 |
|------|---------|------|
| common (Bitnami) | 2.x.x | 公共模板库 |
| redis (Bitnami) | 23.x.x | 可选内置 Redis |

**注意**：版本范围比其他 Chart 更宽松（`2.x.x` vs `~2.31.0`），已有打包的 tgz 在 `charts/` 子目录。

## ANTI-PATTERNS

- JWT_SECRET / ENCRYPTION_KEY 设默认值 → 安全风险
- 禁用 waitForRedis 但启用 Redis → 应用可能启动失败
