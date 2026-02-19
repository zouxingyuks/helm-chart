{{/*
渲染期校验规则 — 在 deployment.yaml 顶部 include 触发
*/}}
{{- define "lobehub.validate" -}}

{{/*
规则 1: AUTH_SECRET 必需（existingSecret 模式除外）
*/}}
{{- if not .Values.auth.existingSecret }}
{{- if not .Values.auth.authSecret }}
{{- fail "ERROR: auth.authSecret is required. LobeHub needs AUTH_SECRET for NextAuth signing. Please provide it using --set auth.authSecret=<your-secret> or use --set auth.existingSecret=<secret-name> to reference an existing Secret." }}
{{- end }}

{{/*
规则 2: KEY_VAULTS_SECRET 必需（existingSecret 模式除外）
*/}}
{{- if not .Values.auth.keyVaultsSecret }}
{{- fail "ERROR: auth.keyVaultsSecret is required. LobeHub needs KEY_VAULTS_SECRET for encrypting key vaults. Please provide it using --set auth.keyVaultsSecret=<your-secret> or use --set auth.existingSecret=<secret-name> to reference an existing Secret." }}
{{- end }}
{{- end }}

{{/*
规则 3: database.internal.enabled=true 时仍需显式提供 database.url（指向内置服务）
*/}}
{{- if and .Values.database.internal.enabled (not .Values.database.url) }}
{{- fail "ERROR: database.url is required even when database.internal.enabled=true. The internal PostgreSQL sub-chart does not auto-inject DATABASE_URL. Please provide the connection string pointing to the internal service, e.g. --set database.url=\"postgresql://lobechat:password@<release>-postgresql:5432/lobechat\"." }}
{{- end }}

{{/*
规则 4: redis.internal.enabled=true 时仍需显式提供 redis.url（指向内置服务）
*/}}
{{- if and .Values.redis.internal.enabled (not .Values.redis.url) }}
{{- fail "ERROR: redis.url is required even when redis.internal.enabled=true. The internal Redis sub-chart does not auto-inject REDIS_URL. Please provide the connection string pointing to the internal service, e.g. --set redis.url=\"redis://:password@<release>-redis-master:6379/0\"." }}
{{- end }}

{{/*
规则 5: ingress 启用时 hostname 不能为空
*/}}
{{- if and .Values.ingress.enabled (not .Values.ingress.hostname) }}
{{- fail "ERROR: ingress.hostname is required when ingress.enabled is true. Please provide it using --set ingress.hostname=<your-domain>." }}
{{- end }}

{{/*
规则 6: autoscaling 启用时至少提供一个 metric target
*/}}
{{- if and .Values.autoscaling.enabled (not (or .Values.autoscaling.targetCPUUtilizationPercentage .Values.autoscaling.targetMemoryUtilizationPercentage)) }}
{{- fail "ERROR: autoscaling requires at least one metric target when autoscaling.enabled=true. Please set autoscaling.targetCPUUtilizationPercentage or autoscaling.targetMemoryUtilizationPercentage." }}
{{- end }}

{{- end -}}
