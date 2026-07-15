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
    "completed_at" timestamp with time zone,
    CONSTRAINT "simulation_runs_execution_mode_check"
        CHECK ("execution_mode" IN ('preview', 'solver')),
    CONSTRAINT "simulation_runs_status_check"
        CHECK ("status" IN (
            'queued', 'compiling', 'running', 'postprocessing',
            'completed', 'failed', 'cancelled'
        ))
);

CREATE INDEX IF NOT EXISTS "simulation_runs_tenant_created_idx"
    ON "BrResearch"."simulation_runs" ("tenant_id", "created_at" DESC);

