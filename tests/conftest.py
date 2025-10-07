"""
Pytest configuration and shared fixtures.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import create_app
from api.database import ticket_db
from agent.tools import APIClient, TicketingTools
from agent.conversational_agent import TicketingAgent


@pytest.fixture
def api_app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def api_client(api_app):
    """Create a test client for the API."""
    return TestClient(api_app)


@pytest.fixture
def clean_database():
    """Ensure clean database state for each test."""
    ticket_db.clear()
    ticket_db.initialize_sample_data()
    yield
    ticket_db.clear()


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    return Mock(spec=APIClient)


@pytest.fixture
def ticketing_tools(mock_api_client):
    """Create TicketingTools instance with mocked API client."""
    return TicketingTools(mock_api_client)


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    mock_client = Mock()
    mock_client.test_connection.return_value = True
    return mock_client


@pytest.fixture
def no_network_simulation():
    """Disable network simulation for faster tests."""
    with patch('api.middleware.NetworkSimulationMiddleware.dispatch', 
               side_effect=lambda self, request, call_next: call_next(request)):
        yield


@pytest.fixture
def sample_ticket_data():
    """Sample ticket data for testing."""
    return {
        "title": "Test Ticket",
        "description": "This is a test ticket description",
        "comments": ["Initial comment", "Follow-up comment"]
    }


@pytest.fixture
def sample_ticket_response():
    """Sample ticket response data."""
    return {
        "id": "ticket-12345",
        "title": "Test Ticket",
        "description": "This is a test ticket description",
        "status": "OPEN",
        "created": "2023-01-01T10:00:00",
        "updated": None,
        "resolution": None,
        "comments": ["Initial comment", "Follow-up comment"]
    }