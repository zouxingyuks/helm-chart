|IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning
|Scope:charts/subconverter；遵循根 AGENTS.md；安装与配置说明见 README.md
|事实入口:./:{Chart.yaml,values.yaml,README.md}
|工作负载:templates:{deployment-backend.yaml,deployment-frontend.yaml,service.yaml,_helpers.tpl}；独立 Deployment/Service；后端键位于 backend.*
|路由:templates/ingress.yaml；hosts 非空优先于 hostname；多域名后端须显式 serviceName，不能仅改 servicePort
|配置与存储:templates:{configmap.yaml,pvc.yaml,deployment-backend.yaml}；configmap.yaml 顶层键与 backend.configMode 不一致，修改前核对完整渲染，禁止文档声称已支持一致配置
|扩缩容:templates:{hpa.yaml,hpa-frontend.yaml,pdb.yaml,pdb-frontend.yaml}；核对组件 selector；每组件 PDB 不同时配置 minAvailable/maxUnavailable
|前端:templates/deployment-frontend.yaml；apiURL→VUE_APP_SUBCONVERTER_DEFAULT_BACKEND；默认渲染 Service 地址不代表浏览器可达或镜像运行时支持
|验证:仓库根运行 helm lint charts/subconverter --strict；helm template subconverter charts/subconverter；按变更覆盖组件禁用、Ingress、配置/存储冲突
|边界:本地 lint/template 不证明浏览器连通或镜像行为；部署/port-forward 另按目标环境执行
