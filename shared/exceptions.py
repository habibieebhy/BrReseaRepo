class PipelineException(Exception):
    pass


class DownloadError(PipelineException):
    pass


class ParseError(PipelineException):
    pass


class ChunkingError(PipelineException):
    pass


class EmbeddingError(PipelineException):
    pass


class DatabaseError(PipelineException):
    pass


class ValidationError(PipelineException):
    pass