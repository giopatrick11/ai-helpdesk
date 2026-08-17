from sqlalchemy.orm import Session

from app.models.document import Document


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
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document