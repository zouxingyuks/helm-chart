# SUBCONVERTER CHART

订阅转换工具 Chart（v1.0.0），仓库中模板最多的 Chart——双容器架构 + 多域名 Ingress。

## WHERE TO LOOK

| 任务 | 文件 | 备注 |
|------|------|------|
| 后端部署 | `templates/deployment-backend.yaml` | configMode 三模式切换 |
| 前端部署 | `templates/deployment-frontend.yaml` | Vue.js 环境变量（`VUE_APP_*`） |
| Ingress 路由 | `templates/ingress.yaml` | 单域名 / 多域名两种模式 |
| 组件标签 | `templates/_helpers.tpl` | backend/frontend 独立标签体系 |
| 扩缩容 | `templates/hpa.yaml` + `hpa-frontend.yaml` | 后端/前端独立 HPA |

## UNIQUE PATTERNS

### 双容器架构

同一 Pod 内运行 backend（port 25500）+ frontend（port 80），通过 `localhost` 通信。Service 根据 `frontend.enabled` 条件暴露不同端口：
- 前端启用 → 仅暴露 80
- 前端禁用 → 仅暴露 25500

### 三种 configMode

```
default     → 使用镜像内置配置
configmap   → ConfigMap 挂载（与 persistence 互斥，fail 验证）
customImage → 自定义镜像内嵌配置
```

### 多域名 Ingress

`ingress.hosts[]` 数组，每个 host 生成独立 Ingress 资源（`range` 循环），支持独立 TLS 和 annotations。与单域名 `ingress.hostname` 互斥。

### 组件级 Helper 函数

`_helpers.tpl` 定义了 6 个额外函数：
- `subconverter.backend.fullname` / `frontend.fullname`
- `subconverter.backend.labels` / `frontend.labels`（含 `app.kubernetes.io/component`）
- `subconverter.backend.selectorLabels` / `frontend.selectorLabels`

### checksum 注解

`deployment-backend.yaml` 使用 `sha256sum` 计算 configmap 校验和，ConfigMap 变更自动触发 Pod 重启。

## ANTI-PATTERNS

- `configMode: configmap` + `persistence.enabled: true` → fail（互斥）
- PDB `minAvailable` + `maxUnavailable` 同时设置 → fail
- 前端环境变量不以 `VUE_APP_` 开头 → Vue.js 不识别
