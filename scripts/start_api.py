#!/usr/bin/env python3
"""
Script to start the ticketing API server.
"""
import sys
import os
import argparse
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import api_settings
from api.main import app


def main():
    """Start the API server."""
    parser = argparse.ArgumentParser(
        description="Start the Ticketing API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Start with default settings
  %(prog)s --host 0.0.0.0 --port 8080  # Custom host and port
  %(prog)s --debug                  # Enable debug mode with auto-reload
  %(prog)s --no-simulation          # Disable network simulation
        """
    )
    
    parser.add_argument(
        "--host",
        default=api_settings.host,
        help=f"Host to bind to (default: {api_settings.host})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=api_settings.port,
        help=f"Port to bind to (default: {api_settings.port})"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with auto-reload"
    )
    
    parser.add_argument(
        "--no-simulation",
        action="store_true",
        help="Disable network simulation (for development)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        default="info",
        help="Log level (default: info)"
    )
    
    args = parser.parse_args()
    
    # Handle no-simulation flag
    if args.no_simulation:
        print("⚠️  Network simulation disabled")
        # Temporarily disable simulation by setting failure rate to 0
        api_settings.failure_rate = 0.0
        api_settings.min_latency = 0.0
        api_settings.max_latency = 0.0
    
    print(f"🚀 Starting Ticketing API Server...")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"📚 Docs: http://{args.host}:{args.port}/docs")
    print(f"🔄 Redoc: http://{args.host}:{args.port}/redoc")
    
    if not args.no_simulation:
        print(f"⚡ Network simulation enabled:")
        print(f"   - Latency: {api_settings.min_latency}s - {api_settings.max_latency}s")
        print(f"   - Failure rate: {api_settings.failure_rate * 100}%")
    
    print(f"🐛 Debug mode: {'ON' if args.debug else 'OFF'}")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "api.main:app",
            host=args.host,
            port=args.port,
            reload=args.debug,
            log_level=args.log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down API server...")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()