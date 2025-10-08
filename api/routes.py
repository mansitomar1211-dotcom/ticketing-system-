# api/routes.py
"""
API route definitions.
"""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse

from .database import ticket_db
from .exception import TicketNotFoundError, InvalidStatusError, ValidationError
from .models import (
    Ticket, 
    TicketCreate, 
    TicketUpdate, 
    TicketStatus,
    SuccessResponse,
    ErrorResponse
)

router = APIRouter()


@router.get("/tickets", response_model=List[Ticket], summary="Get all tickets")
async def get_tickets(
    status: Optional[TicketStatus] = Query(None, description="Filter by ticket status")
) -> List[Ticket]:
    """
    Retrieve all tickets, optionally filtered by status.
    
    - **status**: Optional status filter (OPEN, RESOLVED, CLOSED)
    """
    return ticket_db.get_all_tickets(status_filter=status)


@router.get("/tickets/{ticket_id}", response_model=Ticket, summary="Get ticket by ID")
async def get_ticket(ticket_id: str) -> Ticket:
    """
    Retrieve a specific ticket by ID.
    
    - **ticket_id**: The unique identifier of the ticket
    """
    ticket = ticket_db.get_ticket_by_id(ticket_id)
    if not ticket:
        raise TicketNotFoundError(ticket_id)
    
    return ticket


@router.post("/tickets", response_model=Ticket, status_code=201, summary="Create a new ticket")
async def create_ticket(ticket_data: TicketCreate) -> Ticket:
    """
    Create a new support ticket.
    
    - **title**: Short descriptive title (1-200 characters)
    - **description**: Detailed description of the issue (1-1000 characters)  
    - **comments**: Optional list of initial comments
    """
    ticket_id = f"ticket-{uuid4().hex[:8]}"
    
    new_ticket = Ticket(
        id=ticket_id,
        title=ticket_data.title,
        description=ticket_data.description,
        comments=ticket_data.comments or [],
        created=datetime.now(),
        status=TicketStatus.OPEN
    )
    
    return ticket_db.create_ticket(new_ticket)


@router.put("/tickets/{ticket_id}", response_model=Ticket, summary="Update a ticket")
async def update_ticket(ticket_id: str, ticket_update: TicketUpdate) -> Ticket:
    """
    Update an existing ticket.
    
    - **ticket_id**: The unique identifier of the ticket
    - **title**: New title (optional)
    - **description**: New description (optional)
    - **status**: New status - OPEN, RESOLVED, or CLOSED (optional)
    - **resolution**: Resolution notes (required when status is RESOLVED)
    - **comments**: New comments list (optional)
    """
    existing_ticket = ticket_db.get_ticket_by_id(ticket_id)
    if not existing_ticket:
        raise TicketNotFoundError(ticket_id)
    
    # Validate status if provided
    if ticket_update.status:
        try:
            TicketStatus(ticket_update.status)
        except ValueError:
            valid_statuses = [status.value for status in TicketStatus]
            raise InvalidStatusError(ticket_update.status, valid_statuses)
        
        # Check resolution requirement for RESOLVED status
        if (ticket_update.status == TicketStatus.RESOLVED and 
            not ticket_update.resolution and 
            not existing_ticket.resolution):
            raise ValidationError(
                "Resolution note is required when setting ticket status to 'RESOLVED'. Please provide a resolution."
            )
    
    # Apply updates
    update_data = ticket_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_ticket, field, value)
    
    existing_ticket.updated = datetime.now()
    
    updated_ticket = ticket_db.update_ticket(ticket_id, existing_ticket)
    return updated_ticket


@router.delete("/tickets/{ticket_id}", response_model=SuccessResponse, summary="Delete a ticket")
async def delete_ticket(ticket_id: str) -> SuccessResponse:
    """
    Delete a ticket permanently.
    
    - **ticket_id**: The unique identifier of the ticket to delete
    """
    if not ticket_db.ticket_exists(ticket_id):
        raise TicketNotFoundError(ticket_id)
    
    success = ticket_db.delete_ticket(ticket_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete ticket")
    
    return SuccessResponse(message=f"Ticket '{ticket_id}' has been successfully deleted")


@router.get("/health", summary="Health check")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
