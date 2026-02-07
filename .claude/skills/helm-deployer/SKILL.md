---
name: helm-deployer
description: 通用 Helm Chart 部署和故障排查技能，适用于任何 Kubernetes 应用的 Helm 部署场景。当用户需要: (1) 部署或升级 Helm Release (2) 诊断 Pod/PVC/Ingress 问题 (3) 配置持久化存储 (4) 处理镜像拉取失败 (5) 验证部署状态 (6) 清理 Helm 部署资源 时使用此技能。基于生产环境实战经验，提供标准化部署流程、问题诊断脚本和配置最佳实践。
---

# Helm Deployer

## 概述

此技能提供通用化的 Helm 部署和故障排查能力，适用于任何 Helm Chart。它基于真实生产环境的部署经验（特别是复杂应用如 Dify 的部署实践），提取出可复用的部署流程、诊断工具和最佳实践。

## 核心能力

1. **自动化诊断** - 使用脚本快速诊断 Pod、PVC 和 Helm Release 状态
2. **标准化部署流程** - 提供经过验证的部署前检查、部署执行和部署后验证流程
3. **配置最佳实践** - 包含存储配置、镜像配置、资源限制等关键配置项的模板和指南
4. **故障排查指南** - 覆盖常见部署问题的根本原因和解决方案

## 快速开始

### 典型使用场景

**场景 1: 部署新应用**
```bash
# 1. 使用诊断脚本检查环境
./scripts/diagnose_pods.sh <namespace>

# 2. 参考 deployment-workflow.md 执行部署
# 3. 使用检查清单验证部署
```

**场景 2: 诊断 Pod 问题**
```bash
# 直接运行诊断脚本
./scripts/diagnose_pods.sh <namespace> [pod-name]
```

**场景 3: PVC 绑定失败**
```bash
# 检查 PVC 配置
./scripts/check_pvc.sh <namespace>

# 参考 storage-guide.md 了解访问模式兼容性
```

**场景 4: 清理并重新部署**
```bash
# 完全清理部署
./scripts/cleanup_deployment.sh <release> <namespace> --full
```

## 工作流程决策树

```
用户请求
│
├─ 部署新应用或升级
│   └─ → 阅读 [deployment-workflow.md](references/deployment-workflow.md)
│       → 使用 [deployment-checklist.md](references/deployment-checklist.md) 验证
│       → 参考 [assets/values-template.yaml](assets/values-template.yaml) 配置
│
├─ 诊断问题
│   ├─ Pod 状态异常
│   │   └─ → 运行 diagnose_pods.sh
│   │       → 阅读 [troubleshooting.md](references/troubleshooting.md) 第 2 节
│   │
│   ├─ PVC 绑定失败
│   │   └─ → 运行 check_pvc.sh
│   │       → 阅读 [troubleshooting.md](references/troubleshooting.md) 第 3 节
│   │       → 参考 [storage-guide.md](references/storage-guide.md)
│   │
│   ├─ 镜像拉取失败
│   │   └─ → 阅读 [troubleshooting.md](references/troubleshooting.md) 第 4 节
│   │
│   └─ Release 状态异常
│       └─ → 运行 check_helm_release.sh
│           → 阅读 [troubleshooting.md](references/troubleshooting.md) 第 1 节
│
├─ 配置存储
│   └─ → 阅读 [storage-guide.md](references/storage-guide.md)
│       → 参考 assets/values-template.yaml 中的 persistence 部分
│
└─ 清理部署
    └─ → 运行 cleanup_deployment.sh
```

## 任务指南

### 1. 部署应用

**步骤:**

1. **环境检查** - 参考 [deployment-checklist.md](references/deployment-checklist.md) "部署前检查清单"
2. **配置准备** - 使用 [assets/values-template.yaml](assets/values-template.yaml) 作为模板
3. **执行部署** - 参考 [deployment-workflow.md](references/deployment-workflow.md) "执行部署" 节
4. **验证部署** - 运行 `check_helm_release.sh` 并使用检查清单

