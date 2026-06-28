import { pgSchema, text, uuid, bigserial, customType } from 'drizzle-orm/pg-core';

// 1. Declare your exact custom schema from the dashboard
export const brixtaSchema = pgSchema('BrResearch');

// Custom type helper for pgvector data weights
const vector = customType<{ data: number[] }>({
  dataType() {
    return 'vector(1536)';
  },
});

// 2. Use brixtaSchema.table instead of pgTable
export const ingestionJobs = brixtaSchema.table('ingestion_jobs', {
  id: uuid('id').primaryKey().defaultRandom(),
  sourceType: text('source_type').notNull(),
  sourceTarget: text('source_target').notNull(),
  tenantId: text('tenant_id').notNull(),
  status: text('status').default('queued').notNull(),
  errorLog: text('error_log'),
});

export const documentChunks = brixtaSchema.table('document_chunks', {
  id: bigserial('id', { mode: 'bigint' }).primaryKey(),
  jobId: uuid('job_id').references(() => ingestionJobs.id, { onDelete: 'cascade' }),
  tenantId: text('tenant_id').notNull(),
  content: text('content').notNull(),
  embedding: vector('embedding'),
});