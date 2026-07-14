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

export interface Job {
  id: string;
  source_type: string;
  source_target: string;
  tenant_id: string;
  status: string;
  error?: string;
  current_stage?: string;
  attempt_count: number;
  max_attempts: number;
  retry_count: number;
  max_job_runs: number;
  retryable: boolean;
  terminal: boolean;
  can_retry: boolean;
  created_at?: string;
  updated_at?: string;
  completed_at?: string;
  parent_job_id?: string;
}

export interface KnowledgeBase {
  id: string;
  uri: string;
  name: string;
  tenant_id: string;
  source_type: string;
  source_target: string;
  status: string;
  ready: boolean;
  chunk_count: number;
  embedding_model: string;
  embedding_dimension: number;
  completed_at?: string;
  dashboard_url: string;
  manifest_url: string;
  retrieval_url: string;
  mcp_url: string;
  mcp_scope: { knowledge_base_id: string; tenant_id: string };
  mcp_tools: string[];
  chatgpt_ready: boolean;
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
