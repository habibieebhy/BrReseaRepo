import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ServiceStatusCard } from "@/components/system/ServiceStatusCard";
import { fetchPythonApi } from "@/lib/api";

type Health = { healthy?: boolean; error?: string; provider?: string; status?: string };

export default async function DashboardOverview() {
  const [core, celery, docker, storage, redis] = await Promise.all([
    fetchPythonApi("/health", { cache: "no-store" }), fetchPythonApi("/prod/celery", { cache: "no-store" }), fetchPythonApi("/prod/docker", { cache: "no-store" }), fetchPythonApi("/prod/storage", { cache: "no-store" }), fetchPythonApi("/prod/redis", { cache: "no-store" }),
  ]) as Health[];
  const state = (value: Health) => value.error && value.healthy === undefined ? null : Boolean(value.healthy ?? value.status === "healthy");
  return <div className="mx-auto max-w-7xl space-y-6 p-6"><div className="flex flex-wrap items-center justify-between gap-4"><div><h1 className="text-3xl font-bold tracking-tight">Mission Control</h1><p className="text-muted-foreground">Live application and local infrastructure availability.</p></div><div className="flex gap-2"><Button render={<Link href="/sources" />}>Add source</Button><Button variant="outline" render={<Link href="/ingestion" />}>Run pipeline</Button></div></div><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"><ServiceStatusCard name="BRIXTA Core" description="FastAPI control plane" healthy={state(core)} detail={core.error} /><ServiceStatusCard name="Celery" description="Pipeline workers" healthy={state(celery)} detail={celery.error} /><ServiceStatusCard name="Redis" description="Broker and queue state" healthy={state(redis)} detail={redis.error} /><ServiceStatusCard name="Artifact storage" description="Local or MinIO backend" healthy={state(storage)} detail={storage.provider} /><ServiceStatusCard name="Docker" description="Local container engine" healthy={state(docker)} detail={docker.error} /></div></div>;
}
