#!/bin/bash
# check_helm_release.sh - 检查 Helm Release 状态的通用脚本
#
# 用法: ./check_helm_release.sh <release-name> [namespace]
#
# 示例:
#   ./check_helm_release.sh dify dify
#   ./check_helm_release.sh my-app default

set -e

RELEASE_NAME="${1}"
NAMESPACE="${2:-default}"

if [ -z "$RELEASE_NAME" ]; then
    echo "❌ 错误: 请提供 Helm Release 名称"
    echo "用法: $0 <release-name> [namespace]"
    exit 1
fi

echo "======================================"
echo "Helm Release 检查工具"
echo "Release: $RELEASE_NAME"
echo "命名空间: $NAMESPACE"
echo "======================================"
echo

# 检查 Helm Release 状态
echo "📊 Helm Release 状态:"
if helm status "$RELEASE_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
    helm status "$RELEASE_NAME" -n "$NAMESPACE"
    echo
else
    echo "❌ Release '$RELEASE_NAME' 不存在于命名空间 '$NAMESPACE'"
    exit 1
fi

# 获取 Release 的所有资源
echo "🔍 Release 关联资源:"
echo
echo "Deployments:"
kubectl get deployments -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" 2>/dev/null || echo "无"
echo
echo "StatefulSets:"
kubectl get statefulsets -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" 2>/dev/null || echo "无"
echo
echo "Services:"
kubectl get services -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" 2>/dev/null || echo "无"
echo
echo "Ingress:"
kubectl get ingress -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" 2>/dev/null || echo "无"
echo
echo "PVCs:"
kubectl get pvc -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" 2>/dev/null || echo "无"
echo

# 检查 Pod 状态
echo "📦 Pod 状态:"
PODS=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" -o name)
if [ -n "$PODS" ]; then
    kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME"

    # 检查是否有异常 Pod
    PENDING_PODS=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" --field-selector=status.phase=Pending -o name)
    CRASH_LOOP_PODS=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" --field-selector=status.phase!=Running -o name)

    if [ -n "$PENDING_PODS" ]; then
        echo
        echo "⚠️  发现 Pending 状态的 Pod:"
        echo "$PENDING_PODS"
    fi

    if [ -n "$CRASH_LOOP_PODS" ]; then
        echo
        echo "❌ 发现非 Running 状态的 Pod:"
        echo "$CRASH_LOOP_PODS"
    fi
else
    echo "无 Pod"
fi
echo

# 获取 Release 历史
echo "📜 Release 历史:"
helm history "$RELEASE_NAME" -n "$NAMESPACE" -o json | jq -r '.[] | "\(.revision): \(.status) - \(.description)"' 2>/dev/null || helm history "$RELEASE_NAME" -n "$NAMESPACE"
echo

# 检查 Values 文件
echo "🔧 获取当前 Values:"
echo "命令: helm get values $RELEASE_NAME -n $NAMESPACE"
echo

echo "======================================"
echo "✅ 检查完成"
echo "======================================"
echo
echo "💡 常用操作:"
echo "  查看 Release 详情: helm status $RELEASE_NAME -n $NAMESPACE"
echo "  获取 Values: helm get values $RELEASE_NAME -n $NAMESPACE -a"
echo "  获取 Manifests: helm get manifest $RELEASE_NAME -n $NAMESPACE"
echo "  升级 Release: helm upgrade $RELEASE_NAME <chart> -n $NAMESPACE"
echo "  回滚 Release: helm rollback $RELEASE_NAME -n $NAMESPACE"