**关键注意事项:**
- 确保 StorageClass 与访问模式兼容（见 storage-guide.md）
- 检查镜像仓库可访问性
- 验证 imagePullSecrets 配置（私有仓库）

### 2. 诊断 Pod 问题

**工具:**
```bash
./scripts/diagnose_pods.sh <namespace> [pod-name]
```

**输出内容:**
- Pod 列表和状态
- Pending/Failed Pod 诊断
- Pod 详细信息和事件
- 最近日志（50 行）

**下一步:**
- 查看日志中的错误信息
- 检查 Pod 事件中的调度问题
- 参考 [troubleshooting.md](references/troubleshooting.md) 对应章节

### 3. 配置持久化存储

**参考文档:**
- [storage-guide.md](references/storage-guide.md) - 完整存储配置指南
- [deployment-checklist.md](references/deployment-checklist.md) - 存储准备清单

**关键决策点:**
1. **选择 StorageClass** - 考虑性能、可用性、成本
2. **确定访问模式** - 根据应用类型选择 RWO/RWX
3. **规划容量** - 预留 50% 增长空间

**常见错误:**
- ❌ 使用 ReadWriteMany 与 local-path（不兼容）
- ✅ 使用 ReadWriteOnce 与 local-path（兼容）

### 4. 处理镜像拉取失败

**诊断:**
```bash
# 测试镜像可访问性
docker pull <image>:<tag>

# 检查 imagePullSecrets
kubectl get secret regcred -n <namespace>
```

**解决方案:**
1. 使用私有镜像仓库（在 values.yaml 配置 global.imageRegistry）
2. 更换镜像源（使用 docker.io 替代专用 registry）
3. 配置 imagePullSecrets

### 5. 清理部署

**工具:**
```bash
# 卸载 Release（保留 PVC）
./scripts/cleanup_deployment.sh <release> <namespace>

# 完全清理（包括 PVC）
./scripts/cleanup_deployment.sh <release> <namespace> --full
```

**注意:** 使用 `--full` 会删除所有 PVC，数据将永久丢失。

## 脚本使用指南

### diagnose_pods.sh

诊断指定命名空间中的 Pod 状态。

**用法:**
```bash
./scripts/diagnose_pods.sh <namespace> [pod-name]
```

**示例:**
```bash
# 检查命名空间所有 Pod
./scripts/diagnose_pods.sh dify

# 诊断特定 Pod
./scripts/diagnose_pods.sh dify dify-api-xxx
```

### check_pvc.sh

检查 PVC 状态和配置兼容性。

**用法:**
```bash
./scripts/check_pvc.sh <namespace>
```

**输出:**
- PVC 列表和状态
- Pending PVC 诊断
- StorageClass 兼容性分析

### check_helm_release.sh

检查 Helm Release 状态和关联资源。

**用法:**
```bash
./scripts/check_helm_release.sh <release-name> [namespace]
```

**输出:**
- Helm Release 状态
- 关联资源（Deployment、StatefulSet、Service、Ingress、PVC）
- Pod 状态和事件
- Release 历史记录

### cleanup_deployment.sh

清理 Helm 部署资源。

**用法:**
```bash
./scripts/cleanup_deployment.sh <release-name> <namespace> [--full]
```

**选项:**
- `--full` - 完全清理（包括 PVC）

## 参考资料使用时机

### deployment-workflow.md

**何时阅读:**
- 首次部署应用
- 建立标准化部署流程
- 编写部署脚本

**内容:**
- 部署前检查清单
- 配置准备步骤
- 执行部署命令
- 部署验证流程
- 问题处理方法
- 部署后维护

### storage-guide.md

**何时阅读:**
- 配置持久化存储
- 解决 PVC 绑定问题
- 选择 StorageClass
- 规划存储容量

**内容:**
- 存储基础概念
- StorageClass 选择指南
- 访问模式详解
- 常见存储后端特性
- 配置示例
- 最佳实践

### troubleshooting.md

**何时阅读:**
- 遇到部署问题
- Pod/PVC 状态异常
- 镜像拉取失败
- 服务无法访问

**内容:**
- Pod 状态问题（Pending、CrashLoopBackOff）
- PVC 绑定问题
- 镜像拉取问题
- Ingress 配置问题
- Service 发现问题
- 调试技巧

