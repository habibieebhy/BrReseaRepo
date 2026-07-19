# BRIXTA Production Deployment Runbook

This is the operational record and repeatable production procedure for deploying BRIXTA to a single-node K3s server using Docker Hub images, Infisical secrets, Kubernetes NodePorts, Cloudflare Tunnel, Auth0, Neon PostgreSQL, Redis, MinIO, Celery workers, Celery Beat, MCP, CalculiX, and OpenFOAM.

> Never commit real credentials. Several credentials were exposed during initial deployment and must remain rotated. Store application secrets in Infisical and only deployment bootstrap credentials in the server-side `.env`.

## 1. Production topology

| Component | Kubernetes workload | Image/service |
| --- | --- | --- |
| Dashboard | `deployment/brixta-dashboard` | `brresearepo-dashboard` |
| Python API | `deployment/gateway` | `brresearepo` |
| MCP gateway | `deployment/brixta-mcp` | `brresearepo` |
| Light Celery worker | `deployment/workers-light` | `brresearepo` |
| Embedding worker | `deployment/worker-embeddings` | `brresearepo` |
| Celery Beat | `deployment/brixta-scheduler` | `brresearepo` |
| CalculiX worker | `deployment/worker-simulations-calculix` | `brresearepo-simulations` |
| OpenFOAM worker | `deployment/worker-simulations-openfoam` | `brresearepo-openfoam` |
| Redis | `deployment/redis` | Kubernetes-local service |
| MinIO | `deployment/minio` | Kubernetes-local service and persistent volume |
| PostgreSQL | external | Neon serverless PostgreSQL with pgvector |
| Secrets | external + operator | Infisical → Kubernetes `app-secrets` |
| Public ingress | host-managed | Cloudflare Tunnel → NodePorts |

Production public endpoints:

```text
Dashboard: https://brixta-dashboard.addigitallsolutions.in
MCP:       https://brixta-mcp.addigitallsolutions.in/mcp
Storage:   https://brixta-storage.addigitallsolutions.in
```

NodePorts on the server:

```text
Dashboard: 127.0.0.1:30020
MCP:       127.0.0.1:30021
MinIO UI:  127.0.0.1:30022
```

Cloudflare Tunnel is a reverse tunnel. TLS terminates at Cloudflare; its local origins use HTTP.

## 2. Files that control production

```text
start.sh                         deployment orchestrator
.env                             server-only deployment bootstrap settings
k8s/namespace.yaml              namespace
k8s/infisical-secret.yaml       Infisical synchronization
k8s/pvc.yaml                    persistent volumes
k8s/network-policy.yaml         network policies
k8s/redis.yaml                  Redis
k8s/minio.yaml                  MinIO
k8s/minio-init.yaml             bucket, application user and policy initialization
k8s/drizzle-job.yaml            Neon schema migration Job
k8s/gateway.yaml                Python API
k8s/workers-light.yaml          lightweight Celery worker
k8s/worker-embeddings.yaml      embedding worker
k8s/scheduler.yaml              Celery Beat
k8s/dashboard.yaml              Next.js dashboard and NodePort 30020
k8s/mcp-service.yaml            MCP NodePort 30021
k8s/mcp-deployment.yaml         MCP server
k8s/worker-simulations.yaml     CalculiX worker
k8s/worker-openfoam.yaml        OpenFOAM worker
k8s/hpa.yaml                    horizontal autoscaling
k8s/vpa-embeddings.yaml         optional VPA
infra/migrate.mjs               ordered forward-only migrations
infra/drizzle/*.sql             migration files packaged in the core image
.github/workflows/*             tests, image publishing, package release, deployment
```

Normal releases only require a new immutable image tag in the server `.env`; deployment files only need copying/pulling when `start.sh` or `k8s/*.yaml` themselves change.

## 3. Prerequisites

Server:

- Debian/Ubuntu host
- K3s installed and node `Ready`
- `kubectl`
- Cloudflare Tunnel installed as a system service
- Infisical Secrets Operator installed
- default/local-path storage class
- enough disk for large core/OpenFOAM images and model caches
- Docker Hub images publicly readable, or an image pull secret if private

Verify:

