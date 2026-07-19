{{/* 渲染期跨字段校验。 */}}
{{- define "deeplx.validate" -}}
{{- $hasInlineAuth := or .Values.auth.token .Values.auth.dlSession .Values.auth.proxy -}}
{{- if and .Values.auth.existingSecret.name $hasInlineAuth -}}
{{- fail "ERROR: auth.existingSecret.name is mutually exclusive with auth.token, auth.dlSession, and auth.proxy. Choose exactly one credential source." -}}
{{- end -}}

{{- $managedEnvVars := list "IP" "PORT" "TOKEN" "DL_SESSION" "PROXY" -}}
{{- range $index, $envVar := .Values.extraEnvVars -}}
{{- if has $envVar.name $managedEnvVars -}}
{{- fail (printf "ERROR: extraEnvVars[%d].name %q is managed by the Chart and cannot be overridden. Reserved names: IP, PORT, TOKEN, DL_SESSION, PROXY." $index $envVar.name) -}}
{{- end -}}
{{- end -}}

{{- if .Values.ingress.enabled -}}
{{- if eq (len .Values.ingress.hosts) 0 -}}
{{- fail "ERROR: ingress.hosts must contain at least one host when ingress.enabled=true." -}}
{{- end -}}
{{- $hostnames := dict -}}
{{- range $index, $host := .Values.ingress.hosts -}}
{{- if not $host.hostname -}}
{{- fail (printf "ERROR: ingress.hosts[%d].hostname is required when ingress.enabled=true." $index) -}}
{{- end -}}
{{- $hostname := $host.hostname | lower -}}
{{- if hasKey $hostnames $hostname -}}
{{- fail (printf "ERROR: ingress.hosts contains duplicate hostname %q; each host must be unique." $host.hostname) -}}
{{- end -}}
{{- $_ := set $hostnames $hostname true -}}
{{- end -}}
{{- end -}}

{{- if .Values.autoscaling.enabled -}}
{{- if lt (int .Values.autoscaling.maxReplicas) (int .Values.autoscaling.minReplicas) -}}
{{- fail "ERROR: autoscaling.maxReplicas must be greater than or equal to autoscaling.minReplicas." -}}
{{- end -}}
{{- if not (or .Values.autoscaling.targetCPUUtilizationPercentage .Values.autoscaling.targetMemoryUtilizationPercentage) -}}
{{- fail "ERROR: autoscaling requires at least one CPU or memory metric when autoscaling.enabled=true." -}}
{{- end -}}
{{- end -}}

{{- if .Values.podDisruptionBudget.enabled -}}
{{- $minSet := not (kindIs "invalid" .Values.podDisruptionBudget.minAvailable) -}}
{{- $maxSet := not (kindIs "invalid" .Values.podDisruptionBudget.maxUnavailable) -}}
{{- if eq $minSet $maxSet -}}
{{- fail "ERROR: podDisruptionBudget requires exactly one of minAvailable or maxUnavailable when enabled." -}}
{{- end -}}
{{- $value := ternary .Values.podDisruptionBudget.minAvailable .Values.podDisruptionBudget.maxUnavailable $minSet -}}
{{- if or (eq (toString $value) "0") (eq (toString $value) "0%") -}}
{{- fail "ERROR: podDisruptionBudget minAvailable or maxUnavailable must be greater than zero when enabled." -}}
{{- end -}}
{{- end -}}
{{- end -}}
