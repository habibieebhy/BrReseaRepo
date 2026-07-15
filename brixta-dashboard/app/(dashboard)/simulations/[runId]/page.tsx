"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { ArrowLeft, FileDown, LoaderCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { browserApiUrl, requestPythonApi } from "@/lib/api";
import type { SimulationRun } from "@/types/types";

export default function SimulationRunPage() {
  const params = useParams<{ runId: string }>();
  const search = useSearchParams();
  const tenant = search.get("tenant") || "default";
  const [run, setRun] = useState<SimulationRun | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const response = await requestPythonApi<{ run: SimulationRun }>(`/prod/simulations/runs/${params.runId}?tenant_id=${encodeURIComponent(tenant)}`);
        if (active) setRun(response.run);
      } catch (reason) { if (active) setError(reason instanceof Error ? reason.message : "Could not load run."); }
    };
    void refresh();
    const timer = window.setInterval(refresh, 2500);
    return () => { active = false; window.clearInterval(timer); };
  }, [params.runId, tenant]);

  return <div className="mx-auto max-w-6xl space-y-6 p-6 md:p-8">
    <Button variant="ghost" render={<Link href="/simulations" />}><ArrowLeft size={15} /> Simulation Lab</Button>
    {error && <div className="rounded-2xl bg-destructive/10 p-4 text-destructive">{error}</div>}
    {!run && !error && <div className="flex items-center gap-2 text-muted-foreground"><LoaderCircle className="animate-spin" /> Loading run…</div>}
    {run && <>
      <div className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-3xl font-bold">{run.label || run.case_card_id}</h1><p className="text-muted-foreground">{run.id}</p></div><Badge variant={run.status === "failed" ? "destructive" : run.status === "completed" ? "default" : "secondary"}>{run.status}</Badge></div>
      {run.error && <Card className="border-destructive/30"><CardHeader><CardTitle className="text-destructive">Run failed</CardTitle></CardHeader><CardContent><pre className="max-h-72 overflow-auto whitespace-pre-wrap text-xs">{run.error}</pre></CardContent></Card>}
      <div className="grid gap-6 md:grid-cols-2"><Card><CardHeader><CardTitle>Result summary</CardTitle><CardDescription>{run.execution_mode} · {run.solver}</CardDescription></CardHeader><CardContent><pre className="overflow-auto whitespace-pre-wrap rounded-xl bg-muted p-4 text-xs">{JSON.stringify(run.summary || { status: run.status, stage: run.current_stage }, null, 2)}</pre></CardContent></Card><Card><CardHeader><CardTitle>Evidence</CardTitle><CardDescription>Knowledge retrieved before compilation.</CardDescription></CardHeader><CardContent className="space-y-3">{run.evidence.map((item) => <div key={item.result_id} className="rounded-xl border p-3"><p className="text-sm font-medium">{item.title}</p><p className="mt-1 line-clamp-3 text-xs text-muted-foreground">{item.snippet}</p><p className="mt-2 text-xs">Score {item.score.toFixed(3)}</p></div>)}{run.evidence.length === 0 && <p className="text-sm text-muted-foreground">No knowledge evidence was attached.</p>}</CardContent></Card></div>
      <Card><CardHeader><CardTitle>Artifacts</CardTitle><CardDescription>Inputs, manifest, logs and report preserved by BRIXTA storage.</CardDescription></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{run.artifacts.map((artifact) => <a key={artifact.object_name} className="flex items-center gap-3 rounded-xl border p-3 hover:bg-muted/50" href={`${browserApiUrl}/prod/simulations/runs/${run.id}/artifacts/${encodeURIComponent(artifact.name)}?tenant_id=${encodeURIComponent(run.tenant_id)}`}><FileDown size={17} /><span className="min-w-0"><span className="block truncate text-sm font-medium">{artifact.name}</span><span className="text-xs text-muted-foreground">{artifact.size} bytes</span></span></a>)}</CardContent></Card>
    </>}
  </div>;
}

