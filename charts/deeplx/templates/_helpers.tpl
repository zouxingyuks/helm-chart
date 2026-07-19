{{/* DeepLX helpers. */}}
{{- define "deeplx.name" -}}
{{- include "common.names.name" . -}}
{{- end -}}

{{- define "deeplx.fullname" -}}
{{- include "common.names.fullname" . -}}
{{- end -}}

{{- define "deeplx.namespace" -}}
{{- include "common.names.namespace" . -}}
{{- end -}}

{{- define "deeplx.labels" -}}
{{- include "common.labels.standard" (dict "customLabels" .Values.commonLabels "context" $) -}}
{{- end -}}

{{- define "deeplx.selectorLabels" -}}
{{- include "common.labels.matchLabels" . -}}
{{- end -}}

{{- define "deeplx.podLabels" -}}
{{- $customLabels := include "common.tplvalues.render" (dict "value" .Values.podLabels "context" $) | fromYaml -}}
{{- $selectorLabels := include "deeplx.selectorLabels" . | fromYaml -}}
{{- merge $selectorLabels $customLabels | toYaml -}}
{{- end -}}

{{- define "deeplx.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "deeplx.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "deeplx.secretName" -}}
{{- include "common.secrets.name" (dict "existingSecret" .Values.auth.existingSecret "context" $) -}}
{{- end -}}

{{- define "deeplx.ingressName" -}}
{{- $hostname := .hostname | lower -}}
{{- $sanitized := $hostname | replace "." "-" | replace "_" "-" -}}
{{- $base := printf "%s-%s" (include "deeplx.fullname" .context) $sanitized -}}
{{- printf "%s-%s" ($base | trunc 54 | trimSuffix "-") ($hostname | sha256sum | trunc 8) -}}
{{- end -}}

{{- define "deeplx.authEnabled" -}}
{{- if or .Values.auth.existingSecret.name .Values.auth.token .Values.auth.dlSession .Values.auth.proxy -}}true{{- end -}}
{{- end -}}

{{- define "deeplx.presetAffinity" -}}
{{- with .Values.podAffinityPreset }}
podAffinity:
  {{- include "common.affinities.pods" (dict "type" . "customLabels" (dict) "context" $) | nindent 2 }}
{{- end }}
{{- with .Values.podAntiAffinityPreset }}
podAntiAffinity:
  {{- include "common.affinities.pods" (dict "type" . "customLabels" (dict) "context" $) | nindent 2 }}
{{- end }}
{{- with .Values.nodeAffinityPreset.type }}
nodeAffinity:
  {{- include "common.affinities.nodes" (dict "type" . "key" $.Values.nodeAffinityPreset.key "values" $.Values.nodeAffinityPreset.values) | nindent 2 }}
{{- end }}
{{- end -}}
