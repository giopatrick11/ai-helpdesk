from fastapi import APIRouter
from app.schemas.ticket import TicketCreate

router = APIRouter()

tickets = []


@router.get("/")
def get_tickets():
    return tickets


@router.post("/", status_code=201)
def create_ticket(ticket: TicketCreate):
    new_ticket = {
        "id": len(tickets) + 1,
        "subject": ticket.subject,
        "description": ticket.description,
        "priority": ticket.priority,
        "status": "open",
    }

    tickets.append(new_ticket)

    return new_ticket