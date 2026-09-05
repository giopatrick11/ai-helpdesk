"""Seed a demo user and support tickets for local development.

Run from the backend directory with::

    python -m app.seed

The seed is idempotent: the demo user's credentials are refreshed and tickets
are matched by subject before any missing records are inserted.
"""

import os
from dataclasses import dataclass

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.ticket import Ticket
from app.models.user import User


DEFAULT_NAME = "Alex Morgan"
DEFAULT_EMAIL = "demo@example.com"
DEFAULT_PASSWORD = "Demo123!"
LEGACY_EMAIL = "demo@ai-helpdesk.local"


@dataclass(frozen=True)
class TicketSeed:
    subject: str
    description: str
    priority: str
    status: str
    category: str
    ai_summary: str


TICKET_SEEDS = (
    TicketSeed(
        subject="Unable to sign in after password reset",
        description=(
            "I reset my password this morning, but the sign-in page still says "
            "my credentials are invalid. I have already cleared my browser cache."
        ),
        priority="high",
        status="open",
        category="Account Access",
        ai_summary=(
            "Customer cannot sign in after a password reset and has already "
            "tried clearing the browser cache."
        ),
    ),
    TicketSeed(
        subject="Duplicate charge on August invoice",
        description=(
            "Our August invoice includes the same workspace subscription charge "
            "twice. Please review the invoice and reverse the duplicate charge."
        ),
        priority="high",
        status="in_progress",
        category="Billing",
        ai_summary=(
            "Customer reports a duplicated workspace subscription charge on the "
            "August invoice and is requesting a reversal."
        ),
    ),
    TicketSeed(
        subject="Exported CSV is missing ticket tags",
        description=(
            "Ticket exports complete successfully, but the generated CSV does not "
            "contain the tags column shown in the export preview."
        ),
        priority="medium",
        status="open",
        category="Product Issue",
        ai_summary=(
            "CSV exports omit ticket tags even though tags appear in the export "
            "preview."
        ),
    ),
    TicketSeed(
        subject="Invite email never arrived",
        description=(
            "A new support agent was invited yesterday and has not received the "
            "invitation email. We checked their address and spam folder."
        ),
        priority="medium",
        status="resolved",
        category="Account Access",
        ai_summary=(
            "A team invitation email did not arrive after the address and spam "
            "folder were checked."
        ),
    ),
    TicketSeed(
        subject="How do I change notification hours?",
        description=(
            "I only want email notifications during our support team's business "
            "hours. Where can I configure the notification schedule?"
        ),
        priority="low",
        status="resolved",
        category="How-to",
        ai_summary=(
            "Customer wants instructions for restricting email notifications to "
            "business hours."
        ),
    ),
    TicketSeed(
        subject="Dashboard loads slowly for large queues",
        description=(
            "The dashboard takes around fifteen seconds to load when our open "
            "ticket count is above 500. Smaller queues load normally."
        ),
        priority="medium",
        status="in_progress",
        category="Performance",
        ai_summary=(
            "Dashboard load time rises to about fifteen seconds when the queue "
            "contains more than 500 open tickets."
        ),
    ),
)


def seed_database(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
) -> tuple[User, int]:
    """Create or refresh the demo user and insert any missing demo tickets."""

    password_hasher = PasswordHash.recommended()
    user = db.scalar(select(User).where(User.email == email))

    if user is None and email == DEFAULT_EMAIL:
        user = db.scalar(select(User).where(User.email == LEGACY_EMAIL))

        if user is not None:
            user.email = email

    if user is None:
        user = User(
            name=name,
            email=email,
            password_hash=password_hasher.hash(password),
        )
        db.add(user)
        db.flush()
    else:
        user.name = name
        user.password_hash = password_hasher.hash(password)

    existing_subjects = set(
        db.scalars(
            select(Ticket.subject).where(Ticket.user_id == user.id)
        ).all()
    )
    missing_tickets = [
        seed for seed in TICKET_SEEDS
        if seed.subject not in existing_subjects
    ]

    db.add_all(
        Ticket(
            user_id=user.id,
            subject=seed.subject,
            description=seed.description,
            priority=seed.priority,
            status=seed.status,
            category=seed.category,
            ai_summary=seed.ai_summary,
            ai_status="completed",
            ai_error=None,
        )
        for seed in missing_tickets
    )
    db.commit()
    db.refresh(user)

    return user, len(missing_tickets)


def main() -> None:
    name = os.getenv("SEED_USER_NAME", DEFAULT_NAME)
    email = os.getenv("SEED_USER_EMAIL", DEFAULT_EMAIL)
    password = os.getenv("SEED_USER_PASSWORD", DEFAULT_PASSWORD)

    with SessionLocal() as db:
        user, inserted_ticket_count = seed_database(
            db,
            name=name,
            email=email,
            password=password,
        )

    print(f"Seeded demo user {user.email} (id={user.id}).")
    print(
        f"Inserted {inserted_ticket_count} ticket(s); "
        f"{len(TICKET_SEEDS)} total expected."
    )
    print(f"Sign in with {email} and the configured seed password.")


if __name__ == "__main__":
    main()
