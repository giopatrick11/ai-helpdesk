from fastapi import FastAPI
from app.routes.tickets import router as tickets_router

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