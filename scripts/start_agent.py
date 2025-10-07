#!/usr/bin/env python3
"""
Script to start the conversational agent CLI.
"""
import sys
import os
import argparse
import requests
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import agent_settings
from agent.cli import TicketingCLI


def check_api_health(api_url: str, max_retries: int = 5, delay: float = 2.0) -> bool:
    """
    Check if the API is healthy and accessible.
    
    Args:
        api_url: Base URL of the API
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        True if API is healthy, False otherwise
    """
    health_url = f"{api_url.rstrip('/')}/health"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_retries - 1:
            print(f"⏳ API not ready, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
    
    return False


def main():
    """Start the conversational agent."""
    parser = argparse.ArgumentParser(
        description="Start the Ticketing System AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Connect to default API (localhost:8000)
  %(prog)s --api-url http://api:8080 # Connect to custom API URL
  %(prog)s --no-health-check         # Skip API health check
  %(prog)s --debug                   # Enable debug logging
        """
    )
    
    parser.add_argument(
        "--api-url",
        default=agent_settings.api_base_url,
        help=f"Base URL for the ticketing API (default: {agent_settings.api_base_url})"
    )
    
    parser.add_argument(
        "--no-health-check",
        action="store_true",
        help="Skip API health check on startup"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=agent_settings.max_retries,
        help=f"Maximum API retry attempts (default: {agent_settings.max_retries})"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        print("🐛 Debug logging enabled")
    
    print("🤖 Starting Ticketing System AI Assistant...")
    print(f"🌐 API URL: {args.api_url}")
    
    # Check API health unless skipped
    if not args.no_health_check:
        print("🔍 Checking API health...")
        if not check_api_health(args.api_url):
            print("❌ API health check failed!")
            print("💡 Make sure the API server is running:")
            print(f"   python scripts/start_api.py")
            print("💡 Or skip the health check with --no-health-check")
            sys.exit(1)
        print("✅ API is healthy and ready")
    
    print("=" * 50)
    
    try:
        # Update agent settings if custom values provided
        if args.max_retries != agent_settings.max_retries:
            agent_settings.max_retries = args.max_retries
        
        cli = TicketingCLI(args.api_url)
        cli.run()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start agent: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()