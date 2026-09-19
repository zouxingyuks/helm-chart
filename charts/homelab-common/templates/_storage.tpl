{{/*
Copyright Broadcom, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
Adapted from Bitnami common 2.41.0. Changes: private namespace and explicit
application compatibility contracts; see README.md and NOTICE.
*/}}
{{- define "homelab.common.storage.class" -}}
{{- $class := default ((.global).defaultStorageClass) (.persistence).storageClass -}}
{{- if $class -}}
{{- if eq $class "-" -}}
storageClassName: ""
{{- else -}}
storageClassName: {{ $class | quote }}
{{- end -}}
{{- end -}}
{{- end -}}
{{- define "homelab.common.storage.claimName" -}}
{{- default .defaultName (.persistence).existingClaim | required "homelab.common.storage.claimName: existingClaim or defaultName is required" -}}
{{- end -}}
