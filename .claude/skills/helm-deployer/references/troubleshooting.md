# Helm 部署故障排查指南

本文档提供 Helm 部署中常见问题的诊断和解决方案。

## 目录

- [Pod 状态问题](#pod-状态问题)
- [PVC 绑定问题](#pvc-绑定问题)
- [镜像拉取问题](#镜像拉取问题)
- [Ingress 配置问题](#ingress-配置问题)
- [Service 发现问题](#service-发现问题)
- [资源限制问题](#资源限制问题)

---

## Pod 状态问题

### Pending 状态

#### 原因 1: PVC 未绑定

**症状:**
```
pod has unbound immediate PersistentVolumeClaims
```

**诊断步骤:**
1. 检查 PVC 状态:
   ```bash
   kubectl get pvc -n <namespace>
   ```
2. 查看 PVC 详情:
   ```bash
   kubectl describe pvc -n <namespace> <pvc-name>
   ```

**解决方案:**
- 检查 StorageClass 是否正确配置
- 确保 StorageClass 存在: `kubectl get storageclass`
- 检查访问模式是否兼容 StorageClass

#### 原因 2: 资源不足

**症状:**
```
0/1 nodes are available: 1 Insufficient cpu/memory
```

**解决方案:**
- 减少容器资源请求
- 添加更多节点到集群
- 检查其他 Pod 的资源使用情况

#### 原因 3: 节点选择器不匹配

**症状:**
```
0/1 nodes are available: 1 node(s) didn't match node selector
```

**解决方案:**
- 检查节点标签: `kubectl get nodes --show-labels`
- 调整 Pod 的 nodeSelector 或 tolerations

### CrashLoopBackOff 状态

#### 原因 1: 应用启动失败

**诊断:**
```bash
kubectl logs -n <namespace> <pod-name>
kubectl logs -n <namespace> <pod-name> --previous
```

**常见原因:**
- 配置错误（环境变量、ConfigMap、Secret）
- 依赖服务未就绪
- 健康检查配置错误

#### 原因 2: 健康检查失败

**症状:**
```
Readiness probe failed: HTTP probe failed with statuscode: 500
Liveness probe failed: HTTP probe failed with statuscode: 500
```

**解决方案:**
- 检查健康检查配置:
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 10
  ```
- 延长 initialDelaySeconds
- 检查应用健康检查端点

---

## PVC 绑定问题

### StorageClass 不存在

**症状:**
```
persistentvolume-controller: no persistent volumes available for this claim
```

**解决方案:**
1. 检查可用的 StorageClass:
   ```bash
   kubectl get storageclass
   ```
2. 在 values.yaml 中配置正确的 StorageClass:
   ```yaml
   persistence:
     persistentVolumeClaim:
       storageClass: "local-path"  # 使用存在的 StorageClass
   ```

### AccessMode 不兼容

**症状:**
```
NodePath only supports ReadWriteOnce and ReadWriteOncePod (1.22+) access modes
```

**StorageClass 访问模式限制:**
- `local-path`: 只支持 ReadWriteOnce
- `nfs`: 支持 ReadWriteMany
- `ceph-rbd`: 支持 ReadWriteOnce 和 ReadOnlyMany

**解决方案:**
```yaml
persistence:
  persistentVolumeClaim:
    accessModes:
      - ReadWriteOnce  # 改为支持的访问模式
```

### StatefulSet PVC 修改失败

**问题:**
StatefulSet 不允许修改 volumeClaimTemplates

**解决方案:**
1. 删除 StatefulSet:
   ```bash
   kubectl delete statefulset <statefulset-name> -n <namespace>
   ```
2. 删除关联的 PVC（如需要）:
   ```bash
   kubectl delete pvc -n <namespace> <pvc-name>
   ```
3. 重新部署:
   ```bash
   helm upgrade <release> <chart> -n <namespace>
   ```

---

## 镜像拉取问题

### 镜像拉取超时

**症状:**
```
Failed to pull image: rpc error: code = Unknown desc = pulling image: context deadline exceeded
```

**原因:**
- 镜像 registry 网络不可达
- 镜像过大，下载超时

**解决方案:**

1. **使用私有镜像仓库:**
   ```yaml
   global:
     imageRegistry: "your-registry.com"
   ```

2. **更改镜像源:**
   ```yaml
   image:
     repository: docker.io/library/image  # 使用可访问的源
   ```

3. **配置 imagePullSecrets:**
   ```bash
   kubectl create secret docker-registry regcred \
     --docker-server=your-registry.com \
     --docker-username=user \
     --docker-password=pass \
     -n <namespace>
   ```

   ```yaml
   imagePullSecrets:
     - name: regcred
   ```

### 镜像不存在

**症状:**
```
Failed to pull image: rpc error: code = NotFound desc = Error response from daemon: pull access denied
```

**解决方案:**
- 检查镜像标签是否正确
- 确认镜像已推送到 registry
- 检查 imagePullSecrets 配置

---

## Ingress 配置问题

### Ingress 未创建

**检查:**
1. Ingress Controller 是否已安装:
   ```bash
   kubectl get pods -n ingress-nginx
   ```
2. Ingress 资源是否创建:
   ```bash
   kubectl get ingress -n <namespace>
   ```

**解决方案:**
- 安装 Ingress Controller（如 nginx-ingress）
- 在 values.yaml 中启用 Ingress:
  ```yaml
  ingress:
    enabled: true
  ```

### Ingress 无法访问

**诊断步骤:**
1. 检查 Ingress 状态:
   ```bash
   kubectl describe ingress -n <namespace>
   ```
2. 检查 Ingress Controller 日志:
   ```bash
   kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
   ```
3. 检查 DNS 解析:
   ```bash
   nslookup <domain>
   ```

**常见问题:**
- DNS 未正确配置
- Ingress Class 不匹配
- TLS 证书配置错误
- Service 端口不正确

---

## Service 发现问题

### Service 无法访问

**诊断:**
1. 检查 Service 状态:
   ```bash
   kubectl get svc -n <namespace>
   kubectl describe svc -n <namespace> <service-name>
   ```
2. 检查 Endpoints:
   ```bash
   kubectl get endpoints -n <namespace> <service-name>
   ```

**常见问题:**
- Service Selector 不匹配 Pod 标签
- 端口配置错误
- 网络策略阻止访问

### Pod 无法访问 Service

**检查:**
1. DNS 解析:
   ```bash
   kubectl exec -n <namespace> <pod-name> -- nslookup <service-name>
   ```
2. 网络连接:
   ```bash
   kubectl exec -n <namespace> <pod-name> -- curl http://<service-name>:<port>
   ```

---

## 资源限制问题

### OOMKilled

**症状:**
```
Last State:     Terminated
Reason:         OOMKilled
Exit Code:      137
```

**解决方案:**
增加内存限制:
```yaml
resources:
  limits:
    memory: "512Mi"  # 增加内存限制
  requests:
    memory: "256Mi"
```

### CPU 节流

**症状:**
Pod 运行缓慢，CPU 使用率高

**解决方案:**
```yaml
resources:
  limits:
    cpu: "1000m"  # 增加 CPU 限制
  requests:
    cpu: "500m"
```

---

## 调试技巧

### 查看 Pod 事件

```bash
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
kubectl describe pod -n <namespace> <pod-name>
```

### 查看日志

```bash
# 实时日志
kubectl logs -n <namespace> <pod-name> -f

# 多容器 Pod
kubectl logs -n <namespace> <pod-name> -c <container-name>

# 之前的日志
kubectl logs -n <namespace> <pod-name> --previous
```

### 进入 Pod 调试

```bash
kubectl exec -n <namespace> <pod-name> -- /bin/sh
```

### 导出资源配置

```bash
kubectl get pod -n <namespace> <pod-name> -o yaml > pod.yaml
kubectl get svc -n <namespace> <service-name> -o yaml > svc.yaml
```

---

## 常用调试命令参考

### Pods
```bash
kubectl get pods -n <namespace> -w
kubectl describe pod -n <namespace> <pod-name>
kubectl logs -n <namespace> <pod-name> --tail=100
```

### PVC
```bash
kubectl get pvc -n <namespace>
kubectl describe pvc -n <namespace> <pvc-name>
kubectl get pv
```

### Helm
```bash
helm status <release> -n <namespace>
helm get values <release> -n <namespace> -a
helm history <release> -n <namespace>
```

### Ingress
```bash
kubectl get ingress -n <namespace>
kubectl describe ingress -n <namespace> <ingress-name>
```

---

**文档版本:** 1.0
**最后更新:** 2026-01-24
