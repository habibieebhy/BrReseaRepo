export type PluginStage = "downloader" | "parser" | "chunker" | "embedding" | "storage";

export interface ModelProfile {
  id: string;
  dimensions: number;
  document_prefix: string;
  query_prefix: string;
  normalize: boolean;
  revision: string | null;
  default: boolean;
}

export interface PluginSpec {
  id: string;
  stage: PluginStage;
  name: string;
  version: string;
  capabilities: string[];
  models: ModelProfile[];
  default: boolean;
}

export interface PluginsResponse {
  plugins: PluginSpec[];
}

export interface IngestionResponse {
  message: string;
  job_id: string;
  tenant_id: string;
  status: string;
  plugins: Record<PluginStage, string>;
}

export interface SourceDefinition {
  id: string;
  name: string;
  tenant_id: string;
  start_url: string;
  crawl_strategy: "single_page" | "sitemap" | "recursive";
  max_depth: number;
  max_pages: number;
  include_patterns: string[];
  exclude_patterns: string[];
  schedule_enabled: boolean;
  cron_expression: string;
  timezone: string;
  plugins: Record<PluginStage, string>;
  config: Record<string, unknown>;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  last_run_at: string | null;
  last_job_id: string | null;
  last_status: string;
}

export interface SourcesResponse {
  sources: SourceDefinition[];
}
