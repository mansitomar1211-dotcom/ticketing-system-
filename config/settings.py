# config/settings.py
"""
Application configuration settings.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """API configuration settings."""
    
    title: str = "Mock Ticketing API"
    description: str = "A mock API for testing ticket management systems"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Simulation settings
    min_latency: float = 0.25
    max_latency: float = 2.0
    failure_rate: float = 0.25
    
    class Config:
        env_file = ".env"
        env_prefix = "API_"


class LLMSettings(BaseSettings):
    """LLM configuration settings."""
    
    azure_endpoint: str = "https://candidate-take-home.openai.azure.com/"
    api_key: str = ""
    api_version: str = "2024-12-01-preview"
    model: str = "gpt-4o"
    temperature: float = 0.1
    
    class Config:
        env_file = ".env"
        env_prefix = "LLM_"


class AgentSettings(BaseSettings):
    """Agent configuration settings."""
    
    api_base_url: str = "http://localhost:8000"
    max_retries: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0
    
    class Config:
        env_file = ".env"
        env_prefix = "AGENT_"


# Global settings instances
api_settings = APISettings()
llm_settings = LLMSettings()
agent_settings = AgentSettings()