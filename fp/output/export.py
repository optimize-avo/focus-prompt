"""Export focuses and prompts to JSON / CSV."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from fp.models import ProjectState


def export_json(state: ProjectState, path: str | Path):
    """Export full project state as JSON."""
    path = Path(path)
    data = state.model_dump(mode="json")
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return path


def export_csv(state: ProjectState, path: str | Path):
    """Export prompts as CSV (flat)."""
    path = Path(path)
    rows = []
    for focus in state.focuses:
        for prompt in focus.prompts:
            rows.append({
                "focus": focus.name,
                "focus_priority": focus.priority,
                "prompt": prompt.text,
                "mode": prompt.mode.value,
                "intent": prompt.intent.value,
                "language": prompt.language,
                "service_match": prompt.service_match,
                "mention_likelihood": prompt.mention_likelihood,
                "overall_score": prompt.overall_score,
                "needs_review": prompt.needs_review,
            })

    with open(path, "w", newline="", encoding="utf-8") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        else:
            f.write("")

    return path


def export_csv_content(state: ProjectState) -> str:
    """Export prompts as CSV string (for MCP download)."""
    import io
    output = io.StringIO()
    rows = []
    for focus in state.focuses:
        for prompt in focus.prompts:
            rows.append({
                "focus": focus.name,
                "focus_priority": focus.priority,
                "prompt": prompt.text,
                "mode": prompt.mode.value,
                "intent": prompt.intent.value,
                "language": prompt.language,
                "service_match": prompt.service_match,
                "mention_likelihood": prompt.mention_likelihood,
                "overall_score": prompt.overall_score,
                "needs_review": prompt.needs_review,
            })

    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return output.getvalue()


def export_table_content(state: ProjectState) -> str:
    """Export prompts as markdown table string (for MCP display)."""
    if not state.focuses:
        return "No focuses yet."

    lines = []
    lines.append("# Focus Prompt Export\n")

    # Summary table
    lines.append("## Summary\n")
    lines.append("| # | Focus | Priority | Service Match | Unbranded | Branded | Total | Review |")
    lines.append("|---|-------|----------|---------------|-----------|---------|-------|--------|")

    for i, focus in enumerate(state.focuses, 1):
        unbranded = sum(1 for p in focus.prompts if p.mode.value == "unbranded")
        branded = sum(1 for p in focus.prompts if p.mode.value == "branded")
        total = len(focus.prompts)
        review = sum(1 for p in focus.prompts if p.needs_review)
        service = f"{focus.service_match_score:.0f}%" if focus.service_match_score else "-"
        priority = focus.priority.upper() if focus.priority else "-"

        lines.append(
            f"| {i} | {focus.name} | {priority} | {service} | {unbranded} | {branded} | {total} | {review} |"
        )

    lines.append("")

    # Detailed prompts table
    lines.append("## Prompts\n")
    lines.append("| Focus | Mode | Prompt | Intent | Service | Mention | Score | Review |")
    lines.append("|-------|------|--------|--------|---------|---------|-------|--------|")

    for focus in state.focuses:
        for prompt in focus.prompts:
            mode = "UN" if prompt.mode.value == "unbranded" else "BR"
            service = f"{prompt.service_match:.0f}%" if prompt.service_match else "-"
            mention = f"{prompt.mention_likelihood:.0f}%" if prompt.mention_likelihood else "-"
            score = f"{prompt.overall_score:.0f}" if prompt.overall_score else "-"
            review = "⚠" if prompt.needs_review else ""

            # Escape pipe characters in prompt text
            prompt_text = prompt.text.replace("|", "\\|")

            lines.append(
                f"| {focus.name} | {mode} | {prompt_text} | {prompt.intent.value} | {service} | {mention} | {score} | {review} |"
            )

    return "\n".join(lines)
