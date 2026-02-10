# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-10
**Commit:** 876bdea
**Branch:** feature/smartdns


## OVERVIEW

多 Chart Helm 仓库，托管 4 个独立 Kubernetes 应用 Chart（booklore、claude-relay-service、subconverter、smartdns），通过 Artifact Hub 发布至 `https://helm-chart.anubis.cafe`。技术栈：Helm 3 + Go Template + YAML + Bitnami 依赖。

## STRUCTURE

```
helm-chart/
├── charts/
│   ├── booklore/                # 数字图书馆 (MariaDB, 多PVC, Schema验证)
│   ├── claude-relay-service/    # Claude API 中继 (Redis, Init Container)
│   ├── subconverter/            # 订阅转换 (双容器: backend+frontend)
│   └── smartdns/                # DNS 服务器 (hostNetwork, ConfigMap)
├── index.yaml                   # Helm 仓库索引 (helm repo index 生成)
├── artifacthub-repo.yml         # Artifact Hub 元数据
├── *.tgz                        # 已打包的 Chart 归档
├── .claude/                     # Claude Code 配置 (skills, commands, hooks)
└── .serena/                     # Serena LSP 配置 (bash, yaml)
```

## WHERE TO LOOK

| 任务 | 位置 | 备注 |
|------|------|------|
| 新增 Chart | `charts/<name>/` | 参照 smartdns 最简结构 |
| 修改模板 | `charts/<name>/templates/` | 改完跑 `helm lint` + `helm template` |
| 更新依赖 | `charts/<name>/Chart.yaml` | 改版本后 `helm dependency update` |
| 发布 Chart | 根目录 | `helm package` → `helm repo index .` |
| 值验证 | `charts/booklore/values.schema.json` | 仅 booklore 有 JSON Schema |
| 变更日志 | `charts/{booklore,subconverter}/CHANGELOG.md` | Keep a Changelog 格式 |

## CONVENTIONS

### Chart 间共享模式

- **_helpers.tpl 标准函数**：每个 Chart 必须定义 `{name}.name`、`{name}.fullname`、`{name}.chart`、`{name}.labels`、`{name}.selectorLabels`、`{name}.serviceAccountName`
- **Kubernetes 标签**：统一使用 `app.kubernetes.io/*` 标签体系
- **apiVersion**：所有 Chart 使用 `apiVersion: v2`
- **类型**：全部为 `type: application`（无 library chart）
- **依赖源**：Bitnami (`https://charts.bitnami.com/bitnami`)
- **版本锁定**：`~X.Y.0` 格式（允许补丁更新，锁定次版本）

### 模板技术

- **fail 验证**：必需字段和互斥配置用 `{{- fail "..." }}` 提前报错
- **checksum 注解**：ConfigMap/Secret 变更触发 Pod 重启（`sha256sum`）
- **nindent 缩进**：`toYaml . | nindent N` 处理嵌套结构
- **条件渲染**：`{{- if not .Values.autoscaling.enabled }}replicas:{{- end }}`

### 命名规范

- Chart 名：kebab-case（`claude-relay-service`）
- 模板文件：小写（`deployment.yaml`、`pvc-data.yaml`）
- 多组件：后缀区分（`deployment-backend.yaml`、`deployment-frontend.yaml`）
- Values 键：camelCase（`replicaCount`、`imagePullSecrets`）

### 文档规范

- README 使用中文（面向中文用户）
- 每个 Chart 必须有 README.md
- CHANGELOG.md 遵循 Keep a Changelog

## ANTI-PATTERNS (THIS PROJECT)

- **禁止默认密码**：敏感字段（数据库密码、JWT Secret）不设默认值，必须用户提供
- **禁止直接提交 charts/*.tgz 依赖包**：`.gitignore` 已排除，仅提交 Chart.lock
- **禁止 persistence + configmap 同时启用**：subconverter 中互斥配置会 fail
- **PDB 互斥**：`minAvailable` 和 `maxUnavailable` 不可同时设置

## COMMANDS

```bash
# 验证
helm lint charts/<name>
helm template test charts/<name>

# 依赖
helm dependency update charts/<name>
helm dependency list charts/<name>

# 打包发布
helm package charts/<name>
helm repo index . --url https://helm-chart.anubis.cafe

# 测试安装
helm install test charts/<name> --dry-run --debug
```

## RULES

- Always use Chinese answer.
- Always use LSP.
- Always use SKILL firtst.
Always use:
- **serena** - Semantic code retrieval and editing tools
- **context7** - Up-to-date documentation on third-party code
- **sequential thinking** - For any decision-making

## NOTES

- `index.yaml` 由 `helm repo index` 自动生成，手动编辑会被覆盖
- 根目录 `*.tgz` 是已发布的 Chart 包，被 `index.yaml` 引用
- `.serena/project.yml` 配置了 bash + yaml 语言服务器
- 当前仅 booklore 有 `values.schema.json`，其他 Chart 可参照添加
- smartdns Chart 尚未发布到 index.yaml（新增中）
