"""Export focuses and prompts to JSON / CSV."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from fp.models import Focus, ProjectState


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
