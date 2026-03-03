from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from schema import ReviewResult

console = Console()

def format_status(status: str) -> str:
    if status == "pass":
        return "[green]PASS[/green]"
    elif status == "fail":
        return "[red]FAIL[/red]"
    elif status == "warn":
        return "[yellow]WARN[/yellow]"
    return status

def display_review(result: ReviewResult):
    console.print(Panel(
        Text(result.summary, style="bold italic"),
        title=f"Overall Verdict: {format_status(result.overall)}",
        subtitle=f"Word Count: {result.word_count} | Post Type: {result.post_type.title()}",
        expand=False
    ))

    table = Table(title="Checklist Items", show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan", width=20)
    table.add_column("Status", width=10)
    table.add_column("Note")

    for item in result.items:
        table.add_row(item.category, format_status(item.status), item.note)

    console.print(table)
