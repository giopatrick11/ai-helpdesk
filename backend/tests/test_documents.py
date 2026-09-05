from app.models.document import Document, DocumentChunk
from app.models.user import User
import pytest

from app.jobs.document_jobs import process_document
from app.services.retrieval_service import search_documents


def register_and_login(client, name, email):
    register_response = client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_create_document(client):
    token = register_and_login(
        client,
        "Document User",
        "document@example.com",
    )

    response = client.post(
        "/api/documents/",
        json={
            "title": "Refund Policy",
            "content": "Refunds are processed within five business days.",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Refund Policy"
    assert data["status"] == "processing"
    assert data["processing_error"] is None


def test_user_only_sees_own_documents(client):
    user1_token = register_and_login(
        client,
        "Document Owner",
        "doc-owner@example.com",
    )

    user2_token = register_and_login(
        client,
        "Other Document User",
        "doc-other@example.com",
    )

    create_response = client.post(
        "/api/documents/",
        json={
            "title": "Private Document",
            "content": "Only User 1 should see this.",
        },
        headers={
            "Authorization": f"Bearer {user1_token}"
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/documents/",
        headers={
            "Authorization": f"Bearer {user2_token}"
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_user_cannot_access_another_users_document(client):
    user1_token = register_and_login(
        client,
        "Document Owner 2",
        "doc-owner2@example.com",
    )

    user2_token = register_and_login(
        client,
        "Document Other 2",
        "doc-other2@example.com",
    )

    create_response = client.post(
        "/api/documents/",
        json={
            "title": "Secret Document",
            "content": "This belongs to User 1.",
        },
        headers={
            "Authorization": f"Bearer {user1_token}"
        },
    )

    assert create_response.status_code == 201

    document_id = create_response.json()["id"]

    response = client.get(
        f"/api/documents/{document_id}",
        headers={
            "Authorization": f"Bearer {user2_token}"
        },
    )

    assert response.status_code == 404


def test_user_cannot_delete_another_users_document(client):
    user1_token = register_and_login(
        client,
        "Delete Document Owner",
        "delete-doc-owner@example.com",
    )

    user2_token = register_and_login(
        client,
        "Delete Document Other",
        "delete-doc-other@example.com",
    )

    create_response = client.post(
        "/api/documents/",
        json={
            "title": "Do Not Delete",
            "content": "Only the owner can delete this document.",
        },
        headers={
            "Authorization": f"Bearer {user1_token}"
        },
    )

    assert create_response.status_code == 201

    document_id = create_response.json()["id"]

    response = client.delete(
        f"/api/documents/{document_id}",
        headers={
            "Authorization": f"Bearer {user2_token}"
        },
    )

    assert response.status_code == 404

def test_deleting_document_deletes_chunks(
    client,
    db_session,
):
    token = register_and_login(
        client,
        "Cascade User",
        "cascade@example.com",
    )

    create_response = client.post(
        "/api/documents/",
        json={
            "title": "Cascade Document",
            "content": "This document will be deleted.",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert create_response.status_code == 201

    document_id = create_response.json()["id"]

    chunk = DocumentChunk(
        document_id=document_id,
        content="Test chunk",
        embedding=[0.0] * 768,
    )

    db_session.add(chunk)
    db_session.commit()

    chunk_count = (
        db_session.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id == document_id
        )
        .count()
    )

    assert chunk_count == 1

    delete_response = client.delete(
        f"/api/documents/{document_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert delete_response.status_code == 204

    db_session.expire_all()

    remaining_chunks = (
        db_session.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id == document_id
        )
        .count()
    )

    assert remaining_chunks == 0

def test_search_only_uses_ready_documents(
    client,
    db_session,
    monkeypatch,
):
    token = register_and_login(
        client,
        "Search User",
        "search-user@example.com",
    )

    user = (
        db_session.query(User)
        .filter(User.email == "search-user@example.com")
        .first()
    )

    assert user is not None

    processing_document = Document(
        user_id=user.id,
        title="Processing Document",
        content="Refunds take five business days.",
        status="processing",
    )

    ready_document = Document(
        user_id=user.id,
        title="Ready Document",
        content="Refunds take five business days.",
        status="ready",
    )

    db_session.add(processing_document)
    db_session.add(ready_document)
    db_session.commit()

    db_session.refresh(processing_document)
    db_session.refresh(ready_document)

    test_vector = [0.1] * 768

    processing_chunk = DocumentChunk(
        document_id=processing_document.id,
        content="Processing document chunk",
        embedding=test_vector,
    )

    ready_chunk = DocumentChunk(
        document_id=ready_document.id,
        content="Ready document chunk",
        embedding=test_vector,
    )

    db_session.add(processing_chunk)
    db_session.add(ready_chunk)
    db_session.commit()

    monkeypatch.setattr(
        "app.services.retrieval_service.create_query_embedding",
        lambda question: test_vector,
    )

    results = search_documents(
        db=db_session,
        user_id=user.id,
        question="How long do refunds take?",
        limit=10,
    )

    assert len(results) == 1
    assert results[0]["document"].id == ready_document.id
    assert results[0]["document"].status == "ready"


def test_document_enqueue_failure_marks_document_failed(client, monkeypatch):
    token = register_and_login(
        client,
        "Document Queue Failure",
        "document-queue-failure@example.com",
    )

    def fail_enqueue(*args, **kwargs):
        raise ConnectionError("Redis is unavailable")

    monkeypatch.setattr(
        "app.routes.documents.ai_queue.enqueue",
        fail_enqueue,
    )

    response = client.post(
        "/api/documents/",
        json={
            "title": "Queue Failure Document",
            "content": "This document must not remain processing.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert response.json()["processing_error"] == (
        "Document processing could not be queued."
    )


def test_document_enqueue_uses_retry_policy(client, monkeypatch):
    token = register_and_login(
        client,
        "Document Queue Success",
        "document-queue-success@example.com",
    )
    enqueue_calls = []

    def capture_enqueue(*args, **kwargs):
        enqueue_calls.append((args, kwargs))

    monkeypatch.setattr(
        "app.routes.documents.ai_queue.enqueue",
        capture_enqueue,
    )

    response = client.post(
        "/api/documents/",
        json={
            "title": "Queue Success Document",
            "content": "This document should be queued with retries.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "processing"
    assert len(enqueue_calls) == 1
    assert enqueue_calls[0][1]["retry"].max == 2
    assert enqueue_calls[0][1]["retry"].intervals == [10, 30]


def test_pdf_upload_success(client, monkeypatch):
    token = register_and_login(
        client,
        "PDF Upload User",
        "pdf-upload@example.com",
    )
    monkeypatch.setattr(
        "app.routes.documents.extract_pdf_text",
        lambda file_bytes: ("Readable PDF content.", 2),
    )

    response = client.post(
        "/api/documents/upload-pdf",
        data={"title": "Policy PDF"},
        files={"file": ("policy.pdf", b"pdf-bytes", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "policy.pdf"
    assert response.json()["pages"] == 2
    assert response.json()["status"] == "processing"


def test_invalid_pdf_is_rejected(client):
    token = register_and_login(
        client,
        "Invalid PDF User",
        "invalid-pdf@example.com",
    )

    response = client.post(
        "/api/documents/upload-pdf",
        data={"title": "Broken PDF"},
        files={"file": ("broken.pdf", b"not a pdf", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The PDF could not be read"


def test_oversized_pdf_is_rejected(client, monkeypatch):
    token = register_and_login(
        client,
        "Large PDF User",
        "large-pdf@example.com",
    )
    monkeypatch.setattr("app.routes.documents.MAX_PDF_UPLOAD_BYTES", 4)

    response = client.post(
        "/api/documents/upload-pdf",
        data={"title": "Large PDF"},
        files={"file": ("large.pdf", b"12345", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "PDF file is too large"


def test_document_job_marks_ready_and_creates_chunks(
    client,
    db_session,
    monkeypatch,
):
    token = register_and_login(
        client,
        "Document Job User",
        "document-job@example.com",
    )
    response = client.post(
        "/api/documents/",
        json={
            "title": "Worker Document",
            "content": "A short document for the worker.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    document_id = response.json()["id"]

    monkeypatch.setattr(
        "app.jobs.document_jobs.SessionLocal",
        lambda: db_session,
    )
    monkeypatch.setattr(
        "app.jobs.document_jobs.create_document_embedding",
        lambda content: [0.1] * 768,
    )

    process_document(document_id)

    document = db_session.query(Document).filter(
        Document.id == document_id
    ).first()
    assert document.status == "ready"
    assert document.processing_error is None
    assert len(document.chunks) == 1


def test_document_job_failure_marks_failed(
    client,
    db_session,
    monkeypatch,
):
    token = register_and_login(
        client,
        "Document Job Failure",
        "document-job-failure@example.com",
    )
    response = client.post(
        "/api/documents/",
        json={
            "title": "Failing Worker Document",
            "content": "Embedding should fail safely.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    document_id = response.json()["id"]

    monkeypatch.setattr(
        "app.jobs.document_jobs.SessionLocal",
        lambda: db_session,
    )

    def fail_embedding(content):
        raise RuntimeError("Provider failure")

    monkeypatch.setattr(
        "app.jobs.document_jobs.create_document_embedding",
        fail_embedding,
    )

    with pytest.raises(RuntimeError):
        process_document(document_id)

    document = db_session.query(Document).filter(
        Document.id == document_id
    ).first()
    assert document.status == "failed"
    assert document.processing_error == "Document processing failed."


def test_document_job_stays_processing_while_retry_is_available(
    client,
    db_session,
    monkeypatch,
):
    token = register_and_login(
        client,
        "Document Retry User",
        "document-retry@example.com",
    )
    response = client.post(
        "/api/documents/",
        json={
            "title": "Retry Document",
            "content": "Embedding should be retried.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    document_id = response.json()["id"]

    monkeypatch.setattr(
        "app.jobs.document_jobs.SessionLocal",
        lambda: db_session,
    )
    monkeypatch.setattr(
        "app.jobs.document_jobs.get_current_job",
        lambda: type("RetryingJob", (), {"should_retry": True})(),
    )

    def fail_embedding(content):
        raise RuntimeError("Temporary provider failure")

    monkeypatch.setattr(
        "app.jobs.document_jobs.create_document_embedding",
        fail_embedding,
    )

    with pytest.raises(RuntimeError):
        process_document(document_id)

    document = db_session.query(Document).filter(
        Document.id == document_id
    ).first()
    assert document.status == "processing"
    assert document.processing_error is None


def test_ask_endpoint_returns_mocked_sources(client, monkeypatch):
    token = register_and_login(
        client,
        "RAG Ask User",
        "rag-ask@example.com",
    )
    monkeypatch.setattr(
        "app.routes.documents.ask_rag",
        lambda db, user_id, question: {
            "answer": "Refunds take five business days.",
            "sources": [
                {
                    "chunk_id": 1,
                    "document_id": 2,
                    "title": "Refund Policy",
                    "distance": 0.1,
                }
            ],
        },
    )

    response = client.post(
        "/api/documents/ask",
        json={"question": "How long do refunds take?"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["sources"][0]["title"] == "Refund Policy"


def test_search_isolates_documents_by_user(
    client,
    db_session,
    monkeypatch,
):
    register_and_login(
        client,
        "RAG Owner",
        "rag-owner@example.com",
    )
    register_and_login(
        client,
        "RAG Other",
        "rag-other@example.com",
    )
    users = {
        user.email: user
        for user in db_session.query(User).filter(
            User.email.in_(["rag-owner@example.com", "rag-other@example.com"])
        )
    }
    test_vector = [0.1] * 768

    for email, title in [
        ("rag-owner@example.com", "Owner Policy"),
        ("rag-other@example.com", "Other Policy"),
    ]:
        document = Document(
            user_id=users[email].id,
            title=title,
            content="Shared search terms.",
            status="ready",
        )
        db_session.add(document)
        db_session.flush()
        db_session.add(DocumentChunk(
            document_id=document.id,
            content=f"{title} content",
            embedding=test_vector,
        ))

    db_session.commit()
    monkeypatch.setattr(
        "app.services.retrieval_service.create_query_embedding",
        lambda question: test_vector,
    )

    owner = users["rag-owner@example.com"]
    results = search_documents(
        db=db_session,
        user_id=owner.id,
        question="Shared search terms",
        limit=10,
    )

    assert [result["document"].title for result in results] == ["Owner Policy"]


def test_deleted_document_is_not_retrievable(
    client,
    db_session,
    monkeypatch,
):
    token = register_and_login(
        client,
        "Deleted RAG User",
        "deleted-rag@example.com",
    )
    user = db_session.query(User).filter(
        User.email == "deleted-rag@example.com"
    ).first()
    document = Document(
        user_id=user.id,
        title="Temporary Policy",
        content="Temporary searchable content.",
        status="ready",
    )
    db_session.add(document)
    db_session.flush()
    db_session.add(DocumentChunk(
        document_id=document.id,
        content="Temporary searchable content.",
        embedding=[0.1] * 768,
    ))
    db_session.commit()
    document_id = document.id

    monkeypatch.setattr(
        "app.services.retrieval_service.create_query_embedding",
        lambda question: [0.1] * 768,
    )

    delete_response = client.delete(
        f"/api/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 204

    results = search_documents(
        db=db_session,
        user_id=user.id,
        question="Temporary searchable content",
        limit=10,
    )
    assert results == []
