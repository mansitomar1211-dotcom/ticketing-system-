
"""Conversational AI agent for ticketing system interactions."""
import json
import logging
from typing import List, Dict, Any, Optional

from .llm_client import AzureOpenAIClient, LLMClientError
from .tools import TicketingTools, APIClient
from .config import SYSTEM_PROMPT, FUNCTION_DEFINITIONS

# Set up logging
logger = logging.getLogger(__name__)


class ConversationalAgentError(Exception):
    """Custom exception for conversational agent errors."""
    pass


class TicketingAgent:
    """LLM-powered conversational agent for ticketing operations."""
    
    def __init__(self, api_base_url: str):
        """
        Initialize the ticketing agent.
        
        Args:
            api_base_url: Base URL for the ticketing API
        """
        try:
            self.llm_client = AzureOpenAIClient()
            self.api_client = APIClient(api_base_url)
            self.ticketing_tools = TicketingTools(self.api_client)
            self.conversation_history: List[Dict[str, Any]] = []
            
            self.system_message = {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
            
            logger.info(f"Initialized ticketing agent with API: {api_base_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ticketing agent: {e}")
            raise ConversationalAgentError(f"Failed to initialize agent: {e}")
    
    def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the requested function and return results.
        
        Args:
            function_name: Name of the function to execute
            arguments: Function arguments
            
        Returns:
            Function execution result
        """
        try:
            logger.info(f"Executing function: {function_name} with args: {arguments}")
            
            if function_name == "create_ticket":
                return self.ticketing_tools.create_ticket(**arguments)
            elif function_name == "create_ticket_with_recommendations":
                return self.ticketing_tools.create_ticket_with_recommendations(**arguments)
            elif function_name == "get_recommendations":
                return self.ticketing_tools.get_recommendations(**arguments)
            elif function_name == "get_tickets":
                return self.ticketing_tools.get_tickets(**arguments)
            elif function_name == "get_ticket_by_id":
                return self.ticketing_tools.get_ticket_by_id(**arguments)
            elif function_name == "update_ticket":
                return self.ticketing_tools.update_ticket(**arguments)
            elif function_name == "delete_ticket":
                return self.ticketing_tools.delete_ticket(**arguments)
            elif function_name == "get_trending_issues":
                return self.ticketing_tools.get_trending_issues(**arguments)
            elif function_name == "search_similar_tickets":
                return self.ticketing_tools.search_similar_tickets(**arguments)
            else:
                logger.error(f"Unknown function: {function_name}")
                return {
                    "success": False,
                    "message": f"Unknown function: {function_name}"
                }
                
        except Exception as e:
            logger.error(f"Error executing {function_name}: {e}")
            return {
                "success": False,
                "message": f"Error executing {function_name}: {str(e)}"
            }
    
    def chat(self, user_message: str) -> str:
        """
        Process user message and return response.
        
        Args:
            user_message: User's input message
            
        Returns:
            Agent's response
        """
        try:
            logger.info(f"Processing user message: {user_message[:100]}...")
            
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Prepare messages for LLM
            messages = [self.system_message] + self.conversation_history
            
            # Get LLM response with function calling
            llm_response = self.llm_client.chat_completion(
                messages=messages,
                tools=FUNCTION_DEFINITIONS
            )
            
            if not llm_response["success"]:
                error_msg = f"LLM Error: {llm_response['error']}"
                logger.error(error_msg)
                self.conversation_history.append({
                    "role": "assistant",
                    "content": error_msg
                })
                return error_msg
            
            response = llm_response["response"]
            message = response.choices[0].message
            
            # Check if LLM wants to call functions
            if message.tool_calls:
                logger.info(f"LLM requested {len(message.tool_calls)} function calls")
                
                # Add the assistant's message with tool calls to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in message.tool_calls
                    ]
                })
                
                # Execute function calls
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in function arguments: {e}")
                        function_args = {}
                    
                    logger.info(f"Calling {function_name} with args: {function_args}")
                    
                    # Execute the function
                    result = self._execute_function(function_name, function_args)
                    
                    # Add function result to conversation
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # Get final response from LLM after function execution
                messages = [self.system_message] + self.conversation_history
                final_response = self.llm_client.chat_completion(messages=messages)
                
                if final_response["success"]:
                    final_message = final_response["response"].choices[0].message.content
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": final_message
                    })
                    logger.info("Successfully completed conversation turn with function calls")
                    return final_message
                else:
                    error_msg = f"Error getting final response: {final_response['error']}"
                    logger.error(error_msg)
                    self.conversation_history.append({
                        "role": "assistant", 
                        "content": error_msg
                    })
                    return error_msg
            else:
                # No function calls, just return the message
                response_content = message.content
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_content
                })
                logger.info("Successfully completed conversation turn without function calls")
                return response_content
                
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        logger.info("Resetting conversation history")
        self.conversation_history = []
    
    def get_conversation_summary(self) -> str:
        """
        Get a summary of the current conversation.
        
        Returns:
            Formatted conversation summary
        """
        if not self.conversation_history:
            return "No conversation history."
        
        summary = f"Conversation with {len(self.conversation_history)} exchanges:\\n"
        
        # Show last 6 messages
        recent_messages = self.conversation_history[-6:]
        for i, msg in enumerate(recent_messages, 1):
            role = msg["role"].title()
            content = msg.get("content", "")
            
            if content:
                preview = content[:100] + "..." if len(content) > 100 else content
                summary += f"{i}. {role}: {preview}\\n"
            elif msg.get("tool_calls"):
                # Show function calls
                tool_names = [tc["function"]["name"] for tc in msg["tool_calls"]]
                summary += f"{i}. {role}: Called functions: {', '.join(tool_names)}\\n"
        
        return summary
    
    def test_connection(self) -> bool:
        """
        Test connections to both LLM and API services.
        
        Returns:
            True if both connections are working
        """
        try:
            # Test LLM connection
            llm_ok = self.llm_client.test_connection()
            
            # Test API connection
            try:
                import requests
                response = requests.get(f"{self.api_client.base_url}/health", timeout=5)
                api_ok = response.status_code == 200
            except Exception as e:
                logger.error(f"API connection test failed: {e}")
                api_ok = False
            
            logger.info(f"Connection test - LLM: {'OK' if llm_ok else 'FAILED'}, API: {'OK' if api_ok else 'FAILED'}")
            return llm_ok and api_ok
            
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return False


# # Write the complete file
# with open('agent/conversational_agent.py', 'w') as f:
#     f.write(conversational_agent_complete)

# print("✅ Complete conversational_agent.py file created")
