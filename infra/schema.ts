import {
  pgSchema,
  text,
  uuid,
  bigserial,
  integer,
  customType,
  timestamp,
  boolean,
  jsonb,
  uniqueIndex,
  primaryKey,
} from "drizzle-orm/pg-core";

// -----------------------------------------------------------------------------
// Schema
// -----------------------------------------------------------------------------

export const brixtaSchema = pgSchema("BrResearch");

// -----------------------------------------------------------------------------
// pgvector
// Model dimensions are recorded per row so pipelines may select different
// approved embedding models. Similarity queries must filter by model/dimension.
// -----------------------------------------------------------------------------

const vector = customType<{ data: number[] }>({
  dataType() {
    return "vector";
  },
});

// -----------------------------------------------------------------------------
// Ingestion Jobs
// -----------------------------------------------------------------------------

export const ingestionJobs = brixtaSchema.table("ingestion_jobs", {
  id: uuid("id").primaryKey().defaultRandom(),

  sourceType: text("source_type").notNull(),

  sourceTarget: text("source_target").notNull(),

  tenantId: text("tenant_id").notNull(),

  status: text("status")
    .default("queued")
    .notNull(),

  errorLog: text("error_log"),

  createdAt: timestamp("created_at", { withTimezone: true })
    .defaultNow()
    .notNull(),

  updatedAt: timestamp("updated_at", { withTimezone: true })
    .defaultNow()
    .notNull(),

  startedAt: timestamp("started_at", { withTimezone: true }),

  completedAt: timestamp("completed_at", { withTimezone: true }),

  currentStage: text("current_stage"),

  celeryTaskId: text("celery_task_id"),

  attemptCount: integer("attempt_count").default(0).notNull(),

  maxAttempts: integer("max_attempts").default(3).notNull(),

  terminal: boolean("terminal").default(false).notNull(),

  retryable: boolean("retryable").default(true).notNull(),

  retryCount: integer("retry_count").default(0).notNull(),

  parentJobId: uuid("parent_job_id"),

  contextJson: jsonb("context_json"),
});

// -----------------------------------------------------------------------------
// Document Chunks
// One row = One semantic chunk
// -----------------------------------------------------------------------------

export const documentChunks = brixtaSchema.table("document_chunks", {
  id: bigserial("id", {
    mode: "bigint",
  }).primaryKey(),

  jobId: uuid("job_id")
    .notNull()
    .references(() => ingestionJobs.id, {
      onDelete: "cascade",
    }),

  tenantId: text("tenant_id").notNull(),

  chunkIndex: integer("chunk_index").notNull(),

  content: text("content").notNull(),

  embeddingModel: text("embedding_model").notNull(),

  embeddingDimension: integer("embedding_dimension").notNull(),

  embedding: vector("embedding").notNull(),
}, (table) => [
  uniqueIndex("document_chunks_job_chunk_idx").on(table.jobId, table.chunkIndex),
]);

// -----------------------------------------------------------------------------
// Knowledge access
// Shared by the dashboard API and MCP gateway; default-ready knowledge remains
// visible until an explicit tenant-scoped disable row is written.
// -----------------------------------------------------------------------------

export const knowledgeAccess = brixtaSchema.table("knowledge_access", {
  tenantId: text("tenant_id").notNull(),
  knowledgeBaseId: uuid("knowledge_base_id")
    .notNull()
    .references(() => ingestionJobs.id, { onDelete: "cascade" }),
  enabled: boolean("enabled").default(true).notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
}, (table) => [
  primaryKey({
    name: "knowledge_access_tenant_knowledge_pk",
    columns: [table.tenantId, table.knowledgeBaseId],
  }),
]);
