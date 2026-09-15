# Changelog

All notable changes to this repository are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
releases follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) as
[the README](README.md) defines MAJOR, MINOR and PATCH for a caller.

## [Unreleased]

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

[Unreleased]: https://github.com/steven-cutting/biscuit_games_tooling/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/steven-cutting/biscuit_games_tooling/releases/tag/v0.1.0
