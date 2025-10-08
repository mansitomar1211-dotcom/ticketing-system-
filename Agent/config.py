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
- create_ticket_with_recommendations: Create tickets with AI recommendations and similar ticket analysis
- get_recommendations: Get AI recommendations without creating tickets
- get_trending_issues: Get trending issues and common problems
- search_similar_tickets: Find tickets similar to described issues

Important guidelines:
1. Always be helpful and provide clear, actionable responses
2. When API calls fail with server errors (5xx), the tools automatically retry
3. For business logic errors (4xx), explain the error clearly and provide guidance
4. Valid ticket statuses are: OPEN, RESOLVED, CLOSED
5. When updating a ticket to RESOLVED status, a resolution note should be provided
6. Always confirm successful operations and provide relevant details
7. Use recommendation features to help users find solutions before creating tickets

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
            "name": "create_ticket_with_recommendations",
            "description": "Create a new support ticket with AI recommendations for similar issues and solutions",
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
                    },
                    "get_recommendations": {
                        "type": "boolean",
                        "description": "Whether to get AI recommendations (default: true)",
                        "default": True
                    }
                },
                "required": ["title", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommendations",
            "description": "Get AI recommendations for a ticket without creating it - shows similar tickets and suggested solutions",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the potential ticket or issue summary"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the issue to get recommendations for"
                    },
                    "max_similar": {
                        "type": "integer",
                        "description": "Maximum number of similar tickets to return (1-10)",
                        "default": 5
                    },
                    "max_solutions": {
                        "type": "integer", 
                        "description": "Maximum number of solutions to suggest (1-5)",
                        "default": 3
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
            "description": "Retrieve tickets, optionally filtered by status, category, or priority",
            "parameters": {
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "enum": ["OPEN", "RESOLVED", "CLOSED"],
                        "description": "Filter tickets by status"
                    },
                    "category_filter": {
                        "type": "string",
                        "enum": ["HARDWARE", "SOFTWARE", "NETWORK", "ACCESS", "PERFORMANCE", "OTHER"],
                        "description": "Filter tickets by category"
                    },
                    "priority_filter": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                        "description": "Filter tickets by priority"
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
                    },
                    "category": {
                        "type": "string",
                        "enum": ["HARDWARE", "SOFTWARE", "NETWORK", "ACCESS", "PERFORMANCE", "OTHER"],
                        "description": "New category for the ticket"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                        "description": "New priority for the ticket"
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending_issues",
            "description": "Get trending issues and common problems from recent tickets",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (1-30)",
                        "default": 7
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_similar_tickets",
            "description": "Search for tickets similar to a given issue description",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title or summary of the issue to search for"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue to find similar tickets for"
                    }
                },
                "required": ["title", "description"]
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
    "Update ticket non-existent-id to 'CLOSED'.",
    # New AI-powered scenarios
    "Create a ticket about printer issues and show me similar problems.",
    "What are common solutions for network connectivity problems?",
    "What are the trending issues this week?",
    "Find tickets similar to login authentication problems."
]
