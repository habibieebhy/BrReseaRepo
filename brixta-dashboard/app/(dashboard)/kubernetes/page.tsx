"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { requestPythonApi } from "@/lib/api";

interface Pod { name: string; namespace: string; status: string; node?: string }
interface Deployment { name: string; namespace: string; replicas: number; available: number }

export default function KubernetesPage() {
  const [health, setHealth] = useState<{ healthy?: boolean; error?: string }>({});
  const [pods, setPods] = useState<Pod[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [logs, setLogs] = useState<{ title: string; body: string } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const load = () => Promise.all([requestPythonApi<{ healthy: boolean; error?: string }>("/prod/kubernetes"), requestPythonApi<{ pods: Pod[] }>("/prod/kubernetes/pods"), requestPythonApi<{ deployments: Deployment[] }>("/prod/kubernetes/deployments")]).then(([h, p, d]) => { setHealth(h); setPods(p.pods); setDeployments(d.deployments); }).catch((reason: Error) => setHealth({ healthy: false, error: reason.message }));
  useEffect(() => { void load(); }, []);
  async function restart(item: Deployment) { setBusy(`${item.namespace}/${item.name}`); try { await requestPythonApi(`/prod/kubernetes/deployments/${item.namespace}/${item.name}/restart`, { method: "POST" }); await load(); } finally { setBusy(null); } }
  async function showLogs(item: Pod) { setBusy(`${item.namespace}/${item.name}`); try { const value = await requestPythonApi<{ logs: string }>(`/prod/kubernetes/pods/${item.namespace}/${item.name}/logs`); setLogs({ title: `${item.namespace}/${item.name}`, body: value.logs }); } catch (reason) { setLogs({ title: "Logs unavailable", body: reason instanceof Error ? reason.message : "Unknown error" }); } finally { setBusy(null); } }
  return <div className="mx-auto max-w-7xl space-y-6 p-6"><div><h1 className="text-3xl font-bold tracking-tight">Kubernetes</h1><p className="text-muted-foreground">Uses local kubeconfig during development and the service account when deployed in-cluster.</p></div>{!health.healthy && <div className="border border-destructive/30 bg-destructive/10 p-4"><p className="font-medium text-destructive">Cluster not connected</p><p className="mt-1 text-xs text-muted-foreground">{health.error || "Configure ~/.kube/config or deploy BRIXTA with Kubernetes RBAC permissions."}</p></div>}<div className="grid gap-6 xl:grid-cols-2"><Card><CardHeader><CardTitle>Deployments</CardTitle><CardDescription>Restart triggers a rolling rollout by patching the pod-template annotation.</CardDescription></CardHeader><CardContent className="space-y-2">{deployments.length === 0 && <p className="text-muted-foreground">No deployments available.</p>}{deployments.map((item) => <div key={`${item.namespace}/${item.name}`} className="flex items-center justify-between gap-3 border p-3"><div><p className="font-medium">{item.name}</p><p className="text-xs text-muted-foreground">{item.namespace} · {item.available}/{item.replicas} available</p></div><Button size="sm" variant="outline" onClick={() => restart(item)} disabled={busy === `${item.namespace}/${item.name}`}>Restart rollout</Button></div>)}</CardContent></Card><Card><CardHeader><CardTitle>Pods</CardTitle><CardDescription>Read the latest 200 timestamped log lines.</CardDescription></CardHeader><CardContent className="space-y-2">{pods.length === 0 && <p className="text-muted-foreground">No pods available.</p>}{pods.map((item) => <div key={`${item.namespace}/${item.name}`} className="flex items-center justify-between gap-3 border p-3"><div><div className="flex items-center gap-2"><p className="font-medium">{item.name}</p><Badge variant={item.status === "Running" ? "default" : "secondary"}>{item.status}</Badge></div><p className="text-xs text-muted-foreground">{item.namespace} · {item.node || "unassigned"}</p></div><Button size="sm" variant="outline" onClick={() => showLogs(item)}>Logs</Button></div>)}</CardContent></Card></div>{logs && <Card><CardHeader><CardTitle>{logs.title}</CardTitle><CardDescription>Pod logs</CardDescription></CardHeader><CardContent><pre className="max-h-96 overflow-auto bg-muted p-4 text-xs whitespace-pre-wrap">{logs.body}</pre></CardContent></Card>}</div>;
}
