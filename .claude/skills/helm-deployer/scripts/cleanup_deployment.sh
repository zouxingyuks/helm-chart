#!/bin/bash
# cleanup_deployment.sh - 清理 Helm 部署的通用脚本
#
# 用法: ./cleanup_deployment.sh <release-name> <namespace> [--full]
#
# 选项:
#   --full    完全清理（包括 PVC），谨慎使用！
#
# 示例:
#   ./cleanup_deployment.sh dify dify              # 卸载 Release，保留 PVC
#   ./cleanup_deployment.sh dify dify --full       # 完全清理（包括 PVC）

set -e

RELEASE_NAME="${1}"
NAMESPACE="${2:-default}"
FULL_CLEANUP="${3:-}"

if [ -z "$RELEASE_NAME" ]; then
    echo "❌ 错误: 请提供 Helm Release 名称"
    echo "用法: $0 <release-name> <namespace> [--full]"
    exit 1
fi

echo "======================================"
echo "Helm 部署清理工具"
echo "Release: $RELEASE_NAME"
echo "命名空间: $NAMESPACE"
echo "======================================"
echo

# 确认清理操作
echo "⚠️  警告: 此操作将删除以下资源:"
echo "  - Helm Release: $RELEASE_NAME"
if [ "$FULL_CLEANUP" == "--full" ]; then
    echo "  - 所有关联的 PVC（数据将丢失！）"
fi
echo
read -p "确认继续？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ 取消操作"
    exit 0
fi

# 获取关联的 StatefulSet（用于后续清理）
STATEFULSETS=$(kubectl get statefulsets -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" -o jsonpath='{.items[*].metadata.name}')

# 卸载 Helm Release
echo "📦 卸载 Helm Release..."
helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" 2>/dev/null || echo "Release 已不存在或已卸载"
echo

# 等待 Pod 删除
echo "⏳ 等待 Pod 删除..."
sleep 5

# 强制删除 StatefulSet（如果存在）
if [ -n "$STATEFULSETS" ]; then
    echo "🔧 强制删除 StatefulSet..."
    for st in $STATEFULSETS; do
        kubectl delete statefulset "$st" -n "$NAMESPACE" --force --grace-period=0 2>/dev/null || echo "StatefulSet $st 已删除"
    done
    echo
fi

# 完全清理（包括 PVC）
if [ "$FULL_CLEANUP" == "--full" ]; then
    echo "🗑️  删除所有 PVC..."
    PVCS=$(kubectl get pvc -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" -o jsonpath='{.items[*].metadata.name}')

    if [ -n "$PVCS" ]; then
        echo "将删除以下 PVC:"
        for pvc in $PVCS; do
            echo "  - $pvc"
        done
        echo

        kubectl delete pvc -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" --force --grace-period=0 2>/dev/null || echo "PVC 已删除"
    else
        echo "未找到关联的 PVC"
    fi
    echo
fi

# 检查清理结果
echo "✅ 清理完成"
echo
echo "验证结果:"
echo "  Helm Release: $(helm status "$RELEASE_NAME" -n "$NAMESPACE" 2>/dev/null && echo "仍存在" || echo "已删除")"
echo "  Pod 数量: $(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" 2>/dev/null | wc -l)"
echo "  PVC 数量: $(kubectl get pvc -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" 2>/dev/null | wc -l)"

echo
echo "======================================"
echo "💡 如果还有残留资源，请手动检查:"
echo "  kubectl get all -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME"
echo "  kubectl get pvc -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME"
echo "======================================"
