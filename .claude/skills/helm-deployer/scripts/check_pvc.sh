#!/bin/bash
# check_pvc.sh - 检查 PVC 状态和配置的通用脚本
#
# 用法: ./check_pvc.sh <namespace>
#
# 示例:
#   ./check_pvc.sh dify

set -e

NAMESPACE="${1:-default}"

echo "======================================"
echo "PVC 检查工具"
echo "命名空间: $NAMESPACE"
echo "======================================"
echo

# 获取所有 PVC
echo "📊 PVC 列表:"
kubectl get pvc -n "$NAMESPACE"
echo

# 检查 PVC 状态
BOUND_PVCS=$(kubectl get pvc -n "$NAMESPACE" -o jsonpath='{.items[?(@.status.phase=="Bound")].metadata.name}')
PENDING_PVCS=$(kubectl get pvc -n "$NAMESPACE" -o jsonpath='{.items[?(@.status.phase=="Pending")].metadata.name}')

if [ -n "$PENDING_PVCS" ]; then
    echo "⚠️  发现 Pending 状态的 PVC:"
    for pvc in $PENDING_PVCS; do
        echo "  - $pvc"
    done
    echo
fi

# 详细检查每个 PVC
echo "🔍 PVC 详细信息:"
kubectl get pvc -n "$NAMESPACE" -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,STORAGECLASS:.spec.storageClassName,ACCESSMODES:.spec.accessModes[0],CAPACITY:.status.capacity.storage
echo

# 检查 Pending PVC 的原因
if [ -n "$PENDING_PVCS" ]; then
    echo "❌ Pending PVC 诊断:"
    for pvc in $PENDING_PVCS; do
        echo "--------------------------------------"
        echo "PVC: $pvc"
        echo "--------------------------------------"

        # 检查 StorageClass
        SC=$(kubectl get pvc -n "$NAMESPACE" "$pvc" -o jsonpath='{.spec.storageClassName}')
        echo "StorageClass: $SC"

        if [ -z "$SC" ] || [ "$SC" == "<none>" ]; then
            echo "⚠️  警告: 未设置 StorageClass，可能导致 PVC 无法绑定"
        else
            # 检查 StorageClass 是否存在
            if kubectl get storageclass "$SC" >/dev/null 2>&1; then
                echo "✅ StorageClass '$SC' 存在"
            else
                echo "❌ 错误: StorageClass '$SC' 不存在"
            fi
        fi

        # 检查访问模式
        ACCESS_MODES=$(kubectl get pvc -n "$NAMESPACE" "$pvc" -o jsonpath='{.spec.accessModes[*]}')
        echo "访问模式: $ACCESS_MODES"

        # 检查 PVC 事件
        echo "事件:"
        kubectl describe pvc -n "$NAMESPACE" "$pvc" | grep -A 20 "Events:" || echo "无事件"
        echo
    done
fi

# 检查 StorageClass 兼容性
echo "📚 StorageClass 兼容性指南:"
echo "  local-path: 只支持 ReadWriteOnce"
echo "  nfs: 支持 ReadWriteMany"
echo "  ceph-rbd: 支持 ReadWriteOnce 和 ReadOnlyMany"
echo

echo "======================================"
echo "✅ 检查完成"
echo "======================================"
