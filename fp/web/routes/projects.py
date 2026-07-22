"""Project CRUD API routes."""
from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from fp import db

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    website: str = ""
    services: list[str] = []
    competitors: list[str] = []
    prompt_mode: str = "unbranded"
    language: str = "id"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    services: Optional[list[str]] = None
    competitors: Optional[list[str]] = None
    prompt_mode: Optional[str] = None
    language: Optional[str] = None


@router.get("/projects")
async def list_projects():
    """List all projects."""
    return db.list_projects()


@router.post("/projects")
async def create_project(body: ProjectCreate):
    """Create a new project."""
    pid = db.create_project(
        name=body.name,
        description=body.description,
        website=body.website,
        services=json.dumps(body.services),
        competitors=json.dumps(body.competitors),
        prompt_mode=body.prompt_mode,
        language=body.language,
    )
    return db.get_project(pid)


@router.get("/projects/active")
async def get_active_project():
    """Get the active project."""
    pid = db.get_active_project_id()
    if not pid:
        raise HTTPException(status_code=404, detail="No active project")
    project = db.get_project(pid)
    if not project:
        raise HTTPException(status_code=404, detail="Active project not found")
    return project


@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    """Get a project by ID."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/projects/{project_id}")
async def update_project(project_id: int, body: ProjectUpdate):
    """Update a project."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    fields = body.model_dump(exclude_unset=True)
    if "services" in fields:
        fields["services"] = json.dumps(fields["services"])
    if "competitors" in fields:
        fields["competitors"] = json.dumps(fields["competitors"])
    db.update_project(project_id, **fields)
    return db.get_project(project_id)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    """Delete a project and all related data."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete_project(project_id)
    return {"status": "ok"}


@router.post("/projects/{project_id}/activate")
async def activate_project(project_id: int):
    """Set a project as active."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.set_active_project(project_id)
    return {"status": "ok", "active_project_id": project_id}
