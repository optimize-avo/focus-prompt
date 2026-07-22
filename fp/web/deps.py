"""Shared dependencies for web routes."""
from __future__ import annotations

import json

from fp import db
from fp.config import load_user_config, get_current_config


def get_db_path():
    """Return the database path (for monkeypatching in tests)."""
    return db.DB_PATH


def get_state():
    """Load active project state from SQLite, or None if no active project."""
    db.init_db()
    project_id = db.get_active_project_id()
    if not project_id:
        return None
    try:
        return db.project_row_to_state(project_id)
    except ValueError:
        return None


def save_state(state) -> None:
    """Save project state to SQLite (upsert active project)."""

    db.init_db()
    project_id = db.get_active_project_id()
    if project_id:
        # Update existing project in place
        brand = state.config.brand
        db.update_project(
            project_id,
            name=brand.name,
            description=brand.description,
            website=brand.website,
            services=json.dumps(brand.service_categories),
            competitors=json.dumps(brand.competitors),
            prompt_mode=state.config.prompt_mode.value,
            language=state.config.language,
        )
        # Delete old focuses and re-create
        old_focuses = db.get_focuses(project_id)
        for f in old_focuses:
            db.delete_focus(f["id"])
        for focus in state.focuses:
            fid = db.create_focus(
                project_id=project_id,
                name=focus.name,
                description=focus.description,
                lens=focus.lens,
                priority=focus.priority,
                signals=json.dumps(focus.signals),
                service_match_score=focus.service_match_score,
            )
            for prompt in focus.prompts:
                db.create_prompt(
                    focus_id=fid,
                    text=prompt.text,
                    intent=prompt.intent.value,
                    mode=prompt.mode.value,
                    language=prompt.language,
                    service_match=prompt.service_match,
                    mention_likelihood=prompt.mention_likelihood,
                    overall_score=prompt.overall_score,
                    needs_review=int(prompt.needs_review),
                )
        # Clear and re-save web_data
        db.delete_web_data(project_id)
        if state.web_data:
            db.save_web_data(project_id, state.web_data)
        # Clear and re-save step_selections
        db.delete_step_selections(project_id)
        for step, selections in state.step_selections.items():
            db.save_step_selections(project_id, step, selections)
    else:
        # No active project — create new one
        new_id = db.state_to_db(state)
        db.set_active_project(new_id)


def get_config() -> dict[str, str]:
    """Get current config values."""
    load_user_config()
    return get_current_config()