```bash
kubectl get nodes
kubectl get storageclass
kubectl cluster-info
sudo systemctl status cloudflared --no-pager
```

If K3s returns permission denied for `/etc/rancher/k3s/k3s.yaml`, create a user-readable kubeconfig once:

```bash
mkdir -p "$HOME/.kube"
sudo cp /etc/rancher/k3s/k3s.yaml "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
chmod 600 "$HOME/.kube/config"
export KUBECONFIG="$HOME/.kube/config"
kubectl get nodes
```

Persist `KUBECONFIG` in the shell profile if required.

## 4. Docker Hub release workflow

Four images are built:

```text
docker.io/goswamirohit/brresearepo
docker.io/goswamirohit/brresearepo-dashboard
docker.io/goswamirohit/brresearepo-openfoam
docker.io/goswamirohit/brresearepo-simulations
```

Before releasing, update the package/CLI/default deployment versions. Example for `2.1.2`:

```bash
grep -n '^version = ' pyproject.toml
grep -n '"version":' brixta_cli/verify.py
grep -n 'IMAGE_TAG=' start.sh
bash -n start.sh
git diff --check
```

Commit and push:

```bash
git add -A
git commit -m "release: BRIXTA 2.1.2"
git push origin main
```

Create the immutable semantic tag:

```bash
git fetch --tags origin
git tag -l v2.1.2
git ls-remote --tags origin refs/tags/v2.1.2
git tag -a v2.1.2 -m "BRIXTA v2.1.2"
git push origin v2.1.2
```

The main-branch workflow publishes `sha-...` tags. A `v2.1.2` Git tag publishes semantic Docker tags such as `2.1.2` and triggers the Python release asset workflow.

Confirm all four Docker Hub repositories contain the same immutable tag before deploying.

## 5. Server deployment `.env`

The server directory can remain small:

```text
~/brresea/
  .env
  start.sh
  k8s/
```

Example server-only `.env`:

```dotenv
INFISICAL_PROJECT_SLUG=REPLACE_ME
INFISICAL_PROJECT_ID=REPLACE_ME
INFISICAL_ENV_SLUG=prod
INFISICAL_CLIENT_ID=REPLACE_ME
INFISICAL_CLIENT_SECRET=REPLACE_ME

SECRETS_MODE=infisical
BRIXTA_IMAGE_REGISTRY=docker.io/goswamirohit
BRIXTA_IMAGE_TAG=2.1.2
BRIXTA_NAMESPACE=brixta
BRIXTA_DEPLOY_TIMEOUT=900s
```

Protect it:

```bash
chmod 600 ~/brresea/.env
```

`start.sh` loads this file. Application secrets do not belong here; they are synchronized from Infisical.

## 6. Infisical production secrets

Use the `prod` environment. If secrets are stored under an Infisical folder named `addigital`, configure:

```text
Environment: prod
Secret path: /addigital
```

`INFISICAL_ENV_SLUG` remains `prod`; `addigital` is a secret path, not an environment slug.

At minimum, production includes the values validated by `start.sh`, including:

