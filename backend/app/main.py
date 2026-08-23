from fastapi import FastAPI

from app.routes.tickets import router as tickets_router
from app.routes.auth import router as auth_router
from app.routes.ai import router as ai_router
from app.routes.documents import router as documents_router
from app.config import CORS_ORIGINS
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
