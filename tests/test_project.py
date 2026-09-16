"""What `[tool.biscuit-games-tooling]` asks of the tools, and where the root is.

The golden test runs on checkouts that carry no such table, so it proves only the
defaults. These cases prove a consumer's table is what the scripts read.
"""

from __future__ import annotations

import contextlib
import subprocess
from typing import TYPE_CHECKING

import pytest

from biscuit_games_tooling import _project

if TYPE_CHECKING:
    from pathlib import Path


def test_defaults_without_a_table(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "game"\n', encoding="utf-8")
    assert _project.recipes(tmp_path) == _project.DEFAULT_RECIPES
    assert _project.predicates(tmp_path) == (set(), set())


def test_defaults_without_a_manifest(tmp_path: Path) -> None:
    assert _project.recipes(tmp_path) == _project.DEFAULT_RECIPES
    assert _project.predicates(tmp_path) == (set(), set())


def test_a_consumer_table_is_read(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.biscuit-games-tooling]\n"
        'recipes = ["lint", "package-build"]\n'
        "predicates = { online = true, daily = false }\n",
        encoding="utf-8",
    )
    assert _project.recipes(tmp_path) == ("lint", "package-build")
    assert _project.predicates(tmp_path) == ({"online", "daily"}, {"online"})


def test_root_is_the_worktree_top_from_a_subdirectory(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    nested = tmp_path / "docs" / "specs"
    nested.mkdir(parents=True)
    with contextlib.chdir(nested):
        assert _project.root() == tmp_path.resolve()


def test_root_refuses_a_directory_outside_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Stop Git's discovery at tmp_path, so an enclosing repository cannot answer.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    with contextlib.chdir(tmp_path), pytest.raises(SystemExit) as stop:
        _project.root()
    assert stop.value.code == 2
    assert "run this from inside a Git worktree" in capsys.readouterr().err
