{{/*
Expand the name of the chart.
*/}}
{{- define "booklore.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "booklore.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "booklore.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "booklore.labels" -}}
helm.sh/chart: {{ include "booklore.chart" . }}
{{ include "booklore.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "booklore.selectorLabels" -}}
app.kubernetes.io/name: {{ include "booklore.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "booklore.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "booklore.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get MariaDB host
*/}}
{{- define "booklore.mariadb.host" -}}
{{- if .Values.mariadb.enabled }}
{{- printf "%s-%s" .Release.Name .Values.mariadb.serviceName | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- .Values.externalDatabase.host }}
{{- end }}
{{- end }}

{{/*
Get MariaDB secret name
*/}}
{{- define "booklore.mariadb.secretName" -}}
{{- if .Values.mariadb.auth.existingSecret }}
{{- .Values.mariadb.auth.existingSecret }}
{{- else }}
{{- printf "%s-%s" .Release.Name "mariadb" | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Get MariaDB secret key
*/}}
{{- define "booklore.mariadb.secretKey" -}}
{{- if .Values.mariadb.auth.existingSecret }}
{{- if .Values.mariadb.auth.existingSecretPasswordKey }}
{{- .Values.mariadb.auth.existingSecretPasswordKey }}
{{- else }}
{{- "mariadb-password" }}
{{- end }}
{{- else }}
{{- "mariadb-password" }}
{{- end }}
{{- end }}

{{/*
Get external database secret name
*/}}
{{- define "booklore.externalDatabase.secretName" -}}
{{- if .Values.externalDatabase.existingSecret }}
{{- .Values.externalDatabase.existingSecret }}
{{- else }}
{{- printf "%s-external-db" (include "booklore.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Get external database secret key
*/}}
{{- define "booklore.externalDatabase.secretKey" -}}
{{- "password" }}
{{- end }}
