# api/exceptions.py
"""
Custom exceptions for the ticketing API.
"""
from fastapi import HTTPException
from typing import Optional


class TicketNotFoundError(HTTPException):
    """Raised when a ticket is not found."""
    def __init__(self, ticket_id: str):
        super().__init__(
            status_code=404,
            detail=f"Ticket with ID '{ticket_id}' not found. Please check the ticket ID and try again."
        )


class InvalidStatusError(HTTPException):
    """Raised when an invalid status is provided."""
    def __init__(self, status: str, valid_statuses: list):
        valid_status_str = ", ".join(valid_statuses)
        super().__init__(
            status_code=422,
            detail=f"Invalid status '{status}'. Valid statuses are: {valid_status_str}"
        )


class ValidationError(HTTPException):
    """Raised for validation errors."""
    def __init__(self, message: str):
        super().__init__(
            status_code=422,
            detail=message
        )


class SimulatedServerError(HTTPException):
    """Raised to simulate server errors."""
    def __init__(self, error_type: int = 500):
        if error_type == 500:
            detail = "Internal Server Error - Simulated failure"
        elif error_type == 503:
            detail = "Service Unavailable - Simulated failure"
        else:
            detail = "Server Error - Simulated failure"
            
        super().__init__(status_code=error_type, detail=detail)