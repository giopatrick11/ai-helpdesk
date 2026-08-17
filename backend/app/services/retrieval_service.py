from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.services.embedding_service import create_query_embedding


def search_documents(
    db: Session,
    user_id: int,
    question: str,
    limit: int = 3,
    max_distance: float = 0.45,
):
    query_embedding = create_query_embedding(question)

    distance = DocumentChunk.embedding.cosine_distance(
        query_embedding
    )

    results = (
        db.query(
            DocumentChunk,
            Document,
            distance.label("distance"),
        )
        .join(
            Document,
            Document.id == DocumentChunk.document_id
        )
        .filter(
            Document.user_id == user_id,
            Document.status == "ready",
        )
        .order_by(distance)
        .limit(limit)
        .all()
    )

    return [
        {
            "chunk": chunk,
            "document": document,
            "distance": float(score),
        }
        for chunk, document, score in results
        if score <= max_distance
    ]