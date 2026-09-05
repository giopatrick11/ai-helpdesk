import app.models
from rq import get_current_job

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

        ticket.ai_status = "processing"
        ticket.ai_error = None
        db.commit()

        analysis = analyze_ticket(
            ticket.subject,
            ticket.description,
        )

        ticket.priority = analysis.priority.value
        ticket.category = analysis.category
        ticket.ai_summary = analysis.summary
        ticket.ai_status = "completed"
        ticket.ai_error = None

        db.commit()

    except Exception as error:
        db.rollback()

        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id
        ).first()

        if ticket:
            job = get_current_job()

            if job is not None and job.should_retry:
                ticket.ai_status = "processing"
                ticket.ai_error = None
            else:
                ticket.ai_status = "failed"
                ticket.ai_error = "Ticket AI analysis failed."

            db.commit()

        print(f"Background AI analysis failed: {error}")
        raise

    finally:
        db.close()
