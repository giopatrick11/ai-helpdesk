from io import BytesIO

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.document import Document


class PDFProcessingError(ValueError):
    """Raised when a PDF cannot be safely converted to text."""


def extract_pdf_text(file_bytes: bytes) -> tuple[str, int]:
    try:
        reader = PdfReader(BytesIO(file_bytes))

        if reader.is_encrypted:
            raise PDFProcessingError("Encrypted PDFs are not supported")

        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)
    except PDFProcessingError:
        raise
    except Exception as error:
        raise PDFProcessingError("The PDF could not be read") from error

    content = "\n\n".join(pages)

    if not content.strip():
        raise PDFProcessingError("No readable text found in PDF")

    return content, len(reader.pages)


def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    words = text.split()

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    step = chunk_size - overlap

    for i in range(0, len(words), step):
        chunk_words = words[i:i + chunk_size]

        if not chunk_words:
            break

        chunks.append(" ".join(chunk_words))

        if i + chunk_size >= len(words):
            break

    return chunks


def create_document(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    filename: str | None = None,
):
    document = Document(
        user_id=user_id,
        title=title,
        filename=filename,
        content=content,
        status="processing",
        processing_error=None,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document
