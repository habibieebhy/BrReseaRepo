"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Activity, CheckCircle2, FlaskConical, LoaderCircle, Play, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { requestPythonApi } from "@/lib/api";
import type { KnowledgeBase, SimulationCaseCard, SimulationPreflight, SimulationRun } from "@/types/types";

const initialParameters = {
  length_mm: 100,
  width_mm: 10,
  thickness_mm: 2,
  youngs_modulus_mpa: 70000,
  poisson_ratio: 0.33,
  density_kg_m3: 2700,
  load_n: 1000,
  yield_strength_mpa: 250,
  mesh_divisions_length: 10,
};

export default function SimulationsPage() {
  const [tenantId, setTenantId] = useState("default");
  const [label, setLabel] = useState("Material coupon screening");
  const [executionMode, setExecutionMode] = useState<"preview" | "solver">("preview");
  const [parameters, setParameters] = useState(initialParameters);
  const [cards, setCards] = useState<SimulationCaseCard[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeBase[]>([]);
  const [selectedKnowledge, setSelectedKnowledge] = useState<string[]>([]);
  const [runs, setRuns] = useState<SimulationRun[]>([]);
  const [preflight, setPreflight] = useState<SimulationPreflight | null>(null);
  const [busy, setBusy] = useState<"preflight" | "run" | null>(null);
  const [error, setError] = useState("");

  const card = cards[0];
  const payload = useMemo(() => ({
    tenant_id: tenantId,
    case_card_id: card?.id || "structural_coupon_tension_v1",
    parameters,
    knowledge_base_ids: selectedKnowledge,
    evidence_query: "material elastic modulus yield strength density tensile loading",
  }), [tenantId, card?.id, parameters, selectedKnowledge]);

  const refresh = useCallback(async () => {
    const [runData, knowledgeData] = await Promise.all([
      requestPythonApi<{ runs: SimulationRun[] }>(`/prod/simulations/runs?tenant_id=${encodeURIComponent(tenantId)}`),
      requestPythonApi<{ knowledge_bases: KnowledgeBase[] }>(`/prod/knowledge?tenant_id=${encodeURIComponent(tenantId)}`),
    ]);
    setRuns(runData.runs);
    setKnowledge(knowledgeData.knowledge_bases);
  }, [tenantId]);

  useEffect(() => {
    requestPythonApi<{ case_cards: SimulationCaseCard[] }>("/prod/simulations/case-cards")
      .then((response) => setCards(response.case_cards))
      .catch((reason: Error) => setError(reason.message));
  }, []);

  useEffect(() => {
    const initial = window.setTimeout(() => {
      void refresh().catch((reason: Error) => setError(reason.message));
    }, 0);
    const timer = window.setInterval(() => void refresh().catch(() => undefined), 3000);
    return () => { window.clearTimeout(initial); window.clearInterval(timer); };
  }, [refresh]);

  function setNumber(name: keyof typeof initialParameters, value: string) {
    setParameters((current) => ({ ...current, [name]: Number(value) }));
    setPreflight(null);
  }

  async function validate(event: FormEvent) {
    event.preventDefault(); setBusy("preflight"); setError("");
    try {
      setPreflight(await requestPythonApi<SimulationPreflight>("/prod/simulations/preflight", {
        method: "POST", body: JSON.stringify(payload),
      }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Preflight failed."); }
    finally { setBusy(null); }
  }

  async function run() {
    setBusy("run"); setError("");
    try {
      await requestPythonApi("/prod/simulations/runs", {
        method: "POST",
        body: JSON.stringify({ ...payload, execution_mode: executionMode, label }),
      });
      setPreflight(null);
      await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not queue simulation."); }
    finally { setBusy(null); }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6 md:p-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div><h1 className="flex items-center gap-3 text-3xl font-bold"><FlaskConical /> Structural & Material Lab</h1><p className="text-muted-foreground">Knowledge-backed Case Cards, deterministic CalculiX inputs, bounded execution and evidence-preserving reports.</p></div>
        <Badge variant="secondary">Pack 04 · v1</Badge>
      </div>

      {error && <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">{error}</div>}
      <div className="grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
        <Card>
          <CardHeader><CardTitle>{card?.name || "Linear-elastic tensile coupon"}</CardTitle><CardDescription>{card?.description || "Loading Case Card…"}</CardDescription></CardHeader>
          <CardContent>
            <form onSubmit={validate} className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2"><div className="space-y-2"><Label htmlFor="sim-tenant">Tenant</Label><Input id="sim-tenant" value={tenantId} onChange={(event) => { setTenantId(event.target.value); setSelectedKnowledge([]); }} required /></div><div className="space-y-2"><Label htmlFor="sim-label">Run label</Label><Input id="sim-label" value={label} onChange={(event) => setLabel(event.target.value)} /></div></div>
              <div className="grid gap-4 md:grid-cols-3">
                {Object.entries(parameters).map(([name, value]) => <div key={name} className="space-y-2"><Label htmlFor={name}>{name.replaceAll("_", " ")}</Label><Input id={name} type="number" step="any" value={value} onChange={(event) => setNumber(name as keyof typeof initialParameters, event.target.value)} required /></div>)}
              </div>
              <div className="space-y-2"><Label>Engineering knowledge evidence</Label><div className="max-h-44 space-y-2 overflow-y-auto rounded-2xl border p-3">{knowledge.map((item) => <label key={item.id} className="flex items-start gap-3 text-sm"><input className="mt-1" type="checkbox" checked={selectedKnowledge.includes(item.id)} onChange={(event) => setSelectedKnowledge((current) => event.target.checked ? [...current, item.id] : current.filter((id) => id !== item.id))} /><span><span className="font-medium">{item.name}</span><span className="block text-xs text-muted-foreground">{item.chunk_count} chunks · {item.embedding_model}</span></span></label>)}{knowledge.length === 0 && <p className="text-sm text-muted-foreground">No completed knowledge bases exist for tenant “{tenantId}”. The run may still be validated using explicit material inputs.</p>}</div></div>
              <div className="flex flex-wrap items-end gap-3"><div className="space-y-2"><Label htmlFor="execution-mode">Execution mode</Label><select id="execution-mode" className="h-9 rounded-xl border bg-background px-3 text-sm" value={executionMode} onChange={(event) => setExecutionMode(event.target.value as "preview" | "solver")}><option value="preview">Preview · analytical reference</option><option value="solver">Solver · CalculiX worker</option></select></div><Button type="submit" variant="outline" disabled={busy !== null}>{busy === "preflight" ? <LoaderCircle className="animate-spin" size={15} /> : <ShieldCheck size={15} />} Validate case</Button><Button type="button" disabled={!preflight || busy !== null} onClick={run}>{busy === "run" ? <LoaderCircle className="animate-spin" size={15} /> : <Play size={15} />} Queue run</Button></div>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card><CardHeader><CardTitle>Preflight</CardTitle><CardDescription>Only validated values enter the deterministic compiler.</CardDescription></CardHeader><CardContent className="space-y-3">{preflight ? <><div className="flex items-center gap-2 text-sm font-medium"><CheckCircle2 size={17} /> Case is structurally valid</div><div className="grid grid-cols-2 gap-3 text-sm"><div className="rounded-xl bg-muted p-3"><p className="text-xs text-muted-foreground">Stress</p><p className="font-semibold">{Number(preflight.analytical_reference.axial_stress_mpa).toPrecision(5)} MPa</p></div><div className="rounded-xl bg-muted p-3"><p className="text-xs text-muted-foreground">Displacement</p><p className="font-semibold">{Number(preflight.analytical_reference.axial_displacement_mm).toPrecision(5)} mm</p></div></div><p className="text-sm">Evidence attached: <strong>{preflight.evidence.length}</strong></p><ul className="space-y-1 text-xs text-muted-foreground">{preflight.warnings.map((warning) => <li key={warning}>• {warning}</li>)}</ul></> : <p className="text-sm text-muted-foreground">Validate the Case Card to preview derived quantities, evidence and limitations.</p>}</CardContent></Card>
          <Card><CardHeader><CardTitle>Safety boundary</CardTitle></CardHeader><CardContent className="text-sm text-muted-foreground">The LLM may help retrieve evidence or propose values. It cannot inject commands or edit solver source. BRIXTA validates values and compiles an allowlisted Case Card.</CardContent></Card>
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Activity size={18} /> Run history</CardTitle><CardDescription>Live PostgreSQL-backed status. Solver results and provenance remain attached to the run.</CardDescription></CardHeader>
        <CardContent className="space-y-3">{runs.map((run) => <Link key={run.id} href={`/simulations/${run.id}?tenant=${encodeURIComponent(run.tenant_id)}`} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border p-4 transition-colors hover:bg-muted/50"><div><p className="font-medium">{run.label || run.case_card_id}</p><p className="text-xs text-muted-foreground">{run.execution_mode} · {run.solver} · {run.id}</p></div><Badge variant={run.status === "failed" ? "destructive" : run.status === "completed" ? "default" : "secondary"}>{run.status}</Badge></Link>)}{runs.length === 0 && <p className="py-6 text-center text-sm text-muted-foreground">No simulation runs for this tenant yet.</p>}</CardContent>
      </Card>
    </div>
  );
}
