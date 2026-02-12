# Helm 部署工作流程

本文档提供标准化的 Helm 部署流程，包括部署前准备、部署执行和部署后验证。

## 目录

- [部署前检查](#部署前检查)
- [配置准备](#配置准备)
- [执行部署](#执行部署)
- [部署验证](#部署验证)
- [问题处理](#问题处理)
- [部署后维护](#部署后维护)

---

## 部署前检查

### 1. 环境检查清单

#### Kubernetes 集群状态

```bash
# 检查集群节点状态
kubectl get nodes

# 检查集群资源使用
kubectl top nodes

# 检查集群版本
kubectl version --short
```

**标准:**
- [ ] 所有节点状态为 Ready
- [ ] 资源使用率 < 80%
- [ ] Kubernetes 版本 >= 1.20

#### 必要组件检查

```bash
# 检查 Helm 安装
helm version

# 检查 StorageClass
kubectl get storageclass

# 检查 Ingress Controller
kubectl get pods -n ingress-nginx

# 检查 CRD（如需要）
kubectl get crd | grep <custom-resource>
```

**标准:**
- [ ] Helm 版本 >= 3.0
- [ ] 默认 StorageClass 已配置
- [ ] Ingress Controller 已安装（如需要）
- [ ] 必要的 CRD 已安装

#### 命名空间准备

```bash
# 创建命名空间
kubectl create namespace <namespace>

# 设置默认命名空间（可选）
kubectl config set-context --current --namespace=<namespace>
```

#### 镜像仓库准备

```bash
# 登录私有镜像仓库（如需要）
docker login <registry-url>

# 创建 imagePullSecret
kubectl create secret docker-registry regcred \
  --docker-server=<registry-url> \
  --docker-username=<username> \
  --docker-password=<password> \
  -n <namespace>
```

### 2. Chart 准备

#### 获取 Chart

```bash
# 从仓库添加
helm repo add <repo-name> <repo-url>
helm repo update
helm pull <repo-name>/<chart-name>

# 或从本地目录
cd /path/to/chart
```

#### 检查 Chart

```bash
# 查看 Chart 信息
helm show chart <chart-path>

# 查看 Chart values
helm show values <chart-path> > default-values.yaml

# 模板渲染（dry-run）
helm template <release-name> <chart-path> \
  -n <namespace> \
  --values values.yaml \
  --debug
```

---

## 配置准备

### 1. 创建 values.yaml

#### 基础配置

```yaml
# 全局配置
global:
  imageRegistry: "your-registry.com"
  imagePullSecrets:
    - name: regcred
  storageClass: "local-path"

# 镜像配置
image:
  repository: your-registry.com/app
  tag: "v1.0.0"
  pullPolicy: IfNotPresent

# 副本数
replicaCount: 2

# 服务配置
service:
  type: ClusterIP
  port: 80

# Ingress 配置
ingress:
  enabled: true
  className: nginx
  annotations: {}
  hosts:
    - host: app.example.com
      paths:
        - path: /
          pathType: Prefix
```

#### 资源限制配置

```yaml
resources:
  limits:
    cpu: "1000m"
    memory: "1024Mi"
  requests:
    cpu: "500m"
    memory: "512Mi"
```

#### 持久化存储配置

```yaml
persistence:
  enabled: true
  persistentVolumeClaim:
    storageClass: "local-path"
    accessModes:
      - ReadWriteOnce
    size: 10Gi
```

### 2. 配置验证

#### 语法检查

```bash
# YAML 语法检查
yamllint values.yaml

# 或使用 Python
python3 -c "import yaml; yaml.safe_load(open('values.yaml'))"
```

#### 值验证

```bash
# 使用 helm template 验证
helm template test <chart-path> -f values.yaml --debug

# 检查生成的资源
helm template test <chart-path> -f values.yaml | kubectl apply --dry-run=client -f -
```

---

## 执行部署

### 1. 首次部署

```bash
# 基础部署
helm install <release-name> <chart-path> \
  -n <namespace> \
  --values values.yaml

# 带超时的部署
helm install <release-name> <chart-path> \
  -n <namespace> \
  --values values.yaml \
  --timeout 10m

# 等待 Pod 就绪
helm install <release-name> <chart-path> \
  -n <namespace> \
  --values values.yaml \
  --wait
```

### 2. 升级部署

```bash
# 检查配置变更
helm diff upgrade <release-name> <chart-path> \
  -n <namespace> \
  --values values.yaml

# 执行升级
helm upgrade <release-name> <chart-path> \
  -n <namespace> \
  --values values.yaml

# 保留旧版本的升级
helm upgrade <release-name> <chart-path> \
  -n <namespace> \
  --values values.yaml \
  --history-max 10
```

### 3. 回滚部署

```bash
# 查看历史
helm history <release-name> -n <namespace>

# 回滚到上一版本
helm rollback <release-name> -n <namespace>

# 回滚到指定版本
helm rollback <release-name> <revision> -n <namespace>
```

---

## 部署验证

### 1. 快速验证

```bash
# 检查 Helm Release 状态
helm status <release-name> -n <namespace>

# 检查 Pod 状态
kubectl get pods -n <namespace> -l app.kubernetes.io/instance=<release-name>

# 检查所有资源
kubectl get all -n <namespace> -l app.kubernetes.io/instance=<release-name>
```

**成功标准:**
- [ ] Helm Release 状态为 `deployed`
- [ ] 所有 Pod 状态为 `Running`
- [ ] 所有 Pod 就绪 (Ready 1/1)

### 2. 详细验证

#### 服务端点验证

```bash
# 检查 Service
kubectl get svc -n <namespace> -l app.kubernetes.io/instance=<release-name>

# 检查 Endpoints
kubectl get endpoints -n <namespace> -l app.kubernetes.io/instance=<release-name>

# 检查 Ingress
kubectl get ingress -n <namespace> -l app.kubernetes.io/instance=<release-name>
```

#### 持久化存储验证

```bash
# 检查 PVC 状态
kubectl get pvc -n <namespace> -l app.kubernetes.io/instance=<release-name>

# 检查 PV 绑定
kubectl get pv | grep <namespace>
```

**成功标准:**
- [ ] 所有 PVC 状态为 `Bound`
- [ ] 存储容量符合配置

#### 应用功能验证

```bash
# 端口转发测试
kubectl port-forward -n <namespace> svc/<service-name> 8080:80

# 访问测试
curl http://localhost:8080/health

# 或从集群内测试
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://<service-name>.<namespace>.svc.cluster.local:80
```

### 3. 日志检查

```bash
# 查看应用日志
kubectl logs -n <namespace> -l app.kubernetes.io/instance=<release-name> --tail=100

# 查看启动日志
kubectl logs -n <namespace> -l app.kubernetes.io/instance=<release-name> --previous

# 实时日志
kubectl logs -n <namespace> -l app.kubernetes.io/instance=<release-name> -f
```

---

## 问题处理

### 1. 诊断流程

#### 使用诊断脚本

```bash
# 诊断 Pod
./scripts/diagnose_pods.sh <namespace>

# 检查 PVC
./scripts/check_pvc.sh <namespace>

# 检查 Helm Release
./scripts/check_helm_release.sh <release-name> <namespace>
```

#### 手动诊断

```bash
# 查看 Pod 事件
kubectl describe pod -n <namespace> <pod-name>

# 查看 PVC 事件
kubectl describe pvc -n <namespace> <pvc-name>

# 查看集群事件
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

### 2. 常见问题快速修复

#### Pod 启动失败

```bash
# 检查日志
kubectl logs -n <namespace> <pod-name>

# 进入 Pod 调试
kubectl exec -n <namespace> <pod-name> -- /bin/sh
```

#### PVC 绑定失败

```bash
# 检查 StorageClass
kubectl get storageclass

# 修改 values.yaml 配置后升级
helm upgrade <release-name> <chart-path> -n <namespace> --values values.yaml
```

#### 镜像拉取失败

```bash
# 验证镜像存在
docker pull <image>:<tag>

# 检查 imagePullSecrets
kubectl get secret -n <namespace> regcred --template={{.data.\.dockerconfigjson}} | base64 -d
```

### 3. 清理和重新部署

```bash
# 完全清理
./scripts/cleanup_deployment.sh <release-name> <namespace> --full

# 或手动清理
helm uninstall <release-name> -n <namespace>
kubectl delete pvc -n <namespace> --all -l app.kubernetes.io/instance=<release-name>

# 重新部署
helm install <release-name> <chart-path> -n <namespace> --values values.yaml
```

---

## 部署后维护

### 1. 监控

#### 资源监控

```bash
# Pod 资源使用
kubectl top pods -n <namespace>

# 节点资源使用
kubectl top nodes
```

#### 日志收集

```bash
# 导出最近日志
kubectl logs -n <namespace> -l app.kubernetes.io/instance=<release-name> --tail=1000 > app.log

# 持续收集日志
kubectl logs -n <namespace> -l app.kubernetes.io/instance=<release-name> -f >> app.log
```

### 2. 备份

#### Helm Release 备份

```bash
# 导出当前 values
helm get values <release-name> -n <namespace> -a > values-backup.yaml

# 导出 Release 清单
helm get manifest <release-name> -n <namespace> > manifest-backup.yaml
```

#### 数据备份

```bash
# PVC 数据备份（使用 Velero 或其他备份工具）
velero backup create <backup-name> \
  --include-namespaces <namespace> \
  --include-resources pvc,pv
```

### 3. 更新策略

#### 滚动更新

```bash
# 更新镜像版本
helm upgrade <release-name> <chart-path> \
  -n <namespace> \
  --set image.tag=v1.1.0 \
  --wait
```

#### 金丝雀发布

```bash
# 部署新版本
helm install <release-name>-canary <chart-path> \
  -n <namespace> \
  --values values-canary.yaml \
  --set image.tag=v1.1.0

# 流量分流（通过 Service 或 Ingress 配置）
```

---

## 标准化部署脚本

### 完整部署脚本示例

```bash
#!/bin/bash
# deploy.sh - 标准 Helm 部署脚本

set -e

RELEASE_NAME="${1}"
CHART_PATH="${2}"
NAMESPACE="${3:-default}"
VALUES_FILE="${4:-values.yaml}"

echo "======================================"
echo "Helm 部署脚本"
echo "Release: $RELEASE_NAME"
echo "Chart: $CHART_PATH"
echo "Namespace: $NAMESPACE"
echo "Values: $VALUES_FILE"
echo "======================================"
echo

# 1. 前置检查
echo "🔍 前置检查..."
kubectl get namespace "$NAMESPACE" >/dev/null 2>&1 || kubectl create namespace "$NAMESPACE"
echo "✅ 命名空间就绪"
echo

# 2. 配置验证
echo "🔧 配置验证..."
helm template "$RELEASE_NAME" "$CHART_PATH" -n "$NAMESPACE" --values "$VALUES_FILE" >/dev/null
echo "✅ 配置有效"
echo

# 3. 部署或升级
if helm status "$RELEASE_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
    echo "📦 升级现有 Release..."
    helm upgrade "$RELEASE_NAME" "$CHART_PATH" \
      -n "$NAMESPACE" \
      --values "$VALUES_FILE" \
      --wait \
      --timeout 10m
else
    echo "📦 部署新 Release..."
    helm install "$RELEASE_NAME" "$CHART_PATH" \
      -n "$NAMESPACE" \
      --values "$VALUES_FILE" \
      --wait \
      --timeout 10m
fi
echo

# 4. 部署验证
echo "✅ 部署验证..."
helm status "$RELEASE_NAME" -n "$NAMESPACE"
echo
echo "Pod 状态:"
kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME"
echo

echo "======================================"
echo "✅ 部署完成"
echo "======================================"
```

### 使用示例

```bash
# 部署新应用
./deploy.sh my-app ./charts/my-app production values-prod.yaml

# 升级应用
./deploy.sh my-app ./charts/my-app production values-prod.yaml
```

---

## 最佳实践总结

### 1. 部署前

- ✅ 详细检查集群环境和必要组件
- ✅ 提前测试 Chart 配置（dry-run）
- ✅ 准备好 imagePullSecrets
- ✅ 验证 values.yaml 语法

### 2. 部署中

- ✅ 使用 `--wait` 等待 Pod 就绪
- ✅ 设置合理的 `--timeout`
- ✅ 记录部署日志
- ✅ 小步快跑，迭代部署

### 3. 部署后

- ✅ 全面验证资源状态
- ✅ 检查应用功能和日志
- ✅ 备份配置和数据
- ✅ 设置监控和告警

### 4. 问题处理

- ✅ 使用诊断脚本快速定位问题
- ✅ 查看事件和日志定位根本原因
- ✅ 修改配置后使用 `helm upgrade` 更新
- ✅ 必要时清理重建

---

**文档版本:** 1.0
**最后更新:** 2026-01-24
