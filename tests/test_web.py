"""Tests for the web UI."""

import pytest
from fastapi.testclient import TestClient

from chatter.web.app import create_web_app


@pytest.fixture
def client():
    app = create_web_app()
    with TestClient(app) as c:
        yield c


def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Chatter" in response.text
    assert "Dashboard" in response.text


def test_memory_page_loads(client):
    response = client.get("/memory")
    assert response.status_code == 200
    assert "Memory" in response.text


def test_soul_page_loads(client):
    response = client.get("/soul")
    assert response.status_code == 200
    assert "Soul" in response.text


def test_tools_page_loads(client):
    response = client.get("/tools")
    assert response.status_code == 200
    assert "Tools" in response.text


def test_conversations_page_loads(client):
    response = client.get("/conversations")
    assert response.status_code == 200
    assert "Conversations" in response.text


def test_settings_page_loads(client):
    response = client.get("/settings")
    assert response.status_code == 200
    assert "Settings" in response.text
