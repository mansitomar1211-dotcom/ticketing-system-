# agent/tools.py
"""
Tools for interacting with the ticketing API.
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import agent_settings

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0


class APIClientError(Exception):
    """Custom exception for API client errors."""
    pass


class APIClient:
    """HTTP client for interacting with the ticketing API."""
    
    def __init__(self, base_url: str, retry_config: Optional[RetryConfig] = None):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            retry_config: Retry configuration
        """
        self.base_url = base_url.rstrip('/')
        self.retry_config = retry_config or RetryConfig(
            max_retries=agent_settings.max_retries,
            base_delay=agent_settings.base_delay,
            backoff_factor=agent_settings.backoff_factor
        )
        
        # Configure session with connection pooling
        self.session = requests.Session()
        
        # Set up retry strategy for connection errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"Initialized API client for {self.base_url}")
    
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with exponential backoff retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object
            
        Raises:
            APIClientError: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                response = self.session.request(method, url, **kwargs)
                
                # If we get a 5xx error, retry
                if response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code} on attempt {attempt + 1}")
                    
                    if attempt == self.retry_config.max_retries - 1:
                        logger.error(f"All retries exhausted for {method} {url}")
                        return response  # Return the error response on final attempt
                    
                    delay = self.retry_config.base_delay * (self.retry_config.backoff_factor ** attempt)
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                
                logger.debug(f"Request successful: {response.status_code}")
                return response
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"Request exception on attempt {attempt + 1}: {e}")
                
                if attempt == self.retry_config.max_retries - 1:
                    logger.error(f"All retries exhausted due to exceptions")
                    break
                
                delay = self.retry_config.base_delay * (self.retry_config.backoff_factor ** attempt)
                logger.info(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)
        
        if last_exception:
            raise APIClientError(f"Request failed after {self.retry_config.max_retries} attempts: {last_exception}")
        
        # This shouldn't happen but just in case
        raise APIClientError(f"Request failed after {self.retry_config.max_retries} attempts")
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        return self._make_request_with_retry("GET", url, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make POST request."""
        url = f"{self.base_url}{endpoint}"
        return self._make_request_with_retry("POST", url, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Make PUT request."""
        url = f"{self.base_url}{endpoint}"
        return self._make_request_with_retry("PUT", url, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make DELETE request."""
        url = f"{self.base_url}{endpoint}"
        return self._make_request_with_retry("DELETE", url, **kwargs)


class TicketingTools:
    """Tools for performing ticketing operations via API."""
    
    def __init__(self, api_client: APIClient):
        """
        Initialize ticketing tools.
        
        Args:
            api_client: API client instance
        """
        self.api_client = api_client
        logger.info("Initialized ticketing tools")
    
    def _handle_response(self, response: requests.Response, operation: str) -> Dict[str, Any]:
        """
        Handle API response and return standardized result.
        
        Args:
            response: HTTP response object
            operation: Description of the operation
            
        Returns:
            Standardized result dictionary
        """
        try:
            if response.status_code >= 500:
                return {
                    "success": False,
                    "message": f"Server error during {operation}: {response.status_code}",
                    "status_code": response.status_code,
                    "retryable": True
                }
            
            if 200 <= response.status_code < 300:
                data = response.json()
                return {
                    "success": True,
                    "data": data,
                    "status_code": response.status_code
                }
            
            # 4xx errors
            try:
                error_data = response.json()
                error_message = error_data.get("detail", f"HTTP {response.status_code}")
            except:
                error_message = f"HTTP {response.status_code}"
            
            return {
                "success": False,
                "message": error_message,
                "status_code": response.status_code,
                "retryable": False
            }
            
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            return {
                "success": False,
                "message": f"Error processing response: {str(e)}",
                "retryable": False
            }
    
    def create_ticket(self, title: str, description: str, comments: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new support ticket.
        
        Args:
            title: Short title for the ticket
            description: Detailed description of the issue
            comments: Optional list of initial comments
            
        Returns:
            Dictionary containing ticket details or error information
        """
        try:
            payload = {
                "title": title,
                "description": description,
                "comments": comments or []
            }
            
            logger.info(f"Creating ticket: {title}")
            response = self.api_client.post(
                "/tickets",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            result = self._handle_response(response, "ticket creation")
            
            if result["success"]:
                ticket = result["data"]
                logger.info(f"Successfully created ticket: {ticket['id']}")
                return {
                    "success": True,
                    "message": f"Successfully created ticket '{ticket['id']}'",
                    "ticket": ticket
                }
            else:
                logger.warning(f"Failed to create ticket: {result['message']}")
                return {
                    "success": False,
                    "message": f"Failed to create ticket: {result['message']}",
                    "status_code": result.get("status_code")
                }
                
        except Exception as e:
            logger.error(f"Exception creating ticket: {e}")
            return {
                "success": False,
                "message": f"Error creating ticket: {str(e)}"
            }
    
    def get_tickets(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve tickets, optionally filtered by status.
        
        Args:
            status_filter: Filter by ticket status (OPEN, RESOLVED, CLOSED)
            
        Returns:
            Dictionary containing list of tickets or error information
        """
        try:
            params = {}
            if status_filter:
                params["status"] = status_filter.upper()
                logger.info(f"Retrieving tickets with status: {status_filter}")
            else:
                logger.info("Retrieving all tickets")
            
            response = self.api_client.get("/tickets", params=params)
            result = self._handle_response(response, "ticket retrieval")
            
            if result["success"]:
                tickets = result["data"]
                logger.info(f"Successfully retrieved {len(tickets)} tickets")
                return {
                    "success": True,
                    "message": f"Found {len(tickets)} tickets",
                    "tickets": tickets
                }
            else:
                logger.warning(f"Failed to retrieve tickets: {result['message']}")
                return {
                    "success": False,
                    "message": f"Failed to retrieve tickets: {result['message']}",
                    "status_code": result.get("status_code")
                }
                
        except Exception as e:
            logger.error(f"Exception retrieving tickets: {e}")
            return {
                "success": False,
                "message": f"Error retrieving tickets: {str(e)}"
            }
    
    def get_ticket_by_id(self, ticket_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific ticket by ID.
        
        Args:
            ticket_id: The ticket ID to retrieve
            
        Returns:
            Dictionary containing ticket details or error information
        """
        try:
            logger.info(f"Retrieving ticket: {ticket_id}")
            response = self.api_client.get(f"/tickets/{ticket_id}")
            result = self._handle_response(response, f"ticket {ticket_id} retrieval")
            
            if result["success"]:
                ticket = result["data"]
                logger.info(f"Successfully retrieved ticket: {ticket_id}")
                return {
                    "success": True,
                    "message": f"Retrieved ticket '{ticket_id}'",
                    "ticket": ticket
                }
            else:
                logger.warning(f"Failed to retrieve ticket {ticket_id}: {result['message']}")
                return {
                    "success": False,
                    "message": result["message"],
                    "status_code": result.get("status_code")
                }
                
        except Exception as e:
            logger.error(f"Exception retrieving ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Error retrieving ticket: {str(e)}"
            }
    
    def update_ticket(self, ticket_id: str, title: Optional[str] = None, 
                     description: Optional[str] = None, status: Optional[str] = None,
                     resolution: Optional[str] = None, comments: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update an existing ticket.
        
        Args:
            ticket_id: The ticket ID to update
            title: New title (optional)
            description: New description (optional)
            status: New status - must be OPEN, RESOLVED, or CLOSED (optional)
            resolution: Resolution notes (optional)
            comments: New comments list (optional)
            
        Returns:
            Dictionary containing updated ticket details or error information
        """
        try:
            payload = {}
            if title is not None:
                payload["title"] = title
            if description is not None:
                payload["description"] = description
            if status is not None:
                payload["status"] = status.upper()
            if resolution is not None:
                payload["resolution"] = resolution
            if comments is not None:
                payload["comments"] = comments
            
            logger.info(f"Updating ticket: {ticket_id}")
            response = self.api_client.put(
                f"/tickets/{ticket_id}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            result = self._handle_response(response, f"ticket {ticket_id} update")
            
            if result["success"]:
                ticket = result["data"]
                logger.info(f"Successfully updated ticket: {ticket_id}")
                return {
                    "success": True,
                    "message": f"Successfully updated ticket '{ticket_id}'",
                    "ticket": ticket
                }
            else:
                logger.warning(f"Failed to update ticket {ticket_id}: {result['message']}")
                return {
                    "success": False,
                    "message": result["message"],
                    "status_code": result.get("status_code")
                }
                
        except Exception as e:
            logger.error(f"Exception updating ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Error updating ticket: {str(e)}"
            }
    
    def delete_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """
        Delete a ticket.
        
        Args:
            ticket_id: The ticket ID to delete
            
        Returns:
            Dictionary containing success/error information
        """
        try:
            logger.info(f"Deleting ticket: {ticket_id}")
            response = self.api_client.delete(f"/tickets/{ticket_id}")
            result = self._handle_response(response, f"ticket {ticket_id} deletion")
            
            if result["success"]:
                logger.info(f"Successfully deleted ticket: {ticket_id}")
                return {
                    "success": True,
                    "message": f"Successfully deleted ticket '{ticket_id}'"
                }
            else:
                logger.warning(f"Failed to delete ticket {ticket_id}: {result['message']}")
                return {
                    "success": False,
                    "message": result["message"],
                    "status_code": result.get("status_code")
                }
                
        except Exception as e:
            logger.error(f"Exception deleting ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Error deleting ticket: {str(e)}"
            }