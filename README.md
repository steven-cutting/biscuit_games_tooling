# biscuit_games_tooling

Reusable GitHub Actions workflows, a composite toolchain action and a Python package of
checkers for Biscuit Games repositories. A game rendered from
[biscuit_games_template](https://github.com/steven-cutting/biscuit_games_template) keeps
three thin workflows that call the ones here, and runs its documentation, agent and
specification gates through the package's console scripts. A fix to a job, to the
toolchain setup or to a checker is then a release of this repository and a moved pin,
rather than the same edit merged into every game's copy.

## What it hosts

| Path | What it is |
| --- | --- |
| `.github/workflows/game-ci.yml` | The three gate jobs, `frontend`, `documents` and `stories`, called by a game's `ci.yml`. |
| `.github/workflows/game-chromatic.yml` | The `/chromatic` gate and the publish, called by a game's `chromatic.yml`. `CHROMATIC_PROJECT_TOKEN` is optional: without it the publish is skipped with a notice. |
| `.github/workflows/game-pages.yml` | The Pages build and deploy, called by a game's `pages.yml` with `base_path`, and with `stage` and `artifact_path` for a layout that stages a domain root around the build. |
| `actions/setup-toolchain/action.yml` | Node with the GitHub Packages registry for the `@steven-cutting` scope, uv with its cache, Python, `just` and npm, at pinned defaults. |
| `src/biscuit_games_tooling/` | The Python package `biscuit-games-tooling`: six console scripts a repository's hooks and recipes run. See [The package](#the-package). |

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

## The package

`biscuit-games-tooling` holds the checkers every Biscuit Games repository runs. Poodl,
the hub and the template each carried a copy of the same six scripts under `scripts/`, so
a fix reached a game only as a merge `copier update` made into a file the game may have
edited. As a package, the fix is a release here and a one-line pin bump there, and
`just lock-check` proves the pin.

| Console script | Was | Does |
| --- | --- | --- |
| `bg-validate-docs` | `scripts/validate_docs.py` | The documentation contract: `docs/manifest.yml` against every page's frontmatter, links and anchors, reachability from `docs/README.md`, and no unfinished or placeholder prose. |
| `bg-validate-agents` | `scripts/validate_agents.py` | The agent contract: the inventory under `.agents/`, `.claude/` and `.codex/`, the byte-pinned adapters, the skill bridges and the phrases `AGENTS.md` must carry. |
| `bg-install-allium` | `scripts/install_allium.py` | Installs the pinned, checksummed `allium` into `.tools/bin`; `--check` reports whether it is there. |
| `bg-run-allium` | `scripts/run_allium.py` | `check` or `analyse` over `docs/specs/`, passing only when every module reports empty `diagnostics` and `findings` arrays. |
| `bg-project-check` | `scripts/run_project_check.py` | `run`: every recipe of the gate in order, failing if one changes the worktree. `clean [baseline]`: the worktree matches the baseline, or Git reports it clean. |
| `bg-ripsecrets` | `scripts/run_ripsecrets_redacted.py` | Runs `ripsecrets` with its output suppressed, so a matched credential never reaches a log. |

Five of the scripts find the repository they check with `git rev-parse --show-toplevel`,
from the directory they run in, because an installed package sits in a virtual
environment, nowhere near that repository. Run one from inside the worktree, which is what
`uv run` from a hook or a recipe does; outside a Git worktree it exits 2. A render that has
not yet run `git init` resolves to whatever repository encloses it. `bg-ripsecrets` has no
root, as the script it replaces had none: it hands its arguments to `ripsecrets` unchanged,
and those are the paths prek passes, relative to the directory the hook runs in, so moving
to another directory would break them.

### Consuming it

The package is a git dependency, pinned to a release tag in the development group. The
lockfile records the commit behind the tag, and `uv lock --check` fails when the tag in
`pyproject.toml` changes without a relock:

```toml
[dependency-groups]
dev = [
  "biscuit-games-tooling @ git+https://github.com/steven-cutting/biscuit_games_tooling@v0.2.0",
  "prek==0.4.12",
  "ruff==0.16.2",
]

[tool.biscuit-games-tooling]
recipes = [
  "lock-check", "lint", "frontend-static", "frontend-coverage", "frontend-build",
  "storybook-build", "storybook-test", "check-docs", "check-agents", "check-specs",
  "analyse-specs",
]
predicates = {}
```

Hooks and recipes call the scripts through the project environment, for example
`uv run --frozen bg-validate-docs`. The first `uv lock` needs GitHub reachable. The
repository is public, so no credential is involved. A tag is never moved: a consumer's
`uv.lock` keeps the commit it resolved, and only
`uv lock --upgrade-package biscuit-games-tooling` would re-read a moved tag.

### Configuration

The two things that differ between consumers live in the consumer's `pyproject.toml`,
under `[tool.biscuit-games-tooling]`. Both keys are optional.

| Key | Type | Default | Read by |
| --- | --- | --- | --- |
| `recipes` | list of `just` recipe names | Poodl's eleven: `lock-check`, `lint`, `frontend-static`, `frontend-coverage`, `frontend-build`, `storybook-build`, `storybook-test`, `check-docs`, `check-agents`, `check-specs`, `analyse-specs` | `bg-project-check run`, which runs them in order and then `check-clean`. The hub adds `package-build` and `package-check` after `frontend-build`. |
| `predicates` | table of name to boolean | `{}` | `bg-validate-docs`. A page's `requires` may name only a declared predicate, and only one set to the boolean `true` lets the page pass: any other value, `"true"` included, leaves it disabled. |

### Moving the Allium pin

`install_allium.py` holds the version and the SHA-256 of each supported artefact. Upstream
publishes no checksums for these files, because its `SHA256SUMS.txt` covers only the editor
extension and the language server. So all four have to be recomputed by hand:

```console
V=3.6.1
for t in aarch64-apple-darwin x86_64-apple-darwin \
         aarch64-unknown-linux-gnu x86_64-unknown-linux-gnu; do
  printf '%s  ' "$t"
  curl -sL "https://github.com/juxt/allium-tools/releases/download/v$V/allium-$t.tar.gz" \
    | shasum -a 256 | awk '{print $1}'
done
```

Replace `VERSION` and all four entries in `CHECKSUMS`. A moved version can change what the
checker reports, in either direction, so the move is a MAJOR release (see below), and a
consumer runs `just install-allium`, `just check-specs` and `just analyse-specs` on the
commit that takes it.

### The golden test

`tests/test_golden.py` proves the console scripts say exactly what the scripts they replace
said. The baseline is the hub's six scripts at `09b4894a`, kept byte for byte under
`tests/golden/scripts/`. For Poodl at `0a46a485` and the hub at `09b4894a`, each fetched one
commit deep, every case runs the baseline script and the console script from the same
directory with the same environment and holds stdout, stderr and the exit status equal.
The package's result must also equal the recording under `tests/golden/expected/`.

Five cases run under `just test`. Two more, `bg-run-allium check` and `analyse`, download
`allium` and run under `just test-network`. `BG_GOLDEN_POODL` and
`BG_GOLDEN_BISCUIT_GAMES` name local clones to fetch from instead of GitHub. The run's
`PATH` is the virtual environment and the system directories alone, so neither side finds
a `ripsecrets` installed elsewhere: that case compares the two "unavailable" exits.

A release that changes what a script says on purpose re-records with `BG_GOLDEN_RECORD=1`,
in the commit that bumps the version naming the change.

## Versions

Releases are annotated tags `vMAJOR.MINOR.PATCH` on `main`, and the workflows, the action
and the package share one series: a release of either is a release of the repository, and a
tag names both. The package's first release is `0.2.0` because the workflows were `v0.1.0`
first.

A workflow caller pins the commit a tag points at, with the tag as a comment, exactly as
actions are pinned:

```console
gh api repos/steven-cutting/biscuit_games_tooling/commits/v0.1.0 --jq .sha
```

A package consumer pins the tag itself in `pyproject.toml`, and `uv.lock` records the
commit.

For a caller of the workflows:

- MAJOR when a caller must change: a job renamed, which renames a required check; an input
  or a secret made required; a scope a calling job must now grant.
- MINOR when the jobs or the action change and no caller needs an edit.
- PATCH for prose.

For a consumer of the package:

| Change | Level |
| --- | --- |
| A tree that passed now fails: an error added, a rule tightened, a phrase added to `REQUIRED_GUIDANCE`, an inventory rule changed | Major |
| A console script, a configuration key or a recipe name the runner expects removed or renamed | Major |
| The allium `VERSION` moved: what the checker reports can move in both directions | Major |
| A check added behind a configuration key whose default keeps today's verdicts | Minor |
| A console script or a configuration key added, with today's behaviour as the default | Minor |
| A message reworded with the verdict and the exit status kept, or a comment | Patch |

A release takes the highest level either side calls for.

The action's defaults are the toolchain pins a game also carries: node 26 and npm 11.17.0
in `package.json`, rendered from the template's `template/package.json.jinja`, and Python
3.14 in `.python-version`, rendered from `template/.python-version`. Nothing checks the two
against each other any more, so a default changed in `action.yml` ships together with a
template release that moves the same pin and the callers' SHA in one change.

## Maintaining

| Recipe | Does |
| --- | --- |
| `just sync` | Installs the package, editable, with `prek`, `pytest` and `ruff`, from `uv.lock`. |
| `just check` | `lock-check`, `lint`, then `test`: what the CI job `check` runs before `test-network`. |
| `just lint` | The hook gate over every file: ruff, the builtin checks, markdownlint, typos, actionlint and ripsecrets. |
| `just test` | The golden test's five offline cases on both checkouts, and `tests/test_project.py` on the configuration table and the root. |
| `just test-network` | Every golden case, the two that download `allium` included. |
| `just format` | Applies ruff's fixes and formatting. |
| `just install-hooks` | Installs the gate as the pre-commit hook. |
| `just lock` | Relocks `uv.lock`. |

`actionlint` reads only `.github/workflows/`, so `action.yml` is covered by `check-yaml`
and by the CI job that runs it. `actionlint` also hands a `run:` block to `shellcheck` only
when it finds `shellcheck` on its own `PATH`, which under `prek` it does not. The multi-line
blocks in `game-chromatic.yml` are therefore checked by extracting them and running
`shellcheck` over each by hand whenever one changes.
