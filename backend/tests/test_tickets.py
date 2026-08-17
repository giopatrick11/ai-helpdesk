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