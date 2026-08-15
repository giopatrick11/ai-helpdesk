from app.database.database import SessionLocal
from app.models.ticket import Ticket
from app.services.ai_service import analyze_ticket


def analyze_ticket_job(ticket_id: int):
    db = SessionLocal()

    try:
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id
        ).first()

        if not ticket:
            return

        analysis = analyze_ticket(
            ticket.subject,
            ticket.description,
        )

        ticket.priority = analysis.priority.value
        ticket.category = analysis.category
        ticket.ai_summary = analysis.summary

        db.commit()

    except Exception as error:
        db.rollback()
        print(f"Background AI analysis failed: {error}")

    finally:
        db.close()