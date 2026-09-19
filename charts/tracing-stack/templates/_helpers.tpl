{{/* Match upstream default fullnames, including releases containing component names. */}}
{{- define "tracing-stack.backendName" -}}
{{- include "homelab.common.names.fullname" (dict "Chart" (dict "Name" .name) "Values" (dict) "Release" .Release) -}}
{{- end -}}

{{- define "tracing-stack.prometheusURL" -}}
{{- if .Values.global.prometheus.install -}}
{{- $name := printf "%s-prometheus-server" .Release.Name -}}
{{- if contains "prometheus" .Release.Name -}}
{{- $name = printf "%s-server" .Release.Name -}}
{{- end -}}
{{- printf "http://%s:80" ($name | trunc 63 | trimSuffix "-") -}}
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
