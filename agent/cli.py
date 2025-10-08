# agent/cli.py (continued from where it was cut off)
"""
Command-line interface for the ticketing agent.
"""
import logging
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from .conversational_agent import TicketingAgent, ConversationalAgentError
from .config import TEST_SCENARIOS

# Set up rich logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)


class TicketingCLI:
    """Command-line interface for the ticketing agent."""
    
    def __init__(self, api_base_url: str):
        """
        Initialize the CLI.
        
        Args:
            api_base_url: Base URL for the ticketing API
        """
        self.console = Console()
        self.api_base_url = api_base_url
        self.agent: Optional[TicketingAgent] = None
        self.running = True
        
        # Initialize agent
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        """Initialize the conversational agent."""
        try:
            with self.console.status("[bold green]Initializing AI agent..."):
                self.agent = TicketingAgent(self.api_base_url)
                
                # Test connections
                if not self.agent.test_connection():
                    self.console.print("[red]Warning: Some services may not be available[/red]")
                
            self.console.print("[green]✓ Agent initialized successfully[/green]")
            
        except ConversationalAgentError as e:
            self.console.print(f"[red]Failed to initialize agent: {e}[/red]")
            sys.exit(1)
        except Exception as e:
            self.console.print(f"[red]Unexpected error during initialization: {e}[/red]")
            sys.exit(1)
    
    def display_welcome(self) -> None:
        """Display welcome message."""
        welcome_text = Text("🎫 Ticketing System AI Assistant", style="bold blue")
        welcome_panel = Panel(
            welcome_text,
            subtitle="Type 'help' for commands, 'quit' to exit",
            border_style="blue"
        )
        self.console.print(welcome_panel)
        self.console.print(f"[dim]Connected to API: {self.api_base_url}[/dim]\n")
    
    def display_help(self) -> None:
        """Display help information."""
        help_table = Table(title="Available Commands", border_style="green")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")
        
        commands = [
            ("help", "Show this help message"),
            ("quit / exit", "Exit the application"),
            ("clear", "Clear conversation history"),
            ("history", "Show conversation summary"),
            ("test", "Run test scenarios"),
            ("status", "Check system status"),
            ("", ""),
            ("[bold]Natural Language Examples:[/bold]", ""),
            ("create ticket about [issue]", "Create a new ticket"),
            ("get all tickets", "Retrieve all tickets"),
            ("get open tickets", "Retrieve only open tickets"),
            ("get ticket [id]", "Get specific ticket details"),
            ("update ticket [id] to [status]", "Update ticket status"),
            ("delete ticket [id]", "Delete a ticket"),
        ]
        
        for command, description in commands:
            help_table.add_row(command, description)
        
        self.console.print(help_table)
    
    def check_status(self) -> None:
        """Check and display system status."""
        if not self.agent:
            self.console.print("[red]Agent not initialized[/red]")
            return
        
        with self.console.status("[bold green]Checking system status..."):
            connection_ok = self.agent.test_connection()
        
        status_table = Table(title="System Status", border_style="blue")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="white")
        
        status_table.add_row("API Connection", "✓ OK" if connection_ok else "✗ Failed")
        status_table.add_row("LLM Connection", "✓ OK" if connection_ok else "✗ Failed")
        status_table.add_row("Agent", "✓ Ready" if self.agent else "✗ Not Ready")
        
        self.console.print(status_table)
    
    def run_test_scenarios(self) -> None:
        """Run the predefined test scenarios."""
        if not self.agent:
            self.console.print("[red]Agent not initialized[/red]")
            return
        
        self.console.print("\n🧪 [bold yellow]Running Test Scenarios...[/bold yellow]\n")
        
        for i, scenario in enumerate(TEST_SCENARIOS, 1):
            self.console.print(f"[bold cyan]Test {i}:[/bold cyan] {scenario}")
            
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                ) as progress:
                    task = progress.add_task("Processing...", total=None)
                    response = self.agent.chat(scenario)
                    progress.remove_task(task)
                
                # Display response in a panel
                response_panel = Panel(
                    response,
                    title=f"🤖 Test {i} Response",
                    border_style="green",
                    expand=False
                )
                self.console.print(response_panel)
                self.console.print()  # Add spacing
                
            except Exception as e:
                self.console.print(f"[red]Error in test {i}: {str(e)}[/red]\n")
    
    def process_command(self, user_input: str) -> bool:
        """
        Process user commands and return False if should quit.
        
        Args:
            user_input: User's input string
            
        Returns:
            True to continue, False to quit
        """
        command = user_input.lower().strip()
        
        if command in ['quit', 'exit', 'q']:
            self.console.print("👋 [bold blue]Goodbye![/bold blue]")
            return False
        
        elif command == 'help':
            self.display_help()
            
        elif command == 'clear':
            if self.agent:
                self.agent.reset_conversation()
                self.console.print("🧹 [green]Conversation history cleared.[/green]")
            else:
                self.console.print("[red]Agent not available[/red]")
            
        elif command == 'history':
            if self.agent:
                summary = self.agent.get_conversation_summary()
                self.console.print(Panel(summary, title="Conversation History", border_style="yellow"))
            else:
                self.console.print("[red]Agent not available[/red]")
            
        elif command == 'test':
            self.run_test_scenarios()
            
        elif command == 'status':
            self.check_status()
            
        else:
            # Send to AI agent
            if not self.agent:
                self.console.print("[red]Agent not available. Please restart the application.[/red]")
                return True
            
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                ) as progress:
                    task = progress.add_task("🤖 Processing your request...", total=None)
                    response = self.agent.chat(user_input)
                    progress.remove_task(task)
                
                # Display response in a nice panel
                response_panel = Panel(
                    response,
                    title="🤖 Assistant Response",
                    border_style="green",
                    expand=False
                )
                self.console.print(response_panel)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Request cancelled by user[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error processing request: {str(e)}[/red]")
                logger.error(f"Error in process_command: {e}", exc_info=True)
        
        return True
    
    def run(self) -> None:
        """Main CLI loop."""
        self.display_welcome()
        
        while self.running:
            try:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                
                if not user_input.strip():
                    continue
                
                should_continue = self.process_command(user_input)
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                self.console.print("\n\n👋 [bold blue]Goodbye![/bold blue]")
                break
            except EOFError:
                self.console.print("\n\n👋 [bold blue]Goodbye![/bold blue]")
                break
            except Exception as e:
                self.console.print(f"[red]Unexpected error: {str(e)}[/red]")
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)


def main() -> None:
    """Entry point for the CLI application."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ticketing System AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Connect to default API (localhost:8000)
  %(prog)s --api-url http://api:8080 # Connect to custom API URL
  %(prog)s --debug                   # Enable debug logging
        """
    )
    
    parser.add_argument(
        "--api-url", 
        default="http://localhost:8000",
        help="Base URL for the ticketing API (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        cli = TicketingCLI(args.api_url)
        cli.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()