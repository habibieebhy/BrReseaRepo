from pathlib import Path

from brixta_sdk.context import PipelineContext
from brixta_sdk.downloader import DownloaderPlugin


class LocalFileDownloaderPlugin(DownloaderPlugin):
    name = "Local File"
    version = "1.0.0"
    source_types = ["local_file"]

    def download(self, context: PipelineContext) -> PipelineContext:
        if context.source_type != "local_file":
            raise ValueError(f"Unsupported source type '{context.source_type}'.")
        path = Path(context.source_target).resolve()
        uploads = Path("storage/uploads").resolve()
        if uploads not in path.parents or not path.is_file():
            raise FileNotFoundError("Uploaded source file is unavailable.")
        context.raw_path = path
        return context
