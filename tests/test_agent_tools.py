# tests/test_agent_tools.py (continued)
"""
Tests for the agent tools and API client.
"""
import pytest
from unittest.mock import Mock, patch
import requests
import time

from agent.tools import APIClient, TicketingTools, RetryConfig, APIClientError


class TestRetryConfig:
    """Test the retry configuration."""
    
    def test_default_values(self):
        """Test that retry config has proper defaults."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.backoff_factor == 2.0
    
    def test_custom_values(self):
        """Test custom retry configuration values."""
        config = RetryConfig(max_retries=5, base_delay=0.5, backoff_factor=1.5)
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.backoff_factor == 1.5


class TestAPIClient:
    """Test the API client functionality."""
    
    @patch('requests.Session.request')
    @patch('time.sleep')
    def test_retry_mechanism_success_after_failure(self, mock_sleep, mock_request):
        """Test that retry mechanism works for server errors."""
        client = APIClient("http://test.com", RetryConfig(max_retries=2, base_delay=0.1))
        
        # First call fails with 500, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True}
        
        mock_request.side_effect = [mock_response_fail, mock_response_success]
        
        result = client.get("/tickets")
        
        assert result.status_code == 200
        assert mock_request.call_count == 2
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(0.1)  # base_delay
    
    @patch('requests.Session.request')
    @patch('time.sleep')
    def test_retry_exhausted_returns_error(self, mock_sleep, mock_request):
        """Test that after all retries are exhausted, the error is returned."""
        client = APIClient("http://test.com", RetryConfig(max_retries=2, base_delay=0.1))
        
        # All calls fail with 500
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        
        mock_request.return_value = mock_response_fail
        
        result = client.get("/tickets")
        
        assert result.status_code == 500
        assert mock_request.call_count == 2
        assert mock_sleep.call_count == 1  # Only sleep between retries
    
    @patch('requests.Session.request')
    def test_no_retry_for_4xx_errors(self, mock_request):
        """Test that 4xx errors are not retried."""
        client = APIClient("http://test.com", RetryConfig(max_retries=3))
        
        mock_response_404 = Mock()
        mock_response_404.status_code = 404
        mock_request.return_value = mock_response_404
        
        result = client.get("/tickets/non-existent")
        
        assert result.status_code == 404
        assert mock_request.call_count == 1  # No retries
    
    @patch('requests.Session.request')
    @patch('time.sleep')
    def test_exponential_backoff(self, mock_sleep, mock_request):
        """Test that exponential backoff is applied correctly."""
        client = APIClient("http://test.com", RetryConfig(max_retries=3, base_delay=1.0, backoff_factor=2.0))
        
        # All calls fail with 500
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_request.return_value = mock_response_fail
        
        result = client.get("/tickets")
        
        assert result.status_code == 500
        assert mock_request.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between attempts
        
        # Check exponential backoff delays: 1.0, 2.0
        sleep_calls = mock_sleep.call_args_list
        assert sleep_calls[0][0][0] == 1.0  # First retry delay
        assert sleep_calls[1][0][0] == 2.0  # Second retry delay
    
    @patch('requests.Session.request')
    @patch('time.sleep')
    def test_request_exception_retry(self, mock_sleep, mock_request):
        """Test retry behavior for request exceptions."""
        client = APIClient("http://test.com", RetryConfig(max_retries=2, base_delay=0.1))
        
        # First call raises exception, second succeeds
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        
        mock_request.side_effect = [requests.exceptions.ConnectionError("Connection failed"), mock_response_success]
        
        result = client.get("/tickets")
        
        assert result.status_code == 200
        assert mock_request.call_count == 2
        assert mock_sleep.call_count == 1
    
    @patch('requests.Session.request')
    def test_request_exception_exhausted(self, mock_request):
        """Test that APIClientError is raised when all retries fail with exceptions."""
        client = APIClient("http://test.com", RetryConfig(max_retries=2))
        
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(APIClientError) as exc_info:
            client.get("/tickets")
        
        assert "Connection failed" in str(exc_info.value)
        assert mock_request.call_count == 2
    
    def test_url_construction(self):
        """Test proper URL construction."""
        client = APIClient("http://test.com/")  # With trailing slash
        assert client.base_url == "http://test.com"
        
        client = APIClient("http://test.com")  # Without trailing slash
        assert client.base_url == "http://test.com"


class TestTicketingTools:
    """Test the ticketing tools functionality."""
    
    def test_create_ticket_success(self, ticketing_tools, mock_api_client, sample_ticket_response):
        """Test successful ticket creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = sample_ticket_response
        
        mock_api_client.post.return_value = mock_response
        
        result = ticketing_tools.create_ticket("Test Ticket", "Test Description", ["Initial comment"])
        
        assert result["success"] is True
        assert "ticket-12345" in result["message"]
        assert result["ticket"]["id"] == "ticket-12345"
        assert result["ticket"]["title"] == "Test Ticket"
        
        # Verify API call
        mock_api_client.post.assert_called_once_with(
            "/tickets",
            json={
                "title": "Test Ticket",
                "description": "Test Description",
                "comments": ["Initial comment"]
            },
            headers={"Content-Type": "application/json"}
        )
    
    def test_create_ticket_validation_error(self, ticketing_tools, mock_api_client):
        """Test ticket creation with validation error."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {"detail": "Title cannot be empty"}
        
        mock_api_client.post.return_value = mock_response
        
        result = ticketing_tools.create_ticket("", "Test Description")
        
        assert result["success"] is False
        assert "Title cannot be empty" in result["message"]
        assert result["status_code"] == 422
    
    def test_create_ticket_server_error(self, ticketing_tools, mock_api_client):
        """Test ticket creation with server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        
        mock_api_client.post.return_value = mock_response
        
        result = ticketing_tools.create_ticket("Test", "Description")
        
        assert result["success"] is False
        assert "Server error during ticket creation" in result["message"]
        assert result["status_code"] == 500
    
    def test_get_tickets_success(self, ticketing_tools, mock_api_client):
        """Test successful ticket retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "ticket-1", "title": "Ticket 1", "status": "OPEN"},
            {"id": "ticket-2", "title": "Ticket 2", "status": "RESOLVED"}
        ]
        
        mock_api_client.get.return_value = mock_response
        
        result = ticketing_tools.get_tickets()
        
        assert result["success"] is True
        assert len(result["tickets"]) == 2
        assert "Found 2 tickets" in result["message"]
        
        mock_api_client.get.assert_called_once_with("/tickets", params={})
    
    def test_get_tickets_filtered(self, ticketing_tools, mock_api_client):
        """Test filtered ticket retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "ticket-1", "title": "Ticket 1", "status": "OPEN"}
        ]
        
        mock_api_client.get.return_value = mock_response
        
        result = ticketing_tools.get_tickets(status_filter="OPEN")
        
        assert result["success"] is True
        assert len(result["tickets"]) == 1
        
        mock_api_client.get.assert_called_once_with("/tickets", params={"status": "OPEN"})
    
    def test_get_ticket_by_id_success(self, ticketing_tools, mock_api_client):
        """Test successful ticket retrieval by ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket-123",
            "title": "Test Ticket",
            "status": "OPEN"
        }
        
        mock_api_client.get.return_value = mock_response
        
        result = ticketing_tools.get_ticket_by_id("ticket-123")
        
        assert result["success"] is True
        assert result["ticket"]["id"] == "ticket-123"
        assert "Retrieved ticket 'ticket-123'" in result["message"]
        
        mock_api_client.get.assert_called_once_with("/tickets/ticket-123")
    
    def test_get_ticket_by_id_not_found(self, ticketing_tools, mock_api_client):
        """Test getting a non-existent ticket."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Ticket not found"}
        
        mock_api_client.get.return_value = mock_response
        
        result = ticketing_tools.get_ticket_by_id("non-existent")
        
        assert result["success"] is False
        assert result["status_code"] == 404
        assert "Ticket not found" in result["message"]
    
    def test_update_ticket_success(self, ticketing_tools, mock_api_client):
        """Test successful ticket update."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket-123",
            "title": "Updated Ticket",
            "status": "RESOLVED",
            "resolution": "Fixed the issue"
        }
        
        mock_api_client.put.return_value = mock_response
        
        result = ticketing_tools.update_ticket(
            "ticket-123",
            title="Updated Ticket",
            status="RESOLVED",
            resolution="Fixed the issue"
        )
        
        assert result["success"] is True
        assert result["ticket"]["id"] == "ticket-123"
        assert result["ticket"]["status"] == "RESOLVED"
        assert "Successfully updated ticket 'ticket-123'" in result["message"]
        
        # Verify API call
        mock_api_client.put.assert_called_once_with(
            "/tickets/ticket-123",
            json={
                "title": "Updated Ticket",
                "status": "RESOLVED",
                "resolution": "Fixed the issue"
            },
            headers={"Content-Type": "application/json"}
        )
    
    def test_update_ticket_invalid_status(self, ticketing_tools, mock_api_client):
        """Test updating ticket with invalid status."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "detail": "Invalid status 'PROGRESS'. Valid statuses are: OPEN, RESOLVED, CLOSED"
        }
        
        mock_api_client.put.return_value = mock_response
        
        result = ticketing_tools.update_ticket("ticket-1", status="PROGRESS")
        
        assert result["success"] is False
        assert result["status_code"] == 422
        assert "Invalid status" in result["message"]
        assert "Valid statuses are" in result["message"]
    
    def test_update_ticket_not_found(self, ticketing_tools, mock_api_client):
        """Test updating a non-existent ticket."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Ticket not found"}
        
        mock_api_client.put.return_value = mock_response
        
        result = ticketing_tools.update_ticket("non-existent", status="RESOLVED")
        
        assert result["success"] is False
        assert result["status_code"] == 404
        assert "Ticket not found" in result["message"]
    
    def test_update_ticket_partial_update(self, ticketing_tools, mock_api_client):
        """Test partial ticket update with only some fields."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ticket-123",
            "title": "Original Title",
            "status": "RESOLVED",
            "resolution": "Issue fixed"
        }
        
        mock_api_client.put.return_value = mock_response
        
        result = ticketing_tools.update_ticket("ticket-123", status="RESOLVED", resolution="Issue fixed")
        
        assert result["success"] is True
        
        # Verify only specified fields were included in the request
        expected_payload = {
            "status": "RESOLVED",
            "resolution": "Issue fixed"
        }
        mock_api_client.put.assert_called_once_with(
            "/tickets/ticket-123",
            json=expected_payload,
            headers={"Content-Type": "application/json"}
        )
    
    def test_delete_ticket_success(self, ticketing_tools, mock_api_client):
        """Test successful ticket deletion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Ticket deleted successfully"}
        
        mock_api_client.delete.return_value = mock_response
        
        result = ticketing_tools.delete_ticket("ticket-123")
        
        assert result["success"] is True
        assert "Successfully deleted ticket 'ticket-123'" in result["message"]
        
        mock_api_client.delete.assert_called_once_with("/tickets/ticket-123")
    
    def test_delete_ticket_not_found(self, ticketing_tools, mock_api_client):
        """Test deleting a non-existent ticket."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Ticket not found"}
        
        mock_api_client.delete.return_value = mock_response
        
        result = ticketing_tools.delete_ticket("non-existent")
        
        assert result["success"] is False
        assert result["status_code"] == 404
        assert "Ticket not found" in result["message"]
    
    def test_server_error_handling(self, ticketing_tools, mock_api_client):
        """Test handling of server errors (5xx)."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        
        mock_api_client.get.return_value = mock_response
        
        result = ticketing_tools.get_tickets()
        
        assert result["success"] is False
        assert result["status_code"] == 500
        assert "Server error during ticket retrieval" in result["message"]
    
    def test_exception_handling(self, ticketing_tools, mock_api_client):
        """Test handling of unexpected exceptions."""
        mock_api_client.get.side_effect = Exception("Unexpected error")
        
        result = ticketing_tools.get_tickets()
        
        assert result["success"] is False
        assert "Error retrieving tickets: Unexpected error" in result["message"]
    
    def test_json_decode_error_handling(self, ticketing_tools, mock_api_client):
        """Test handling of JSON decode errors."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        mock_api_client.post.return_value = mock_response
        
        result = ticketing_tools.create_ticket("Test", "Description")
        
        assert result["success"] is False
        assert result["status_code"] == 422
        assert "HTTP 422" in result["message"]
    
    def test_status_code_upper_case_conversion(self, ticketing_tools, mock_api_client):
        """Test that status values are converted to uppercase."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "ticket-123", "status": "RESOLVED"}
        
        mock_api_client.put.return_value = mock_response
        
        # Pass lowercase status
        result = ticketing_tools.update_ticket("ticket-123", status="resolved")
        
        assert result["success"] is True
        
        # Verify uppercase conversion in API call
        mock_api_client.put.assert_called_once_with(
            "/tickets/ticket-123",
            json={"status": "RESOLVED"},  # Should be uppercase
            headers={"Content-Type": "application/json"}
        )
    
    def test_comments_handling(self, ticketing_tools, mock_api_client):
        """Test proper handling of comments in create and update operations."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "ticket-123",
            "title": "Test",
            "description": "Description",
            "status": "OPEN",
            "comments": ["Comment 1", "Comment 2"]
        }
        
        mock_api_client.post.return_value = mock_response
        
        # Test create with comments
        result = ticketing_tools.create_ticket("Test", "Description", ["Comment 1", "Comment 2"])
        
        assert result["success"] is True
        assert result["ticket"]["comments"] == ["Comment 1", "Comment 2"]
        
        # Verify API call includes comments
        mock_api_client.post.assert_called_once_with(
            "/tickets",
            json={
                "title": "Test",
                "description": "Description",
                "comments": ["Comment 1", "Comment 2"]
            },
            headers={"Content-Type": "application/json"}
        )
    
    def test_empty_comments_handling(self, ticketing_tools, mock_api_client):
        """Test handling of empty or None comments."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "ticket-123",
            "title": "Test",
            "description": "Description",
            "status": "OPEN",
            "comments": []
        }
        
        mock_api_client.post.return_value = mock_response
        
        # Test create without comments
        result = ticketing_tools.create_ticket("Test", "Description")
        
        assert result["success"] is True
        
        # Verify API call includes empty comments list
        mock_api_client.post.assert_called_once_with(
            "/tickets",
            json={
                "title": "Test",
                "description": "Description",
                "comments": []
            },
            headers={"Content-Type": "application/json"}
        )
    
    def test_handle_response_success(self, ticketing_tools):
        """Test _handle_response method with successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        result = ticketing_tools._handle_response(mock_response, "test operation")
        
        assert result["success"] is True
        assert result["data"] == {"data": "test"}
        assert result["status_code"] == 200
    
    def test_handle_response_server_error(self, ticketing_tools):
        """Test _handle_response method with server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        
        result = ticketing_tools._handle_response(mock_response, "test operation")
        
        assert result["success"] is False
        assert "Server error during test operation" in result["message"]
        assert result["status_code"] == 500
        assert result["retryable"] is True
    
    def test_handle_response_client_error(self, ticketing_tools):
        """Test _handle_response method with client error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        
        result = ticketing_tools._handle_response(mock_response, "test operation")
        
        assert result["success"] is False
        assert result["message"] == "Not found"
        assert result["status_code"] == 404
        assert result["retryable"] is False
    
    def test_handle_response_json_error(self, ticketing_tools):
        """Test _handle_response method when JSON parsing fails."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        result = ticketing_tools._handle_response(mock_response, "test operation")
        
        assert result["success"] is False
        assert result["message"] == "HTTP 400"
        assert result["status_code"] == 400
    
    def test_multiple_http_methods(self, mock_api_client):
        """Test that all HTTP methods are properly called."""
        client = APIClient("http://test.com")
        client.session = mock_api_client
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_api_client.request.return_value = mock_response
        
        # Test all methods
        client.get("/test")
        mock_api_client.request.assert_called_with("GET", "http://test.com/test")
        
        client.post("/test", json={"data": "test"})
        mock_api_client.request.assert_called_with("POST", "http://test.com/test", json={"data": "test"})
        
        client.put("/test", json={"data": "updated"})
        mock_api_client.request.assert_called_with("PUT", "http://test.com/test", json={"data": "updated"})
        
        client.delete("/test")
        mock_api_client.request.assert_called_with("DELETE", "http://test.com/test")