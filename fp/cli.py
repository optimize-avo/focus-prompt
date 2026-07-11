"""CLI — Focus Prompt Research Tool."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

import asyncio

from fp.generate.focuses import generate_focuses
from fp.generate.prompts import generate_all_prompts
from fp.enrichment.problems import discover_problems, discover_problems_enriched
from fp.research.web import research_queries
from fp.models import (
    Brand,
    Focus,
    ProjectConfig,
    ProjectState,
    PromptMode,
    ScoredPrompt,
)
from fp.output.export import export_csv, export_json
from fp.output.table import render_focus_table, render_prompt_table
from fp.scoring.scorer import score_all

app = typer.Typer(
    name="fp",
    help="Focus Prompt — AI Brand Visibility Research Tool",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)

PROJECT_FILE = "fp-project.json"


def _load_state() -> ProjectState:
    if not Path(PROJECT_FILE).exists():
        err_console.print("[red]Error:[/red] No project found. Run [bold]fp init[/] first.")
        raise typer.Exit(1)
    return ProjectState.load(PROJECT_FILE)


def _save_state(state: ProjectState):
    state.save(PROJECT_FILE)
    console.print(f"[dim]Saved to {PROJECT_FILE}[/dim]")


@app.command()
def init(
    name: str = typer.Argument(..., help="Brand name"),
    description: str = typer.Option("", "--desc", "-d", help="Brand description"),
    website: str = typer.Option("", "--url", "-u", help="Brand website URL"),
    categories: str = typer.Option("", "--services", "-s", help="Comma-separated service categories"),
    competitors: str = typer.Option("", "--competitors", "-c", help="Comma-separated competitor names"),
    mode: str = typer.Option("unbranded", "--mode", "-m", help="Prompt mode: unbranded, branded, both"),
    language: str = typer.Option("id", "--lang", "-l", help="Primary language"),
):
    """Initialize a new brand project."""
    if Path(PROJECT_FILE).exists():
        overwrite = typer.confirm("Project already exists. Overwrite?")
        if not overwrite:
            raise typer.Exit()

    cats = [c.strip() for c in categories.split(",") if c.strip()]
    comps = [c.strip() for c in competitors.split(",") if c.strip()]

    brand = Brand(
        name=name,
        description=description,
        website=website,
        service_categories=cats,
        competitors=comps,
    )

    config = ProjectConfig(
        brand=brand,
        prompt_mode=PromptMode(mode),
        language=language,
    )

    state = ProjectState(config=config)
    _save_state(state)

    console.print(f"\n[bold green]✓[/] Project initialized for [cyan]{name}[/]")
    console.print(f"  Mode: [yellow]{mode}[/]")
    console.print(f"  Services: {', '.join(cats) if cats else '—'}")
    console.print(f"  Competitors: {', '.join(comps) if comps else '—'}")
    console.print("\nNext: [bold]fp focus discover[/] — discover user problems and generate focuses")


@app.command()
def research(
    extra: str = typer.Option("", "--extra", "-e", help="Extra seed queries, comma-separated"),
    no_autocomplete: bool = typer.Option(False, "--no-autocomplete", help="Skip Google Autocomplete"),
):
    """Fetch real user queries from Google Autocomplete."""
    state = _load_state()
    brand = state.config.brand

    extra_queries = [q.strip() for q in extra.split(",") if q.strip()] if extra else None

    console.print(f"\n🌐 Researching real user queries for [cyan]{brand.name}[/]...")

    try:
        web_data = asyncio.run(research_queries(
            brand,
            extra_queries=extra_queries,
            include_autocomplete=not no_autocomplete,
        ))
    except Exception as e:
        err_console.print(f"[red]Web research failed:[/red] {e}")
        raise typer.Exit(1)

    stats = web_data["stats"]
    console.print(f"  ✓ Autocomplete: [bold]{stats['autocomplete_count']}[/] suggestions")
    console.print(f"  ✓ Total queries: [bold]{stats['total_queries']}[/]")

    # Save web data to state
    state.web_data = web_data
    _save_state(state)

    # Show sample
    if web_data["autocomplete"]:
        console.print("\n[dim]Sample autocomplete:[/dim]")
        for q in web_data["autocomplete"][:5]:
            console.print(f"  • {q}")

    console.print("\nNext: [bold]fp discover[/] — uses this real data for problem discovery")


@app.command()
def discover(
    model: str = typer.Option("", "--model", "-M", help="LLM model (default: env FP_MODEL or gpt-4o-mini)"),
):
    """Discover problems and generate focuses from LLM + web signals."""
    state = _load_state()
    brand = state.config.brand

    if not brand.description and not brand.service_categories:
        err_console.print("[red]Error:[/red] Brand needs description or service categories.")
        err_console.print("Re-run: [bold]fp init[/] with --desc or --services")
        raise typer.Exit(1)

    console.print(f"\n🔍 Discovering problems around [cyan]{brand.name}[/]...")

    try:
        web_data = getattr(state, 'web_data', None)
        if web_data and web_data.get("stats", {}).get("total_queries", 0) > 0:
            console.print("  📡 Using real web research data as ground truth")
            problems = discover_problems_enriched(brand, web_data, model=model)
        else:
            console.print("  ⚠ No web data — using LLM-only discovery (run [bold]fp research[/] first for better results)")
            problems = discover_problems(brand, model=model)
    except Exception as e:
        err_console.print(f"[red]Problem discovery failed:[/red] {e}")
        raise typer.Exit(1)

    if not problems:
        console.print("[yellow]No problems discovered. Check your brand input.[/yellow]")
        raise typer.Exit(1)

    console.print(f"  Found problems in {len(problems)} service categories\n")

    console.print("🧠 Generating focuses...")
    try:
        focuses = generate_focuses(brand, problems, model=model)
    except Exception as e:
        err_console.print(f"[red]Focus generation failed:[/red] {e}")
        raise typer.Exit(1)

    state.focuses = focuses
    _save_state(state)

    console.print(f"  Generated [bold]{len(focuses)}[/] focuses\n")
    render_focus_table(focuses)

    console.print("\nNext: [bold]fp prompt generate[/] — generate prompt variants per focus")
    console.print("Or:   [bold]fp focus list[/] — see focus details again")


@app.command()
def prompt_generate(
    model: str = typer.Option("", "--model", "-M", help="LLM model (default: env FP_MODEL or gpt-4o-mini)"),
):
    """Generate prompt variants for each focus (unbranded-first)."""
    state = _load_state()
    brand = state.config.brand

    if not state.focuses:
        err_console.print("[red]Error:[/red] No focuses yet. Run [bold]fp focus discover[/] first.")
        raise typer.Exit(1)

    console.print(f"\n✍️  Generating prompts for {len(state.focuses)} focuses...")
    console.print(f"   Mode: [yellow]{state.config.prompt_mode.value}[/]")

    try:
        updated = generate_all_prompts(brand, state.focuses, state.config.prompt_mode, model=model)
    except Exception as e:
        err_console.print(f"[red]Prompt generation failed:[/red] {e}")
        raise typer.Exit(1)

    state.focuses = updated
    _save_state(state)

    total = sum(len(f.prompts) for f in state.focuses)
    console.print(f"\n  Generated [bold]{total}[/] total prompts\n")
    render_focus_table(state.focuses)

    console.print("\nNext: [bold]fp score[/] — score prompts for brand relevance")
    console.print("Or:   [bold]fp prompt list[/] — view prompts per focus")


@app.command()
def score(
    model: str = typer.Option("", "--model", "-M", help="LLM model (default: env FP_MODEL or gpt-4o-mini)"),
):
    """Score all prompts for brand relevance and mention likelihood."""
    state = _load_state()
    brand = state.config.brand

    total_prompts = sum(len(f.prompts) for f in state.focuses)
    if total_prompts == 0:
        err_console.print("[red]Error:[/red] No prompts to score. Run [bold]fp prompt generate[/] first.")
        raise typer.Exit(1)

    console.print(f"\n📊 Scoring {total_prompts} prompts for relevance to [cyan]{brand.name}[/]...")

    try:
        state.focuses = score_all(state.focuses, brand, model=model)
    except Exception as e:
        err_console.print(f"[red]Scoring failed:[/red] {e}")
        raise typer.Exit(1)

    _save_state(state)

    needs_review = sum(
        1 for f in state.focuses for p in f.prompts if p.needs_review
    )

    console.print("\n  [bold green]✓[/] Scoring complete!\n")
    render_focus_table(state.focuses)

    if needs_review:
        console.print(f"\n[yellow]⚠ {needs_review} prompt(s) flagged for review[/yellow]")
        console.print("  Run [bold]fp prompt list --review[/] to see flagged prompts")

    console.print("\nNext: [bold]fp export json[/] — export results")
    console.print("Or:   [bold]fp prompt list[/] — view all prompts")


@app.command()
def focus_list():
    """List all focuses."""
    state = _load_state()
    if not state.focuses:
        console.print("[yellow]No focuses yet. Run [bold]fp focus discover[/] first.[/yellow]")
        raise typer.Exit()
    render_focus_table(state.focuses)


@app.command()
def prompt_list(
    focus_name: Optional[str] = typer.Option(None, "--focus", "-f", help="Filter by focus name"),
    mode_filter: Optional[str] = typer.Option(None, "--mode", "-m", help="Filter by mode: unbranded, branded"),
    review: bool = typer.Option(False, "--review", "-r", help="Show only prompts needing review"),
):
    """List prompts, optionally filtered."""
    state = _load_state()

    focuses = state.focuses
    if focus_name:
        focuses = [f for f in focuses if focus_name.lower() in f.name.lower()]
        if not focuses:
            err_console.print(f"[red]No focus matching '{focus_name}'[/red]")
            raise typer.Exit(1)

    for focus in focuses:
        prompts_to_show = focus.prompts
        if mode_filter:
            prompts_to_show = [p for p in prompts_to_show if p.mode.value == mode_filter]
        if review:
            prompts_to_show = [p for p in prompts_to_show if p.needs_review]

        temp_focus = focus.model_copy(deep=True)
        temp_focus.prompts = prompts_to_show
        render_prompt_table(temp_focus, mode_filter)

    needs_review = sum(1 for f in state.focuses for p in f.prompts if p.needs_review)
    console.print(f"\n[dim]Total: {sum(len(f.prompts) for f in state.focuses)} prompts | {needs_review} need review[/dim]")


@app.command()
def export(
    fmt: str = typer.Argument("json", help="json or csv"),
    output: str = typer.Option("", "--output", "-o", help="Output file path"),
):
    """Export project data."""
    state = _load_state()
    path = output or f"fp-export.{fmt}"

    if fmt == "json":
        result = export_json(state, path)
    elif fmt == "csv":
        result = export_csv(state, path)
    else:
        err_console.print(f"[red]Unsupported format:[/red] {fmt}. Use json or csv.")
        raise typer.Exit(1)

    console.print(f"[bold green]✓[/] Exported to [cyan]{result}[/cyan]")


@app.command()
def status():
    """Show current project status."""
    state = _load_state()
    brand = state.config.brand
    total_prompts = sum(len(f.prompts) for f in state.focuses)
    needs_review = sum(1 for f in state.focuses for p in f.prompts if p.needs_review)

    console.print(f"\n[bold]Brand:[/] [cyan]{brand.name}[/]")
    console.print(f"  Description: {brand.description or '—'}")
    console.print(f"  Website:     {brand.website or '—'}")
    console.print(f"  Services:    {', '.join(brand.service_categories) or '—'}")
    console.print(f"  Competitors: {', '.join(brand.competitors) or '—'}")
    console.print(f"\n[bold]State:[/]")
    console.print(f"  Focuses:     {len(state.focuses)}")
    console.print(f"  Prompts:     {total_prompts}")
    console.print(f"  Needs review:{' [yellow]' + str(needs_review) + '[/]' if needs_review else ' 0'}")

    if state.focuses:
        console.print()
        render_focus_table(state.focuses)


if __name__ == "__main__":
    app()
