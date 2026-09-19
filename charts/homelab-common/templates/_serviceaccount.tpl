{{/* SPDX-License-Identifier: APACHE-2.0 */}}
{{- define "homelab.common.serviceAccount.name" -}}
{{- $account := .serviceAccount | default dict -}}
{{- if $account.create -}}
{{- default (include "homelab.common.names.fullname" .context) $account.name -}}
{{- else -}}
{{- default "default" $account.name -}}
{{- end -}}
{{- end -}}
