# BOOKLORE CHART

数字图书馆应用 Chart（v0.0.1），最复杂的 Chart——唯一带 JSON Schema 验证。

## WHERE TO LOOK

| 任务 | 文件 | 备注 |
|------|------|------|
| 修改部署逻辑 | `templates/deployment.yaml` | 含 MariaDB 密码 fail 验证 |
| 数据库切换 | `templates/_helpers.tpl` | `booklore.mariadb.host` 内外切换 |
| 添加配置项 | `values.yaml` + `values.schema.json` | 两处必须同步更新 |
| 存储变更 | `templates/pvc-*.yaml` | 三个 PVC：data、books、bookdrop |
| 环境配置示例 | `values-minimal.yaml` / `values-production.yaml` | 不同场景参考 |

## UNIQUE PATTERNS

### Schema 验证（仅此 Chart 有）

`values.schema.json` 在 `helm install/upgrade/lint/template` 时自动校验。新增 values 键时**必须同步更新 schema**，否则用户传入会被静默忽略或报错。

### 自定义 Helper 函数

- `booklore.mariadb.host`：`mariadb.enabled` → 内置地址；否则 → `externalDatabase.host`
- `booklore.mariadb.secretName` / `secretKey`：支持 `existingSecret` 覆盖
- `booklore.externalDatabase.secretName` / `secretKey`：外部数据库 Secret 处理

### 多 PVC 持久化

三个独立 PVC（`pvc-data.yaml`、`pvc-books.yaml`、`pvc-bookdrop.yaml`），各自可独立启用/禁用和调整大小。bookdrop 默认禁用。

### fail 验证链

```
mariadb.enabled + 无密码 → fail
PDB enabled + 无 minAvailable 且无 maxUnavailable → fail
PDB minAvailable + maxUnavailable 同时设置 → fail
```

## DEPENDENCIES

| 依赖 | 版本范围 | 用途 |
|------|---------|------|
| common (Bitnami) | ~2.31.0 | 公共模板库 |
| mariadb (Bitnami) | ~23.2.0 | 可选内置数据库 |

依赖更新：`helm dependency update charts/booklore`

## ANTI-PATTERNS

- 改 values.yaml 不改 schema → 验证断裂
- MariaDB 密码设默认值 → 违反安全约定
- bookdrop PVC 默认启用 → 浪费存储（保持 `false`）
