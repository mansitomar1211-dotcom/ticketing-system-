# api/models.py
"""
Pydantic models for the ticketing API.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class TicketStatus(str, Enum):
    """Valid ticket status values."""
    OPEN = "OPEN"  
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketBase(BaseModel):
    """Base ticket model with common fields."""
    title: str = Field(..., min_length=1, max_length=200, description="Ticket title")
    description: str = Field(..., min_length=1, max_length=1000, description="Ticket description")
    comments: Optional[List[str]] = Field(default_factory=list, description="List of comments")


class TicketCreate(TicketBase):
    """Model for creating a new ticket."""
    pass


class TicketUpdate(BaseModel):
    """Model for updating an existing ticket."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    status: Optional[TicketStatus] = None
    resolution: Optional[str] = Field(None, max_length=500)
    comments: Optional[List[str]] = None
    
    @validator('resolution')
    def validate_resolution(cls, v, values):
        """Validate resolution field based on status."""
        status = values.get('status')
        if status == TicketStatus.RESOLVED and not v:
            raise ValueError("Resolution is required when status is RESOLVED")
        return v


class Ticket(TicketBase):
    """Complete ticket model."""
    id: str = Field(..., description="Unique ticket identifier")
    created: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")
    status: TicketStatus = Field(default=TicketStatus.OPEN, description="Current ticket status")
    resolution: Optional[str] = Field(None, max_length=500, description="Resolution notes")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponse(BaseModel):
    """Standard success response model."""
    message: str = Field(..., description="Success message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }