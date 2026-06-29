from enum import Enum


class JobStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"

    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"

    PARSING = "parsing"
    PARSED = "parsed"

    CLEANING = "cleaning"

    CHUNKING = "chunking"

    EMBEDDING = "embedding"

    STORING = "storing"

    COMPLETED = "completed"

    FAILED = "failed"

    RETRYING = "retrying"

    CANCELLED = "cancelled"


class SourceType(str, Enum):
    URL = "url"
    PDF = "pdf"
    HTML = "html"
    DOI = "doi"
    ARXIV = "arxiv"
    PATENT = "patent"
    LOCAL_FILE = "local_file"
    SITEMAP = "sitemap"