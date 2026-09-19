{{/* Match upstream default fullnames, including releases containing component names. */}}
{{- define "tracing-stack.backendName" -}}
{{- include "homelab.common.names.fullname" (dict "Chart" (dict "Name" .name) "Values" (dict) "Release" .Release) -}}
{{- end -}}

{{- define "tracing-stack.prometheusURL" -}}
{{- if .Values.global.prometheus.install -}}
{{- printf "http://%s-prometheus:9090" (include "kube-prometheus-stack.fullname" (dict "Chart" (dict "Name" "monitoring") "Values" (dict) "Release" .Release)) -}}
{{- else -}}
{{- required "global.prometheus.url is required when reusing Prometheus" .Values.global.prometheus.url | trimSuffix "/" -}}
{{- end -}}
{{- end -}}

{{- define "tracing-stack.lokiURL" -}}
{{- if .Values.global.loki.install -}}
{{- printf "http://%s:3100" (include "tracing-stack.backendName" (dict "Release" .Release "name" "loki")) -}}
{{- else -}}
{{- required "global.loki.url is required when reusing Loki" .Values.global.loki.url | trimSuffix "/" -}}
{{- end -}}
{{- end -}}

{{- define "tracing-stack.thanosName" -}}
{{- printf "%s-thanos-%s" (include "homelab.common.names.fullname" .context | trunc 40 | trimSuffix "-") .component -}}
{{- end -}}

{{- define "tracing-stack.metricsQueryURL" -}}
{{- if .Values.thanos.enabled -}}
{{- printf "http://%s:10902" (include "tracing-stack.thanosName" (dict "context" . "component" "query")) -}}
{{- else -}}
{{- include "tracing-stack.prometheusURL" . -}}
{{- end -}}
{{- end -}}
