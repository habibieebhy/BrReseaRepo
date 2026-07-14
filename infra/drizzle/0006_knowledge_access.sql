CREATE TABLE IF NOT EXISTS "BrResearch"."knowledge_access" (
  "tenant_id" text NOT NULL,
  "knowledge_base_id" uuid NOT NULL REFERENCES "BrResearch"."ingestion_jobs"("id") ON DELETE CASCADE,
  "enabled" boolean DEFAULT true NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "knowledge_access_tenant_knowledge_pk" PRIMARY KEY ("tenant_id", "knowledge_base_id")
);
