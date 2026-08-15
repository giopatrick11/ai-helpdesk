from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import (
    TicketAnalysisRequest,
    TicketAnalysisResponse,
)
from app.services.ai_service import analyze_ticket


router = APIRouter()


@router.post(
    "/analyze-ticket",
    response_model=TicketAnalysisResponse
)
def analyze_ticket_route(
    ticket: TicketAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    return analyze_ticket(
        ticket.subject,
        ticket.description
    )   