```dotenv
DATABASE_URL=postgresql://...neon...?...sslmode=require
REDIS_PASSWORD=REPLACE_WITH_RANDOM_VALUE
REDIS_URL=redis://:REPLACE_WITH_RANDOM_VALUE@redis-service.brixta.svc.cluster.local:6379/0

ARTIFACT_BACKEND=minio
MINIO_ENDPOINT=minio-service.brixta.svc.cluster.local:9000
MINIO_CONSOLE_URL=https://brixta-storage.addigitallsolutions.in
MINIO_ROOT_USER=REPLACE_ME
MINIO_ROOT_PASSWORD=REPLACE_WITH_RANDOM_VALUE
MINIO_ACCESS_KEY=brixta-app
MINIO_SECRET_KEY=REPLACE_WITH_A_DIFFERENT_RANDOM_VALUE
MINIO_BUCKET=brixta
MINIO_SECURE=false

BRIXTA_ENVIRONMENT=production
BRIXTA_API_PUBLIC_URL=https://brixta-dashboard.addigitallsolutions.in/api/core
BRIXTA_DASHBOARD_PUBLIC_URL=https://brixta-dashboard.addigitallsolutions.in
BRIXTA_CORS_ORIGINS=https://brixta-dashboard.addigitallsolutions.in

APP_BASE_URL=https://brixta-dashboard.addigitallsolutions.in
AUTH0_DOMAIN=YOUR_AUTH0_DOMAIN
AUTH0_CLIENT_ID=REPLACE_ME
AUTH0_CLIENT_SECRET=REPLACE_ME
AUTH0_SECRET=REPLACE_WITH_LONG_RANDOM_VALUE
AUTH0_AUDIENCE=YOUR_EXISTING_AUTH0_API_IDENTIFIER

BRIXTA_AUTH_MODE=jwks
BRIXTA_AUTH_JWKS_URL=https://YOUR_AUTH0_DOMAIN/.well-known/jwks.json
BRIXTA_AUTH_ISSUER=https://YOUR_AUTH0_DOMAIN/
BRIXTA_AUTH_AUDIENCE=YOUR_EXISTING_AUTH0_API_IDENTIFIER
BRIXTA_AUTH_ALGORITHMS=RS256
BRIXTA_AUTHORIZATION_BACKEND=postgres

BRIXTA_MCP_PUBLIC_URL=https://brixta-mcp.addigitallsolutions.in/mcp
BRIXTA_MCP_AUTH_MODE=oauth
BRIXTA_MCP_AUTH0_CONFIG_URL=https://YOUR_AUTH0_DOMAIN/.well-known/openid-configuration
BRIXTA_MCP_AUTH0_CLIENT_ID=REPLACE_ME
BRIXTA_MCP_AUTH0_CLIENT_SECRET=REPLACE_ME
BRIXTA_MCP_AUTH0_AUDIENCE=YOUR_EXISTING_MCP_AUTH0_API_IDENTIFIER
BRIXTA_MCP_OAUTH_SIGNING_KEY=REPLACE_ME
BRIXTA_MCP_OAUTH_STORAGE_KEY=REPLACE_WITH_FERNET_KEY
BRIXTA_MCP_AUTHORIZATION_BACKEND=postgres
```

Auth0 audiences are identifiers, not public routing URLs. Do not change a working audience merely because the public hostname changes; doing so caused Auth0 `Service not found` errors during testing.

Generate a valid Fernet storage key:

```bash
python3 -c 'import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())'
```

It must be a 44-character URL-safe base64 string decoding to exactly 32 bytes.

Validate the synchronized key without printing it:

```bash
kubectl -n brixta get secret app-secrets \
  -o jsonpath='{.data.BRIXTA_MCP_OAUTH_STORAGE_KEY}' \
  | base64 -d \
  | python3 -c '
import sys, base64
value = sys.stdin.read().strip()
decoded = base64.urlsafe_b64decode(value)
print("Text length:", len(value))
print("Decoded length:", len(decoded))
print("Valid:", len(value) == 44 and len(decoded) == 32)
'
```

List synchronized secret key names without revealing values:

```bash
kubectl -n brixta get secret app-secrets \
  -o go-template='{{range $key, $value := .data}}{{printf "%s\n" $key}}{{end}}' \
  | sort
```

## 7. Auth0 production URLs

For the regular web application, configure:

```text
Application Login URI:
https://brixta-dashboard.addigitallsolutions.in/auth/login

Allowed Callback URLs:
http://localhost:3000/auth/callback
https://brixta-dashboard.addigitallsolutions.in/auth/callback

Allowed Logout URLs:
http://localhost:3000
https://brixta-dashboard.addigitallsolutions.in

Allowed Web Origins:
http://localhost:3000
https://brixta-dashboard.addigitallsolutions.in
```

Keep localhost entries for development. Auth0 authenticates identity; BRIXTA stores tenant memberships and roles in PostgreSQL.

## 8. Cloudflare Tunnel and DNS

Use flat hostnames with Universal SSL:

```text
brixta-dashboard.addigitallsolutions.in
brixta-mcp.addigitallsolutions.in
brixta-storage.addigitallsolutions.in
```

Avoid nested names such as `dashboard.brixta.addigitallsolutions.in` on the basic wildcard certificate. That hostname produced a TLS handshake failure while the flat storage hostname worked.

