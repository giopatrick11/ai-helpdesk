from types import SimpleNamespace

import pytest

from app.models.ticket import Ticket
from app.schemas.ticket import Priority
from app.jobs.ticket_jobs import analyze_ticket_job


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


def test_create_ticket(client):
    token = register_and_login(
        client,
        "Ticket User",
        "ticket@example.com",
    )

    response = client.post(
        "/api/tickets/",
        json={
            "subject": "Refund issue",
            "description": "My refund has not arrived yet.",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["subject"] == "Refund issue"
    assert data["description"] == "My refund has not arrived yet."
    assert data["status"] == "open"
    assert data["ai_status"] == "processing"
    assert data["ai_error"] is None


def test_ticket_list_includes_ai_status_fields(client):
    token = register_and_login(
        client,
        "AI Fields User",
        "ai-fields@example.com",
    )

    create_response = client.post(
        "/api/tickets/",
        json={
            "subject": "AI fields",
            "description": "Check response fields.",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/tickets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["ai_status"] == "processing"
    assert data[0]["ai_error"] is None


def test_user_only_sees_own_tickets(client):
    user1_token = register_and_login(
        client,
        "User One",
        "user1@example.com",
    )

    user2_token = register_and_login(
        client,
        "User Two",
        "user2@example.com",
    )

    create_response = client.post(
        "/api/tickets/",
        json={
            "subject": "User 1 Ticket",
            "description": "This belongs only to User 1.",
        },
        headers={
            "Authorization": f"Bearer {user1_token}"
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/tickets/",
        headers={
            "Authorization": f"Bearer {user2_token}"
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_user_cannot_access_another_users_ticket(client):
    user1_token = register_and_login(
        client,
        "Owner User",
        "owner@example.com",
    )

    user2_token = register_and_login(
        client,
        "Other User",
        "other@example.com",
    )

    create_response = client.post(
        "/api/tickets/",
        json={
            "subject": "Private Ticket",
            "description": "This ticket belongs to User 1.",
        },
        headers={
            "Authorization": f"Bearer {user1_token}"
        },
    )

    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]

    response = client.get(
        f"/api/tickets/{ticket_id}",
        headers={
            "Authorization": f"Bearer {user2_token}"
        },
    )

    assert response.status_code == 404


def test_user_cannot_update_another_users_ticket(client):
    user1_token = register_and_login(
        client,
        "Update Owner",
        "update-owner@example.com",
    )

    user2_token = register_and_login(
        client,
        "Update Other",
        "update-other@example.com",
    )

    create_response = client.post(
        "/api/tickets/",
        json={
            "subject": "Original Ticket",
            "description": "Original description.",
        },
        headers={
            "Authorization": f"Bearer {user1_token}"
        },
    )

    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]

    response = client.put(
        f"/api/tickets/{ticket_id}",
        json={
            "subject": "Changed",
            "description": "Changed by another user.",
            "priority": "high",
            "status": "resolved",
        },
        headers={
            "Authorization": f"Bearer {user2_token}"
        },
    )

    assert response.status_code == 404


def test_status_only_update_succeeds_and_preserves_existing_fields(
    client,
    db_session,
):
    token = register_and_login(
        client,
        "Status Owner",
        "status-owner@example.com",
    )

    create_response = client.post(
        "/api/tickets/",
        json={
            "subject": "Status Only Ticket",
            "description": "The original description.",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]

    ticket = (
        db_session.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    assert ticket is not None

    ticket.priority = "high"
    ticket.category = "Billing"
    ticket.ai_summary = "Customer needs billing help."
    ticket.ai_status = "completed"
    ticket.ai_error = None

    db_session.commit()

    response = client.put(
        f"/api/tickets/{ticket_id}",
        json={
            "status": "resolved",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "resolved"
    assert data["priority"] == "high"
    assert data["subject"] == "Status Only Ticket"
    assert data["description"] == "The original description."
    assert data["category"] == "Billing"
    assert data["ai_summary"] == "Customer needs billing help."
    assert data["ai_status"] == "completed"
    assert data["ai_error"] is None


def test_successful_ticket_analysis_job_marks_completed(
    client,
    db_session,
    monkeypatch,
):
    token = register_and_login(
        client,
        "AI Success User",
        "ai-success@example.com",
    )

    create_response = client.post(
        "/api/tickets/",
        json={
            "subject": "Cannot log in",
            "description": "Password reset is not working.",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]

    monkeypatch.setattr(
        "app.jobs.ticket_jobs.SessionLocal",
        lambda: db_session,
    )
    monkeypatch.setattr(
        "app.jobs.ticket_jobs.analyze_ticket",
        lambda subject, description: SimpleNamespace(
            priority=Priority.high,
            category="Account Access",
            summary="Customer cannot reset their password.",
        ),
    )

    analyze_ticket_job(ticket_id)

    response = client.get(
        f"/api/tickets/{ticket_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["priority"] == "high"
    assert data["category"] == "Account Access"
    assert data["ai_summary"] == "Customer cannot reset their password."
    assert data["ai_status"] == "completed"
    assert data["ai_error"] is None


def test_failed_ticket_analysis_job_marks_failed(
    client,
    db_session,
    monkeypatch,
):
    token = register_and_login(
        client,
        "AI Failure User",
        "ai-failure@example.com",
    )

    create_response = client.post(
        "/api/tickets/",
        json={
            "subject": "Billing error",
            "description": "Invoice total looks wrong.",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]

    monkeypatch.setattr(
        "app.jobs.ticket_jobs.SessionLocal",
        lambda: db_session,
    )

    def fail_analysis(subject, description):
        raise RuntimeError("Gemini provider exploded")

    monkeypatch.setattr(
        "app.jobs.ticket_jobs.analyze_ticket",
        fail_analysis,
    )

    with pytest.raises(RuntimeError):
        analyze_ticket_job(ticket_id)

    response = client.get(
        f"/api/tickets/{ticket_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ai_status"] == "failed"
    assert data["ai_error"] == "Ticket AI analysis failed."
    assert data["category"] is None
    assert data["ai_summary"] is None


def test_invalid_ticket_status_is_rejected(client):
    token = register_and_login(
        client,
        "Invalid Status User",
        "invalid-status@example.com",
    )

    create_response = client.post(
        "/api/tickets/",
        json={
            "subject": "Invalid Status Ticket",
            "description": "Try to set an invalid status.",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]

    response = client.put(
        f"/api/tickets/{ticket_id}",
        json={
            "status": "closed",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


def test_user_cannot_delete_another_users_ticket(client):
    user1_token = register_and_login(
        client,
        "Delete Owner",
        "delete-owner@example.com",
    )

    user2_token = register_and_login(
        client,
        "Delete Other",
        "delete-other@example.com",
    )

    create_response = client.post(
        "/api/tickets/",
        json={
            "subject": "Do Not Delete",
            "description": "Owned by User 1.",
        },
        headers={
            "Authorization": f"Bearer {user1_token}"
        },
    )

    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]

    response = client.delete(
        f"/api/tickets/{ticket_id}",
        headers={
            "Authorization": f"Bearer {user2_token}"
        },
    )

    assert response.status_code == 404
