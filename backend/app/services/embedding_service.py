from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL


_client = None

MODEL = GEMINI_EMBEDDING_MODEL


def get_client():
    global _client

    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)

    return _client


def create_document_embedding(text: str) -> list[float]:
    response = get_client().models.embed_content(
        model=MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=768,
        ),
    )

    return response.embeddings[0].values


def create_query_embedding(text: str) -> list[float]:
    response = get_client().models.embed_content(
        model=MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768,
        ),
    )

    return response.embeddings[0].values
