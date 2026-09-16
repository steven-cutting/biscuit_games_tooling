# Changelog

All notable changes to this repository are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
releases follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) as
[the README](README.md) defines MAJOR, MINOR and PATCH for a caller of the workflows and
for a consumer of the package.

## [Unreleased]

## [0.2.0] - 2026-09-16

### Added

- The Python package `biscuit-games-tooling`, under `src/biscuit_games_tooling/`: the six
  scripts of Poodl and the hub, unchanged in what they say. Each is a console script,
  `bg-validate-docs`, `bg-validate-agents`, `bg-install-allium`, `bg-run-allium`,
  `bg-project-check` and `bg-ripsecrets`, and each finds the repository it checks with
  `git rev-parse --show-toplevel` rather than from its own location. The validators are
  the hub's; `bg-project-check` is Poodl's runner, whose usage line now names
  `bg-project-check`.
- `[tool.biscuit-games-tooling]` in a consumer's `pyproject.toml`: `recipes`, the gates
  `bg-project-check run` runs, defaulting to Poodl's eleven, and `predicates`, the names a
  page's `requires` may use, defaulting to none, each enabled only by the boolean `true`.
- `bg-validate-agents` no longer counts `scripts/validate_agents.py` in the agent inventory,
  so a repository that still carries that file passes as it did.
- `tests/test_golden.py`: on Poodl at `0a46a485` and the hub at `09b4894a`, each console
  script prints the same stdout and stderr and exits with the same status as the hub's
  script it replaces, and matches the recordings under `tests/golden/expected/`.
  `tests/test_project.py` covers what the golden checkouts cannot: a consumer's own table,
  and the root found from a subdirectory or refused outside Git.
- `just test` and `just test-network`, run by `just check` and by the CI job `check`, and
  ruff in the hook gate.

## [0.1.0] - 2026-09-15

### Added

- `.github/workflows/game-ci.yml`: the `frontend`, `documents` and `stories` jobs of the
  template's `ci.yml` at `v0.1.0`, running the same recipes in the same order, each taking
  its toolchain from the action below.
- `.github/workflows/game-chromatic.yml`: the `authorize` and `chromatic` jobs of the
  template's `chromatic.yml`, with `CHROMATIC_PROJECT_TOKEN` as an optional secret and
  `authorize` naming its own scopes, which leave out `packages`.
- `.github/workflows/game-pages.yml`: the `build` and `deploy` jobs of the template's
  `pages.yml`, with a required `base_path` input and optional `artifact_path` and `stage`
  inputs for a layout that stages a domain root; `deploy` names its two publishing scopes.
- `actions/setup-toolchain/action.yml`: a composite action defaulting to node 26, npm
  11.17.0, uv 0.11.18, Python 3.14, just 1.51.0 and the `@steven-cutting` scope, with every
  `uses:` pinned to a commit.
- This repository's own gate: `just check`, and a CI job `check` that runs the action from
  its checkout.

[Unreleased]: https://github.com/steven-cutting/biscuit_games_tooling/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/steven-cutting/biscuit_games_tooling/releases/tag/v0.2.0
[0.1.0]: https://github.com/steven-cutting/biscuit_games_tooling/releases/tag/v0.1.0
