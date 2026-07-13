"use client";

import { DragEvent, FormEvent, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { requestPythonApi } from "@/lib/api";
import { usePlugins } from "@/hooks/usePlugins";
import type { IngestionResponse, PluginStage } from "@/types/types";

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
  const [error, setError] = useState<string | null>(null);

  const defaults = useMemo(() => {
    const defaults: Partial<Record<PluginStage, string>> = {};
    stages.forEach((stage) => {
      const candidate = byStage[stage].find((plugin) => plugin.default) || byStage[stage][0];
      if (candidate) defaults[stage] = candidate.id;
    });
    return defaults;
  }, [byStage]);

  const selectedEmbeddingId = selection.embedding || defaults.embedding;
  const embeddingModels = byStage.embedding.find((plugin) => plugin.id === selectedEmbeddingId)?.models || [];

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);
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
              body.append("embedding_model", embeddingModel);
              return body;
            })(),
          })
        : await requestPythonApi<IngestionResponse>("/ingest", {
            method: "POST",
            body: JSON.stringify({ source_url: sourceUrl, tenant_id: tenantId, plugins: effective, config: { embedding_model: embeddingModel } }),
          });
      setResult(response);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not queue ingestion.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Run a pipeline</h1>
        <p className="text-muted-foreground">Choose the implementation used at every stage, then queue one URL.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.3fr_.7fr]">
        <Card>
          <CardHeader>
            <CardTitle>Ingestion configuration</CardTitle>
            <CardDescription>Plugin choices are validated by BRIXTA before dispatch.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={submit} className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="flex gap-2 md:col-span-2"><Button type="button" variant={mode === "url" ? "default" : "outline"} onClick={() => setMode("url")}>URL</Button><Button type="button" variant={mode === "file" ? "default" : "outline"} onClick={() => setMode("file")}>File upload</Button></div>
                {mode === "url" ? <div className="space-y-2 md:col-span-2"><Label htmlFor="source-url">Source URL</Label><Input id="source-url" type="url" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} placeholder="https://docs.example.com/start" required /></div> :
                  <div className={`space-y-3 border-2 border-dashed p-8 text-center md:col-span-2 ${dragging ? "border-primary bg-primary/5" : "border-border"}`} onDragOver={(event: DragEvent) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event: DragEvent) => { event.preventDefault(); setDragging(false); setFile(event.dataTransfer.files[0] || null); }}>
                    <p className="font-medium">Drop a document here</p><p className="text-xs text-muted-foreground">PDF, DOCX, PPTX, XLSX, HTML, Markdown or text · maximum 50 MiB</p><Input type="file" accept=".pdf,.docx,.pptx,.xlsx,.html,.htm,.md,.txt" onChange={(event) => setFile(event.target.files?.[0] || null)} required={!file} />{file && <p className="text-sm">Selected: {file.name}</p>}
                  </div>}
                <div className="space-y-2">
                  <Label htmlFor="tenant">Tenant ID</Label>
                  <Input id="tenant" value={tenantId} onChange={(event) => setTenantId(event.target.value)} required />
                </div>
                <div className="space-y-2"><Label htmlFor="embedding-model">Embedding model</Label><select id="embedding-model" className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={embeddingModel} onChange={(event) => setEmbeddingModel(event.target.value)}>{embeddingModels.map((model) => <option key={model.id} value={model.id}>{model.id} · {model.dimensions}d</option>)}{embeddingModels.length === 0 && <option value={embeddingModel}>{embeddingModel}</option>}</select></div>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {stages.map((stage) => (
                  <div key={stage} className="space-y-2">
                    <Label htmlFor={stage} className="capitalize">{stage}</Label>
                    <select id={stage} className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={selection[stage] || defaults[stage] || ""} onChange={(event) => setSelection((current) => ({ ...current, [stage]: event.target.value }))} disabled={pluginsLoading}>
                      {byStage[stage].map((plugin) => <option key={plugin.id} value={plugin.id}>{plugin.name}</option>)}
                    </select>
                  </div>
                ))}
              </div>

              {pluginError && <div className="border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">Could not reach BRIXTA Core: {pluginError}. Start the API on port 8000, then refresh.</div>}
              <Button type="submit" disabled={submitting || pluginsLoading || Boolean(pluginError)}>
                {submitting ? "Queuing…" : "Queue ingestion"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Dispatch result</CardTitle><CardDescription>The job ID becomes the trace key across every stage.</CardDescription></CardHeader>
          <CardContent>
            {!result && !error && <p className="text-muted-foreground">No job submitted in this session.</p>}
            {error && <p className="text-destructive">{error}</p>}
            {result && <div className="space-y-3"><p className="font-medium">{result.message}</p><dl className="grid gap-2 text-sm"><div><dt className="text-muted-foreground">Job</dt><dd className="break-all">{result.job_id}</dd></div><div><dt className="text-muted-foreground">Status</dt><dd>{result.status}</dd></div></dl></div>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
