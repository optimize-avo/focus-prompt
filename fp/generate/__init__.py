"""Generate focus clusters and prompt variants."""
from fp.generate.focuses import generate_focuses
from fp.generate.prompts import generate_all_prompts, generate_prompts_for_focus
from fp.generate.naturalness import naturalize_all_focuses, naturalize_focus_prompts

__all__ = [
    "generate_focuses",
    "generate_all_prompts",
    "generate_prompts_for_focus",
    "naturalize_all_focuses",
    "naturalize_focus_prompts",
]
