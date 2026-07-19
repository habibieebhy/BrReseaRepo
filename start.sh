#!/usr/bin/env bash

set -Eeuo pipefail
# Load server deployment settings so ./start.sh is the complete command.
DEPLOY_ENV_FILE="${BRIXTA_DEPLOY_ENV_FILE:-.env}"

if [[ -f "$DEPLOY_ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$DEPLOY_ENV_FILE"
  set +a
fi

NAMESPACE="${BRIXTA_NAMESPACE:-brixta}"
SECRETS_MODE="${SECRETS_MODE:-infisical}"
IMAGE_REGISTRY="${BRIXTA_IMAGE_REGISTRY:-docker.io/goswamirohit}"
IMAGE_TAG="${BRIXTA_IMAGE_TAG:-2.1.1}"
WAIT_TIMEOUT="${BRIXTA_DEPLOY_TIMEOUT:-600s}"

log() {
  printf '\n==> %s\n' "$*"
}

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command '$1' is unavailable."
}

require_value() {
  local name="$1"
  [[ -n "${!name:-}" ]] || fail "Required environment variable '$name' is empty."
}

render_manifest() {
  sed \
    -e "s#docker.io/goswamirohit/brresearepo:[^[:space:]]*#${IMAGE_REGISTRY}/brresearepo:${IMAGE_TAG}#g" \
    -e "s#docker.io/goswamirohit/brresearepo-dashboard:[^[:space:]]*#${IMAGE_REGISTRY}/brresearepo-dashboard:${IMAGE_TAG}#g" \
    -e "s#docker.io/goswamirohit/brresearepo-openfoam:[^[:space:]]*#${IMAGE_REGISTRY}/brresearepo-openfoam:${IMAGE_TAG}#g" \
    -e "s#docker.io/goswamirohit/brresearepo-simulations:[^[:space:]]*#${IMAGE_REGISTRY}/brresearepo-simulations:${IMAGE_TAG}#g" \
    "$1"
}

apply_manifest() {
  local manifest="$1"
  [[ -f "$manifest" ]] || fail "Manifest '$manifest' does not exist."
  render_manifest "$manifest" | kubectl apply -f -
}

wait_for_secret() {
  local secret_name="$1"
  local attempts="${2:-90}"
  local attempt
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if kubectl -n "$NAMESPACE" get secret "$secret_name" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  fail "Secret '$secret_name' was not created in namespace '$NAMESPACE'."
}

require_secret_key() {
  local secret_name="$1"
  local key="$2"
  local encoded
  encoded="$(
    kubectl -n "$NAMESPACE" get secret "$secret_name" \
      -o "jsonpath={.data.${key}}" 2>/dev/null || true
  )"
  [[ -n "$encoded" ]] || fail "Secret '$NAMESPACE/$secret_name' is missing non-empty key '$key'."
}

wait_for_deployment() {
  kubectl -n "$NAMESPACE" rollout status "deployment/$1" --timeout="$WAIT_TIMEOUT"
}

on_error() {
  local line="$1"
  printf '\nDeployment failed near line %s. Current namespace state:\n' "$line" >&2
  kubectl -n "$NAMESPACE" get pods,deployments,jobs,services 2>/dev/null || true
}
trap 'on_error "$LINENO"' ERR

require_command kubectl
require_command sed

[[ "$NAMESPACE" == "brixta" ]] || fail "The checked-in manifests currently require BRIXTA_NAMESPACE=brixta."
[[ "$SECRETS_MODE" == "infisical" || "$SECRETS_MODE" == "existing" ]] \
  || fail "SECRETS_MODE must be 'infisical' or 'existing'."
