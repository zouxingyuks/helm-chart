# Update Helm Index - 详细工作流程

本文档提供更新 Helm Chart 仓库索引的详细执行步骤、场景说明和最佳实践。

## 使用自动化脚本

本 skill 提供了自动化脚本来简化操作流程:

### 1. 环境检查脚本
```bash
bash .claude/skills/update-helm-index/scripts/check-env.sh
```

验证所有前置条件,包括 Helm 版本、Git 配置、目录权限等。

### 2. 一键更新脚本
```bash
# 预览模式(推荐首次使用)
bash .claude/skills/update-helm-index/scripts/update-index.sh --dry-run

# 执行更新
bash .claude/skills/update-helm-index/scripts/update-index.sh

# 自动推送到远程
bash .claude/skills/update-helm-index/scripts/update-index.sh --auto-push
```

自动执行打包、索引更新、验证和 Git 提交的完整流程。

### 3. 健康检查脚本
```bash
bash .claude/skills/update-helm-index/scripts/health-check.sh
```

定期验证仓库完整性,检查 digest、YAML 语法等。

详细脚本说明请查看 [scripts/README.md](scripts/README.md)

---

## 完整执行流程

### 步骤 1: 验证 Chart 打包状态

**使用脚本快速检查:**
```bash
bash .claude/skills/update-helm-index/scripts/check-env.sh
```

或手动检查当前目录中的所有 .tgz 包文件:

```bash
ls -lh *.tgz
```

**预期输出:**

```
-rw-r--r-- 1 user user 15K Jan 10 10:30 subconverter-0.2.0.tgz
-rw-r--r-- 1 user user 12K Jan  8 15:20 claude-relay-service-1.0.1.tgz
```

**验证要点:**

- ✅ 确认新版本包是否存在
- ✅ 检查文件大小和修改时间
- ✅ 识别需要删除的旧版本包

---

### 步骤 2: 打包 Chart

如果 Chart 源码有更新(Chart.yaml、模板、values等),需要先打包:

```bash
# 打包所有 Chart
helm package charts/*

# 或者打包指定的 Chart
helm package charts/subconverter
helm package charts/claude-relay-service
```

**作用:**

- 将 Chart 目录打包成 .tgz 文件
- 自动验证 Chart 结构
- 生成可发布的压缩包

**输出示例:**

```
Successfully packaged chart and saved it to:
subconverter-0.2.0.tgz
```

**验证打包结果:**

```bash
# 验证包格式
helm lint subconverter-0.2.0.tgz

# 查看包内容
tar -tzf subconverter-0.2.0.tgz | head -20
```

**预期输出:**

```
subconverter/Chart.yaml
subconverter/values.yaml
subconverter/templates/deployment.yaml
subconverter/templates/service.yaml
...
```

---

### 步骤 3: 重新生成 Helm 仓库索引

使用 Helm CLI 重新生成 index.yaml:

```bash
helm repo index . --url https://helm-chart.anubis.cafe
```

**作用:**

- 扫描目录中的所有 .tgz 文件
- 自动计算每个包的 SHA256 digest
- 更新 index.yaml 中的所有 chart 条目
- 确保 index.yaml 与实际 .tgz 文件一致

**参数说明:**

- `.` - 当前目录(Helm 仓库根目录)
- `--url` - Helm 仓库的公共访问 URL
    - 本项目使用: `https://helm-chart.anubis.cafe`
    - 根据实际部署环境调整

**输出示例:**

```
Index file created successfully
```

---

### 步骤 4: 验证索引更新

检查 index.yaml 是否正确更新:

```bash
# 查看特定 chart 的索引
grep -A 20 "subconverter:" index.yaml
```

**预期输出:**

```yaml
subconverter:
  - name: subconverter
    created: 2025-01-10T10:30:00Z
    description: A subscription converter
    digest: a1b2c3d4e5f6...
    home: https://github.com/example/subconverter
    icon: https://example.com/icon.png
    urls:
      - https://helm-chart.anubis.cafe/subconverter-0.2.0.tgz
    version: 0.2.0
    annotations:
      artifacthub.io/changes: |
        - Update to v0.2.0
        - Fix bug in ...
```

**验证清单:**

- [ ] 版本号正确更新
- [ ] URL 指向正确的 .tgz 文件
- [ ] 时间戳为最新
- [ ] digest 值已重新计算
- [ ] 描述和元数据正确

---

### 步骤 5: Git 提交更新

将更新后的文件提交到 Git:

```bash
# 添加更新的文件
git add *.tgz index.yaml

# 检查状态
git status

# 提交变更
git commit -m "chore: 更新 subconverter 到 v0.2.0 并刷新 Helm 索引

- 更新 subconverter Chart 从 0.1.0 到 0.2.0
- 添加新功能: 支持多订阅源
- 修复: 修复配置文件解析错误
- 重新生成 index.yaml 以反映最新的 .tgz 包"
```

**提交文件包括:**

- 新的 .tgz 包文件
- 更新后的 index.yaml
- 可能包含其他已修改的 .tgz 文件

**提交信息模板:**

```
chore: 更新 [chart-name] 到 v[version] 并刷新 Helm 索引

- 更新 [chart-name] Chart 从 [old-version] 到 [new-version]
- [主要变更说明]
- 重新生成 index.yaml 以反映最新的 .tgz 包
```

---

### 步骤 6: 推送到远程仓库 (可选)

```bash
git push
```

