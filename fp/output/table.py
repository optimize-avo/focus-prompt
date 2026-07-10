"""Rich table output for CLI."""
from __future__ import annotations

from rich.console import Console
from rich.table import Table

from fp.models import Focus, PromptMode

console = Console()


def render_focus_table(focuses: list[Focus]):
    """Render focuses as a rich table."""
    table = Table(title="Problem-Based Focuses (Unbranded-First)")

    table.add_column("#", style="dim")
    table.add_column("Focus", style="cyan", no_wrap=False)
    table.add_column("Priority", style="bold")
    table.add_column("Unbranded", justify="right")
    table.add_column("Branded", justify="right")
    table.add_column("Service Match", justify="right")
    table.add_column("Signals", justify="right")

    for i, focus in enumerate(focuses, 1):
        unbranded_count = sum(1 for p in focus.prompts if p.mode == PromptMode.UNBRANDED)
        branded_count = sum(1 for p in focus.prompts if p.mode == PromptMode.BRANDED)

        priority_tag = {
            "high": "🔥 HIGH",
            "medium": "💡 MEDIUM",
            "low": "🔍 EXPLORE",
        }.get(focus.priority, "  ")

        service_str = f"{focus.service_match_score:.0f}%" if focus.service_match_score else "-"

        table.add_row(
            str(i),
            focus.name,
            priority_tag,
            str(unbranded_count) if unbranded_count else "-",
            str(branded_count) if branded_count else "-",
            service_str,
            str(focus.signal_count),
        )

    console.print(table)


def render_prompt_table(focus: Focus, mode_filter: str | None = None):
    """Render prompts for a specific focus."""
    title = f"Prompts — {focus.name}"
    table = Table(title=title)

    table.add_column("#", style="dim")
    table.add_column("Mode", style="bold")
    table.add_column("Prompt", style="white", no_wrap=False)
    table.add_column("Intent", style="yellow")
    table.add_column("Service", justify="right")
    table.add_column("Mention", justify="right")
    table.add_column("Score", justify="right")

    prompts = focus.prompts
    if mode_filter:
        prompts = [p for p in prompts if p.mode.value == mode_filter]

    for i, prompt in enumerate(prompts, 1):
        mode_tag = "[blue]UN[/]" if prompt.mode == PromptMode.UNBRANDED else "[green]BR[/]"
        review_flag = " ⚠" if prompt.needs_review else ""

        table.add_row(
            str(i),
            mode_tag,
            prompt.text + review_flag,
            prompt.intent.value,
            f"{prompt.service_match:.0f}%" if prompt.service_match else "-",
            f"{prompt.mention_likelihood:.0f}%" if prompt.mention_likelihood else "-",
            f"{prompt.overall_score:.0f}" if prompt.overall_score else "-",
        )

    console.print(table)
