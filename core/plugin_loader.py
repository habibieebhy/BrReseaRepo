from plugins.downloader.default import DefaultDownloaderPlugin
from plugins.parser.docling import DoclingParserPlugin
from plugins.chunker.hybrid import HybridChunkerPlugin
from plugins.embedding.nomic import SentenceTransformersEmbeddingPlugin
from plugins.storage.pgvector import PgVectorStoragePlugin


class PluginLoader:

    downloader = DefaultDownloaderPlugin()
    parser = DoclingParserPlugin()
    chunker = HybridChunkerPlugin()
    embedding = SentenceTransformersEmbeddingPlugin()
    storage = PgVectorStoragePlugin()