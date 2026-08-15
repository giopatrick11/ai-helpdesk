from pydantic import BaseModel
from app.schemas.ticket import Priority


class TicketAnalysisRequest(BaseModel):
    subject: str
    description: str


class TicketAnalysisResponse(BaseModel):
    category: str
    priority: Priority
    summary: str