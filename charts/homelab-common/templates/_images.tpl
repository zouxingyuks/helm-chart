{{/*
Copyright Broadcom, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
Adapted from Bitnami common 2.41.0. Changes: private namespace and explicit
application compatibility contracts; see README.md and NOTICE.
*/}}
{{- define "homelab.common.images.image" -}}
{{- $image := .imageRoot | default dict -}}
{{- $repository := required "homelab.common.images.image: imageRoot.repository is required" $image.repository -}}
{{- $registry := default $image.registry (.global).imageRegistry -}}
{{- $tag := default ((.chart).AppVersion) $image.tag -}}
{{- $termination := "" -}}
{{- if $image.digest -}}
{{- $termination = printf "@%s" $image.digest -}}
{{- else -}}
{{- $termination = printf ":%s" (required "homelab.common.images.image: tag, digest or chart.AppVersion is required" $tag | toString) -}}
{{- end -}}
{{- if $registry -}}
{{- printf "%s/%s%s" $registry $repository $termination -}}
{{- else -}}
{{- printf "%s%s" $repository $termination -}}
{{- end -}}
{{- end -}}
{{- define "homelab.common.images.pullSecrets" -}}
{{- $secrets := list -}}
{{- $sources := list ((.global).imagePullSecrets | default list) (.pullSecrets | default list) -}}
{{- range .images -}}
{{- $sources = append $sources (.pullSecrets | default list) -}}
{{- end -}}
{{- range $sources -}}
{{- range . -}}
{{- $name := . -}}
{{- if kindIs "map" . -}}{{- $name = .name -}}{{- end -}}
{{- if not (kindIs "string" $name) -}}{{- fail "homelab.common.images.pullSecrets: expected string or {name: string}" -}}{{- end -}}
{{- $name = required "homelab.common.images.pullSecrets: secret name cannot be empty" $name -}}
{{- $secrets = append $secrets $name -}}
{{- end -}}
{{- end -}}
{{- if $secrets -}}
imagePullSecrets:
{{- range $secrets | uniq }}
  - name: {{ . | quote }}
{{- end -}}
{{- end -}}
{{- end -}}
