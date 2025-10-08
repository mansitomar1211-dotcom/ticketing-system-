# api/database.py
"""
In-memory database for storing tickets.
"""
import threading
from datetime import datetime
from typing import Dict, List, Optional

from .models import Ticket, TicketStatus


class TicketDatabase:
    """Thread-safe in-memory ticket database."""
    
    def __init__(self):
        self._tickets: Dict[str, Ticket] = {}
        self._lock = threading.RLock()
    
    def initialize_sample_data(self) -> None:
        """Initialize database with sample tickets."""
        sample_tickets = [
            {
                "id": "ticket-001",
                "title": "Login issues",
                "description": "Cannot log into the system",
                "created": datetime.now(),
                "status": TicketStatus.OPEN,
                "resolution": None,
                "comments": ["User reported issue at 9 AM"]
            },
            {
                "id": "ticket-002", 
                "title": "Printer not working",
                "description": "Office printer is not responding",
                "created": datetime.now(),
                "status": TicketStatus.RESOLVED,
                "resolution": "Replaced toner cartridge",
                "comments": ["Checked printer status", "Toner was empty"]
            },
            {
                "id": "ticket-003",
                "title": "Software installation request",
                "description": "Need Adobe Photoshop installed",
                "created": datetime.now(),
                "status": TicketStatus.CLOSED,
                "resolution": "Software installed and configured",
                "comments": ["Approved by manager", "Installation completed"]
            }
        ]
        
        with self._lock:
            for ticket_data in sample_tickets:
                ticket = Ticket(**ticket_data)
                self._tickets[ticket.id] = ticket
    
    def get_all_tickets(self, status_filter: Optional[TicketStatus] = None) -> List[Ticket]:
        """Get all tickets, optionally filtered by status."""
        with self._lock:
            tickets = list(self._tickets.values())
            
            if status_filter:
                tickets = [t for t in tickets if t.status == status_filter]
                
            return sorted(tickets, key=lambda x: x.created, reverse=True)
    
    def get_ticket_by_id(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by ID."""
        with self._lock:
            return self._tickets.get(ticket_id)
    
    def create_ticket(self, ticket: Ticket) -> Ticket:
        """Create a new ticket."""
        with self._lock:
            self._tickets[ticket.id] = ticket
            return ticket
    
    def update_ticket(self, ticket_id: str, ticket: Ticket) -> Optional[Ticket]:
        """Update an existing ticket."""
        with self._lock:
            if ticket_id in self._tickets:
                ticket.updated = datetime.now()
                self._tickets[ticket_id] = ticket
                return ticket
            return None
    
    def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket."""
        with self._lock:
            if ticket_id in self._tickets:
                del self._tickets[ticket_id]
                return True
            return False
    
    def ticket_exists(self, ticket_id: str) -> bool:
        """Check if a ticket exists."""
        with self._lock:
            return ticket_id in self._tickets
    
    def clear(self) -> None:
        """Clear all tickets (for testing)."""
        with self._lock:
            self._tickets.clear()


# Global database instance
ticket_db = TicketDatabase()