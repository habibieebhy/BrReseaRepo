import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const commands = [
  "docker start brixta-redis || docker run -d --name brixta-redis -p 6379:6379 redis:7",
  "docker start brixta-minio || docker run -d --name brixta-minio -p 9000:9000 -p 9001:9001 -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin -v ~/minio-data:/data quay.io/minio/minio server /data --console-address :9001",
  "python -m uvicorn api.main:app --reload",
  "python -m celery -A runtime.celery_app.celery worker --loglevel=info",
  "python -m celery -A runtime.celery_app.celery beat --loglevel=info",
  "cd brixta-dashboard && npm run dev",
];

export default function DocsPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div><h1 className="text-3xl font-bold tracking-tight">Local operations</h1><p className="text-muted-foreground">Processes required for the complete self-hosted development loop.</p></div>
      <Card><CardHeader><CardTitle>Start BRIXTA</CardTitle><CardDescription>Run each command in its own terminal with the Python environment activated.</CardDescription></CardHeader><CardContent className="space-y-2">{commands.map((command) => <pre key={command} className="overflow-auto bg-muted p-3 text-xs">{command}</pre>)}</CardContent></Card>
    </div>
  );
}
