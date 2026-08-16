import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.schemas.ai import TicketAnalysisResponse


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

_client = None

MODEL = os.getenv("GEMINI_MODEL")


def get_client():
    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        _client = genai.Client(api_key=api_key)

    return _client


def analyze_ticket(
    subject: str,
    description: str
) -> TicketAnalysisResponse:

    prompt = f"""
Analyze this customer support ticket.

Subject:
{subject}

Description:
{description}

Determine:
- the most appropriate category
- priority: low, medium, or high
- a short summary
"""

    if not MODEL:
        raise ValueError("GEMINI_MODEL is not configured")

    response = get_client().models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TicketAnalysisResponse,
        ),
    )

    return TicketAnalysisResponse.model_validate_json(
        response.text
    )
