"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { requestPythonApi } from "@/lib/api";

interface Container { id: string; name: string; image: string; status: string }
export default function DockerPage() {
  const [health, setHealth] = useState<{ healthy?: boolean; error?: string }>({}); const [containers, setContainers] = useState<Container[]>([]); const [logs, setLogs] = useState<{ name: string; body: string } | null>(null); const [busy, setBusy] = useState<string | null>(null);
  const load = () => Promise.all([requestPythonApi<{ healthy: boolean; error?: string }>("/prod/docker"), requestPythonApi<{ containers: Container[] }>("/prod/docker/containers")]).then(([h, c]) => { setHealth(h); setContainers(c.containers); }).catch((reason: Error) => setHealth({ healthy: false, error: reason.message }));
  useEffect(() => { void load(); }, []);
  async function restart(name: string) { setBusy(name); try { await requestPythonApi(`/prod/docker/restart/${name}`, { method: "POST" }); await load(); } finally { setBusy(null); } }
  async function showLogs(name: string) { setBusy(name); try { const value = await requestPythonApi<{ logs: string }>(`/prod/docker/logs/${name}`); setLogs({ name, body: value.logs }); } catch (reason) { setLogs({ name, body: reason instanceof Error ? reason.message : "Logs unavailable" }); } finally { setBusy(null); } }
  return <div className="mx-auto max-w-7xl space-y-6 p-6"><div><h1 className="text-3xl font-bold tracking-tight">Docker</h1><p className="text-muted-foreground">Local container state, logs, and manual restart controls.</p></div>{!health.healthy && <div className="border border-destructive/30 bg-destructive/10 p-4"><p className="font-medium text-destructive">Docker engine unavailable</p><p className="text-xs text-muted-foreground">{health.error || "Start Docker Desktop and make its socket available to BRIXTA Core."}</p></div>}<Card><CardHeader><CardTitle>Containers</CardTitle><CardDescription>{containers.length} container(s) discovered, including stopped containers.</CardDescription></CardHeader><CardContent className="space-y-2">{containers.map((item) => <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 border p-3"><div><div className="flex items-center gap-2"><p className="font-medium">{item.name}</p><Badge variant={item.status === "running" ? "default" : "secondary"}>{item.status}</Badge></div><p className="text-xs text-muted-foreground">{item.image}</p></div><div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => showLogs(item.name)}>Logs</Button><Button size="sm" onClick={() => restart(item.name)} disabled={busy === item.name}>Restart</Button></div></div>)}{containers.length === 0 && <p className="text-muted-foreground">No containers discovered.</p>}</CardContent></Card>{logs && <Card><CardHeader><CardTitle>{logs.name}</CardTitle><CardDescription>Latest container output</CardDescription></CardHeader><CardContent><pre className="max-h-96 overflow-auto bg-muted p-4 text-xs whitespace-pre-wrap">{logs.body}</pre></CardContent></Card>}</div>;
}
