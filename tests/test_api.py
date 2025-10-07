"""
Tests for the API endpoints.
"""
import pytest
from unittest.mock import patch
import json

from api.models import TicketStatus


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_check(self, api_client, no_network_simulation):
        """Test that health check returns successful response."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestTicketEndpoints:
    """Test the ticket CRUD endpoints."""
    
    def test_get_all_tickets(self, api_client, clean_database, no_network_simulation):
        """Test retrieving all tickets."""
        response = api_client.get("/tickets")
        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 3  # We have 3 sample tickets
        assert all("id" in ticket for ticket in tickets)
        assert all("title" in ticket for ticket in tickets)
        assert all("status" in ticket for ticket in tickets)
    
    def test_get_tickets_filtered_by_status(self, api_client, clean_database, no_network_simulation):
        """Test retrieving tickets filtered by status."""
        response = api_client.get("/tickets?status=OPEN")
        assert response.status_code == 200
        tickets = response.json()
        for ticket in tickets:
            assert ticket["status"] == "OPEN"
    
    def test_get_tickets_filtered_by_resolved_status(self, api_client, clean_database, no_network_simulation):
        """Test retrieving resolved tickets."""
        response = api_client.get("/tickets?status=RESOLVED")
        assert response.status_code == 200
        tickets = response.json()
        for ticket in tickets:
            assert ticket["status"] == "RESOLVED"
    
    def test_get_tickets_filtered_by_closed_status(self, api_client, clean_database, no_network_simulation):
        """Test retrieving closed tickets."""
        response = api_client.get("/tickets?status=CLOSED")
        assert response.status_code == 200
        tickets = response.json()
        for ticket in tickets:
            assert ticket["status"] == "CLOSED"
    
    def test_get_ticket_by_id_success(self, api_client, clean_database, no_network_simulation):
        """Test retrieving a specific ticket by ID."""
        response = api_client.get("/tickets/ticket-001")
        assert response.status_code == 200
        ticket = response.json()
        assert ticket["id"] == "ticket-001"
        assert "title" in ticket
        assert "description" in ticket
        assert "status" in ticket
        assert "created" in ticket
    
    def test_get_ticket_by_id_not_found(self, api_client, clean_database, no_network_simulation):
        """Test retrieving a non-existent ticket."""
        response = api_client.get("/tickets/non-existent")
        assert response.status_code == 404
        error = response.json()
        assert "not found" in error["detail"].lower()
        assert "non-existent" in error["detail"]
    
    def test_create_ticket_success(self, api_client, clean_database, no_network_simulation, sample_ticket_data):
        """Test creating a new ticket."""
        response = api_client.post("/tickets", json=sample_ticket_data)
        assert response.status_code == 201
        ticket = response.json()
        assert ticket["title"] == sample_ticket_data["title"]
        assert ticket["description"] == sample_ticket_data["description"]
        assert ticket["status"] == "OPEN"
        assert ticket["comments"] == sample_ticket_data["comments"]
        assert "id" in ticket
        assert ticket["id"].startswith("ticket-")
        assert "created" in ticket
    
    def test_create_ticket_minimal_data(self, api_client, clean_database, no_network_simulation):
        """Test creating a ticket with minimal required data."""
        ticket_data = {
            "title": "Minimal Ticket",
            "description": "Just the basics"
        }
        response = api_client.post("/tickets", json=ticket_data)
        assert response.status_code == 201
        ticket = response.json()
        assert ticket["title"] == "Minimal Ticket"
        assert ticket["description"] == "Just the basics"
        assert ticket["comments"] == []
    
    def test_create_ticket_validation_empty_title(self, api_client, clean_database, no_network_simulation):
        """Test creating a ticket with empty title."""
        ticket_data = {
            "title": "",  # Empty title should fail validation
            "description": "This is a test ticket"
        }
        response = api_client.post("/tickets", json=ticket_data)
        assert response.status_code == 422
    
    def test_create_ticket_validation_missing_title(self, api_client, clean_database, no_network_simulation):
        """Test creating a ticket without title."""
        ticket_data = {
            "description": "This is a test ticket"
        }
        response = api_client.post("/tickets", json=ticket_data)
        assert response.status_code == 422
    
    def test_create_ticket_validation_empty_description(self, api_client, clean_database, no_network_simulation):
        """Test creating a ticket with empty description."""
        ticket_data = {
            "title": "Valid Title",
            "description": ""  # Empty description should fail
        }
        response = api_client.post("/tickets", json=ticket_data)
        assert response.status_code == 422
    
    def test_update_ticket_success(self, api_client, clean_database, no_network_simulation):
        """Test updating a ticket successfully."""
        update_data = {
            "status": "RESOLVED",
            "resolution": "Issue resolved successfully"
        }
        response = api_client.put("/tickets/ticket-001", json=update_data)
        assert response.status_code == 200
        ticket = response.json()
        assert ticket["status"] == "RESOLVED"
        assert ticket["resolution"] == "Issue resolved successfully"
        assert ticket["updated"] is not None
    
    def test_update_ticket_title_and_description(self, api_client, clean_database, no_network_simulation):
        """Test updating ticket title and description."""
        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }
        response = api_client.put("/tickets/ticket-001", json=update_data)
        assert response.status_code == 200
        ticket = response.json()
        assert ticket["title"] == "Updated Title"
        assert ticket["description"] == "Updated description"
    
    def test_update_ticket_comments(self, api_client, clean_database, no_network_simulation):
        """Test updating ticket comments."""
        update_data = {
            "comments": ["New comment 1", "New comment 2"]
        }
        response = api_client.put("/tickets/ticket-001", json=update_data)
        assert response.status_code == 200
        ticket = response.json()
        assert ticket["comments"] == ["New comment 1", "New comment 2"]
    
    def test_update_ticket_invalid_status(self, api_client, clean_database, no_network_simulation):
        """Test updating a ticket with invalid status."""
        update_data = {"status": "INVALID_STATUS"}
        response = api_client.put("/tickets/ticket-001", json=update_data)
        assert response.status_code == 422
        error = response.json()
        assert "Invalid status" in error["detail"]
        assert "OPEN, RESOLVED, CLOSED" in error["detail"]
        assert "INVALID_STATUS" in error["detail"]
    
    def test_update_ticket_not_found(self, api_client, clean_database, no_network_simulation):
        """Test updating a non-existent ticket."""
        update_data = {"status": "RESOLVED"}
        response = api_client.put("/tickets/non-existent", json=update_data)
        assert response.status_code == 404
        error = response.json()
        assert "not found" in error["detail"].lower()
    
    def test_update_resolved_status_requires_resolution(self, api_client, clean_database, no_network_simulation):
        """Test that setting status to RESOLVED requires a resolution."""
        update_data = {"status": "RESOLVED"}  # No resolution provided
        response = api_client.put("/tickets/ticket-001", json=update_data)
        assert response.status_code == 422
        error = response.json()
        assert "Resolution note is required" in error["detail"]
    
    def test_update_resolved_status_with_existing_resolution(self, api_client, clean_database, no_network_simulation):
        """Test updating to RESOLVED when resolution already exists."""
        # First, set a resolution
        update_data = {
            "status": "RESOLVED",
            "resolution": "Initial resolution"
        }
        response = api_client.put("/tickets/ticket-001", json=update_data)
        assert response.status_code == 200
        
        # Then update status without new resolution (should work)
        update_data = {"status": "CLOSED"}
        response = api_client.put("/tickets/ticket-001", json=update_data)
        assert response.status_code == 200
    
    def test_delete_ticket_success(self, api_client, clean_database, no_network_simulation):
        """Test deleting a ticket successfully."""
        response = api_client.delete("/tickets/ticket-001")
        assert response.status_code == 200
        data = response.json()
        assert "successfully deleted" in data["message"]
        assert "ticket-001" in data["message"]
        
        # Verify ticket is actually deleted
        get_response = api_client.get("/tickets/ticket-001")
        assert get_response.status_code == 404
    
    def test_delete_ticket_not_found(self, api_client, clean_database, no_network_simulation):
        """Test deleting a non-existent ticket."""
        response = api_client.delete("/tickets/non-existent")
        assert response.status_code == 404
        error = response.json()
        assert "not found" in error["detail"].lower()


class TestNetworkSimulation:
    """Test the network simulation middleware."""
    
    @patch('api.middleware.random.random')
    def test_simulated_server_error_500(self, mock_random, api_client, clean_database):
        """Test that simulated 500 server errors are returned."""
        # Force the random function to return a value that triggers server error
        mock_random.return_value = 0.1  # Less than 0.25, should trigger error
        
        with patch('api.middleware.random.choice', return_value=500):
            response = api_client.get("/tickets")
            assert response.status_code == 500
            assert "Simulated failure" in response.json()["detail"]
            assert "Internal Server Error" in response.json()["detail"]
    
    @patch('api.middleware.random.random')
    def test_simulated_server_error_503(self, mock_random, api_client, clean_database):
        """Test that simulated 503 server errors are returned."""
        mock_random.return_value = 0.1  # Less than 0.25, should trigger error
        
        with patch('api.middleware.random.choice', return_value=503):
            response = api_client.get("/tickets")
            assert response.status_code == 503
            assert "Simulated failure" in response.json()["detail"]
            assert "Service Unavailable" in response.json()["detail"]
    
    @patch('api.middleware.asyncio.sleep')
    def test_simulated_latency(self, mock_sleep, api_client, clean_database):
        """Test that latency simulation is applied."""
        with patch('api.middleware.random.uniform', return_value=1.5):
            with patch('api.middleware.random.random', return_value=0.9):  # No failure
                response = api_client.get("/tickets")
                assert response.status_code == 200
                mock_sleep.assert_called_once_with(1.5)
    
    def test_health_endpoint_bypasses_simulation(self, api_client):
        """Test that health endpoint bypasses network simulation."""
        with patch('api.middleware.random.random') as mock_random:
            response = api_client.get("/health")
            assert response.status_code == 200
            # random.random should not be called for health endpoint
            mock_random.assert_not_called()
    
    def test_docs_endpoint_bypasses_simulation(self, api_client):
        """Test that docs endpoint bypasses network simulation."""
        with patch('api.middleware.random.random') as mock_random:
            response = api_client.get("/docs")
            assert response.status_code == 200
            # random.random should not be called for docs endpoint
            mock_random.assert_not_called()


class TestTicketModel:
    """Test ticket model validation and behavior."""
    
    def test_ticket_status_enum_values(self):
        """Test that ticket status enum has correct values."""
        assert TicketStatus.OPEN == "OPEN"
        assert TicketStatus.RESOLVED == "RESOLVED"
        assert TicketStatus.CLOSED == "CLOSED"
        
        # Test that these are the only valid values
        valid_statuses = [status.value for status in TicketStatus]
        assert set(valid_statuses) == {"OPEN", "RESOLVED", "CLOSED"}
    
    def test_create_ticket_with_all_statuses(self, api_client, clean_database, no_network_simulation):
        """Test creating tickets and updating to all valid statuses."""
        # Create ticket
        ticket_data = {
            "title": "Status Test Ticket",
            "description": "Testing status transitions"
        }
        response = api_client.post("/tickets", json=ticket_data)
        assert response.status_code == 201
        ticket_id = response.json()["id"]
        
        # Test each status transition
        for status in ["RESOLVED", "CLOSED", "OPEN"]:
            update_data = {"status": status}
            if status == "RESOLVED":
                update_data["resolution"] = "Test resolution"
            
            response = api_client.put(f"/tickets/{ticket_id}", json=update_data)
            assert response.status_code == 200
            assert response.json()["status"] == status