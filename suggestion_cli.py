import argparse
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm

def display_suggestions(suggestions):
    console = Console()
    table = Table(title="Aider Suggestions")
    
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("File", style="magenta")
    table.add_column("Question", style="green")
    table.add_column("Response", style="yellow")

    for suggestion in suggestions:
        table.add_row(
            str(suggestion['id']),
            suggestion['file'],
            suggestion['question'],
            suggestion['response']['response'][:50] + "..."  # Truncate long responses
        )

    console.print(table)

def display_suggestion_detail(suggestion, highlight):
    console = Console()
    console.print(Panel(f"[cyan]ID:[/cyan] {suggestion['id']}", title="Suggestion Detail", expand=False))
    console.print(f"[magenta]File:[/magenta] {suggestion['file']}")
    console.print(f"[green]Question:[/green] {suggestion['question']}")
    console.print(f"[yellow]Model:[/yellow] {suggestion['model']}")
    console.print(f"[yellow]Timestamp:[/yellow] {suggestion['timestamp']}")
    if highlight:
        console.print(Panel(Syntax(suggestion['response']['response'], "python", theme="monokai", line_numbers=True), title="Response"))
    else:
        console.print(Panel(suggestion['response']['response'], title="Response"))

def delete_suggestion(suggestion_id):
    console = Console()
    response = requests.delete(f"http://localhost:8000/suggestions/{suggestion_id}")
    if response.status_code == 200:
        suggestion = response.json()
        console.print(f"[yellow]Are you sure you want to delete the following suggestion?[/yellow]")
        console.print(f"[cyan]ID:[/cyan] {suggestion['id']}")
        console.print(f"[magenta]File:[/magenta] {suggestion['file']}")
        console.print(f"[green]Question:[/green] {suggestion['question']}")
        console.print(f"[yellow]Response (first 100 characters):[/yellow] {suggestion['response']['response'][:100]}...")
        
        if Confirm.ask("Confirm deletion?"):
            delete_response = requests.post(f"http://localhost:8000/suggestions/{suggestion_id}/confirm_delete")
            if delete_response.status_code == 200:
                console.print("[green]Suggestion deleted successfully.[/green]")
            else:
                console.print("[red]Failed to delete suggestion.[/red]")
        else:
            console.print("[yellow]Deletion cancelled.[/yellow]")
    else:
        console.print(f"[red]Error: Unable to fetch suggestion with ID {suggestion_id}[/red]")

def main():
    parser = argparse.ArgumentParser(description="Aider Suggestions CLI")
    parser.add_argument("--id", type=int, help="Display details for a specific suggestion ID")
    parser.add_argument("--highlight", action="store_true", help="Enable syntax highlighting")
    parser.add_argument("--delete", type=int, help="Delete a specific suggestion by ID")
    args = parser.parse_args()

    if args.delete:
        delete_suggestion(args.delete)
    elif args.id:
        response = requests.get(f"http://localhost:8000/suggestions/{args.id}")
        if response.status_code == 200:
            suggestion = response.json()
            display_suggestion_detail(suggestion, args.highlight)
        else:
            print(f"Error: Unable to fetch suggestion with ID {args.id}")
    else:
        response = requests.get("http://localhost:8000/suggestions/")
        if response.status_code == 200:
            suggestions = response.json()
            display_suggestions(suggestions)
        else:
            print("Error: Unable to fetch suggestions")

if __name__ == "__main__":
    main()
