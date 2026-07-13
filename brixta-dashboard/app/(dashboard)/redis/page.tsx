import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchPythonApi } from "@/lib/api";

interface Queue { name: string; pending: number }
interface Container { name: string; image: string; status: string }
export default async function RedisPage() {
  const [health, queues, docker] = await Promise.all([fetchPythonApi("/prod/redis", { cache: "no-store" }), fetchPythonApi("/prod/redis/queues", { cache: "no-store" }), fetchPythonApi("/prod/docker/containers", { cache: "no-store" })]) as [{ healthy?: boolean; error?: string }, { queues?: Queue[] }, { containers?: Container[] }];
  const container = (docker.containers || []).find((item) => item.name.toLowerCase().includes("redis") || item.image.toLowerCase().includes("redis"));
  return <div className="mx-auto max-w-7xl space-y-6 p-6"><div className="flex flex-wrap items-center justify-between gap-4"><div><h1 className="text-3xl font-bold tracking-tight">Redis</h1><p className="text-muted-foreground">Broker connectivity and pending Celery messages.</p></div>{container && <Button variant="outline" render={<Link href={`/docker/${container.name}`} />}>Manage container</Button>}</div><div className={`border p-4 ${health.healthy ? "border-primary/20 bg-primary/5" : "border-destructive/30 bg-destructive/10"}`}><div className="flex items-center gap-2"><p className="font-medium">Redis broker</p><Badge variant={health.healthy ? "default" : "destructive"}>{health.healthy ? "connected" : "unavailable"}</Badge></div>{health.error && <p className="mt-2 text-xs text-muted-foreground">{health.error}</p>}</div><Card><CardHeader><CardTitle>Queues</CardTitle><CardDescription>{queues.queues?.length || 0} Redis list queue(s) detected</CardDescription></CardHeader><CardContent className="space-y-2">{(queues.queues || []).map((queue) => <div key={queue.name} className="flex items-center justify-between border p-3"><span className="font-medium">{queue.name}</span><Badge variant={queue.pending ? "secondary" : "outline"}>{queue.pending} pending</Badge></div>)}{!queues.queues?.length && <p className="text-muted-foreground">No queues visible. Start Redis and a Celery worker to populate routing queues.</p>}</CardContent></Card></div>;
}
