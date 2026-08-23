from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.schemas.ai import TicketAnalysisResponse


_client = None

MODEL = GEMINI_MODEL


def get_client():
    global _client

    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)

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
