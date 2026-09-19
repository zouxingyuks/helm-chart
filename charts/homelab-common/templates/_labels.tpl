{{/*
Copyright Broadcom, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
Adapted from Bitnami common 2.41.0. Changes: private namespace and explicit
application compatibility contracts; see README.md and NOTICE.
*/}}
{{- define "homelab.common.labels.selector" -}}
{{- $labels := dict "app.kubernetes.io/name" (include "homelab.common.names.name" .context) "app.kubernetes.io/instance" .context.Release.Name -}}
{{- with .component -}}
{{- $_ := set $labels "app.kubernetes.io/component" . -}}
{{- end -}}
{{- toYaml $labels -}}
{{- end -}}
{{- define "homelab.common.labels.standard" -}}
{{- $labels := deepCopy (.customLabels | default dict) -}}
{{- $_ := set $labels "helm.sh/chart" (include "homelab.common.names.chart" .context) -}}
{{- $_ := set $labels "app.kubernetes.io/managed-by" .context.Release.Service -}}
{{- with .context.Chart.AppVersion -}}
{{- $_ := set $labels "app.kubernetes.io/version" (toString .) -}}
{{- end -}}
{{- $selector := include "homelab.common.labels.selector" . | fromYaml -}}
{{- mustMergeOverwrite $labels $selector | toYaml -}}
{{- end -}}
