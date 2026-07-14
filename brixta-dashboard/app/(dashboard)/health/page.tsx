import { ServiceStatusCard } from "@/components/system/ServiceStatusCard";
import { fetchPythonApi } from "@/lib/api";

type Health = { healthy?: boolean; error?: string; provider?: string };
export default async function HealthPage() {
  const endpoints = ["database", "redis", "storage"];
  const values = await Promise.all(endpoints.map((name) => fetchPythonApi(`/prod/health/${name}`, { cache: "no-store" }))) as Health[];
  return <div className="mx-auto max-w-7xl space-y-6 p-6"><div><h1 className="text-3xl font-bold tracking-tight">System health</h1><p className="text-muted-foreground">A failed optional integration is shown as unavailable—not disguised as healthy.</p></div><div className="grid gap-4 md:grid-cols-2">{endpoints.map((name, index) => { const value = values[index]; const connected = value.error && value.healthy === undefined ? null : Boolean(value.healthy); return <ServiceStatusCard key={name} name={name[0].toUpperCase() + name.slice(1)} description={value.provider || "integration"} healthy={connected} detail={value.error} />; })}</div></div>;
}