### deployment-checklist.md

**何时阅读:**
- 部署前验证
- 部署后确认
- 生产环境上线

**内容:**
- 部署前检查清单（环境、Chart、镜像、配置、存储、网络）
- 部署中检查清单（监控部署过程）
- 部署后验证清单（Release、Pod、Service、Ingress、PVC、应用功能）
- 生产环境额外检查（安全、性能、高可用、备份、监控）
- 故障排查检查清单

## 配置模板使用

### assets/values-template.yaml

通用 Helm Chart values.yaml 配置模板，包含常用配置项和最佳实践。

**使用场景:**
- 创建新的 values.yaml
- 检查现有配置完整性
- 学习最佳实践配置

**关键配置区域:**
- **全局配置** (global) - 镜像仓库、StorageClass
- **镜像配置** (image) - 镜像地址、标签、拉取策略
- **资源配置** (resources) - CPU/内存限制和请求
- **持久化存储** (persistence) - PVC 配置
- **服务配置** (service) - Service 类型、端口
- **Ingress 配置** (ingress) - 域名、路径、TLS
- **健康检查** (livenessProbe/readinessProbe) - 探针配置
- **安全配置** (securityContext/podSecurity) - 安全上下文

## 最佳实践

### 1. 部署前准备

- ✅ 详细检查集群环境和必要组件
- ✅ 提前测试 Chart 配置（使用 `helm template --dry-run`）
- ✅ 准备好 imagePullSecrets
- ✅ 验证 values.yaml 语法

### 2. 配置管理

- ✅ 使用配置模板确保完整性
- ✅ 区分环境特定配置（dev/staging/prod）
- ✅ 使用 Secret 管理敏感信息
- ✅ 版本控制 values.yaml

### 3. 存储配置

- ✅ 选择合适的访问模式（RWO vs RWX）
- ✅ 确保 StorageClass 与访问模式兼容
- ✅ 预留足够的存储空间（+50%）
- ✅ 考虑备份和恢复策略

### 4. 问题处理

- ✅ 使用诊断脚本快速定位问题
- ✅ 查看事件和日志定位根本原因
- ✅ 小步快跑，迭代部署
- ✅ 记录问题解决方案

### 5. 生产环境

- ✅ 配置资源限制（requests/limits）
- ✅ 设置健康检查（liveness/readiness probe）
- ✅ 配置 HPA 实现自动扩缩容
- ✅ 配置 PDB 保证高可用
- ✅ 启用监控和告警
- ✅ 定期备份配置和数据

## 资源

### scripts/

可执行的诊断和管理脚本:

- **diagnose_pods.sh** - Pod 状态诊断
- **check_pvc.sh** - PVC 配置检查
- **check_helm_release.sh** - Helm Release 状态检查
- **cleanup_deployment.sh** - 部署资源清理

### references/

详细参考文档:

- **deployment-workflow.md** - 标准化部署流程
- **storage-guide.md** - 存储配置完整指南
- **troubleshooting.md** - 故障排查和解决方案
- **deployment-checklist.md** - 部署检查清单

### assets/

配置模板和示例:

- **values-template.yaml** - 通用 Helm values.yaml 配置模板

## 进阶话题

### StatefulSet 特别注意事项

StatefulSet 的 volumeClaimTemplates 一旦创建就不能修改。如需更改:
1. 删除 StatefulSet
2. 删除关联的 PVC
3. 重新部署

### 迭代部署策略

1. **小步快跑** - 每次只修改一个问题点
2. **快速验证** - 修改后立即验证
3. **详细日志** - 记录每次修改的内容和原因
4. **资源清理** - 必要时清理重建

### 多环境配置管理

建议目录结构:
```
helm-values/
├── common.yaml        # 通用配置
├── dev.yaml           # 开发环境
├── staging.yaml       # 预发布环境
└── production.yaml    # 生产环境
```

部署时合并:
```bash
helm install <release> <chart> \
  -f helm-values/common.yaml \
  -f helm-values/production.yaml
```
