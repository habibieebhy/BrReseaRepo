CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS "BrResearch";

CREATE TABLE IF NOT EXISTS "BrResearch"."ingestion_jobs" (
    "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "source_type" text NOT NULL,
    "source_target" text NOT NULL,
    "tenant_id" text NOT NULL,
    "status" text NOT NULL DEFAULT 'queued',
    "error_log" text,
    "created_at" timestamp with time zone NOT NULL DEFAULT now(),
    "updated_at" timestamp with time zone NOT NULL DEFAULT now(),
    "started_at" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "current_stage" text,
    "celery_task_id" text,
    "attempt_count" integer NOT NULL DEFAULT 0,
    "max_attempts" integer NOT NULL DEFAULT 3,
    "terminal" boolean NOT NULL DEFAULT false,
    "retryable" boolean NOT NULL DEFAULT true,
    "retry_count" integer NOT NULL DEFAULT 0,
    "parent_job_id" uuid,
    "context_json" jsonb
);

ALTER TABLE "BrResearch"."ingestion_jobs"
    ADD COLUMN IF NOT EXISTS "created_at" timestamp with time zone NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS "updated_at" timestamp with time zone NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS "started_at" timestamp with time zone,
    ADD COLUMN IF NOT EXISTS "completed_at" timestamp with time zone,
    ADD COLUMN IF NOT EXISTS "current_stage" text,
    ADD COLUMN IF NOT EXISTS "celery_task_id" text,
    ADD COLUMN IF NOT EXISTS "attempt_count" integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS "max_attempts" integer NOT NULL DEFAULT 3,
    ADD COLUMN IF NOT EXISTS "terminal" boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS "retryable" boolean NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS "retry_count" integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS "parent_job_id" uuid,
    ADD COLUMN IF NOT EXISTS "context_json" jsonb;

CREATE TABLE IF NOT EXISTS "BrResearch"."document_chunks" (
    "id" bigserial PRIMARY KEY,
    "job_id" uuid NOT NULL,
    "tenant_id" text NOT NULL,
    "content" text NOT NULL,
    "embedding" vector NOT NULL,
    "chunk_index" integer NOT NULL,
    "embedding_model" text NOT NULL,
    "embedding_dimension" integer NOT NULL
);

ALTER TABLE "BrResearch"."document_chunks"
    ALTER COLUMN "embedding" TYPE vector USING "embedding"::vector,
    ADD COLUMN IF NOT EXISTS "chunk_index" integer,
    ADD COLUMN IF NOT EXISTS "embedding_model" text,
    ADD COLUMN IF NOT EXISTS "embedding_dimension" integer;

ALTER TABLE "BrResearch"."document_chunks"
    ALTER COLUMN "chunk_index" TYPE integer
    USING NULLIF("chunk_index"::text, '')::integer;

UPDATE "BrResearch"."document_chunks"
SET
    "embedding_model" = COALESCE(
        "embedding_model",
        'nomic-ai/nomic-embed-text-v1.5'
    ),
    "embedding_dimension" = COALESCE(
        "embedding_dimension",
        vector_dims("embedding")
    );

WITH ranked AS (
    SELECT
        "id",
        row_number() OVER (PARTITION BY "job_id" ORDER BY "id") - 1 AS inferred_index
    FROM "BrResearch"."document_chunks"
    WHERE "chunk_index" IS NULL
)
UPDATE "BrResearch"."document_chunks" AS chunks
SET "chunk_index" = ranked.inferred_index
FROM ranked
WHERE chunks."id" = ranked."id";

ALTER TABLE "BrResearch"."document_chunks"
    ALTER COLUMN "job_id" SET NOT NULL,
    ALTER COLUMN "chunk_index" SET NOT NULL,
    ALTER COLUMN "embedding_model" SET NOT NULL,
    ALTER COLUMN "embedding_dimension" SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'document_chunks_job_id_ingestion_jobs_id_fk'
          AND conrelid = '"BrResearch"."document_chunks"'::regclass
    ) THEN
        ALTER TABLE "BrResearch"."document_chunks"
            ADD CONSTRAINT "document_chunks_job_id_ingestion_jobs_id_fk"
            FOREIGN KEY ("job_id")
            REFERENCES "BrResearch"."ingestion_jobs"("id")
            ON DELETE CASCADE;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS "document_chunks_job_chunk_idx"
    ON "BrResearch"."document_chunks" ("job_id", "chunk_index");
CREATE INDEX IF NOT EXISTS "ingestion_jobs_tenant_created_idx"
    ON "BrResearch"."ingestion_jobs" ("tenant_id", "created_at" DESC);
CREATE INDEX IF NOT EXISTS "ingestion_jobs_status_updated_idx"
    ON "BrResearch"."ingestion_jobs" ("status", "updated_at");
CREATE INDEX IF NOT EXISTS "document_chunks_tenant_job_idx"
    ON "BrResearch"."document_chunks" ("tenant_id", "job_id");

CREATE TABLE IF NOT EXISTS "BrResearch"."knowledge_access" (
    "tenant_id" text NOT NULL,
    "knowledge_base_id" uuid NOT NULL
        REFERENCES "BrResearch"."ingestion_jobs"("id") ON DELETE CASCADE,
    "enabled" boolean NOT NULL DEFAULT true,
    "updated_at" timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT "knowledge_access_tenant_knowledge_pk"
        PRIMARY KEY ("tenant_id", "knowledge_base_id")
);

CREATE TABLE IF NOT EXISTS "BrResearch"."sources" (
    "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "tenant_id" text NOT NULL,
    "payload" jsonb NOT NULL DEFAULT '{}'::jsonb,
    "created_at" timestamp with time zone NOT NULL DEFAULT now(),
    "updated_at" timestamp with time zone NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS "sources_tenant_created_idx"
    ON "BrResearch"."sources" ("tenant_id", "created_at" DESC);
CREATE INDEX IF NOT EXISTS "sources_last_job_idx"
    ON "BrResearch"."sources" (("payload"->>'last_job_id'));

CREATE TABLE IF NOT EXISTS "BrResearch"."simulation_runs" (
    "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "tenant_id" text NOT NULL,
    "label" text,
    "case_card_id" text NOT NULL,
    "solver" text NOT NULL,
    "execution_mode" text NOT NULL,
    "status" text NOT NULL DEFAULT 'queued',
    "current_stage" text,
    "spec_json" jsonb NOT NULL,
    "evidence_json" jsonb NOT NULL DEFAULT '[]'::jsonb,
    "summary_json" jsonb,
    "artifacts_json" jsonb NOT NULL DEFAULT '[]'::jsonb,
    "error_log" text,
    "celery_task_id" text,
    "artifact_prefix" text NOT NULL,
    "created_at" timestamp with time zone NOT NULL DEFAULT now(),
    "updated_at" timestamp with time zone NOT NULL DEFAULT now(),
    "started_at" timestamp with time zone,
    "completed_at" timestamp with time zone
);

CREATE INDEX IF NOT EXISTS "simulation_runs_tenant_created_idx"
    ON "BrResearch"."simulation_runs" ("tenant_id", "created_at" DESC);
