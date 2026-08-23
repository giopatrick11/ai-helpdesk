from fastapi import FastAPI

from app.database.database import Base, engine
from app.models.ticket import Ticket
from app.models.user import User
from app.routes.tickets import router as tickets_router
from app.routes.auth import router as auth_router
from app.routes.ai import router as ai_router
from app.models.document import Document, DocumentChunk
from app.routes.documents import router as documents_router
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    tickets_router,
    prefix="/api/tickets",
    tags=["Tickets"],
)


app.include_router(
    documents_router,
    prefix="/api/documents",
    tags=["Documents"],
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

app.include_router(
    ai_router,
    prefix="/api/ai",
    tags=["AI"],
)