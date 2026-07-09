#!/bin/bash

# Ensure the script stops if any command fails
set -e

# 1. Load the credentials from the .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "❌ Error: .env file not found."
  exit 1
fi

if [ -z "$INFISICAL_CLIENT_ID" ] || [ -z "$INFISICAL_CLIENT_SECRET" ]; then
    echo "❌ Error: Infisical Universal Auth credentials are missing from .env" 
    exit 1 
fi

# 2. Inject Auth Credentials
echo "Injecting Infisical Machine Identity..."
kubectl create secret generic universal-auth-credentials \
  --from-literal=clientId="${INFISICAL_CLIENT_ID}" \
  --from-literal=clientSecret="${INFISICAL_CLIENT_SECRET}" \
  --namespace=default \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Apply Base Infrastructure
echo "Applying Base Infrastructure (Storage & Secret Sync)..."
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/infisical-secret.yaml

# 4. Critical Wait: Ensure Secrets are Synced
echo "Waiting for Infisical Operator to fetch 'app-secrets' from the cloud..."
while ! kubectl get secret app-secrets >/dev/null 2>&1; do
    sleep 2
done
echo "Secrets successfully injected!"

# 5. Apply Message Broker
echo "Starting Redis Broker..."
kubectl apply -f k8s/redis.yaml
# Wait for Redis to be fully operational
kubectl wait --for=condition=ready pod -l app=redis --timeout=60s
echo "Redis is online!"

echo "Starting MinIO..."
kubectl apply -f k8s/minio.yaml
kubectl wait --for=condition=ready pod -l app=minio --timeout=120s
echo "MinIO is online"

# 6. Run Database Migrations
echo "Running Drizzle Database Migrations..."
# Delete the old job if it exists so we can run a fresh one
kubectl delete job drizzle-migration --ignore-not-found
kubectl apply -f k8s/drizzle-job.yaml
# Wait for the migration to finish successfully before starting the API
kubectl wait --for=condition=complete job/drizzle-migration --timeout=120s
echo "Database schema is up to date!"

# 7. Start Application Layer
echo "Starting Gateway API and Task Workers..."
kubectl apply -f k8s/gateway.yaml
kubectl apply -f k8s/workers-light.yaml
kubectl apply -f k8s/worker-embeddings.yaml

# 8. Start Autoscalers
echo "Configuring Autoscalers..."
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/vpa-embeddings.yaml

echo "Deployment completed successfully!"