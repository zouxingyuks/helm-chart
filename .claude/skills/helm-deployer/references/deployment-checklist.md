# Helm 部署检查清单

本文档提供完整的 Helm 部署前、部署中和部署后的检查清单。

## 部署前检查清单

### 环境准备

- [ ] **Kubernetes 集群状态正常**
  ```bash
  kubectl get nodes
  ```
  - 所有节点状态为 `Ready`
  - 资源使用率合理

- [ ] **Helm 已安装且版本正确**
  ```bash
  helm version
  ```
  - Helm 版本 >= 3.0

- [ ] **StorageClass 已配置**
  ```bash
  kubectl get storageclass
  ```
  - 默认 StorageClass 已设置
  - 必要的 StorageClass 存在

- [ ] **命名空间已创建**
  ```bash
  kubectl create namespace <namespace>
  ```
  - 目标命名空间存在

### Chart 准备

- [ ] **Chart 文件完整**
  - Chart.yaml 存在且有效
  - values.yaml 存在
  - templates/ 目录完整

- [ ] **Chart 信息已审查**
  ```bash
  helm show chart <chart-path>
  helm show values <chart-path>
  ```
  - Chart 版本和依赖符合要求

- [ ] **模板渲染测试通过**
  ```bash
  helm template test <chart-path> -f values.yaml
  ```
  - 无模板错误

### 镜像准备

- [ ] **镜像已推送到仓库**
  ```bash
  docker pull <image>:<tag>
  ```
  - 镜像可访问

- [ ] **imagePullSecrets 已创建**（私有仓库）
  ```bash
  kubectl get secret regcred -n <namespace>
  ```
  - Secret 存在且有效

### 配置准备

- [ ] **values.yaml 已准备**
  - 基础配置完整（镜像、副本数、端口）
  - 环境变量已设置
  - 资源限制已配置

- [ ] **YAML 语法正确**
  ```bash
  yamllint values.yaml
  ```
  - 无语法错误

- [ ] **敏感数据已处理**
  - 使用 Secret 存储密码
  - 不在 values.yaml 中硬编码敏感信息

### 存储准备

- [ ] **PVC 配置正确**
  - StorageClass 设置正确
  - 访问模式与 StorageClass 兼容
  - 存储容量满足需求

- [ ] **配置路径完整**
  ```yaml
  # ✅ 正确
  persistence:
    persistentVolumeClaim:
      storageClass: "local-path"
  ```

### 网络准备

- [ ] **Ingress Controller 已安装**（如需 Ingress）
  ```bash
  kubectl get pods -n ingress-nginx
  ```

- [ ] **域名已解析**（如使用 Ingress）
  ```bash
  nslookup <domain>
  ```

- [ ] **网络策略已配置**（如需要）
  - 允许必要的 Pod 间通信
  - 限制不必要的访问

---

## 部署中检查清单

### 部署命令

- [ ] **使用正确的部署命令**
  ```bash
  # 新部署
  helm install <release> <chart> -n <namespace> --values values.yaml

  # 升级
  helm upgrade <release> <chart> -n <namespace> --values values.yaml
  ```

- [ ] **设置合理参数**
  - `--wait`: 等待 Pod 就绪
  - `--timeout 10m`: 设置超时
  - `--history-max 10`: 保留历史版本

### 监控部署过程

- [ ] **监控 Helm 输出**
  - 观察是否有错误或警告
  - 记录部署时间

- [ ] **监控 Pod 状态**
  ```bash
  kubectl get pods -n <namespace> -w
  ```
  - Pod 正常启动
  - 无 CrashLoopBackOff

- [ ] **检查 Pod 事件**
  ```bash
  kubectl get events -n <namespace> --sort-by='.lastTimestamp'
  ```
  - 无严重错误事件

---

## 部署后验证清单

### Helm Release 状态

- [ ] **Release 状态正常**
  ```bash
  helm status <release> -n <namespace>
  ```
  - 状态为 `deployed`
  - 无错误信息

- [ ] **Release 历史正常**
  ```bash
  helm history <release> -n <namespace>
  ```
  - 当前版本部署成功

### Pod 状态

- [ ] **所有 Pod 运行正常**
  ```bash
  kubectl get pods -n <namespace> -l app.kubernetes.io/instance=<release>
  ```
  - 所有 Pod 状态为 `Running`
  - 所有 Pod Ready (1/1)

- [ ] **Pod 无重启**
  - Restart Count = 0 或稳定

- [ ] **Pod 日志正常**
  ```bash
  kubectl logs -n <namespace> -l app.kubernetes.io/instance=<release> --tail=100
  ```
  - 无错误日志
  - 无异常堆栈

### 服务状态

- [ ] **Service 已创建**
  ```bash
  kubectl get svc -n <namespace> -l app.kubernetes.io/instance=<release>
  ```
  - Service 类型正确
  - 端口配置正确

- [ ] **Endpoints 正常**
  ```bash
  kubectl get endpoints -n <namespace>
  ```
  - Endpoints 与 Pod 数量匹配

- [ ] **服务可访问**
  ```bash
  # 集群内访问
  kubectl run -it --rm debug --image=busybox --restart=Never -- \
    wget -O- http://<service-name>.<namespace>.svc.cluster.local:<port>
  ```

### Ingress 状态（如使用）

- [ ] **Ingress 已创建**
  ```bash
  kubectl get ingress -n <namespace>
  ```
  - Ingress 地址正确
  - 主机名和路径配置正确

- [ ] **外部访问正常**
  ```bash
  curl http://<domain>/
  ```
  - 可通过域名访问

