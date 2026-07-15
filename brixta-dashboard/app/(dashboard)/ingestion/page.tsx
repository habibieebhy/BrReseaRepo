"use client";

import { DragEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { Check, Circle, FileUp, Globe2, LoaderCircle } from "lucide-react";

import KnowledgeConnectionCard from "@/components/knowledge/KnowledgeConnectionCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { usePlugins } from "@/hooks/usePlugins";
import { requestPythonApi } from "@/lib/api";
import type { IngestionResponse, Job, KnowledgeBase, PluginStage } from "@/types/types";

const stages: PluginStage[] = ["downloader", "parser", "chunker", "embedding", "storage"];

export default function IngestionPage() {
  const { byStage, loading: pluginsLoading, error: pluginError } = usePlugins();
  const [sourceUrl, setSourceUrl] = useState("");
  const [mode, setMode] = useState<"url" | "file">("url");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [tenantId, setTenantId] = useState("default");
  const [embeddingModel, setEmbeddingModel] = useState("nomic-ai/nomic-embed-text-v1.5");
  const [selection, setSelection] = useState<Partial<Record<PluginStage, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<IngestionResponse | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [error, setError] = useState<string | null>(null);

  const defaults = useMemo(() => {
    const value: Partial<Record<PluginStage, string>> = {};
    stages.forEach((stage) => {
      const candidate = byStage[stage].find((plugin) => plugin.default) || byStage[stage][0];
      if (candidate) value[stage] = candidate.id;
    });
    return value;
  }, [byStage]);

  const selectedEmbeddingId = selection.embedding || defaults.embedding;
  const embeddingModels = useMemo(
    () => byStage.embedding.find((plugin) => plugin.id === selectedEmbeddingId)?.models || [],
    [byStage.embedding, selectedEmbeddingId],
  );
  const selectedModel = embeddingModels.some((model) => model.id === embeddingModel)
    ? embeddingModel
    : (embeddingModels.find((model) => model.default) || embeddingModels[0])?.id || embeddingModel;

  useEffect(() => {
    if (!result?.job_id || job?.terminal) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const response = await requestPythonApi<{ job: Job; knowledge_base?: KnowledgeBase }>(`/prod/jobs/${result.job_id}`);
        if (cancelled) return;
        setJob(response.job);
        if (response.knowledge_base) setKnowledgeBase(response.knowledge_base);
      } catch (reason) {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Could not refresh job status.");
      }
    };
    void poll();
    const timer = window.setInterval(poll, 2_000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [result?.job_id, job?.terminal]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);
    setJob(null);
    setKnowledgeBase(null);
    try {
      const effective = { ...defaults, ...selection } as Record<PluginStage, string>;
      const response = mode === "file" && file
        ? await requestPythonApi<IngestionResponse>("/ingest/file", {
            method: "POST",
            body: (() => {
              const body = new FormData();
              body.append("file", file);
              body.append("tenant_id", tenantId);
              body.append("parser", effective.parser);
              body.append("chunker", effective.chunker);
              body.append("embedding", effective.embedding);
              body.append("storage", effective.storage);
              body.append("embedding_model", selectedModel);
              return body;
            })(),
          })
        : await requestPythonApi<IngestionResponse>("/ingest", {
            method: "POST",
            body: JSON.stringify({
              source_url: sourceUrl,
              tenant_id: tenantId,
              plugins: effective,
              config: { embedding_model: selectedModel },
            }),
          });
      setResult(response);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not queue ingestion.");
    } finally {
      setSubmitting(false);
    }
  }

  const activeIndex = job?.status === "completed" ? stages.length : Math.max(0, stages.indexOf((job?.current_stage || "downloader") as PluginStage));

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6 md:p-8">
      <div>
        <h1 className="text-3xl font-bold">Create knowledge</h1>
        <p className="text-muted-foreground">Ingest a source, watch every stage live, then connect the resulting knowledge base.</p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.25fr_.75fr]">
        <Card>
          <CardHeader><CardTitle>Pipeline configuration</CardTitle><CardDescription>Choose implementations; BRIXTA keeps the safe stage order fixed.</CardDescription></CardHeader>
          <CardContent>
            <form onSubmit={submit} className="space-y-5">
              <div className="flex gap-2">
                <Button type="button" variant={mode === "url" ? "default" : "outline"} onClick={() => setMode("url")}><Globe2 size={15} /> URL</Button>
                <Button type="button" variant={mode === "file" ? "default" : "outline"} onClick={() => setMode("file")}><FileUp size={15} /> File</Button>
              </div>
              {mode === "url" ? (
                <div className="space-y-2"><Label htmlFor="source-url">Source URL</Label><Input id="source-url" type="url" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} placeholder="https://docs.example.com/start" required /></div>
              ) : (
                <div
                  className={`rounded-2xl border-2 border-dashed p-8 text-center transition-colors ${dragging ? "border-primary bg-primary/5" : "border-border"}`}
                  onDragOver={(event: DragEvent) => { event.preventDefault(); setDragging(true); }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={(event: DragEvent) => { event.preventDefault(); setDragging(false); setFile(event.dataTransfer.files[0] || null); }}
                >
                  <FileUp className="mx-auto mb-3 text-muted-foreground" />
                  <p className="font-medium">Drop a document here</p>
                  <p className="mb-3 text-xs text-muted-foreground">Documents, engineering configs, solver inputs or source text · up to 50 MiB</p>
                  <Input type="file" accept=".pdf,.docx,.pptx,.xlsx,.html,.htm,.md,.txt,.csv,.json,.yaml,.yml,.xml,.inp,.dat,.f,.for,.c,.cc,.cpp,.h,.hpp,.py,.sh" onChange={(event) => setFile(event.target.files?.[0] || null)} required={!file} />
                  {file && <p className="mt-3 text-sm">Selected: {file.name}</p>}
                </div>
              )}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2"><Label htmlFor="tenant">Tenant ID</Label><Input id="tenant" value={tenantId} onChange={(event) => setTenantId(event.target.value)} required /></div>
                <div className="space-y-2"><Label htmlFor="embedding-model">Embedding model</Label><select id="embedding-model" className="h-9 w-full rounded-xl border bg-background px-3 text-sm" value={selectedModel} onChange={(event) => setEmbeddingModel(event.target.value)}>{embeddingModels.map((model) => <option key={model.id} value={model.id}>{model.id} · {model.dimensions}d</option>)}{embeddingModels.length === 0 && <option value={selectedModel}>{selectedModel}</option>}</select></div>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {stages.map((stage) => <div key={stage} className="space-y-2"><Label htmlFor={stage} className="capitalize">{stage}</Label><select id={stage} className="h-9 w-full rounded-xl border bg-background px-3 text-sm" value={selection[stage] || defaults[stage] || ""} onChange={(event) => setSelection((current) => ({ ...current, [stage]: event.target.value }))} disabled={pluginsLoading}>{byStage[stage].map((plugin) => <option key={plugin.id} value={plugin.id}>{plugin.name}</option>)}</select></div>)}
              </div>
              {pluginError && <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">Could not reach BRIXTA Core: {pluginError}</div>}
              <Button type="submit" disabled={submitting || pluginsLoading || Boolean(pluginError)}>{submitting ? <><LoaderCircle className="animate-spin" size={15} /> Queuing…</> : "Start ingestion"}</Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Live pipeline</CardTitle><CardDescription>{result ? `Job ${result.job_id}` : "Submit a source to begin."}</CardDescription></CardHeader>
          <CardContent className="space-y-3">
            {stages.map((stage, index) => {
              const done = Boolean(job && (job.status === "completed" || index < activeIndex));
              const active = Boolean(job && !job.terminal && index === activeIndex);
              return <div key={stage} className={`flex items-center gap-3 rounded-xl border p-3 ${active ? "border-primary/40 bg-primary/5" : ""}`}>{done ? <Check size={17} /> : active ? <LoaderCircle className="animate-spin" size={17} /> : <Circle size={17} className="text-muted-foreground" />}<span className="flex-1 capitalize">{stage}</span>{active && <Badge variant="secondary">{job?.status}</Badge>}</div>;
            })}
            {!result && <p className="pt-2 text-sm text-muted-foreground">Progress refreshes every two seconds and survives page reloads through PostgreSQL job state.</p>}
            {job?.status === "failed" && <div className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive"><p className="font-medium">Pipeline failed</p><p className="mt-1 whitespace-pre-wrap text-xs">{job.error}</p></div>}
            {error && <p className="text-sm text-destructive">{error}</p>}
          </CardContent>
        </Card>
      </div>

      {knowledgeBase && <KnowledgeConnectionCard knowledgeBase={knowledgeBase} />}
    </div>
  );
}