[[ "$IMAGE_TAG" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] \
  || fail "BRIXTA_IMAGE_TAG contains unsupported characters."

log "Creating the BRIXTA namespace"
kubectl apply -f k8s/namespace.yaml

if [[ "$SECRETS_MODE" == "infisical" ]]; then
  require_value INFISICAL_CLIENT_ID
  require_value INFISICAL_CLIENT_SECRET
  require_value INFISICAL_PROJECT_SLUG
  require_value INFISICAL_ENV_SLUG

  kubectl -n "$NAMESPACE" create secret generic universal-auth-credentials \
    --from-literal=clientId="$INFISICAL_CLIENT_ID" \
    --from-literal=clientSecret="$INFISICAL_CLIENT_SECRET" \
    --dry-run=client -o yaml | kubectl apply -f -

  sed \
    -e "s#projectSlug:.*#projectSlug: \"${INFISICAL_PROJECT_SLUG}\"#" \
    -e "s#envSlug:.*#envSlug: \"${INFISICAL_ENV_SLUG}\"#" \
    k8s/infisical-secret.yaml | kubectl apply -f -
else
  kubectl -n "$NAMESPACE" get secret app-secrets >/dev/null 2>&1 \
    || fail "SECRETS_MODE=existing requires secret '$NAMESPACE/app-secrets'."
fi

log "Waiting for synchronized application secrets"
wait_for_secret app-secrets
required_secret_keys=(
  DATABASE_URL
  REDIS_PASSWORD
  REDIS_URL
  ARTIFACT_BACKEND
  MINIO_ENDPOINT
  MINIO_CONSOLE_URL
  MINIO_ROOT_USER
  MINIO_ROOT_PASSWORD
  MINIO_ACCESS_KEY
  MINIO_SECRET_KEY
  MINIO_BUCKET
  BRIXTA_API_PUBLIC_URL
  BRIXTA_DASHBOARD_PUBLIC_URL
  BRIXTA_CORS_ORIGINS
  BRIXTA_AUTH_MODE
  BRIXTA_AUTH_JWKS_URL
  BRIXTA_AUTH_ISSUER
  BRIXTA_AUTH_AUDIENCE
  AUTH0_DOMAIN
  AUTH0_CLIENT_ID
  AUTH0_CLIENT_SECRET
  AUTH0_SECRET
  AUTH0_AUDIENCE
  APP_BASE_URL
  BRIXTA_MCP_PUBLIC_URL
  BRIXTA_MCP_AUTH_MODE
  BRIXTA_MCP_AUTH0_CONFIG_URL
  BRIXTA_MCP_AUTH0_CLIENT_ID
  BRIXTA_MCP_AUTH0_CLIENT_SECRET
  BRIXTA_MCP_AUTH0_AUDIENCE
  BRIXTA_MCP_OAUTH_SIGNING_KEY
  BRIXTA_MCP_OAUTH_STORAGE_KEY
)
for key in "${required_secret_keys[@]}"; do
  require_secret_key app-secrets "$key"
done

log "Applying storage, network policy, Redis and MinIO"
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/network-policy.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/minio.yaml
wait_for_deployment redis
wait_for_deployment minio

log "Provisioning the MinIO application bucket and identity"
kubectl -n "$NAMESPACE" delete job minio-init --ignore-not-found
kubectl apply -f k8s/minio-init.yaml
kubectl -n "$NAMESPACE" wait --for=condition=complete job/minio-init --timeout="$WAIT_TIMEOUT"

log "Running database migrations with ${IMAGE_REGISTRY}/brresearepo:${IMAGE_TAG}"
kubectl -n "$NAMESPACE" delete job brixta-migration --ignore-not-found
apply_manifest k8s/drizzle-job.yaml
kubectl -n "$NAMESPACE" wait --for=condition=complete job/brixta-migration --timeout="$WAIT_TIMEOUT"

log "Deploying API, workers, scheduler, dashboard and MCP"
apply_manifest k8s/gateway.yaml
apply_manifest k8s/workers-light.yaml
apply_manifest k8s/worker-embeddings.yaml
apply_manifest k8s/scheduler.yaml
apply_manifest k8s/dashboard.yaml
apply_manifest k8s/mcp-service.yaml
apply_manifest k8s/mcp-deployment.yaml
apply_manifest k8s/worker-simulations.yaml
apply_manifest k8s/worker-openfoam.yaml

wait_for_deployment gateway
wait_for_deployment workers-light
wait_for_deployment worker-embeddings
wait_for_deployment brixta-scheduler
wait_for_deployment brixta-dashboard
wait_for_deployment brixta-mcp
wait_for_deployment worker-simulations-calculix
wait_for_deployment worker-simulations-openfoam

log "Applying autoscaling policies"
kubectl apply -f k8s/hpa.yaml
if kubectl api-resources --api-group=autoscaling.k8s.io -o name 2>/dev/null \
  | grep -qx verticalpodautoscalers; then
  kubectl apply -f k8s/vpa-embeddings.yaml
else
  printf 'WARNING: VPA CRDs are not installed; skipping k8s/vpa-embeddings.yaml.\n'
fi

log "BRIXTA deployment completed"
kubectl -n "$NAMESPACE" get pods,deployments,jobs,services
printf '\nHost-managed Cloudflare origins:\n'
printf '  Dashboard: http://127.0.0.1:30020\n'
printf '  MCP:       http://127.0.0.1:30021\n'
printf '  MinIO:     http://127.0.0.1:30022\n'
