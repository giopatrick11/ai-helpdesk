from pydantic import BaseModel


class TicketCreate(BaseModel):
    subject: str
    description: str
    priority: str