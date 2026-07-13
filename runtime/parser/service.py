import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from docling.datamodel.accelerator_options import (
    AcceleratorDevice,
    AcceleratorOptions,
)
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from runtime.artifacts.repository import ArtifactRepository
from brixta_sdk.context import PipelineContext


DEVICE_OPTIONS = {
    "auto": AcceleratorDevice.AUTO,
    "cpu": AcceleratorDevice.CPU,
    "mps": AcceleratorDevice.MPS,
    "cuda": AcceleratorDevice.CUDA,
    "xpu": AcceleratorDevice.XPU,
}

device_name = os.getenv("BRIXTA_DOCLING_DEVICE", "cpu").strip().lower()

if device_name not in DEVICE_OPTIONS:
    raise RuntimeError(
        f"Unsupported BRIXTA_DOCLING_DEVICE '{device_name}'. "
        f"Choose one of: {', '.join(DEVICE_OPTIONS)}"
    )

thread_count = int(os.getenv("BRIXTA_DOCLING_THREADS", "4"))

pdf_options = PdfPipelineOptions()
pdf_options.accelerator_options = AcceleratorOptions(
    device=DEVICE_OPTIONS[device_name],
    num_threads=thread_count,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pdf_options,
        )
    }
)

def parse_document(context: PipelineContext) -> Path:
    """
    Parses a downloaded document into a DoclingDocument and exports
    both the serialized document and Markdown.
    """

    job_id = context.job_id
    if context.source_type == "local_file":
        source = Path(context.source_target)
        if not source.is_file():
            raise FileNotFoundError(f"Uploaded file for job '{job_id}' not found.")
        result = converter.convert(source)
    elif not ArtifactRepository.raw_exists(job_id):
        raise FileNotFoundError(
            f"No downloaded document found for job '{job_id}'."
        )
    else:
        raw_html = ArtifactRepository.load_raw(job_id)
        with NamedTemporaryFile(
            suffix=".html",
            mode="w",
            encoding="utf-8",
            delete=False,
        ) as tmp:
            tmp.write(raw_html)
            temp_file = tmp.name
        result = converter.convert(temp_file)

    document = result.document

    # --------------------------------------------------
    # Save canonical DoclingDocument
    # --------------------------------------------------

    ArtifactRepository.save_docling(
        job_id,
        document.model_dump_json(
            indent=2,
        ),
    )

    # --------------------------------------------------
    # Export Markdown
    # --------------------------------------------------

    ArtifactRepository.save_markdown(
        job_id,
        document.export_to_markdown(),
    )

    return Path(f"markdown/{job_id}.md")
