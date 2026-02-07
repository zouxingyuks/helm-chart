# Helm Chart 存储配置指南

本文档详细说明 Helm Chart 中持久化存储的配置方法和最佳实践。

## 目录

- [存储基础概念](#存储基础概念)
- [StorageClass 选择](#storageclass-选择)
- [PVC 配置模式](#pvc-配置模式)
- [访问模式详解](#访问模式详解)
- [常见存储后端](#常见存储后端)
- [配置示例](#配置示例)
- [最佳实践](#最佳实践)

---

## 存储基础概念

### PersistentVolume (PV)

集群级别的存储资源，由管理员静态创建或通过 StorageClass 动态创建。

### PersistentVolumeClaim (PVC)

命名空间级别的存储请求，用户通过 PVC 申请存储资源。

### StorageClass

定义存储的"类型"和"属性"，用于动态创建 PV。

---

## StorageClass 选择

### 获取可用 StorageClass

```bash
kubectl get storageclass
```

### 设置默认 StorageClass

```bash
kubectl patch storageclass <storage-class-name> \
  -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

### 在 values.yaml 中配置

```yaml
# 全局默认 StorageClass
global:
  storageClass: "local-path"

# 组件特定 StorageClass
persistence:
  persistentVolumeClaim:
    storageClass: "local-path"  # 覆盖全局配置
```

---

## PVC 配置模式

### 正确的配置路径

**✅ 正确:**
```yaml
api:
  persistence:
    persistentVolumeClaim:
      storageClass: "local-path"
      accessModes:
        - ReadWriteOnce
      size: 10Gi
```

**❌ 错误 - 缺少 persistentVolumeClaim 层级:**
```yaml
api:
  persistence:
    storageClass: "local-path"  # 配置路径错误
```

### 动态供应配置

```yaml
persistence:
  enabled: true
  persistentVolumeClaim:
    storageClass: "local-path"  # 使用 StorageClass 动态创建 PV
    accessModes:
      - ReadWriteOnce
    size: 10Gi
```

### 静态供应配置

如果使用预创建的 PV:

```yaml
persistence:
  enabled: true
  persistentVolumeClaim:
    storageClass: ""  # 空字符串，不使用动态供应
    accessModes:
      - ReadWriteOnce
    size: 10Gi
    # volumeName: "my-existing-pv"  # 可选: 绑定到特定 PV
```

---

## 访问模式详解

### ReadWriteOnce (RWO)

- **说明:** 卷可以被单个节点以读写模式挂载
- **支持:** 几乎所有存储后端
- **适用:** 单实例应用、数据库、大多数 StatefulSet

### ReadOnlyMany (ROX)

- **说明:** 卷可以被多个节点以只读模式挂载
- **支持:** Ceph RBD、NFS（部分实现）
- **适用:** 多只读副本场景

### ReadWriteMany (RWX)

- **说明:** 卷可以被多个节点以读写模式挂载
- **支持:** NFS、CephFS、某些云存储
- **适用:** 多实例共享文件系统（如 Web 应用共享静态资源）

### ReadWriteOncePod (RWOP)

- **说明:** 卷可以被单个 Pod 以读写模式挂载（Kubernetes 1.22+）
- **支持:** local-path、部分云存储
- **适用:** 需要更严格隔离的场景

### 访问模式兼容性表

| StorageClass | RWO | ROX | RWX | RWOP |
|--------------|-----|-----|-----|------|
| local-path   | ✅  | ❌  | ❌  | ✅   |
| nfs          | ✅  | ✅  | ✅  | ❌   |
| ceph-rbd     | ✅  | ✅  | ❌  | ❌   |
| cephfs       | ✅  | ✅  | ✅  | ❌   |
| aws-ebs      | ✅  | ❌  | ❌  | ✅   |
| azure-disk   | ✅  | ❌  | ❌  | ✅   |
| gce-pd       | ✅  | ❌  | ❌  | ✅   |

---

## 常见存储后端

### local-path

**特点:**
- 使用节点本地存储
- 高性能、低延迟
- 数据与节点绑定

**配置:**
```yaml
persistence:
  persistentVolumeClaim:
    storageClass: "local-path"
    accessModes:
      - ReadWriteOnce
```

**适用场景:**
- 单实例数据库
- 缓存应用
- 开发测试环境

**注意事项:**
- Pod 调度到特定节点
- 节点故障数据丢失
- 不支持多节点共享

### NFS

**特点:**
- 网络文件系统
- 支持多节点共享
- 依赖网络稳定性

**配置:**
```yaml
persistence:
  persistentVolumeClaim:
    storageClass: "nfs"
    accessModes:
      - ReadWriteMany
```

**适用场景:**
- 多实例应用共享数据
- Web 应用静态资源
- 日志收集

### Ceph RBD

**特点:**
- 块存储
- 高性能、高可用
- 支持快照、克隆

**配置:**
```yaml
persistence:
  persistentVolumeClaim:
    storageClass: "ceph-rbd"
    accessModes:
      - ReadWriteOnce
```

**适用场景:**
- 数据库
- 高性能应用
- 生产环境

### 云存储 (AWS EBS, Azure Disk, GCE PD)

**特点:**
- 托管服务
- 高可用、自动备份
- 按需付费

**配置:**
```yaml
persistence:
  persistentVolumeClaim:
    storageClass: "gp2"  # AWS EBS
    accessModes:
      - ReadWriteOnce
```

---

## 配置示例

### Deployment 单实例应用

```yaml
api:
  persistence:
    enabled: true
    persistentVolumeClaim:
      storageClass: "local-path"
      accessModes:
        - ReadWriteOnce
      size: 10Gi
```

### StatefulSet 数据库

```yaml
postgresql:
  primary:
    persistence:
      enabled: true
      persistentVolumeClaim:
        storageClass: "local-path"
        accessModes:
          - ReadWriteOnce
        size: 20Gi
  read:
    persistence:
      enabled: true
      persistentVolumeClaim:
        storageClass: "local-path"
        accessModes:
          - ReadWriteOnce
        size: 20Gi
```

### 多实例共享存储

```yaml
web:
  persistence:
    enabled: true
    persistentVolumeClaim:
      storageClass: "nfs"  # 支持 RWX
      accessModes:
        - ReadWriteMany
      size: 50Gi
```

### 多存储卷配置

```yaml
api:
  persistence:
    # 主数据卷
    data:
      enabled: true
      persistentVolumeClaim:
        storageClass: "local-path"
        accessModes:
          - ReadWriteOnce
        size: 10Gi
    # 日志卷
    logs:
      enabled: true
      persistentVolumeClaim:
        storageClass: "local-path"
        accessModes:
          - ReadWriteOnce
        size: 5Gi
```

---

## 最佳实践

### 1. 容量规划

**预留空间:**
- 数据库: 预留 50% 增长空间
- 日志: 根据保留期计算
- 文件上传: 考虑用户增长

**示例:**
```yaml
persistence:
  persistentVolumeClaim:
    size: 20Gi  # 当前使用 10Gi，预留增长空间
```

### 2. 选择合适的访问模式

**决策树:**
```
是否需要多节点同时写入？
  ├─ 是 → 使用 ReadWriteMany (NFS/CephFS)
  └─ 否 → 使用 ReadWriteOnce (local-path/Ceph RBD)
```

### 3. StorageClass 选择

**环境因素:**
- **开发环境:** local-path (成本低)
- **测试环境:** NFS (方便共享)
- **生产环境:** Ceph RBD / 云存储 (高可用)

### 4. 数据保护

**备份策略:**
- 定期快照（如果存储后端支持）
- 使用 Velero 等备份工具
- 应用级别备份（数据库导出）

**示例 - Ceph RBD 快照:**
```yaml
persistence:
  persistentVolumeClaim:
    storageClass: "ceph-rbd"
    annotations:
      # 启用快照
      snapshot.storage.kubernetes.io/false: "false"
```

### 5. 监控和告警

**关键指标:**
- PVC 使用率
- PV 可用容量
- 存储性能（IOPS、延迟）

**Prometheus 示例:**
```yaml
# PVC 使用率
kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes
```

### 6. 故障恢复

**数据恢复:**
1. 从备份恢复
2. 重建 PVC 并绑定到新 PV
3. 使用快照克隆恢复

**示例 - 使用快照恢复:**
```bash
# 创建快照
kubectl create volumesnapshot pvc-snapshot --source=pvc-name

# 从快照恢复 PVC
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-pvc
spec:
  dataSource:
    name: pvc-snapshot
    kind: VolumeSnapshot
  accessModes: [ReadWriteOnce]
  storageClassName: local-path
  resources:
    requests:
      storage: 10Gi
EOF
```

### 7. 安全考虑

**加密:**
```yaml
persistence:
  persistentVolumeClaim:
    storageClass: "encrypted-rbd"  # 支持加密的 StorageClass
```

**访问控制:**
- 使用 RBAC 限制 PVC 创建权限
- 敏感数据使用 Secret 而非存储卷

---

## 故障排查

### PVC 一直处于 Pending 状态

**检查:**
```bash
kubectl describe pvc -n <namespace> <pvc-name>
```

**可能原因:**
1. StorageClass 不存在
2. 集群无可用 PV
3. 访问模式不兼容

### Pod 无法挂载 PVC

**检查:**
```bash
kubectl describe pod -n <namespace> <pod-name>
```

**常见错误:**
```
MountVolume.SetUp failed: mount failed:
exit status 32 Mounting command: systemd-run
```

**解决:**
- 检查节点存储插件
- 检查存储网络连接
- 验证 PVC 处于 Bound 状态

---

**文档版本:** 1.0
**最后更新:** 2026-01-24
