"use client";

import { useEffect, useMemo, useState } from "react";
import { requestPythonApi } from "@/lib/api";
import type { PluginSpec, PluginStage, PluginsResponse } from "@/types/types";

export function usePlugins() {
  const [plugins, setPlugins] = useState<PluginSpec[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    requestPythonApi<PluginsResponse>("/plugins")
      .then((data) => setPlugins(data.plugins))
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const byStage = useMemo(() => {
    return plugins.reduce<Record<PluginStage, PluginSpec[]>>(
      (grouped, plugin) => {
        grouped[plugin.stage].push(plugin);
        return grouped;
      },
      { downloader: [], parser: [], chunker: [], embedding: [], storage: [] },
    );
  }, [plugins]);

  return { plugins, byStage, loading, error };
}
