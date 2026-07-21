from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class PromptMode(str, Enum):
    UNBRANDED = "unbranded"
    BRANDED = "branded"
    BOTH = "both"


class PromptIntent(str, Enum):
    INFO = "info"
    COMPARISON = "comparison"
    HOWTO = "how-to"
    HIRE = "hire"
    REVIEW = "review"
    TROUBLESHOOT = "troubleshoot"
    EXPLORE = "explore"
    VERIFY = "verify"


class Prompt(BaseModel):
    text: str
    intent: PromptIntent
    mode: PromptMode
    focus_name: str
    language: str = "id"


class ScoredPrompt(Prompt):
    service_match: float = 0.0
    mention_likelihood: float = 0.0
    overall_score: float = 0.0
    needs_review: bool = False


class Focus(BaseModel):
    name: str
    description: str
    lens: str = "problem"
    priority: str = "medium"
    signals: list[str] = Field(default_factory=list)
    signal_count: int = 0
    service_match_score: float = 0.0
    prompts: list[ScoredPrompt] = Field(default_factory=list)


class Brand(BaseModel):
    name: str
    description: str
    website: str = ""
    service_categories: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    brand: Brand
    prompt_mode: PromptMode = PromptMode.UNBRANDED
    language: str = "id"
    output_dir: str = "."

    def save(self, path: str | Path):
        path = Path(path)
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: str | Path) -> ProjectConfig:
        path = Path(path)
        data = json.loads(path.read_text())
        return cls.model_validate(data)


class ProjectState(BaseModel):
    config: ProjectConfig
    focuses: list[Focus] = Field(default_factory=list)
    web_data: dict | None = None
    step_selections: dict[str, list[str]] = Field(default_factory=dict)

    def save(self, path: str | Path):
        path = Path(path)
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: str | Path) -> ProjectState:
        path = Path(path)
        data = json.loads(path.read_text())
        return cls.model_validate(data)
