---
name: update-helm-index
description: 自动化 Helm Chart 仓库索引更新流程。打包 Chart,重新生成 index.yaml,验证包完整性,创建 Git 提交。使用当提及 'helm index'、'更新索引'、'发布 chart'、'tgz 包' 或 'artifact hub' 时。
---

# 更新 Helm 索引

## 前置要求

运行本 skill 前,请确保满足以下条件:

### 环境要求
- Helm >= 3.0.0
- Git 已配置用户信息
- 对当前目录有写权限
- 网络连接正常(如需推送到远程)

### 快速检查

运行环境检查脚本:
```bash
bash .claude/skills/update-helm-index/scripts/check-env.sh
```

或手动检查:
```bash
# 检查 Helm 版本
helm version

# 检查 Git 配置
git config user.name && git config user.email

# 检查目录权限
test -w . && echo "✓ 有写权限" || echo "✗ 无写权限"
```

---

## 快速开始

### 方式 1: 使用自动化脚本 (推荐)

```bash
# 预览模式(首次使用推荐)
bash .claude/skills/update-helm-index/scripts/update-index.sh --dry-run

# 执行更新
bash .claude/skills/update-helm-index/scripts/update-index.sh

# 自动推送到远程
bash .claude/skills/update-helm-index/scripts/update-index.sh --auto-push
```

详细说明请查看 [scripts/README.md](scripts/README.md)

---

### 方式 2: 手动执行步骤

当 Chart 版本更新后,执行以下命令更新 Helm 仓库索引:

```bash
# 1. 打包 Chart
helm package charts/*

# 2. 重新生成索引
helm repo index . --url https://helm-chart.anubis.cafe

# 3. 验证更新
grep -A 10 "chart-name:" index.yaml

# 4. 提交到 Git
git add *.tgz index.yaml
git commit -m "chore: 更新 [chart-name] 到 v[version] 并刷新 Helm 索引"
```

## 何时使用

在以下场景中使用此 skill:

### 1. Chart 版本更新

- Chart.yaml 版本号变化
- 新的 .tgz 包已创建
- 旧版本 .tgz 包被删除

**触发词:**

- "更新 Helm 索引"
- "发布新版本 chart"
- "更新 helm index"
- "打包 chart"
- "发布到 artifact hub"

### 2. 索引文件过期

- index.yaml 版本与实际 .tgz 不匹配
- 用户报告无法安装最新版本
- Artifact Hub 显示版本过期

### 3. 仓库维护

- 定期检查和更新 Helm 仓库
- 验证仓库完整性
- 同步 chart 包和索引

## 核心步骤

1. **验证 Chart 打包状态** - 检查现有 .tgz 文件
2. **打包 Chart** - 使用 `helm package` 生成 .tgz 包
3. **重新生成索引** - 使用 `helm repo index` 更新 index.yaml
4. **验证索引更新** - 确认版本号、URL 和 digest 正确
5. **Git 提交** - 提交 .tgz 包和 index.yaml
6. **推送到远程** - 可选,推送更新到 Git 仓库

## 关键参数

- **URL**: `https://helm-chart.anubis.cafe` (本项目仓库地址)
- **索引文件**: `index.yaml`
- **Chart 包**: `*.tgz` 文件

## 详细文档

- [workflows.md](workflows.md) - 完整的 6 步执行流程、常见场景和详细说明
- [troubleshooting.md](troubleshooting.md) - 故障排除指南、验证命令和测试方法

## 记住

- [ ] 每次发布新版本都要更新索引
- [ ] 索引文件必须与实际 .tgz 包一致
- [ ] 使用清晰的 Git 提交信息
- [ ] 推送前验证更新结果
- [ ] Artifact Hub 会自动同步更新