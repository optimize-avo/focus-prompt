"""Focus and Prompt CRUD API routes."""
from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from fp import db

router = APIRouter()


# ── Focus ──

class FocusCreate(BaseModel):
    name: str
    description: str = ""
    lens: str = "problem"
    priority: str = "medium"
    signals: list[str] = []
    service_match_score: float = 0.0


class FocusUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    lens: Optional[str] = None
    priority: Optional[str] = None
    signals: Optional[list[str]] = None
    service_match_score: Optional[float] = None


@router.get("/projects/{project_id}/focuses")
async def list_focuses(project_id: int):
    """List all focuses for a project."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.get_focuses(project_id)


@router.post("/projects/{project_id}/focuses")
async def create_focus(project_id: int, body: FocusCreate):
    """Create a focus for a project."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    fid = db.create_focus(
        project_id=project_id,
        name=body.name,
        description=body.description,
        lens=body.lens,
        priority=body.priority,
        signals=json.dumps(body.signals),
        service_match_score=body.service_match_score,
    )
    focuses = db.get_focuses(project_id)
    return [f for f in focuses if f["id"] == fid][0]


@router.put("/projects/{project_id}/focuses/{focus_id}")
async def update_focus(project_id: int, focus_id: int, body: FocusUpdate):
    """Update a focus."""
    focuses = db.get_focuses(project_id)
    if not any(f["id"] == focus_id for f in focuses):
        raise HTTPException(status_code=404, detail="Focus not found")
    fields = body.model_dump(exclude_unset=True)
    if "signals" in fields:
        fields["signals"] = json.dumps(fields["signals"])
    db.update_focus(focus_id, **fields)
    focuses = db.get_focuses(project_id)
    return [f for f in focuses if f["id"] == focus_id][0]


@router.delete("/projects/{project_id}/focuses/{focus_id}")
async def delete_focus(project_id: int, focus_id: int):
    """Delete a focus and its prompts."""
    focuses = db.get_focuses(project_id)
    if not any(f["id"] == focus_id for f in focuses):
        raise HTTPException(status_code=404, detail="Focus not found")
    db.delete_focus(focus_id)
    return {"status": "ok"}


# ── Prompt ──

class PromptCreate(BaseModel):
    text: str
    intent: str = "info"
    mode: str = "unbranded"
    language: str = "id"
    service_match: float = 0.0
    mention_likelihood: float = 0.0
    overall_score: float = 0.0
    needs_review: bool = False


class PromptUpdate(BaseModel):
    text: Optional[str] = None
    intent: Optional[str] = None
    mode: Optional[str] = None
    language: Optional[str] = None
    service_match: Optional[float] = None
    mention_likelihood: Optional[float] = None
    overall_score: Optional[float] = None
    needs_review: Optional[bool] = None


@router.get("/projects/{project_id}/focuses/{focus_id}/prompts")
async def list_prompts(project_id: int, focus_id: int):
    """List all prompts for a focus."""
    focuses = db.get_focuses(project_id)
    if not any(f["id"] == focus_id for f in focuses):
        raise HTTPException(status_code=404, detail="Focus not found")
    return db.get_prompts(focus_id)


@router.post("/projects/{project_id}/focuses/{focus_id}/prompts")
async def create_prompt(project_id: int, focus_id: int, body: PromptCreate):
    """Create a prompt for a focus."""
    focuses = db.get_focuses(project_id)
    if not any(f["id"] == focus_id for f in focuses):
        raise HTTPException(status_code=404, detail="Focus not found")
    pid = db.create_prompt(
        focus_id=focus_id,
        text=body.text,
        intent=body.intent,
        mode=body.mode,
        language=body.language,
        service_match=body.service_match,
        mention_likelihood=body.mention_likelihood,
        overall_score=body.overall_score,
        needs_review=int(body.needs_review),
    )
    prompts = db.get_prompts(focus_id)
    return [p for p in prompts if p["id"] == pid][0]


@router.put("/projects/{project_id}/focuses/{focus_id}/prompts/{prompt_id}")
async def update_prompt(project_id: int, focus_id: int, prompt_id: int, body: PromptUpdate):
    """Update a prompt."""
    prompts = db.get_prompts(focus_id)
    if not any(p["id"] == prompt_id for p in prompts):
        raise HTTPException(status_code=404, detail="Prompt not found")
    fields = body.model_dump(exclude_unset=True)
    if "needs_review" in fields:
        fields["needs_review"] = int(fields["needs_review"])
    db.update_prompt(prompt_id, **fields)
    prompts = db.get_prompts(focus_id)
    return [p for p in prompts if p["id"] == prompt_id][0]


@router.delete("/projects/{project_id}/focuses/{focus_id}/prompts/{prompt_id}")
async def delete_prompt(project_id: int, focus_id: int, prompt_id: int):
    """Delete a prompt."""
    prompts = db.get_prompts(focus_id)
    if not any(p["id"] == prompt_id for p in prompts):
        raise HTTPException(status_code=404, detail="Prompt not found")
    db.delete_prompt(prompt_id)
    return {"status": "ok"}


@router.get("/projects/{project_id}/full")
async def get_full_project(project_id: int):
    """Get full project with focuses and prompts nested."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    focuses = db.get_focuses(project_id)
    for f in focuses:
        f["prompts"] = db.get_prompts(f["id"])
    project["focuses"] = focuses
    return project