**⚠️ 注意:** 此步骤需谨慎,确认无误后再推送

---

## 常见场景

### 场景 1: 发布新版本 Chart

**情况:** 开发了新版本的功能,需要发布

**操作流程:**

1. 更新 `charts/subconverter/Chart.yaml` 中的版本号
   ```yaml
   version: 0.2.0  # 从 0.1.0 更新
   ```
2. 更新 Chart 模板、values 等文件
3. 打包新版本:
   ```bash
   helm package charts/subconverter
   ```
4. 运行完整流程更新索引
5. 推送到 Git 仓库

**验证:**

```bash
helm search repo anubis/subconverter --versions
```

---

### 场景 2: 索引过期检查

**情况:** 定期维护,检查索引是否最新

**操作流程:**

1. 对比 index.yaml 中的版本与实际 .tgz 文件
   ```bash
   # 列出实际包
   ls *.tgz | sed 's/.*-//' | sed 's/.tgz//'

   # 列出索引中的版本
   grep -A 3 "version:" index.yaml | grep "version:"
   ```
2. 如有不匹配,运行此 skill 的完整流程
3. 验证更新结果

---

### 场景 3: 多 Chart 更新

**情况:** 同时更新多个 Chart

**操作流程:**

1. 更新各个 Chart 的 `Chart.yaml` 和相关文件
2. 打包所有更新的 Chart:
   ```bash
   helm package charts/*
   ```
3. 运行完整流程更新所有索引:
   ```bash
   helm repo index . --url https://helm-chart.anubis.cafe
   ```
4. 一次性提交所有变更:
   ```bash
   git add *.tgz index.yaml
   git commit -m "chore: 批量更新 Charts 并刷新索引

   - 更新 subconverter 到 0.2.0
   - 更新 claude-relay-service 到 1.1.0
   - 重新生成 index.yaml"
   ```

---

### 场景 4: 删除旧版本

**情况:** 清理不再支持的旧版本

**操作流程:**

1. 删除旧的 .tgz 包:
   ```bash
   rm subconverter-0.1.0.tgz
   ```
2. 删除旧的 index.yaml:
   ```bash
   rm index.yaml
   ```
3. 重新生成索引(只包含现有的 .tgz):
   ```bash
   helm repo index . --url https://helm-chart.anubis.cafe
   ```
4. 提交变更:
   ```bash
   git add index.yaml
   git commit -m "chore: 移除 subconverter v0.1.0,仅保留最新版本"
   ```

---

### 场景 5: 修复索引 URL

**情况:** 仓库 URL 变更或配置错误

**操作流程:**

1. 删除旧的 index.yaml:
   ```bash
   rm index.yaml
   ```
2. 使用正确的 URL 重新生成:
   ```bash
   helm repo index . --url https://helm-chart.anubis.cafe
   ```
3. 验证 URL 正确:
   ```bash
   grep "urls:" index.yaml
   ```
4. 提交变更

---

## 多环境处理

### 开发环境

```bash
# 使用开发环境 URL
helm repo index . --url http://localhost:8080
```

### 生产环境

```bash
# 使用生产环境 URL
helm repo index . --url https://helm-chart.anubis.cafe
```

### 测试环境

```bash
# 使用测试环境 URL
helm repo index . --url https://test-helm.example.com
```

---

## 批量操作技巧

### 打包所有 Charts

```bash
# 方法 1: 打包 charts 目录下的所有 Chart
helm package charts/*

# 方法 2: 查找所有 Chart 目录并打包
find charts -name "Chart.yaml" -exec dirname {} \; | xargs -I {} helm package {}
```

### 验证所有包

```bash
# 验证所有 .tgz 包
for file in *.tgz; do
  echo "Validating $file..."
  helm lint "$file"
done
```

### 查看索引摘要

```bash
# 查看索引中的所有 Chart
grep "^  [a-z-]*:$" index.yaml | sed 's/://g'

# 查看每个 Chart 的版本数量
grep "^  [a-z-]*:$" -A 100 index.yaml | grep "version:" | wc -l
```

---

## 性能优化

### 大型仓库优化

对于包含大量 Chart 的仓库:

```bash
# 仅更新变更的包
helm repo index . --url https://helm-chart.anubis.cafe --merge index.yaml
```

**参数说明:**

- `--merge`: 合并到现有索引,而不是完全重写
- 优点: 更快,减少计算量
- 缺点: 可能保留已删除包的条目

### 并行打包

```bash
# 使用 GNU parallel 并行打包
ls charts/* | parallel -j 4 helm package
```

---

## 自动化建议

### CI/CD 集成

在 CI/CD 流程中自动化索引更新:

```yaml
# .github/workflows/release-chart.yml
name: Release Helm Chart

on:
  push:
    paths:
      - 'charts/**/Chart.yaml'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Helm
        uses: azure/setup-helm@v3

      - name: Package Chart
        run: |
          helm package charts/*

      - name: Update Index
        run: |
          helm repo index . --url https://helm-chart.anubis.cafe

      - name: Commit Changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add *.tgz index.yaml
          git commit -m "chore: 自动更新 Helm 索引"
          git push
```

---

## 参考文档

- [Helm 仓库最佳实践](https://helm.sh/docs/topics/chart_repository/)
- [Helm Index 文件格式](https://helm.sh/docs/topics/charts/#the-index-file)
- [Artifact Hub 集成](https://artifacthub.io/docs/topics/repositories/#helm-charts)