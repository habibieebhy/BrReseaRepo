from brixta_sdk.context import PipelineContext
from brixta_sdk.downloader import DownloaderPlugin

from runtime.downloader.service import download_document


class DefaultDownloaderPlugin(DownloaderPlugin):

    def download(
        self,
        context: PipelineContext,
    ) -> PipelineContext:

        if context.raw_path and context.raw_path.exists():
            return context

        context.raw_path = download_document(context.job_id)

        return context