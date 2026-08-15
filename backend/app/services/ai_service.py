import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.schemas.ai import TicketAnalysisResponse


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = os.getenv("GEMINI_MODEL")


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

    response = client.models.generate_content(
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