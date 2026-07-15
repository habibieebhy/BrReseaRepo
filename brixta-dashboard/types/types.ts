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

export interface SimulationCaseCard {
  id: string;
  name: string;
  description: string;
  pack: string;
  version: string;
  solver: string;
  analysis_type: string;
  execution_modes: ("preview" | "solver")[];
  outputs: string[];
  limitations: string[];
}

export interface SimulationEvidence {
  knowledge_base_id: string;
  knowledge_base_name: string;
  result_id: string;
  title: string;
  score: number;
  snippet: string;
  url: string;
}

export interface SimulationArtifact {
  name: string;
  object_name: string;
  size: number;
  content_type: string;
}

export interface SimulationRun {
  id: string;
  tenant_id: string;
  label?: string;
  case_card_id: string;
  solver: string;
  execution_mode: "preview" | "solver";
  status: string;
  current_stage: string;
  spec: { parameters: Record<string, number>; validation_warnings?: string[] };
  evidence: SimulationEvidence[];
  summary?: Record<string, unknown>;
  artifacts: SimulationArtifact[];
  error?: string;
  created_at?: string;
  completed_at?: string;
  terminal: boolean;
}

export interface SimulationPreflight {
  valid: boolean;
  case_card: SimulationCaseCard;
  normalized_parameters: Record<string, number>;
  analytical_reference: Record<string, number | string | null>;
  evidence: SimulationEvidence[];
  warnings: string[];
  compiled_files: string[];
}
