import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.database.database import Base, get_db

# Register all SQLAlchemy models with Base.metadata
import app.models


TEST_DATABASE_URL = (
    "postgresql+psycopg://giopatrick@localhost:5432/ai_helpdesk_test"
)


engine = create_engine(
    TEST_DATABASE_URL
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(fastapi_app)

@pytest.fixture()
def db_session():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(autouse=True)
def mock_rq_enqueue(monkeypatch):
    monkeypatch.setattr(
        "app.routes.tickets.ai_queue.enqueue",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        "app.routes.documents.ai_queue.enqueue",
        lambda *args, **kwargs: None,
    )