Host-managed Cloudflare configuration:

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /etc/cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: brixta-dashboard.addigitallsolutions.in
    service: http://127.0.0.1:30020

  - hostname: brixta-mcp.addigitallsolutions.in
    service: http://127.0.0.1:30021

  - hostname: brixta-storage.addigitallsolutions.in
    service: http://127.0.0.1:30022

  - service: http_status:404
```

The host-managed tunnel cannot use `*.svc.cluster.local` reliably because that DNS is Kubernetes-internal. Route to NodePorts on `127.0.0.1`.

Create DNS routes:

```bash
cloudflared tunnel route dns YOUR_TUNNEL_ID brixta-dashboard.addigitallsolutions.in
cloudflared tunnel route dns YOUR_TUNNEL_ID brixta-mcp.addigitallsolutions.in
cloudflared tunnel route dns YOUR_TUNNEL_ID brixta-storage.addigitallsolutions.in
```

Validate and restart:

```bash
sudo cloudflared tunnel ingress validate
sudo systemctl restart cloudflared
sudo systemctl status cloudflared --no-pager
sudo journalctl -u cloudflared -n 50 --no-pager
```

Protect the MinIO administration console with Cloudflare Access or do not expose it publicly.

## 9. Deploy or upgrade

Confirm `.env` contains the intended immutable tag:

```bash
cd ~/brresea
grep '^BRIXTA_IMAGE_TAG=' .env
```

Normal deployment:

```bash
./start.sh
```

Do not repeatedly press `Ctrl+C`. The script waits for Kubernetes rollouts. A cancellation message near an internal line number may simply mean the operator interrupted `kubectl rollout status`.

`start.sh` performs:

1. Namespace creation.
2. Infisical bootstrap secret and synchronization.
3. Required secret validation.
4. PVC and network policy application.
5. Redis and MinIO rollout.
6. MinIO bucket/application identity initialization.
7. Neon schema migrations.
8. API, workers, scheduler, dashboard, MCP and simulators.
9. HPA and optional VPA.
10. Final workload/service inventory.

Unlike Docker Compose, Kubernetes does not require `compose down`. Change `BRIXTA_IMAGE_TAG`, then run `./start.sh`; Deployments roll to the new immutable images.

## 10. Neon migration behavior

The migration Job does not create another database. It connects to Neon through `DATABASE_URL`, applies forward-only BRIXTA schema migrations, records checksums in `BrResearch._brixta_migrations`, then exits.

Check it:

```bash
kubectl -n brixta get job brixta-migration
kubectl -n brixta logs -f job/brixta-migration
```

Expected status:

```text
Complete   1/1
```

Notices such as these are harmless:

```text
extension "vector" already exists, skipping
schema "BrResearch" already exists, skipping
relation ... already exists, skipping
```

### Migration failure encountered in v2.1.1

Error:

```text
ENOENT: no such file or directory, open '/app/infra/drizzle/0007_identity_and_access.sql'
```

Cause: `infra/migrate.mjs` referenced `0007_identity_and_access.sql`, but that file was absent from the repository/image. The repair was to add the migration, publish `2.1.2`, update the server image tag, and redeploy. Migration files referenced by `migrationNames` must always be committed and copied into the core image.

## 11. MinIO initialization fix

Initial failure:

```text
CreateContainerConfigError
container has runAsNonRoot and image will run as root
```

The corrected `k8s/minio-init.yaml` runs the MinIO client under an explicit non-root UID and uses `/tmp` as home:

```yaml
env:
  - name: HOME
    value: /tmp
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  seccompProfile:
    type: RuntimeDefault
