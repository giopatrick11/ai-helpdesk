from fastapi import FastAPI

from app.database.database import Base, engine
from app.models.ticket import Ticket
from app.models.user import User
from app.routes.tickets import router as tickets_router
from app.routes.auth import router as auth_router


Base.metadata.create_all(bind=engine)

app = FastAPI()


app.include_router(
    tickets_router,
    prefix="/api/tickets",
    tags=["Tickets"],
)


@app.get("/")
def root():
    return {
        "message": "AI Helpdesk API is running"
    }

app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["Authentication"],
)