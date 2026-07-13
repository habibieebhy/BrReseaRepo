ALTER TABLE "BrResearch"."document_chunks"
  ALTER COLUMN "embedding" TYPE vector;

ALTER TABLE "BrResearch"."document_chunks"
  ADD COLUMN IF NOT EXISTS "embedding_model" text,
  ADD COLUMN IF NOT EXISTS "embedding_dimension" integer;

UPDATE "BrResearch"."document_chunks"
SET
  "embedding_model" = COALESCE("embedding_model", 'nomic-ai/nomic-embed-text-v1.5'),
  "embedding_dimension" = COALESCE("embedding_dimension", 768);

ALTER TABLE "BrResearch"."document_chunks"
  ALTER COLUMN "embedding_model" SET NOT NULL,
  ALTER COLUMN "embedding_dimension" SET NOT NULL;
