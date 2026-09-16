"""The console scripts say exactly what the scripts they replace said.

The baseline is the hub's six scripts at `09b4894a`, copied byte for byte into
`tests/golden/scripts/`. Each case runs a baseline script and the console script
that replaces it in the same checkout, from the same working directory and with
the same environment, and holds stdout, stderr and the exit status equal. The
package's result is also held to the recording under `tests/golden/expected/`,
which is what a later release compares against once a message deliberately
moves; `BG_GOLDEN_RECORD=1` rewrites the recordings, in the commit that bumps the
version naming the change.

The checkouts are Poodl at `0a46a485` and the hub at `09b4894a`, the commits the
template's CONVENTIONS.md pins. `BG_GOLDEN_POODL` and `BG_GOLDEN_BISCUIT_GAMES`
name local clones to fetch from; GitHub is the fallback. Each fetch is one
commit deep.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import pytest

HERE = Path(__file__).resolve().parent
BASELINE = HERE / "golden" / "scripts"
EXPECTED = HERE / "golden" / "expected"
RECORD = os.environ.get("BG_GOLDEN_RECORD") == "1"

# Unresolved on purpose: the interpreter's own directory is the virtual
# environment's bin, which is where the console scripts are installed.
BIN = Path(sys.executable).parent

# The variable naming a local clone, the fallback URL, and the pinned commit.
CHECKOUTS = {
    "poodl": (
        "BG_GOLDEN_POODL",
        "https://github.com/steven-cutting/poodl",
        "0a46a485da4e85aed878df8dd47a0c738e7c87e2",
    ),
    "biscuit_games": (
        "BG_GOLDEN_BISCUIT_GAMES",
        "https://github.com/steven-cutting/biscuit_games",
        "09b4894a5d3328858d7dc52560422c127dff5399",
    ),
}


class Case(NamedTuple):
    """One case, named as its recording is."""

    name: str
    script: str
    console: str
    arguments: tuple[str, ...]


def _case(name: str, script: str, console: str, *arguments: str, network: bool = False) -> object:
    marks = [pytest.mark.network] if network else []
    return pytest.param(Case(name, script, console, arguments), marks=marks, id=name)


CASES = [
    _case("validate_docs", "validate_docs.py", "bg-validate-docs"),
    _case("validate_agents", "validate_agents.py", "bg-validate-agents"),
    _case("install_allium-check", "install_allium.py", "bg-install-allium", "--check"),
    _case("run_project_check-clean", "run_project_check.py", "bg-project-check", "clean"),
    _case("run_ripsecrets_redacted", "run_ripsecrets_redacted.py", "bg-ripsecrets"),
    _case("run_allium-check", "run_allium.py", "bg-run-allium", "check", network=True),
    _case("run_allium-analyse", "run_allium.py", "bg-run-allium", "analyse", network=True),
]


class Result(NamedTuple):
    stdout: str
    stderr: str
    returncode: int


def _environment() -> dict[str, str]:
    """One environment for both sides of every case.

    PATH is the virtual environment and the system directories alone, so a
    `ripsecrets` or an `allium` installed elsewhere on this machine cannot make a
    recording differ from the one CI makes. Git's own variables are dropped, in
    case a hook is what runs this.
    """
    inherited = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    return {
        **inherited,
        "PATH": os.pathsep.join((str(BIN), "/usr/bin", "/bin")),
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _git(cwd: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-c", "advice.detachedHead=false", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        env=_environment(),
    )


def _run(command: list[str], checkout: Path) -> Result:
    completed = subprocess.run(
        command,
        cwd=checkout,
        check=False,
        capture_output=True,
        text=True,
        env=_environment(),
    )
    return Result(completed.stdout, completed.stderr, completed.returncode)


def _fetch(name: str, destination: Path) -> Path:
    """The pinned commit, one deep, with the baseline scripts committed over its own."""
    variable, url, commit = CHECKOUTS[name]
    destination.mkdir(parents=True)
    _git(destination, "init", "-q", "-b", "golden")
    _git(destination, "fetch", "-q", "--depth", "1", os.environ.get(variable) or url, commit)
    _git(destination, "checkout", "-q", "FETCH_HEAD")
    # The baselines derive the root from their own location, so they run from
    # the checkout's scripts/. For the hub this copy changes nothing.
    for script in BASELINE.glob("*.py"):
        shutil.copyfile(script, destination / "scripts" / script.name)
    _git(destination, "add", "-A")
    _git(
        destination,
        "-c",
        "user.name=golden",
        "-c",
        "user.email=golden@example.invalid",
        "commit",
        "-q",
        "--allow-empty",
        "--no-verify",
        "-m",
        "The golden baseline",
    )
    return destination


@pytest.fixture(scope="session", params=sorted(CHECKOUTS))
def checkout(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> Path:
    name: str = request.param
    return _fetch(name, tmp_path_factory.mktemp("golden") / name)


def _in_module_order(output: str) -> str:
    """Allium's back-to-back JSON blocks sorted by module, and whatever follows them kept.

    allium walks `docs/specs/` in the order the filesystem lists it, which differs
    between macOS and Linux, so the blocks arrive in a different order on each.
    Both sides of a case run on one filesystem and agree; only the recording, made
    on one machine and read on another, needs an order of its own. The verdict
    `bg-run-allium` prints after the blocks does not depend on it.
    """
    decoder = json.JSONDecoder()
    blocks: list[tuple[str, str]] = []
    index = 0
    while True:
        start = len(output) - len(output[index:].lstrip())
        if start == len(output) or output[start] != "{":
            break
        value, index = decoder.raw_decode(output, start)
        blocks.append((str(value.get("spec_file")), output[start:index]))
    if not blocks:
        return output
    return "\n".join(text for _, text in sorted(blocks)) + output[index:]


def _recorded(result: Result, checkout: Path, case: Case) -> dict[str, object]:
    """The result as the recording holds it: this run's checkout path made neutral, and
    allium's blocks in module order."""
    where = str(checkout)
    stdout = result.stdout.replace(where, "<checkout>")
    if case.script == "run_allium.py":
        stdout = _in_module_order(stdout)
    return {
        "returncode": result.returncode,
        "stdout": stdout,
        "stderr": result.stderr.replace(where, "<checkout>"),
    }


@pytest.mark.parametrize("case", CASES)
def test_console_script_matches_the_baseline(
    request: pytest.FixtureRequest, checkout: Path, tmp_path: Path, case: Case
) -> None:
    where = checkout
    if request.node.get_closest_marker("network") is not None:
        # A copy of its own, so the binary installed here is never seen by the
        # `install_allium --check` case, which records an absent binary.
        where = tmp_path / checkout.name
        shutil.copytree(checkout, where, symlinks=True)
        installed = _run([str(BIN / "bg-install-allium")], where)
        assert installed.returncode == 0, installed.stdout + installed.stderr

    baseline = _run([sys.executable, f"scripts/{case.script}", *case.arguments], where)
    package = _run([str(BIN / case.console), *case.arguments], where)
    assert package == baseline

    recording = EXPECTED / checkout.name / f"{case.name}.json"
    observed = _recorded(package, where, case)
    if RECORD:
        recording.parent.mkdir(parents=True, exist_ok=True)
        recording.write_text(json.dumps(observed, indent=2) + "\n", encoding="utf-8")
    assert recording.is_file(), f"no recording at {recording}; run with BG_GOLDEN_RECORD=1"
    assert observed == json.loads(recording.read_text(encoding="utf-8"))