```

Validate and recreate:

```bash
kubectl apply --dry-run=client -f k8s/minio-init.yaml
kubectl -n brixta delete job minio-init --ignore-not-found
./start.sh
```

Inspect failures:

```bash
kubectl -n brixta get job minio-init
kubectl -n brixta get pods -l job-name=minio-init
kubectl -n brixta describe pod $(kubectl -n brixta get pods -l job-name=minio-init -o jsonpath='{.items[0].metadata.name}')
kubectl -n brixta logs -f job/minio-init
```

## 12. MCP fixes encountered

### Invalid Fernet key

Error:

```text
ValueError: Fernet key must be 32 url-safe base64-encoded bytes
```

Generate the key using the command in the Infisical section, synchronize it, then restart MCP.

### Wrong OIDC discovery URL

Error:

```text
Unable to get OIDC configuration
https://brixta.../.well-known/openid-configuration
```

The discovery URL must point to Auth0:

```dotenv
BRIXTA_MCP_AUTH0_CONFIG_URL=https://YOUR_AUTH0_DOMAIN/.well-known/openid-configuration
```

It must not point to the BRIXTA dashboard.

### Insufficient CPU scheduling

Error:

```text
FailedScheduling: 0/1 nodes are available: Insufficient cpu
```

For the single-node deployment, the persistent MCP resources were reduced to:

```yaml
resources:
  requests:
    cpu: 50m
    memory: 512Mi
  limits:
    cpu: "2"
    memory: 4Gi
```

Emergency live update:

```bash
kubectl -n brixta set resources deployment/brixta-mcp \
  --requests=cpu=50m,memory=512Mi \
  --limits=cpu=2,memory=4Gi
```

Always persist the same change in `k8s/mcp-deployment.yaml`; otherwise the next `start.sh` restores the checked-in values.

Restart and inspect:

```bash
kubectl -n brixta rollout restart deployment/brixta-mcp
kubectl -n brixta rollout status deployment/brixta-mcp --timeout=5m
kubectl -n brixta logs -f deployment/brixta-mcp
```

The Authlib/JOSERFC deprecation message is a warning, not a startup failure.

## 13. Celery Beat scheduler fix

Failure:

```text
_gdbm.error: No such file or directory: '/app/storage/control-plane/celerybeat-schedule'
```

The PVC mounted `/app/storage`, but the nested directory did not exist. The persistent scheduler command must create it before starting Beat:

```yaml
command:
  - /bin/sh
  - -ec
args:
  - |
    mkdir -p /app/storage/control-plane
    exec python -m celery \
      -A runtime.celery_app.celery \
      beat \
      --loglevel=info \
      --schedule=/app/storage/control-plane/celerybeat-schedule
```

Emergency live patch:

```bash
kubectl -n brixta patch deployment brixta-scheduler \
  --type=strategic \
  -p '{
    "spec":{"template":{"spec":{"containers":[{
      "name":"celery-beat",
      "command":["/bin/sh","-ec"],
      "args":["mkdir -p /app/storage/control-plane\nexec python -m celery -A runtime.celery_app.celery beat --loglevel=info --schedule=/app/storage/control-plane/celerybeat-schedule"]
    }]}}}
  }'
```

Verify:

```bash
kubectl -n brixta rollout status deployment/brixta-scheduler --timeout=5m
kubectl -n brixta logs -f deployment/brixta-scheduler
```

Expected log:

```text
beat: Starting...
```

## 14. Operational checks

All BRIXTA pods:

```bash
kubectl -n brixta get pods
kubectl -n brixta get pods -o wide
kubectl -n brixta get pods -w
```

All namespaces:

```bash
kubectl get pods --all-namespaces
```

Full BRIXTA inventory:

```bash
kubectl -n brixta get pods,deployments,jobs,services -o wide
```

Deployment audit:

```bash
for deployment in $(kubectl -n brixta get deployments -o name); do
  echo "===== $deployment ====="
  kubectl -n brixta rollout status "$deployment" --timeout=30s || true
done
```

Restart counts:

```bash
kubectl -n brixta get pods \
  -o custom-columns='NAME:.metadata.name,READY:.status.containerStatuses[0].ready,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount'
```

Recent warnings:

```bash
kubectl -n brixta get events \
  --field-selector type=Warning \
  --sort-by='.lastTimestamp' \
  | tail -n 30
