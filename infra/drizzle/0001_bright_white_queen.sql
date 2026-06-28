CREATE SCHEMA "BrResearch";
--> statement-breakpoint
CREATE TABLE "BrResearch"."document_chunks" (
	"id" bigserial PRIMARY KEY NOT NULL,
	"job_id" uuid,
	"tenant_id" text NOT NULL,
	"content" text NOT NULL,
	"embedding" vector(1536)
);
--> statement-breakpoint
CREATE TABLE "BrResearch"."ingestion_jobs" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"source_type" text NOT NULL,
	"source_target" text NOT NULL,
	"tenant_id" text NOT NULL,
	"status" text DEFAULT 'queued' NOT NULL,
	"error_log" text
);
--> statement-breakpoint
DROP TABLE "BRhabibieebhy"."document_chunks" CASCADE;--> statement-breakpoint
DROP TABLE "BRhabibieebhy"."ingestion_jobs" CASCADE;--> statement-breakpoint
ALTER TABLE "BrResearch"."document_chunks" ADD CONSTRAINT "document_chunks_job_id_ingestion_jobs_id_fk" FOREIGN KEY ("job_id") REFERENCES "BrResearch"."ingestion_jobs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
DROP SCHEMA "BRhabibieebhy";
