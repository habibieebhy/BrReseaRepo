import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchPythonApi } from "@/lib/api";
import type { PluginSpec, PluginsResponse } from "@/types/types";

const stages = ["downloader", "parser", "chunker", "embedding", "storage"] as const;

export default async function PluginsPage() {
  const data = await fetchPythonApi("/plugins", { cache: "no-store" }) as PluginsResponse & { error?: string };
  const plugins = data.plugins || [];
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div><h1 className="text-3xl font-bold tracking-tight">Plugin catalog</h1><p className="text-muted-foreground">Installed runtime implementations, grouped by the stage they can execute.</p></div>
      {data.error && <div className="border border-destructive/30 bg-destructive/10 p-3 text-destructive">{data.error}</div>}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {stages.map((stage) => (
          <Card key={stage}>
            <CardHeader><CardTitle className="capitalize">{stage}</CardTitle><CardDescription>{plugins.filter((plugin) => plugin.stage === stage).length} installed implementation(s)</CardDescription></CardHeader>
            <CardContent className="space-y-3">
              {plugins.filter((plugin: PluginSpec) => plugin.stage === stage).map((plugin) => (
                <div key={plugin.id} className="border p-3"><div className="flex items-center justify-between gap-3"><span className="font-medium">{plugin.name}</span>{plugin.default && <Badge>default</Badge>}</div><p className="mt-1 text-xs text-muted-foreground">{plugin.id} · v{plugin.version}</p><div className="mt-3 flex flex-wrap gap-1">{plugin.capabilities.map((capability) => <Badge key={capability} variant="outline">{capability}</Badge>)}</div>{plugin.models.length > 0 && <div className="mt-3 space-y-1">{plugin.models.map((model) => <p key={model.id} className="break-all text-xs text-muted-foreground">{model.id} · {model.dimensions}d{model.default ? " · default" : ""}</p>)}</div>}</div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