### 持久化存储状态

- [ ] **PVC 已绑定**
  ```bash
  kubectl get pvc -n <namespace>
  ```
  - 所有 PVC 状态为 `Bound`
  - 容量符合预期

- [ ] **存储可读写**
  ```bash
  kubectl exec -n <namespace> <pod-name> -- ls /data
  ```
  - 可正常读写数据

### 应用功能

- [ ] **健康检查通过**
  ```bash
  curl http://<service-name>:<port>/health
  ```
  - 返回正确状态码

- [ ] **核心功能正常**
  - 根据应用特性测试关键功能
  - 验证数据读写

- [ ] **配置生效**
  - 环境变量正确加载
  - ConfigMap/Secret 挂载成功

---

## 生产环境额外检查

### 安全检查

- [ ] **RBAC 配置正确**
  - ServiceAccount 权限最小化
  - 无不必要的集群权限

- [ ] **网络策略配置**
  - 限制不必要的 Pod 间通信
  - 隔离敏感服务

- [ ] **Secret 管理**
  - 使用 External Secrets Operator 或类似工具
  - 定期轮换密钥

- [ ] **镜像安全**
  - 使用官方或可信镜像
  - 镜像经过漏洞扫描

### 性能检查

- [ ] **资源限制合理**
  ```yaml
  resources:
    limits:
      cpu: "1000m"
      memory: "1024Mi"
    requests:
      cpu: "500m"
      memory: "512Mi"
  ```

- [ ] **HPA 配置**（如需要）
  ```bash
  kubectl get hpa -n <namespace>
  ```
  - 自动扩缩容阈值合理

- [ ] **Pod 资源使用正常**
  ```bash
  kubectl top pods -n <namespace>
  ```

### 高可用检查

- [ ] **多副本部署**
  - 副本数 >= 2
  - Pod 分布在不同节点

- [ ] **Pod 反亲和性配置**
  ```yaml
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchExpressions:
                - key: app.kubernetes.io/instance
                  operator: In
                  values:
                    - <release>
            topologyKey: kubernetes.io/hostname
  ```

- [ ] **PDB 配置**（如需要）
  ```bash
  kubectl get pdb -n <namespace>
  ```
  - 最大不可用比例合理

### 备份检查

- [ ] **配置已备份**
  ```bash
  helm get values <release> -n <namespace> -a > values-backup.yaml
  ```

- [ ] **数据备份策略**
  - 定期备份 PVC 数据
  - 使用 Velero 或类似工具

- [ ] **灾难恢复计划**
  - 记录恢复步骤
  - 定期演练恢复流程

### 监控和告警

- [ ] **监控已配置**
  - Prometheus 监控目标
  - Grafana 仪表板

- [ ] **日志收集**
  - 日志转发到集中式日志系统
  - 日志保留策略

- [ ] **告警规则**
  - 关键指标告警
  - 告警通知渠道配置

---

## 快速检查命令

### 一键状态检查

```bash
#!/bin/bash
RELEASE="${1}"
NAMESPACE="${2:-default}"

echo "======================================"
echo "Helm Release 状态检查"
echo "Release: $RELEASE"
echo "Namespace: $NAMESPACE"
echo "======================================"
echo

echo "📦 Helm Release:"
helm status "$RELEASE" -n "$NAMESPACE"
echo

echo "📦 Pods:"
kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE"
echo

echo "🔌 Services:"
kubectl get svc -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE"
echo

echo "💾 PVCs:"
kubectl get pvc -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE"
echo

echo "🌐 Ingress:"
kubectl get ingress -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE"
echo

echo "======================================"
```

### 使用示例

```bash
bash quick-check.sh my-app production
```

---

## 故障排查检查清单

当部署失败或运行异常时：

- [ ] **检查事件日志**
  ```bash
  kubectl get events -n <namespace> --sort-by='.lastTimestamp'
  ```

- [ ] **检查 Pod 日志**
  ```bash
  kubectl logs -n <namespace> <pod-name> --tail=100 --previous
  ```

- [ ] **检查资源配置**
  ```bash
  kubectl describe pod -n <namespace> <pod-name>
  ```

- [ ] **运行诊断脚本**
  ```bash
  ./scripts/diagnose_pods.sh <namespace>
  ./scripts/check_pvc.sh <namespace>
  ./scripts/check_helm_release.sh <release> <namespace>
  ```

- [ ] **检查资源配额**
  ```bash
  kubectl get resourcequota -n <namespace>
  kubectl get limitrange -n <namespace>
  ```

---

## 常见错误快速修复

### 错误: Pod 无法启动

```bash
# 检查 Pod 状态
kubectl get pods -n <namespace>

# 查看事件
kubectl describe pod -n <namespace> <pod-name>

# 查看日志
kubectl logs -n <namespace> <pod-name>
```

### 错误: PVC 无法绑定

```bash
# 检查 PVC
kubectl get pvc -n <namespace>

# 检查 StorageClass
kubectl get storageclass

# 修改 values.yaml 后升级
helm upgrade <release> <chart> -n <namespace> --values values.yaml
```

### 错误: 镜像拉取失败

```bash
# 验证镜像
docker pull <image>:<tag>

# 检查 imagePullSecrets
kubectl get secret -n <namespace> regcred

# 重新创建 Secret
kubectl delete secret regcred -n <namespace>
kubectl create secret docker-registry regcred \
  --docker-server=<registry> \
  --docker-username=<user> \
  --docker-password=<pass> \
  -n <namespace>
```

---

**文档版本:** 1.0
**最后更新:** 2026-01-24
