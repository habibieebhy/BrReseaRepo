"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { requestPythonApi } from "@/lib/api";
import { usePlugins } from "@/hooks/usePlugins";
import type { PluginStage, SourceDefinition, SourcesResponse } from "@/types/types";

const stages: PluginStage[] = ["downloader", "parser", "chunker", "embedding", "storage"];

export default function SourcesPage() {
  const { byStage } = usePlugins();
  const [sources, setSources] = useState<SourceDefinition[]>([]);
  const [name, setName] = useState("");
  const [startUrl, setStartUrl] = useState("");
  const [tenantId, setTenantId] = useState("default");
  const [schedule, setSchedule] = useState("0 */6 * * *");
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [scheduled, setScheduled] = useState(true);
  const [selection, setSelection] = useState<Partial<Record<PluginStage, string>>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await requestPythonApi<SourcesResponse>("/sources");
      setSources(data.sources);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load sources.");
    }
  }, []);

  useEffect(() => {
    requestPythonApi<SourcesResponse>("/sources")
      .then((data) => setSources(data.sources))
      .catch((reason: Error) => setError(reason.message));
  }, []);
  const defaults = useMemo(() => {
    const defaults: Partial<Record<PluginStage, string>> = {};
    stages.forEach((stage) => {
      const plugin = byStage[stage].find((item) => item.default) || byStage[stage][0];
      if (plugin) defaults[stage] = plugin.id;
    });
    return defaults;
  }, [byStage]);

  async function create(event: FormEvent) {
    event.preventDefault();
    setBusy("create");
    setError(null);
    try {
      await requestPythonApi<SourceDefinition>("/sources", {
        method: "POST",
        body: JSON.stringify({
          name,
          tenant_id: tenantId,
          start_url: startUrl,
          crawl_strategy: "single_page",
          schedule_enabled: scheduled,
          cron_expression: schedule,
          timezone,
          plugins: { ...defaults, ...selection },
          config: { embedding_model: "nomic-ai/nomic-embed-text-v1.5" },
        }),
      });
      setName("");
      setStartUrl("");
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create source.");
    } finally {
      setBusy(null);
    }
  }

  async function sync(source: SourceDefinition) {
    setBusy(source.id);
    setError(null);
    try {
      await requestPythonApi(`/sources/${source.id}/sync`, { method: "POST" });
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not queue sync.");
    } finally {
      setBusy(null);
    }
  }

  async function remove(source: SourceDefinition) {
    setBusy(source.id);
    try {
      await requestPythonApi(`/sources/${source.id}`, { method: "DELETE" });
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not delete source.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div><h1 className="text-3xl font-bold tracking-tight">Sources & schedules</h1><p className="text-muted-foreground">Persist reusable sources, assign a pipeline, and queue manual or cron-driven syncs.</p></div>
      {error && <div className="border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
      <div className="grid gap-6 xl:grid-cols-[.8fr_1.2fr]">
        <Card>
          <CardHeader><CardTitle>Add website source</CardTitle><CardDescription>The current downloader processes the seed page. Sitemap and recursive crawling are reserved for crawler plugins.</CardDescription></CardHeader>
          <CardContent>
            <form onSubmit={create} className="space-y-4">
              <div className="space-y-2"><Label htmlFor="source-name">Name</Label><Input id="source-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Product documentation" required /></div>
              <div className="space-y-2"><Label htmlFor="start-url">Start URL</Label><Input id="start-url" type="url" value={startUrl} onChange={(event) => setStartUrl(event.target.value)} placeholder="https://docs.example.com" required /></div>
              <div className="space-y-2"><Label htmlFor="source-tenant">Tenant</Label><Input id="source-tenant" value={tenantId} onChange={(event) => setTenantId(event.target.value)} required /></div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2"><Label htmlFor="cron">Cron expression</Label><Input id="cron" value={schedule} onChange={(event) => setSchedule(event.target.value)} disabled={!scheduled} /></div>
                <div className="space-y-2"><Label htmlFor="timezone">Timezone</Label><Input id="timezone" value={timezone} onChange={(event) => setTimezone(event.target.value)} disabled={!scheduled} /></div>
              </div>
              <details className="border p-3">
                <summary className="cursor-pointer text-sm font-medium">Pipeline plugins</summary>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  {stages.map((stage) => (
                    <div key={stage} className="space-y-1">
                      <Label htmlFor={`source-${stage}`} className="capitalize">{stage}</Label>
                      <select id={`source-${stage}`} className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={selection[stage] || defaults[stage] || ""} onChange={(event) => setSelection((current) => ({ ...current, [stage]: event.target.value }))}>
                        {byStage[stage].map((plugin) => <option key={plugin.id} value={plugin.id}>{plugin.name}</option>)}
                      </select>
                    </div>
                  ))}
                </div>
              </details>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={scheduled} onChange={(event) => setScheduled(event.target.checked)} /> Enable recurring sync</label>
              <Button type="submit" disabled={busy === "create" || !(selection.storage || defaults.storage)}>{busy === "create" ? "Saving…" : "Save source"}</Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Configured sources</CardTitle><CardDescription>Celery Beat checks enabled schedules once per minute.</CardDescription></CardHeader>
          <CardContent className="space-y-3">
            {sources.length === 0 && <p className="text-muted-foreground">No sources configured yet.</p>}
            {sources.map((source) => (
              <div key={source.id} className="space-y-3 border p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div><div className="flex items-center gap-2"><h3 className="font-medium">{source.name}</h3><Badge variant={source.enabled ? "default" : "secondary"}>{source.enabled ? "enabled" : "disabled"}</Badge></div><p className="mt-1 break-all text-xs text-muted-foreground">{source.start_url}</p></div>
                  <div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => sync(source)} disabled={busy === source.id}>Sync now</Button><Button size="sm" variant="destructive" onClick={() => remove(source)} disabled={busy === source.id}>Delete</Button></div>
                </div>
                <div className="grid gap-2 text-xs text-muted-foreground sm:grid-cols-3"><span>Schedule: {source.schedule_enabled ? `${source.cron_expression} (${source.timezone})` : "manual"}</span><span>Last status: {source.last_status}</span><span>Last run: {source.last_run_at ? new Date(source.last_run_at).toLocaleString() : "never"}</span></div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
