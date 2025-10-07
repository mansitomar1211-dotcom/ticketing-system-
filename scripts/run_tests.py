#!/usr/bin/env python3
"""
Script to run the test suite with various options.
"""
import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd: list, description: str) -> int:
    """
    Run a command and return its exit code.
    
    Args:
        cmd: Command to run as a list
        description: Description of what the command does
        
    Returns:
        Exit code of the command
    """
    print(f"🔄 {description}...")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
        else:
            print(f"❌ {description} failed with exit code {result.returncode}")
        return result.returncode
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print("💡 Make sure pytest is installed: pip install -r requirements-dev.txt")
        return 1
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return 1


def main():
    """Run tests with various options."""
    parser = argparse.ArgumentParser(
        description="Run the ticketing system test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all tests
  %(prog)s --unit             # Run only unit tests
  %(prog)s --integration      # Run only integration tests
  %(prog)s --api              # Run only API tests
  %(prog)s --coverage         # Run tests with coverage report
  %(prog)s --verbose          # Run tests with verbose output
  %(prog)s --fast             # Run tests in parallel (faster)
  %(prog)s tests/test_api.py  # Run specific test file
        """
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests (exclude integration tests)"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    
    parser.add_argument(
        "--api",
        action="store_true",
        help="Run only API tests"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Run tests with verbose output"
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run tests in parallel for faster execution"
    )
    
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML coverage report"
    )
    
    parser.add_argument(
        "--markers",
        action="store_true",
        help="Show available test markers"
    )
    
    parser.add_argument(
        "test_paths",
        nargs="*",
        help="Specific test files or directories to run"
    )
    
    args = parser.parse_args()
    
    # Show markers if requested
    if args.markers:
        cmd = ["python", "-m", "pytest", "--markers"]
        return run_command(cmd, "Showing test markers")
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add parallel execution
    if args.fast:
        cmd.extend(["-n", "auto"])
    
    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=api",
            "--cov=agent",
            "--cov-report=term-missing"
        ])
        
        if args.html_report:
            cmd.extend(["--cov-report=html:htmlcov"])
    
    # Add test selection
    if args.unit:
        cmd.extend(["-m", "not integration"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.api:
        cmd.append("tests/test_api.py")
    
    # Add specific test paths
    if args.test_paths:
        cmd.extend(args.test_paths)
    else:
        cmd.append("tests/")
    
    print("🧪 Running Ticketing System Tests")
    print("=" * 50)
    
    # Run the tests
    exit_code = run_command(cmd, "Running tests")
    
    # Additional reporting
    if args.coverage and args.html_report and exit_code == 0:
        print(f"📊 HTML coverage report generated: {project_root}/htmlcov/index.html")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())