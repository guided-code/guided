from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

SKILLS_DIR = Path(".guided") / "skills"
SKILL_FILE_NAME = "SKILL.md"
VALID_SKILL_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


@dataclass(frozen=True)
class MarkdownSkill:
    name: str
    path: Path
    content: str

    @property
    def description(self) -> str:
        for line in self.content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            return stripped
        return f"Execute the {self.name} workflow"


def _candidate_roots(start_path: Optional[Path] = None) -> Iterable[Path]:
    start = (start_path or Path.cwd()).resolve()
    yield start
    yield from start.parents


def find_skills_root(start_path: Optional[Path] = None) -> Optional[Path]:
    for base in _candidate_roots(start_path):
        skills_root = base / SKILLS_DIR
        if skills_root.is_dir():
            return skills_root
    return None


def get_skills_root_for_write(start_path: Optional[Path] = None) -> Path:
    for base in _candidate_roots(start_path):
        guided_dir = base / ".guided"
        if guided_dir.is_dir():
            return guided_dir / "skills"
    return ((start_path or Path.cwd()).resolve() / SKILLS_DIR).resolve()


def is_valid_skill_name(name: str) -> bool:
    return bool(VALID_SKILL_NAME.fullmatch(name))


def discover_skills(start_path: Optional[Path] = None) -> dict[str, MarkdownSkill]:
    skills_root = find_skills_root(start_path)
    if skills_root is None:
        return {}

    skills: dict[str, MarkdownSkill] = {}
    for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        skill_file = skill_dir / SKILL_FILE_NAME
        if not skill_file.is_file():
            continue
        skills[skill_dir.name] = MarkdownSkill(
            name=skill_dir.name,
            path=skill_file,
            content=skill_file.read_text().strip(),
        )
    return skills


def create_skill(
    name: str, description: str = "", start_path: Optional[Path] = None
) -> MarkdownSkill:
    skills_root = get_skills_root_for_write(start_path)
    skill_dir = skills_root / name
    skill_file = skill_dir / SKILL_FILE_NAME

    if skill_file.exists():
        raise FileExistsError(f"Skill '{name}' already exists.")

    skills_root.mkdir(parents=True, exist_ok=True)
    skill_dir.mkdir(parents=True, exist_ok=False)

    body = description.strip() or f"Describe the {name} workflow here."
    skill_file.write_text(f"# {name}\n\n{body}\n")

    return MarkdownSkill(
        name=name, path=skill_file, content=skill_file.read_text().strip()
    )


def remove_skill(name: str, start_path: Optional[Path] = None) -> Path:
    skills_root = find_skills_root(start_path)
    if skills_root is None:
        raise FileNotFoundError(f"Skill '{name}' not found.")

    skill_dir = skills_root / name
    skill_file = skill_dir / SKILL_FILE_NAME
    if not skill_file.is_file():
        raise FileNotFoundError(f"Skill '{name}' not found.")

    shutil.rmtree(skill_dir)
    return skill_dir
