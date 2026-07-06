from brixta_sdk.context import PipelineContext
from brixta_sdk.parser import ParserPlugin

from runtime.parser.service import parse_document


class DoclingParserPlugin(ParserPlugin):

    def parse(
        self,
        context: PipelineContext,
    ) -> PipelineContext:

        if context.parsed_path and context.parsed_path.exists():
            return context

        context.parsed_path = parse_document(context.job_id)

        return context