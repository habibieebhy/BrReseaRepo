from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from uuid import UUID

class IngestionJob(BaseModel):
    """
    Matches the Drizzle 'ingestion_jobs' table perfectly.
    """
    id: UUID = Field(..., description="Unique trackable v4 UUID for the job execution")
    source_type: str = Field(default="url", description="Type of source, e.g., 'url' or 'pdf'")
    source_target: HttpUrl = Field(..., description="The validated target URL to be crawled")
    tenant_id: str = Field(..., description="String key identifying the isolated workspace for RLS")
    status: str = Field(default="queued", description="Lifecycle state: queued | processing | completed | failed")
    error_log: Optional[str] = Field(default=None, description="Error log dump if execution halts")

class DocumentChunk(BaseModel):
    """
    Matches the Drizzle 'document_chunks' table perfectly.
    Note: 'id' is omitted because Postgres handles the bigserial auto-increment!
    """
    job_id: UUID = Field(..., description="The parent IngestionJob UUID linking back to source state")
    tenant_id: str = Field(..., description="The isolation string needed to enforce Supabase Row-Level Security")
    content: str = Field(..., description="The clean, open-source PII-scrubbed Markdown text snippet")
    embedding: Optional[List[float]] = Field(default=None, description="1536-dimensional float array for pgvector")