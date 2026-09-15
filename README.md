# biscuit_games_tooling

Reusable GitHub Actions workflows and a composite toolchain action for Biscuit Games
games. A game rendered from
[biscuit_games_template](https://github.com/steven-cutting/biscuit_games_template) keeps
three thin workflows that call the ones here, so a fix to a job or to the toolchain setup
is a release of this repository and a moved pin in the template, rather than the same
edit merged into every game's copy of every job.

## What it hosts

| Path | What it is |
| --- | --- |
| `.github/workflows/game-ci.yml` | The three gate jobs, `frontend`, `documents` and `stories`, called by a game's `ci.yml`. |
| `.github/workflows/game-chromatic.yml` | The `/chromatic` gate and the publish, called by a game's `chromatic.yml`. `CHROMATIC_PROJECT_TOKEN` is optional: without it the publish is skipped with a notice. |
| `.github/workflows/game-pages.yml` | The Pages build and deploy, called by a game's `pages.yml` with `base_path`, and with `stage` and `artifact_path` for a layout that stages a domain root around the build. |
| `actions/setup-toolchain/action.yml` | Node with the GitHub Packages registry for the `@steven-cutting` scope, uv with its cache, Python, `just` and npm, at pinned defaults. |

A reusable workflow runs only from `.github/workflows/` at the root of the repository that
hosts it, which is why these are not in the template, whose tree lives under `template/`.
Nothing here is secret: the registry token is the calling run's own `github.token`, and the
repository is public so that any game can call it without an access setting.

## Calling it

A game's three workflows, as the template ships them less their comments. `<sha>` is the
forty-character commit a release tag points at, and the comment names the tag.

Triggers, the workflow-level `permissions` and `concurrency` stay in the game. A called
workflow can narrow the caller's token and never widen it, so where a called job needs a
scope the workflow-level block lacks, the calling job carries the union of what its called
jobs hold.

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
  push:
    branches: ['main']
  workflow_dispatch:

permissions:
  contents: read
  packages: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  ci:
    uses: steven-cutting/biscuit_games_tooling/.github/workflows/game-ci.yml@<sha> # v0.1.0
```

`.github/workflows/chromatic.yml`:

```yaml
name: Chromatic

on:
  push:
    branches: ['main']
  issue_comment:
    types: [created]
  workflow_dispatch:

permissions:
  contents: read
  issues: write
  pull-requests: write

concurrency:
  group: chromatic-${{ github.event.issue.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'issue_comment' }}

jobs:
  chromatic:
    # The union of what the called jobs hold: the publish job also reads
    # the platform package.
    permissions:
      contents: read
      issues: write
      pull-requests: write
      packages: read
    uses: steven-cutting/biscuit_games_tooling/.github/workflows/game-chromatic.yml@<sha> # v0.1.0
    secrets:
      CHROMATIC_PROJECT_TOKEN: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
```

`.github/workflows/pages.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: ['main']
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  pages:
    # The union of what the called jobs hold: the build reads the platform
    # package, the deploy publishes.
    permissions:
      contents: read
      pages: write
      id-token: write
      packages: read
    uses: steven-cutting/biscuit_games_tooling/.github/workflows/game-pages.yml@<sha> # v0.1.0
    with:
      # A project site, built to live under the repository's name.
      base_path: /${{ github.event.repository.name }}
```

A check from a called workflow is named after the calling job and then the called job, so
the checks a game requires on `main` are `ci / frontend`, `ci / documents` and
`ci / stories`.

## Changing the action

The three workflows name the action by commit, never by a relative path: inside a called
workflow a relative `uses: ./actions/setup-toolchain` would resolve against the checkout
of the game that called it. A reference must name a commit that already exists, so every
change to the action is two commits, in this order:

1. The action alone.
2. The workflows moving their pin to the commit made in step 1.

This repository's own CI job, `check`, uses `./actions/setup-toolchain` from its checkout,
so the action under review runs on every push before any workflow pins it.

## Versions

Releases are annotated tags `vMAJOR.MINOR.PATCH` on `main`. A caller pins the commit a tag
points at, with the tag as a comment, exactly as actions are pinned:

```console
gh api repos/steven-cutting/biscuit_games_tooling/commits/v0.1.0 --jq .sha
```

- MAJOR when a caller must change: a job renamed, which renames a required check; an input
  or a secret made required; a scope a calling job must now grant.
- MINOR when the jobs or the action change and no caller needs an edit.
- PATCH for prose.

The action's defaults are the toolchain pins a game also carries: node 26 and npm 11.17.0
in `package.json`, rendered from the template's `template/package.json.jinja`, and Python
3.14 in `.python-version`, rendered from `template/.python-version`. Nothing checks the two
against each other any more, so a default changed in `action.yml` ships together with a
template release that moves the same pin and the callers' SHA in one change.

## Maintaining

| Recipe | Does |
| --- | --- |
| `just sync` | Installs `prek` from `uv.lock`. |
| `just check` | `lock-check`, then `lint`: what the CI job `check` runs. |
| `just lint` | The hook gate over every file: the builtin checks, markdownlint, typos, actionlint and ripsecrets. |
| `just install-hooks` | Installs the gate as the pre-commit hook. |
| `just lock` | Relocks `uv.lock`. |

`actionlint` reads only `.github/workflows/`, so `action.yml` is covered by `check-yaml`
and by the CI job that runs it. `actionlint` also hands a `run:` block to `shellcheck` only
when it finds `shellcheck` on its own `PATH`, which under `prek` it does not. The multi-line
blocks in `game-chromatic.yml` are therefore checked by extracting them and running
`shellcheck` over each by hand whenever one changes.
