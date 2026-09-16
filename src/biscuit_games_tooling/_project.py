"""Where the consuming repository is, and what its pyproject.toml asks of the tools.

Every console script runs from inside a consumer's worktree and takes the
repository root from Git rather than from its own location, because the
package is installed into a virtual environment, nowhere near the files it checks.
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

# Poodl's `RECIPES` tuple: what `bg-project-check run` executes, in order, before
# `check-clean`. A consumer with more gates lists them in its pyproject.toml.
DEFAULT_RECIPES = (
    "lock-check",
    "lint",
    "frontend-static",
    "frontend-coverage",
    "frontend-build",
    "storybook-build",
    "storybook-test",
    "check-docs",
    "check-agents",
    "check-specs",
    "analyse-specs",
)


def root() -> Path:
    """The top level of the Git worktree the current directory is inside."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        print("biscuit-games-tooling: run this from inside a Git worktree", file=sys.stderr)
        raise SystemExit(2)
    return Path(result.stdout.strip())


def settings(project_root: Path) -> dict[str, Any]:
    """The `[tool.biscuit-games-tooling]` table of the consumer's pyproject.toml, or {}."""
    manifest = project_root / "pyproject.toml"
    if not manifest.is_file():
        return {}
    with manifest.open("rb") as stream:
        return tomllib.load(stream).get("tool", {}).get("biscuit-games-tooling", {})


def recipes(project_root: Path) -> tuple[str, ...]:
    return tuple(settings(project_root).get("recipes", DEFAULT_RECIPES))


def predicates(project_root: Path) -> tuple[set[str], set[str]]:
    """Every predicate the consumer declares, and the subset it enables."""
    declared: dict[str, bool] = settings(project_root).get("predicates", {})
    return set(declared), {name for name, enabled in declared.items() if enabled}
