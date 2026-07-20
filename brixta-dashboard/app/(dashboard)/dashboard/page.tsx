import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ServiceStatusCard } from "@/components/system/ServiceStatusCard";
import { fetchPythonApiServer } from "@/lib/server-api";

type Health = { healthy?: boolean; error?: string; provider?: string; status?: string };

export default async function DashboardOverview() {
  const principal = await fetchPythonApiServer("/auth/me") as { is_admin?: boolean };
  const [core, celery, docker, storage, redis] = await Promise.all([
    fetchPythonApiServer("/health"),
    principal.is_admin ? fetchPythonApiServer("/prod/celery") : Promise.resolve({}),
    principal.is_admin ? fetchPythonApiServer("/prod/docker") : Promise.resolve({}),
    principal.is_admin ? fetchPythonApiServer("/prod/storage") : Promise.resolve({}),
    principal.is_admin ? fetchPythonApiServer("/prod/redis") : Promise.resolve({}),
  ]) as Health[];
  const state = (value: Health) => value.error && value.healthy === undefined ? null : Boolean(value.healthy ?? value.status === "healthy");
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mission Control</h1>
          <p className="text-muted-foreground">Your tenant workspace and BRIXTA service availability.</p>
        </div>
        <div className="flex gap-2">
          {/* Added nativeButton={false} to both buttons */}
          <Button render={<Link href="/sources" />} nativeButton={false}>
            Add source
          </Button>
          <Button variant="outline" render={<Link href="/ingestion" />} nativeButton={false}>
            Run pipeline
          </Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <ServiceStatusCard name="BRIXTA Core" description="FastAPI control plane" healthy={state(core)} detail={core.error} />
        {principal.is_admin && (
          <>
            <ServiceStatusCard name="Celery" description="Pipeline workers" healthy={state(celery)} detail={celery.error} />
            <ServiceStatusCard name="Redis" description="Broker and queue state" healthy={state(redis)} detail={redis.error} />
            <ServiceStatusCard name="Artifact storage" description="Local or MinIO backend" healthy={state(storage)} detail={storage.provider} />
            <ServiceStatusCard name="Docker" description="Local container engine" healthy={state(docker)} detail={docker.error} />
          </>
        )}
      </div>
    </div>
  );
}
