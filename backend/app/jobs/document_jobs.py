import app.models

from app.database.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.services.document_service import split_text
from app.services.embedding_service import create_document_embedding



def process_document(document_id: int):
    db = SessionLocal()

    try:
        document = db.query(Document).filter(
            Document.id == document_id
        ).first()

        if not document:
            return

        chunks = split_text(document.content)

        for chunk_content in chunks:
            embedding = create_document_embedding(
                chunk_content
            )

            chunk = DocumentChunk(
                document_id=document.id,
                content=chunk_content,
                embedding=embedding,
            )

            db.add(chunk)

        document.status = "ready"

        db.commit()

    except Exception:
        db.rollback()

        document = db.query(Document).filter(
            Document.id == document_id
        ).first()

        if document:
            document.status = "failed"
            db.commit()

        raise

    finally:
        db.close()