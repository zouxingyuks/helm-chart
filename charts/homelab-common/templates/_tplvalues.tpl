{{/*
Copyright Broadcom, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
Adapted from Bitnami common 2.41.0. Changes: private namespace and explicit
application compatibility contracts; see README.md and NOTICE.
*/}}
{{- define "homelab.common.tplvalues.render" -}}
{{- $value := typeIs "string" .value | ternary .value (.value | toYaml) }}
{{- if contains "{{" (toJson .value) }}
  {{- if .scope }}
      {{- tpl (cat "{{- with $.RelativeScope -}}" $value "{{- end }}") (merge (dict "RelativeScope" .scope) .context) }}
  {{- else }}
    {{- tpl $value .context }}
  {{- end }}
{{- else }}
    {{- $value }}
{{- end }}
{{- end -}}

{{/* First map wins, including false, zero, empty strings and lists. */}}
{{- define "homelab.common.tplvalues.merge" -}}
{{- if not (hasKey . "values") -}}
{{- fail "homelab.common.tplvalues.merge: values is required (use [] for an empty merge)" -}}
{{- end -}}
{{- if not (kindIs "slice" .values) -}}
{{- fail "homelab.common.tplvalues.merge: values must be a list (use [] for an empty merge)" -}}
{{- end -}}
{{- $dst := dict -}}
{{- range reverse .values -}}
{{- $rendered := include "homelab.common.tplvalues.render" (dict "value" . "context" $.context "scope" $.scope) -}}
{{- $map := fromYaml $rendered -}}
{{- if or (not (kindIs "map" $map)) (hasKey $map "Error") -}}
{{- fail "homelab.common.tplvalues.merge: each rendered value must be a YAML map (Error is reserved)" -}}
{{- end -}}
{{- $dst = mustMergeOverwrite $dst $map -}}
{{- end -}}
{{- toYaml $dst -}}
{{- end -}}
