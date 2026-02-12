#!/bin/bash
# diagnose_pods.sh - 诊断指定命名空间中 Pod 状态的通用脚本
#
# 用法: ./diagnose_pods.sh <namespace> [pod-name]
#
# 示例:
#   ./diagnose_pods.sh default              # 检查命名空间所有 Pod
#   ./diagnose_pods.sh dify my-pod          # 检查特定 Pod

set -e

NAMESPACE="${1:-default}"
POD_NAME="${2:-}"

echo "======================================"
echo "Pod 诊断工具"
echo "命名空间: $NAMESPACE"
echo "======================================"
echo

# 获取所有 Pod（如果未指定 Pod 名称）
if [ -z "$POD_NAME" ]; then
    echo "📊 Pod 列表:"
    kubectl get pods -n "$NAMESPACE" -o wide
    echo

    # 检查是否有异常 Pod
    PENDING_PODS=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Pending -o name)
    FAILED_PODS=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed -o name)

    if [ -n "$PENDING_PODS" ]; then
        echo "⚠️  发现 Pending 状态的 Pod:"
        echo "$PENDING_PODS"
        echo
    fi

    if [ -n "$FAILED_PODS" ]; then
        echo "❌ 发现 Failed 状态的 Pod:"
        echo "$FAILED_PODS"
        echo
    fi
fi

# 诊断特定 Pod 或所有异常 Pod
diagnose_pod() {
    local pod=$1

    echo "--------------------------------------"
    echo "🔍 诊断 Pod: $pod"
    echo "--------------------------------------"

    # Pod 基本信息
    echo "📋 Pod 详细信息:"
    kubectl describe pod -n "$NAMESPACE" "$pod" | tail -n +2 | head -20
    echo

    # Pod 事件
    echo "📅 Pod 事件:"
    kubectl describe pod -n "$NAMESPACE" "$pod" | grep -A 20 "Events:"
    echo

    # Pod 日志（如果有容器在运行）
    echo "📝 Pod 日志（最近 50 行）:"
    kubectl logs -n "$NAMESPACE" "$pod" --tail=50 2>/dev/null || echo "无法获取日志（Pod 可能尚未启动）"
    echo
}

# 如果指定了 Pod 名称，只诊断该 Pod
if [ -n "$POD_NAME" ]; then
    diagnose_pod "$POD_NAME"
else
    # 否则诊断所有异常 Pod
    if [ -n "$PENDING_PODS" ]; then
        echo "$PENDING_PODS" | while read -r pod; do
            diagnose_pod "$(basename "$pod")"
        done
    fi

    if [ -n "$FAILED_PODS" ]; then
        echo "$FAILED_PODS" | while read -r pod; do
            diagnose_pod "$(basename "$pod")"
        done
    fi
fi

echo "======================================"
echo "✅ 诊断完成"
echo "======================================"
