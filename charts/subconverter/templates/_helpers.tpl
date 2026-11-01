{{/*
Expand the name of the chart.
*/}}
{{- define "subconverter.name" -}}
{{- include "homelab.common.names.name" . -}}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "subconverter.fullname" -}}
{{- include "homelab.common.names.fullname" . -}}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "subconverter.chart" -}}
{{- include "homelab.common.names.chart" . -}}
{{- end }}

{{/*
Common labels
*/}}
{{- define "subconverter.labels" -}}
{{- include "homelab.common.labels.standard" (dict "context" .) -}}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "subconverter.selectorLabels" -}}
{{- include "homelab.common.labels.selector" (dict "context" .) -}}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "subconverter.serviceAccountName" -}}
{{- include "homelab.common.serviceAccount.name" (dict "context" . "serviceAccount" .Values.serviceAccount) -}}
{{- end }}

{{/*
Backend fully qualified name. Preserve truncation after adding the suffix.
*/}}
{{- define "subconverter.backend.fullname" -}}
{{- printf "%s-backend" (include "subconverter.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Frontend fully qualified name
*/}}
{{- define "subconverter.frontend.fullname" -}}
{{- printf "%s-frontend" (include "subconverter.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Backend labels
*/}}
{{- define "subconverter.backend.labels" -}}
{{- include "homelab.common.labels.standard" (dict "context" . "component" "backend") -}}
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "subconverter.frontend.labels" -}}
{{- include "homelab.common.labels.standard" (dict "context" . "component" "frontend") -}}
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "subconverter.backend.selectorLabels" -}}
{{- include "homelab.common.labels.selector" (dict "context" . "component" "backend") -}}
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "subconverter.frontend.selectorLabels" -}}
{{- include "homelab.common.labels.selector" (dict "context" . "component" "frontend") -}}
{{- end }}

{{/*
Backend PVC identity: the original fullname receives an untruncated -config suffix.
*/}}
{{- define "subconverter.backend.claimName" -}}
{{- include "homelab.common.storage.claimName" (dict "persistence" .Values.backend.persistence "defaultName" (printf "%s-config" (include "subconverter.fullname" .))) -}}
{{- end }}
