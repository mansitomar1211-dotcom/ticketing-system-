# tests/test_integration.py (continued)
"""
Integration tests for the complete ticketing system.
"""
import pytest
from unittest.mock import Mock, patch
import json
import threading
import time

from agent.conversational_agent import TicketingAgent, ConversationalAgentError
from agent.tools import APIClient
from api.main import create_app
from fastapi.testclient import TestClient


class TestAgentIntegration:
    """Test agent integration with mocked LLM."""
    
    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response for function calling."""
        mock_response = Mock()
        mock_message = Mock()
        
        # Mock tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "get_tickets"
        mock_tool_call.function.arguments = '{"status_filter": "OPEN"}'
        
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        
        mock_response.choices = [Mock(message=mock_message)]
        
        return {
            "success": True,
            "response": mock_response
        }
    
    @pytest.fixture
    def mock_final_response(self):
        """Mock final LLM response after function execution."""
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "I found 2 open tickets for you."
        mock_message.tool_calls = None
        
        mock_response.choices = [Mock(message=mock_message)]
        
        return {
            "success": True,
            "response": mock_response
        }
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_agent_initialization_success(self, mock_llm_client_class):
        """Test successful agent initialization."""
        mock_llm_instance = Mock()
        mock_llm_instance.test_connection.return_value = True
        mock_llm_client_class.return_value = mock_llm_instance
        
        agent = TicketingAgent("http://test-api:8000")
        
        assert agent is not None
        assert agent.llm_client == mock_llm_instance
        assert agent.api_client.base_url == "http://test-api:8000"
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_agent_initialization_failure(self, mock_llm_client_class):
        """Test agent initialization failure."""
        mock_llm_client_class.side_effect = Exception("LLM initialization failed")
        
        with pytest.raises(ConversationalAgentError) as exc_info:
            TicketingAgent("http://test-api:8000")
        
        assert "Failed to initialize agent" in str(exc_info.value)
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_function_execution_flow(self, mock_llm_client_class, mock_llm_response, mock_final_response):
        """Test complete function execution flow."""
        # Setup mock LLM client
        mock_llm_instance = Mock()
        mock_llm_instance.test_connection.return_value = True
        mock_llm_instance.chat_completion.side_effect = [mock_llm_response, mock_final_response]
        mock_llm_client_class.return_value = mock_llm_instance
        
        # Setup mock API client
        with patch('agent.tools.APIClient') as mock_api_client_class:
            mock_api_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"id": "ticket-1", "title": "Issue 1", "status": "OPEN"},
                {"id": "ticket-2", "title": "Issue 2", "status": "OPEN"}
            ]
            mock_api_instance.get.return_value = mock_response
            mock_api_client_class.return_value = mock_api_instance
            
            agent = TicketingAgent("http://test-api:8000")
            
            # Test chat with function calling
            response = agent.chat("Show me all open tickets")
            
            assert response == "I found 2 open tickets for you."
            assert len(agent.conversation_history) == 4  # User, assistant with tool calls, tool result, final assistant
            
            # Verify API was called correctly
            mock_api_instance.get.assert_called_once_with("/tickets", params={"status": "OPEN"})
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_error_handling_in_function_execution(self, mock_llm_client_class):
        """Test error handling when function execution fails."""
        mock_llm_instance = Mock()
        mock_llm_instance.test_connection.return_value = True
        
        # Mock LLM response with tool call
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "get_tickets"
        mock_tool_call.function.arguments = '{"invalid": "json"}'  # This will cause JSON decode error
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        mock_response.choices = [Mock(message=mock_message)]
        
        # Mock final response
        final_response = Mock()
        final_message = Mock()
        final_message.content = "I encountered an error while retrieving tickets."
        final_message.tool_calls = None
        final_response.choices = [Mock(message=final_message)]
        
        mock_llm_instance.chat_completion.side_effect = [
            {"success": True, "response": mock_response},
            {"success": True, "response": final_response}
        ]
        mock_llm_client_class.return_value = mock_llm_instance
        
        agent = TicketingAgent("http://test-api:8000")
        
        response = agent.chat("Show me all tickets")
        
        assert "I encountered an error while retrieving tickets." in response
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_conversation_history_management(self, mock_llm_client_class):
        """Test conversation history management."""
        mock_llm_instance = Mock()
        mock_llm_instance.test_connection.return_value = True
        
        # Mock simple response without tool calls
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Hello! How can I help you with tickets today?"
        mock_message.tool_calls = None
        mock_response.choices = [Mock(message=mock_message)]
        
        mock_llm_instance.chat_completion.return_value = {"success": True, "response": mock_response}
        mock_llm_client_class.return_value = mock_llm_instance
        
        agent = TicketingAgent("http://test-api:8000")
        
        # Test conversation
        response1 = agent.chat("Hello")
        assert len(agent.conversation_history) == 2  # User + Assistant
        
        response2 = agent.chat("How are you?")
        assert len(agent.conversation_history) == 4  # 2 more messages
        
        # Test reset
        agent.reset_conversation()
        assert len(agent.conversation_history) == 0
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_conversation_summary(self, mock_llm_client_class):
        """Test conversation summary generation."""
        mock_llm_instance = Mock()
        mock_llm_instance.test_connection.return_value = True
        mock_llm_client_class.return_value = mock_llm_instance
        
        agent = TicketingAgent("http://test-api:8000")
        
        # Empty conversation
        summary = agent.get_conversation_summary()
        assert "No conversation history" in summary
        
        # Add some conversation
        agent.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there! How can I help you?"},
            {"role": "user", "content": "Show me tickets"},
            {"role": "assistant", "content": "Here are your tickets..."}
        ]
        
        summary = agent.get_conversation_summary()
        assert "Conversation with 4 exchanges" in summary
        assert "User: Hello" in summary
        assert "Assistant: Hi there!" in summary
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_llm_error_handling(self, mock_llm_client_class):
        """Test handling of LLM errors."""
        mock_llm_instance = Mock()
        mock_llm_instance.test_connection.return_value = True
        mock_llm_instance.chat_completion.return_value = {
            "success": False,
            "error": "Rate limit exceeded"
        }
        mock_llm_client_class.return_value = mock_llm_instance
        
        agent = TicketingAgent("http://test-api:8000")
        
        response = agent.chat("Hello")
        
        assert "LLM Error: Rate limit exceeded" in response
        assert len(agent.conversation_history) == 2  # User message + error response
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_connection_test(self, mock_llm_client_class):
        """Test agent connection testing."""
        mock_llm_instance = Mock()
        mock_llm_instance.test_connection.return_value = True
        mock_llm_client_class.return_value = mock_llm_instance
        
        with patch('agent.tools.APIClient') as mock_api_client_class:
            mock_api_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_api_instance.get.return_value = mock_response
            mock_api_client_class.return_value = mock_api_instance
            
            agent = TicketingAgent("http://test-api:8000")
            
            # Test successful connection
            assert agent.test_connection() is True
            
            # Test failed API connection
            mock_api_instance.get.side_effect = Exception("Connection failed")
            assert agent.test_connection() is False


class TestEndToEndIntegration:
    """End-to-end integration tests with real API."""
    
    @pytest.fixture
    def test_api_client(self):
        """Create a test client for the API."""
        app = create_app()
        return TestClient(app)
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_real_api_integration(self, mock_llm_client_class, clean_database, no_network_simulation):
        """Test agent with real API backend."""
        # Mock LLM client
        mock_llm_instance = Mock()
        mock_llm_instance.test_connection.return_value = True
        
        # Mock create ticket function call
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        mock_tool_call.id = "call_create"
        mock_tool_call.function.name = "create_ticket"
        mock_tool_call.function.arguments = '{"title": "Test Issue", "description": "Something is broken"}'
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        mock_response.choices = [Mock(message=mock_message)]
        
        # Mock final response
        final_response = Mock()
        final_message = Mock()
        final_message.content = "I've successfully created a new ticket for you."
        final_message.tool_calls = None
        final_response.choices = [Mock(message=final_message)]
        
        mock_llm_instance.chat_completion.side_effect = [
            {"success": True, "response": mock_response},
            {"success": True, "response": final_response}
        ]
        mock_llm_client_class.return_value = mock_llm_instance
        
        # Use real API client (but mocked LLM)
        agent = TicketingAgent("http://localhost:8000")
        
        # This would normally make real API calls, but we're testing the integration
        response = agent.chat("Create a ticket about a broken keyboard")
        
        assert "successfully created" in response.lower()
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_api_retry_integration(self, mock_llm_client_class):
        """Test that agent properly retries API calls during failures."""
        mock_llm_instance = Mock()
        mock_llm_instance.test_connection.return_value = True
        
        # Mock get tickets function call
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        mock_tool_call.id = "call_get"
        mock_tool_call.function.name = "get_tickets"
        mock_tool_call.function.arguments = '{}'
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        mock_response.choices = [Mock(message=mock_message)]
        
        # Mock final response
        final_response = Mock()
        final_message = Mock()
        final_message.content = "I successfully retrieved the tickets after retrying."
        final_message.tool_calls = None
        final_response.choices = [Mock(message=final_message)]
        
        mock_llm_instance.chat_completion.side_effect = [
            {"success": True, "response": mock_response},
            {"success": True, "response": final_response}
        ]
        mock_llm_client_class.return_value = mock_llm_instance
        
        # Mock API client with retry behavior
        with patch('agent.tools.APIClient') as mock_api_client_class:
            mock_api_instance = Mock()
            
            # First call fails, second succeeds
            fail_response = Mock()
            fail_response.status_code = 500
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = [{"id": "ticket-1", "title": "Test"}]
            
            mock_api_instance.get.side_effect = [fail_response, success_response]
            mock_api_client_class.return_value = mock_api_instance
            
            agent = TicketingAgent("http://test-api:8000")
            
            response = agent.chat("Show me all tickets")
            
            assert "successfully retrieved" in response.lower()
            # Verify retry happened
            assert mock_api_instance.get.call_count == 2


class TestScenarioValidation:
    """Test the specific scenarios mentioned in the requirements."""
    
    @pytest.fixture
    def mock_agent_with_responses(self):
        """Create a mock agent that responds to specific scenarios."""
        with patch('agent.conversational_agent.AzureOpenAIClient') as mock_llm_class:
            mock_llm_instance = Mock()
            mock_llm_instance.test_connection.return_value = True
            mock_llm_class.return_value = mock_llm_instance
            
            with patch('agent.tools.APIClient') as mock_api_class:
                mock_api_instance = Mock()
                mock_api_class.return_value = mock_api_instance
                
                agent = TicketingAgent("http://test-api:8000")
                agent.llm_client = mock_llm_instance
                agent.api_client = mock_api_instance
                
                return agent, mock_llm_instance, mock_api_instance
    
    def test_create_keyboard_ticket_scenario(self, mock_agent_with_responses):
        """Test: 'Create a new ticket about a keyboard not working.'"""
        agent, mock_llm, mock_api = mock_agent_with_responses
        
        # Mock function call response
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        mock_tool_call.id = "call_create"
        mock_tool_call.function.name = "create_ticket"
        mock_tool_call.function.arguments = '{"title": "Keyboard not working", "description": "Keyboard is not responding"}'
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        mock_response.choices = [Mock(message=mock_message)]
        
        # Mock API response
        api_response = Mock()
        api_response.status_code = 201
        api_response.json.return_value = {
            "id": "ticket-kb001",
            "title": "Keyboard not working",
            "description": "Keyboard is not responding",
            "status": "OPEN"
        }
        mock_api.post.return_value = api_response
        
        # Mock final LLM response
        final_response = Mock()
        final_message = Mock()
        final_message.content = "I've created ticket ticket-kb001 for the keyboard issue."
        final_message.tool_calls = None
        final_response.choices = [Mock(message=final_message)]
        
        mock_llm.chat_completion.side_effect = [
            {"success": True, "response": mock_response},
            {"success": True, "response": final_response}
        ]
        
        response = agent.chat("Create a new ticket about a keyboard not working.")
        
        assert "ticket-kb001" in response
        assert "keyboard" in response.lower()
        mock_api.post.assert_called_once()
    
    def test_get_open_tickets_scenario(self, mock_agent_with_responses):
        """Test: 'Retrieve all open tickets.'"""
        agent, mock_llm, mock_api = mock_agent_with_responses
        
        # Mock function call response
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        mock_tool_call.id = "call_get"
        mock_tool_call.function.name = "get_tickets"
        mock_tool_call.function.arguments = '{"status_filter": "OPEN"}'
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        mock_response.choices = [Mock(message=mock_message)]
        
        # Mock API response
        api_response = Mock()
        api_response.status_code = 200
        api_response.json.return_value = [
            {"id": "ticket-1", "title": "Issue 1", "status": "OPEN"},
            {"id": "ticket-2", "title": "Issue 2", "status": "OPEN"}
        ]
        mock_api.get.return_value = api_response
        
        # Mock final LLM response
        final_response = Mock()
        final_message = Mock()
        final_message.content = "I found 2 open tickets for you."
        final_message.tool_calls = None
        final_response.choices = [Mock(message=final_message)]
        
        mock_llm.chat_completion.side_effect = [
            {"success": True, "response": mock_response},
            {"success": True, "response": final_response}
        ]
        
        response = agent.chat("Retrieve all open tickets.")
        
        assert "2 open tickets" in response
        mock_api.get.assert_called_once_with("/tickets", params={"status": "OPEN"})
    
    def test_invalid_status_scenario(self, mock_agent_with_responses):
        """Test: 'Update ticket [id] to have the status PROGRESS' (should explain invalid status)."""
        agent, mock_llm, mock_api = mock_agent_with_responses
        
        # Mock function call response
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        mock_tool_call.id = "call_update"
        mock_tool_call.function.name = "update_ticket"
        mock_tool_call.function.arguments = '{"ticket_id": "ticket-001", "status": "PROGRESS"}'
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        mock_response.choices = [Mock(message=mock_message)]
        
        # Mock API error response
        api_response = Mock()
        api_response.status_code = 422
        api_response.json.return_value = {
            "detail": "Invalid status 'PROGRESS'. Valid statuses are: OPEN, RESOLVED, CLOSED"
        }
        mock_api.put.return_value = api_response
        
        # Mock final LLM response
        final_response = Mock()
        final_message = Mock()
        final_message.content = "I'm sorry, but 'PROGRESS' is not a valid status. Valid statuses are: OPEN, RESOLVED, CLOSED."
        final_message.tool_calls = None
        final_response.choices = [Mock(message=final_message)]
        
        mock_llm.chat_completion.side_effect = [
            {"success": True, "response": mock_response},
            {"success": True, "response": final_response}
        ]
        
        response = agent.chat("Update ticket ticket-001 to have the status 'PROGRESS'.")
        
        assert "not a valid status" in response.lower()
        assert "OPEN, RESOLVED, CLOSED" in response
        mock_api.put.assert_called_once()
    
    def test_ticket_not_found_scenario(self, mock_agent_with_responses):
        """Test: 'Update ticket [non-existent-id] to CLOSED' (should report not found)."""
        agent, mock_llm, mock_api = mock_agent_with_responses
        
        # Mock function call response
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        mock_tool_call.id = "call_update"
        mock_tool_call.function.name = "update_ticket"
        mock_tool_call.function.arguments = '{"ticket_id": "non-existent-id", "status": "CLOSED"}'
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        mock_response.choices = [Mock(message=mock_message)]
        
        # Mock API 404 response
        api_response = Mock()
        api_response.status_code = 404
        api_response.json.return_value = {
            "detail": "Ticket with ID 'non-existent-id' not found. Please check the ticket ID and try again."
        }
        mock_api.put.return_value = api_response
        
        # Mock final LLM response
        final_response = Mock()
        final_message = Mock()
        final_message.content = "I couldn't find a ticket with ID 'non-existent-id'. Please check the ticket ID and try again."
        final_message.tool_calls = None
        final_response.choices = [Mock(message=final_message)]
        
        mock_llm.chat_completion.side_effect = [
            {"success": True, "response": mock_response},
            {"success": True, "response": final_response}
        ]
        
        response = agent.chat("Update ticket non-existent-id to 'CLOSED'.")
        
        assert "couldn't find" in response.lower() or "not found" in response.lower()
        assert "non-existent-id" in response
        mock_api.put.assert_called_once()
    
    def test_resolve_with_resolution_scenario(self, mock_agent_with_responses):
        """Test: 'Update ticket [id] to be RESOLVED, adding resolution'."""
        agent, mock_llm, mock_api = mock_agent_with_responses
        
        # Mock function call response
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        mock_tool_call.id = "call_update"
        mock_tool_call.function.name = "update_ticket"
        mock_tool_call.function.arguments = '{"ticket_id": "ticket-001", "status": "RESOLVED", "resolution": "Replaced faulty cable"}'
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        mock_response.choices = [Mock(message=mock_message)]
        
        # Mock API success response
        api_response = Mock()
        api_response.status_code = 200
        api_response.json.return_value = {
            "id": "ticket-001",
            "status": "RESOLVED",
            "resolution": "Replaced faulty cable"
        }
        mock_api.put.return_value = api_response
        
        # Mock final LLM response
        final_response = Mock()
        final_message = Mock()
        final_message.content = "I've successfully updated ticket-001 to RESOLVED status with the resolution 'Replaced faulty cable'."
        final_message.tool_calls = None
        final_response.choices = [Mock(message=final_message)]
        
        mock_llm.chat_completion.side_effect = [
            {"success": True, "response": mock_response},
            {"success": True, "response": final_response}
        ]
        
        response = agent.chat("Update ticket ticket-001 to be RESOLVED, adding 'Replaced faulty cable' as the resolution.")
        
        assert "successfully updated" in response.lower()
        assert "RESOLVED" in response
        assert "Replaced faulty cable" in response
        mock_api.put.assert_called_once()


class TestConcurrencyAndThreadSafety:
    """Test thread safety and concurrent access."""
    
    @patch('agent.conversational_agent.AzureOpenAIClient')
    def test_multiple_agents_concurrent_access(self, mock_llm_client_class):
        """Test multiple agent instances accessing API concurrently."""
        mock_llm_instance = Mock()
        mock_llm_instance.test_connection.return_value = True
        mock_llm_client_class.return_value = mock_llm_instance
        
        def create_and_test_agent(agent_id):
            agent = TicketingAgent(f"http://test-api-{agent_id}:8000")
            return agent.api_client.base_url
        
        # Create multiple agents concurrently
        import threading
        results = []
        threads = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda i=i: results.append(create_and_test_agent(i)))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all agents were created with correct URLs
        assert len(results) == 5
        for i, url in enumerate(results):
            assert f"test-api-{i}" in url
    
    def test_database_thread_safety(self, clean_database):
        """Test that the in-memory database is thread-safe."""
        from api.database import ticket_db
        
        def create_tickets(thread_id, count):
            for i in range(count):
                from api.models import Ticket, TicketStatus
                from datetime import datetime
                
                ticket = Ticket(
                    id=f"thread-{thread_id}-ticket-{i}",
                    title=f"Thread {thread_id} Ticket {i}",
                    description=f"Created by thread {thread_id}",
                    created=datetime.now(),
                    status=TicketStatus.OPEN
                )
                ticket_db.create_ticket(ticket)
        
        # Create tickets from multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=create_tickets, args=(thread_id, 5))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all tickets were created
        all_tickets = ticket_db.get_all_tickets()
        thread_tickets = [t for t in all_tickets if t.id.startswith("thread-")]
        assert len(thread_tickets) == 15  # 3 threads * 5 tickets each