```

Node reservations:

```bash
kubectl describe node debian | sed -n '/Allocated resources:/,/Events:/p'
```

Service logs:

```bash
kubectl -n brixta logs -f deployment/gateway
kubectl -n brixta logs -f deployment/workers-light
kubectl -n brixta logs -f deployment/worker-embeddings
kubectl -n brixta logs -f deployment/brixta-scheduler
kubectl -n brixta logs -f deployment/brixta-mcp
kubectl -n brixta logs -f deployment/worker-simulations-calculix
kubectl -n brixta logs -f deployment/worker-simulations-openfoam
```

Previous crashed container:

```bash
kubectl -n brixta logs deployment/DEPLOYMENT_NAME --previous --tail=150
```

## 15. Reachability tests

Local NodePorts:

```bash
curl -sS -o /dev/null -w 'Dashboard: %{http_code}\n' http://127.0.0.1:30020
curl -sS -o /dev/null -w 'MCP: %{http_code}\n' http://127.0.0.1:30021/mcp
curl -sS -o /dev/null -w 'MinIO: %{http_code}\n' http://127.0.0.1:30022
```

Public endpoints:

```bash
curl -sS -o /dev/null -w 'Dashboard: %{http_code}\n' https://brixta-dashboard.addigitallsolutions.in
curl -sS -o /dev/null -w 'API health: %{http_code}\n' https://brixta-dashboard.addigitallsolutions.in/api/core/health
curl -sS -o /dev/null -w 'MCP: %{http_code}\n' https://brixta-mcp.addigitallsolutions.in/mcp
curl -sS -o /dev/null -w 'Storage: %{http_code}\n' https://brixta-storage.addigitallsolutions.in
```

MCP can validly return `401`, `405`, or `406` to a plain curl request. A response proves reachability; `000`, timeout, or connection refusal indicates routing failure.

Detailed TLS diagnosis:

```bash
curl -vkI https://HOSTNAME
```

## 16. Production acceptance test

1. Open `https://brixta-dashboard.addigitallsolutions.in`.
2. Confirm the BRIXTA login flow appears.
3. Authenticate through Auth0.
4. Confirm BRIXTA resolves or provisions the PostgreSQL tenant membership.
5. Open the dashboard and verify API health.
6. Ingest one small URL or document.
7. Watch light and embedding worker logs.
8. Confirm the job completes and a knowledge base appears.
9. Run one small CalculiX/OpenFOAM preflight or approved simulation.
10. Add `https://brixta-mcp.addigitallsolutions.in/mcp` to ChatGPT and complete OAuth approval.
11. Ask ChatGPT to list BRIXTA knowledge bases.

## 17. Definition of healthy

```bash
kubectl -n brixta get deployments
```

Every deployment should report all replicas ready, normally `1/1` for this server:

```text
brixta-dashboard
brixta-mcp
brixta-scheduler
gateway
minio
redis
worker-embeddings
worker-simulations-calculix
worker-simulations-openfoam
workers-light
```

Migration and initialization Jobs should be `Complete`. Historical restart counts and old warning Events do not indicate a current failure if the newest pods are ready and stable.

## 18. Rules learned during the first deployment

1. Do not embed secrets in Git or documentation.
2. Do not use mutable `latest` tags for production.
3. Do not rerun `start.sh` repeatedly while it is legitimately waiting for a large image pull.
4. Inspect pod Events for `Pending` and `CreateContainerConfigError`; logs do not exist until a container starts.
5. A successful database connection does not mean every migration file was packaged.
6. Persist every emergency `kubectl patch` in the corresponding YAML.
7. The host Cloudflare daemon routes to NodePorts, not Kubernetes-internal DNS.
8. Use flat hostnames on basic Universal SSL.
9. Auth0 audiences and public URLs solve different problems.
10. MCP OIDC discovery points to Auth0, while MCP public URL points to BRIXTA.
11. External Neon still requires BRIXTA schema migrations.
12. On a single node, realistic resource requests matter; limits may remain higher for bursts.

## 19. Routine future upgrade

After CI publishes all four images under a new immutable tag:

```bash
cd ~/brresea
nano .env
```

Change only:

```dotenv
BRIXTA_IMAGE_TAG=NEXT_VERSION
```

Then:

```bash
./start.sh
kubectl -n brixta get pods -w
```

If `start.sh` or a Kubernetes manifest changed in the release, copy/pull those deployment files first. If only application code changed, updating the image tag is sufficient.
