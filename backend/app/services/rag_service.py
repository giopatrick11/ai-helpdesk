from sqlalchemy.orm import Session

from app.services.retrieval_service import search_documents
from app.services.ai_service import get_client, MODEL


def ask_rag(
    db: Session,
    user_id: int,
    question: str,
):
    results = search_documents(
        db=db,
        user_id=user_id,
        question=question,
        limit=3,
    )

    if not results:
        return {
            "answer": "I do not have enough information to answer that.",
            "sources": []
        }

    context = "\n\n".join(
        result["chunk"].content
        for result in results
    )

    prompt = f"""
You are a helpdesk assistant.

Answer the question using only the provided context.

If the answer is not contained in the context, say that you do not have enough information.

Context:
{context}

Question:
{question}
"""

    if not MODEL:
        raise ValueError("GEMINI_MODEL is not configured")

    response = get_client().models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    return {
        "answer": response.text,
        "sources": [
            {
                "chunk_id": result["chunk"].id,
                "document_id": result["document"].id,
                "title": result["document"].title,
                "distance": result["distance"],
            }
            for result in results
        ],
    }