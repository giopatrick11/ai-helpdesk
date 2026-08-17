from app.models.document import DocumentChunk
from app.models.document import Document, DocumentChunk
from app.models.user import User
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