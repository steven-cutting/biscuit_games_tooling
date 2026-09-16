set positional-arguments := true
set shell := ["sh", "-eu", "-c"]

default:
    @just --list

sync:
    uv sync --frozen

lock:
    uv lock

lock-check:
    uv lock --check

install-hooks:
    git rev-parse --is-inside-work-tree >/dev/null
    uv run --frozen prek install --overwrite --hook-type=pre-commit

format:
    uv run --frozen ruff check --fix-only .
    uv run --frozen ruff format .

lint:
    uv run --frozen prek run --all-files

# The golden test without the two cases that download allium. It still fetches
# one commit of Poodl and one of the hub: from the local clones that
# BG_GOLDEN_POODL and BG_GOLDEN_BISCUIT_GAMES name, or else from GitHub.
test *args:
    uv run --frozen pytest "$@"

# Every golden case, the two allium cases included: each downloads the pinned
# binary into a copy of its checkout.
test-network *args:
    BG_TOOLING_NETWORK=1 uv run --frozen pytest "$@"

check: lock-check lint test
