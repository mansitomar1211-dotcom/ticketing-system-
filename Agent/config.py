# agent/config.py
"""
Agent-specific configuration and constants.
"""
from typing import Dict, Any, List

# System prompt for the conversational agent
SYSTEM_PROMPT = """You are a helpful ticketing system assistant. You can help users manage support tickets through a ticketing API.

You have access to the following tools:
- create_ticket: Create new support tickets
- get_tickets: Retrieve all tickets or filter by status (OPEN, RESOLVED, CLOSED)
- get_ticket_by_id: Get details for a specific ticket
- update_ticket: Update ticket details including status, resolution, etc.
- delete_ticket: Delete a ticket

Important guidelines:
1. Always be helpful and provide clear, actionable responses
2. When API calls fail with server errors (5xx), the tools automatically retry - inform the user if retries are happening
3. For business logic errors (4xx), explain the error clearly and provide guidance on valid options
4. Valid ticket statuses are: OPEN, RESOLVED, CLOSED
5. When updating a ticket to RESOLVED status, a resolution note should be provided
6. Always confirm successful operations and provide relevant details
7. If a ticket ID doesn't exist, clearly state this and suggest checking the ID

Be conversational and helpful while being precise about technical details."""

# Function definitions for the LLM
FUNCTION_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create a new support ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short title for the ticket"
                    },
                    "description": {
                        "type": "string", 
                        "description": "Detailed description of the issue"
                    },
                    "comments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of initial comments"
                    }
                },
                "required": ["title", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tickets",
            "description": "Retrieve tickets, optionally filtered by status",
            "parameters": {
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "enum": ["OPEN", "RESOLVED", "CLOSED"],
                        "description": "Filter tickets by status"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket_by_id",
            "description": "Retrieve a specific ticket by its ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ticket ID to retrieve"
                    }
                },
                "required": ["ticket_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_ticket",
            "description": "Update an existing ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ticket ID to update"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title for the ticket"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description for the ticket"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["OPEN", "RESOLVED", "CLOSED"],
                        "description": "New status for the ticket"
                    },
                    "resolution": {
                        "type": "string",
                        "description": "Resolution notes (recommended when status is RESOLVED)"
                    },
                    "comments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New comments list"
                    }
                },
                "required": ["ticket_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_ticket",
            "description": "Delete a ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ticket ID to delete"
                    }
                },
                "required": ["ticket_id"]
            }
        }
    }
]

# Test scenarios for validation
TEST_SCENARIOS = [
    "Create a new ticket about a keyboard not working.",
    "Retrieve all open tickets.",
    "Get details for ticket ticket-001.",
    "Update ticket ticket-001 to have the status 'PROGRESS'.",
    "Update ticket ticket-001 to be RESOLVED, adding 'Replaced faulty cable' as the resolution.",
    "Update ticket non-existent-id to 'CLOSED'."
]