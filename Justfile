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

lint:
    uv run --frozen prek run --all-files

check: lock-check lint
