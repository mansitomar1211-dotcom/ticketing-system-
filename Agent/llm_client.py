# agent/llm_client.py
"""
Azure OpenAI client for LLM interactions.
"""
import logging
from typing import List, Dict, Any, Optional

import openai
from openai.types.chat import ChatCompletion

from config.settings import llm_settings

# Set up logging
logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Custom exception for LLM client errors."""
    pass


class AzureOpenAIClient:
    """Client for Azure OpenAI API interactions."""
    
    def __init__(self):
        """Initialize the Azure OpenAI client."""
        try:
            self.client = openai.AzureOpenAI(
                azure_endpoint=llm_settings.azure_endpoint,
                api_key=llm_settings.api_key,
                api_version=llm_settings.api_version
            )
            self.model = llm_settings.model
            self.temperature = llm_settings.temperature
            logger.info(f"Initialized Azure OpenAI client with model: {self.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise LLMClientError(f"Failed to initialize LLM client: {e}")
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None, 
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate chat completion with optional tool calling.
        
        Args:
            messages: List of message dictionaries
            tools: Optional list of available tools
            tool_choice: Tool choice strategy ("auto", "none", or specific tool)
            
        Returns:
            Dictionary containing success status and response or error
        """
        try:
            logger.debug(f"Making chat completion request with {len(messages)} messages")
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice
            
            response = self.client.chat.completions.create(**kwargs)
            
            logger.debug("Chat completion successful")
            return {
                "success": True,
                "response": response
            }
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                "success": False,
                "error": f"API Error: {e}"
            }
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            return {
                "success": False,
                "error": f"Connection Error: {e}"
            }
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {e}")
            return {
                "success": False,
                "error": f"Rate Limit Error: {e}"
            }
        except Exception as e:
            logger.error(f"Unexpected error in chat completion: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {e}"
            }
    
    def test_connection(self) -> bool:
        """
        Test the connection to the Azure OpenAI service.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            test_messages = [{"role": "user", "content": "Hello"}]
            result = self.chat_completion(test_messages)
            return result["success"]
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False