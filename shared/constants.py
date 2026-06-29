EMBEDDING_DIMENSION = 1536

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

MAX_RETRIES = 3

DOWNLOAD_TIMEOUT = 60

DOCS_DIRECTORY = "storage/documents"

MARKDOWN_DIRECTORY = "storage/markdown"

QUEUE_DOWNLOAD = "download_queue"
QUEUE_PARSE = "parse_queue"
QUEUE_CLEAN = "clean_queue"
QUEUE_CHUNK = "chunk_queue"
QUEUE_EMBED = "embedding_queue"
QUEUE_STORE = "storage_queue"