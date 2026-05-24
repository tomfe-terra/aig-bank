{{- define "aig-bank.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aig-bank.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "aig-bank.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "aig-bank.labels" -}}
helm.sh/chart: {{ include "aig-bank.name" . }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "aig-bank.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "aig-bank.selectorLabels" -}}
app.kubernetes.io/name: {{ include "aig-bank.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "aig-bank.postgres.fullname" -}}
{{- printf "%s-postgresql" .Release.Name -}}
{{- end -}}

{{- define "aig-bank.api.fullname" -}}
{{- printf "%s-api" (include "aig-bank.fullname" .) -}}
{{- end -}}

{{- define "aig-bank.app.fullname" -}}
{{- printf "%s-app" (include "aig-bank.fullname" .) -}}
{{- end -}}

{{- define "aig-bank.pay.fullname" -}}
{{- printf "%s-pay" (include "aig-bank.fullname" .) -}}
{{- end -}}

{{- define "aig-bank.pgweb.fullname" -}}
{{- printf "%s-pgweb" (include "aig-bank.fullname" .) -}}
{{- end -}}

{{- define "aig-bank.secretName" -}}
{{- printf "%s-secrets" (include "aig-bank.fullname" .) -}}
{{- end -}}

{{- define "aig-bank.configMapName" -}}
{{- printf "%s-config" (include "aig-bank.fullname" .) -}}
{{- end -}}

{{- define "aig-bank.internalAppOrigin" -}}
{{- printf "http://%s.%s.svc.cluster.local" (include "aig-bank.app.fullname" .) .Release.Namespace -}}
{{- end -}}

{{- define "aig-bank.internalPayOrigin" -}}
{{- printf "http://%s.%s.svc.cluster.local" (include "aig-bank.pay.fullname" .) .Release.Namespace -}}
{{- end -}}

{{- define "aig-bank.apiCorsOriginsJson" -}}
{{- if .Values.api.env.corsOrigins -}}
{{- toJson .Values.api.env.corsOrigins -}}
{{- else -}}
{{- toJson (list (printf "https://app.%s" .Values.domain) (printf "https://pay.%s" .Values.domain) (include "aig-bank.internalAppOrigin" .) (include "aig-bank.internalPayOrigin" .)) -}}
{{- end -}}
{{- end -}}

{{- define "aig-bank.payApiEndpoint" -}}
{{- if .Values.pay.env.apiEndpoint -}}
{{- .Values.pay.env.apiEndpoint -}}
{{- else -}}
{{- printf "https://api.%s" .Values.domain -}}
{{- end -}}
{{- end -}}

{{- define "aig-bank.databaseUrl" -}}
{{- printf "postgresql+asyncpg://%s:%s@%s:%v/%s" .Values.postgresql.auth.username .Values.postgresql.auth.password (include "aig-bank.postgres.fullname" .) 5432 .Values.postgresql.auth.database -}}
{{- end -}}

{{- define "aig-bank.pgwebDatabaseUrl" -}}
{{- printf "postgres://%s:%s@%s:%v/%s?sslmode=disable" .Values.postgresql.auth.username .Values.postgresql.auth.password (include "aig-bank.postgres.fullname" .) 5432 .Values.postgresql.auth.database -}}
{{- end -}}
