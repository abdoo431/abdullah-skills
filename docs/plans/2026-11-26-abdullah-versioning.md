# abdullah-versioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `abdullah-versioning` and `setup-abdullah-versioning` skills in this repository, test them on a real project and a new one, and cut this repository's next release with them.

**Architecture:** Two skill folders under `skills/`. `abdullah-versioning` (model-invoked) holds the procedure, reference pages, templates, and one stdlib-Python CLI, `version.py`, built on small modules: SemVer, policy settings, changelog, version sources, git, the bump proposal, and the survey. `setup-abdullah-versioning` (user-invoked) is a thin entry point into the setup procedure that `abdullah-versioning` owns. The script edits files and reads git; the agent runs branches, commits, tags and every outward step.

**Tech Stack:** Python 3.10+ standard library only (`argparse`, `subprocess`, `re`, `json`, `dataclasses`, `unittest`), git, Markdown, the Agent Skills `SKILL.md` format, Claude Code plugin manifests, GitHub Actions.

**Spec:** [docs/design/2026-11-26-abdullah-versioning-design.md](../design/2026-11-26-abdullah-versioning-design.md). Section numbers below (§, V, C) refer to it.

## Global Constraints

- Python 3.10 or later, standard library only. `version.py` runs as `python <path>/version.py`, from any current directory, and inserts its own folder into `sys.path` to import its modules.
- Module names start with `ver_` so they never collide with `abdullah-docs`' `docs_*` modules when both folders are on `sys.path` in one test run. Skills share no files: helpers needed from `abdullah-docs` are copied.
- Cross-platform: Windows and Linux. Files are read as bytes and decoded as UTF-8; a leading BOM and each file's line endings are kept on write. Repository paths print with forward slashes.
- Exit codes: 0 done or clean, 1 refused or `error` findings, 2 usage error. Nothing is written on 1 or 2.
- Finding format, one per line: `path:line: severity: kind: message`; `line` is 1 when there is none.
- The script never runs `git fetch`, `git commit`, `git tag`, `git push`, `git merge` or `gh`. It only reads git.
- Writers change only the version text: every other byte of a source file, and every changelog line outside the moved or edited sections, is unchanged.
- Tags and the changelog use SemVer 2.0.0 (`0.2.0-rc.1`); Python sources use PEP 440 (`0.2.0rc1`, `0.2.0a1`, `0.2.0b1`, `0.2.0.dev0`) (C13).
- `-dev` never appears in a tag (C7). A version of `1.0.0` or higher for the first time needs `--first-major` (§9.1).
- `SKILL.md` front matter: `name` equals the folder name; `description` is a non-empty string; quote any value containing `: `. `setup-abdullah-versioning` has `disable-model-invocation: true` and, in `agents/openai.yaml`, `policy.allow_implicit_invocation: false`; `abdullah-versioning` has neither.
- Procedure text names no tool of one agent. A dependency on another skill reads: call the Skill tool with `<name>` (listed as `abdullah-skills:<name>` when installed as a plugin).
- All documentation in English. No path on the owner's machine, no private project name and no personal data in any committed file: the private project used in Task 13 is never named.
- Git: work on `feature/abdullah-versioning`, created from `docs/abdullah-versioning-design`. Conventional Commits, lower-case imperative summary, no trailing period, a `Refs:` line naming the design section and plan task, and the attribution line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A lock file with the old version elsewhere.** `package-lock.json` whose dependencies include a package at the same version string as the project (`"version": "0.1.0"` under `node_modules/some-lib`): only the two root entries change. Test in Task 4.
2. **CRLF, a BOM, odd spacing.** A `Directory.Build.props` with CRLF and a BOM, a `pyproject.toml` with `version="0.1.0"` (no spaces), and a `package.json` indented with tabs come back byte-identical except the version. Tests in Task 4.
3. **Stray tags.** A repository holding `v0.1.0`, `v0.2.0` and a non-version tag such as `plan1-pre-squash` reports `0.2.0`, ignores the stray tag, and does not call the tags non-SemVer. Test in Task 7.
4. **Changelog shapes.** `## Unreleased` without brackets, an empty subsection, a multi-line bullet, and no link references at all: the cut moves everything, keeps the multi-line bullet whole, and adds no links when the file had none. Tests in Task 3.
5. **No git, no tags, detached HEAD.** In a plain folder or a detached checkout, `status` and `survey` still report the sources and changelog, with one `warning: git` finding, and exit 0. Tests in Tasks 7 and 8.

---

## File Structure

```
skills/
├── abdullah-versioning/
│   ├── SKILL.md  agents/openai.yaml
│   ├── reference/setup.md  rules.md  layouts.md  hotfix.md  sources.md
│   ├── templates/releasing.md  agent-section.md
│   ├── scripts/ver_findings.py   findings and UTF-8 output (copied from docs_findings.py)
│   ├── scripts/ver_semver.py     Version: parse, order, bump, pre-releases, PEP 440
│   ├── scripts/ver_policy.py     the abdullah-versioning settings block
│   ├── scripts/ver_changelog.py  read and edit Keep a Changelog files
│   ├── scripts/ver_sources.py    read and write each version source type
│   ├── scripts/ver_git.py        read-only git: tags, branches, refs
│   ├── scripts/ver_plan.py       the next-version proposal
│   ├── scripts/ver_survey.py     survey (setup) and status
│   ├── scripts/version.py        the CLI
│   └── tests/fixtures.py  test_*.py
└── setup-abdullah-versioning/SKILL.md  agents/openai.yaml
```

Skill tests run with `python -m unittest discover -s skills/abdullah-versioning/tests -t skills/abdullah-versioning -v`. Each test module inserts `skills/abdullah-versioning/scripts` into `sys.path`.

---

### Task 1: Scaffold, findings and SemVer

**Files:**
- Create: `skills/abdullah-versioning/scripts/ver_findings.py`, `skills/abdullah-versioning/scripts/ver_semver.py`, `skills/abdullah-versioning/tests/__init__.py`
- Test: `skills/abdullah-versioning/tests/test_semver.py`

**Interfaces:**
- Produces:
  - `ver_findings`: the same API as `skills/abdullah-docs/scripts/docs_findings.py` (`Finding`, `warning`, `error`, `format_finding`, `exit_code`, `use_utf8_output`), copied.
  - `ver_semver.Version` (frozen dataclass): `major: int`, `minor: int`, `patch: int`, `pre: tuple = ()` (identifiers, ints for numeric ones: `("rc", 1)`, `("dev",)`). `Version.parse(text: str) -> Version` (raises `ValueError`; no leading `v`), `str(v)`, rich comparison by SemVer §11 precedence, `v.is_final -> bool`, `v.stage -> str | None` (`"alpha"`, `"beta"`, `"rc"`, `"dev"`, or the first identifier), `v.final -> Version` (pre dropped).
  - `bump(v: Version, part: str) -> Version` for `"major" | "minor" | "patch"`, always final.
  - `next_pre(target: Version, stage: str, existing: list[Version]) -> Version`: `target`'s `-stage.N`, N one more than the highest existing `stage` pre-release of `target`, else 1. Raises `ValueError` when an existing pre-release of `target` has a later stage (order `alpha < beta < rc`).
  - `to_pep440(v: Version) -> str` and `from_pep440(text: str) -> Version`.

- [ ] **Step 1: Write the failing tests** in `test_semver.py`:
  - `test_parse_and_format_round_trip`: `"1.2.3"`, `"0.2.0-rc.1"`, `"0.5.0-dev"`, `"1.0.0-alpha.10"` each give back the same string; `"1.2"`, `"v1.2.3"`, `"01.2.3"`, `"1.2.3-"` raise `ValueError`.
  - `test_precedence`: sorting `["0.2.0", "0.2.0-rc.2", "0.2.0-alpha.1", "0.2.0-beta.1", "0.2.0-rc.1", "0.2.0-alpha.2", "0.1.9"]` gives `0.1.9, 0.2.0-alpha.1, 0.2.0-alpha.2, 0.2.0-beta.1, 0.2.0-rc.1, 0.2.0-rc.2, 0.2.0`; `alpha.10 > alpha.2`; and `Version.parse("0.5.0-dev") > Version.parse("0.5.0-beta.1")` (the reason `-dev` is never tagged, §5.5).
  - `test_bump`: `0.3.0` minor → `0.4.0`, patch → `0.3.1`, `1.4.2` major → `2.0.0`; `0.4.0-dev` minor → `0.5.0`.
  - `test_next_pre`: no existing → `0.2.0-rc.1`; existing `[0.2.0-rc.1]` → `rc.2`; existing `[0.2.0-beta.3]` with stage `rc` → `rc.1`; existing `[0.2.0-rc.1]` with stage `beta` raises `ValueError`; pre-releases of another version are ignored.
  - `test_pep440`: `0.2.0-rc.1` ↔ `0.2.0rc1`, `0.2.0-alpha.1` ↔ `0.2.0a1`, `0.2.0-beta.2` ↔ `0.2.0b2`, `0.5.0-dev` ↔ `0.5.0.dev0`, `1.0.0` ↔ `1.0.0`; `from_pep440("0.2.0-rc.1")` (non-normalized) also gives `0.2.0-rc.1`.
- [ ] **Step 2: Run them to see them fail.** Run the skill test command. Expected: `ModuleNotFoundError: ver_semver`.
- [ ] **Step 3: Implement** `ver_findings.py` (copy) and `ver_semver.py` with the signatures above; ordering follows SemVer §11 (numeric identifiers compare numerically and sort below alphanumeric ones; a shorter identifier list sorts first when all shared ones are equal).
- [ ] **Step 4: Run the tests to see them pass.** Expected: OK.
- [ ] **Step 5: Commit** `feat: add semver parsing, ordering and pre-release numbering for the versioning script` with `Refs: design §5.1, §5.4, C13, plan task 1`.

---

### Task 2: Policy settings

**Files:**
- Create: `skills/abdullah-versioning/scripts/ver_policy.py`
- Test: `skills/abdullah-versioning/tests/test_policy.py`

**Interfaces:**
- Produces:
  - `BLOCK = "abdullah-versioning"`; `AGENT_SECTION_HEADING = "## Versioning (abdullah-versioning)"`; `POLICY_PLACES = ("docs/RELEASING.md", "RELEASING.md", "CONTRIBUTING.md", "docs/DOCUMENTATION.md")`.
  - `Settings` dataclass with the keys of §8 and their defaults: `layout: str | None = None`, `production = "main"`, `staging = "staging"`, `integration = "dev"`, `sources: list[str] = []`, `tag = "v{version}"`, `changelog = "CHANGELOG.md"`, `dev_suffix: str | None` (resolved: `"dev"` unless `layout == "main"`, then `None`; the value `none` gives `None`), `pre_releases: list[str] = ["rc"]` (`none` gives `[]`), `release_branch = "release/{version}"`, `hotfix_branch = "hotfix/{version}-{name}"`, `support_branch = "support/{major}.{minor}.x"`.
  - `find_policy(root: Path) -> Path | None`: the first of `POLICY_PLACES` that contains a fenced block opened by ```` ```abdullah-versioning ````.
  - `read_settings(policy: Path | None) -> Settings`; unknown keys are ignored; `layout` outside `dev-staging-main | dev-main | main` raises `ValueError`.

- [ ] **Step 1: Write the failing tests**:
  - `test_defaults_without_policy`: `read_settings(None)` gives the defaults above, `dev_suffix == "dev"`.
  - `test_reads_the_design_example`: the block of design §8 gives `layout="dev-staging-main"`, `sources=["Directory.Build.props", "src/web/package.json", "src/web/package-lock.json"]`, `pre_releases=["rc"]`, `support_branch="support/{major}.{minor}.x"`.
  - `test_main_layout_turns_dev_suffix_off`: `layout: main` and no `dev-suffix` gives `dev_suffix is None`; `layout: main` with `dev-suffix: dev` gives `"dev"`.
  - `test_find_policy_order`: with blocks in both `CONTRIBUTING.md` and `docs/RELEASING.md`, `docs/RELEASING.md` wins; a `CONTRIBUTING.md` without the block is skipped.
  - `test_bad_layout`: `layout: gitflow` raises `ValueError` naming the allowed values.
- [ ] **Step 2: Run them to see them fail.** Expected: `ModuleNotFoundError: ver_policy`.
- [ ] **Step 3: Implement `ver_policy.py`**, parsing the block line by line as `key: value` the way `docs_policy.read_settings` does.
- [ ] **Step 4: Run the tests to see them pass.**
- [ ] **Step 5: Commit** `feat: read the abdullah-versioning settings block` with `Refs: design §8, C8, plan task 2`.

---

### Task 3: Changelog

**Files:**
- Create: `skills/abdullah-versioning/scripts/ver_changelog.py`
- Test: `skills/abdullah-versioning/tests/test_changelog.py`

**Interfaces:**
- Consumes: `ver_semver.Version`.
- Produces (all functions take and return the full file text; the caller handles bytes, BOM and line endings through `read_text(path) -> tuple[str, str, bool]` and `write_text(path, text, newline, bom)`, also in this module):
  - `Section` dataclass: `title: str` (`"Unreleased"` or the version string), `version: Version | None`, `date: str | None`, `line: int` (1-based heading line), `entries: dict[str, list[str]]` (subsection → bullets; a bullet keeps its continuation lines).
  - `sections(text) -> list[Section]`. Unreleased headings: `## [Unreleased]`, `## Unreleased`, any case. Version headings: `## [X.Y.Z] - YYYY-MM-DD` or `## X.Y.Z - YYYY-MM-DD`, pre-releases included.
  - `unreleased(text) -> dict[str, list[str]]`.
  - `cut(text, version: Version, date: str, previous_tag: str | None, tag_format: str) -> str`: a new empty `## [Unreleased]` above `## [X.Y.Z] - date`, which receives the unreleased subsections. When the file has an `[Unreleased]:` link reference of the form `<base>/compare/<tag>...HEAD`, it becomes `<base>/compare/<new tag>...HEAD` and `[X.Y.Z]: <base>/compare/<previous tag>...<new tag>` is added below it (`<base>/releases/tag/<new tag>` when `previous_tag` is `None`). No link references in the file: none are added. Raises `ValueError("[Unreleased] has no entries to release")`.
  - `fold_unreleased_into(text, version: Version) -> str`: moves the unreleased entries into the existing `[version]` section, subsection by subsection in Keep a Changelog order; a no-op when unreleased is empty.
  - `set_date(text, version: Version, date: str) -> str`.
  - `section_body(text, version: Version) -> str`: the section's lines under its heading, for `notes`.
  - `insert_section(text, heading_and_body: str, version: Version) -> str`: places a whole section among the version sections in descending version order (for `carry`); raises `ValueError` if `[version]` is already present.
  - `problems(text) -> list[tuple[int, str]]`: no unreleased section; a version section twice; version sections not in descending version order.
  - `fold_candidates(text, version: Version) -> list[str]`: the `Fixed` bullets of `[version]` when the section also has `Added` (reported for the agent's fold, §7.3).

- [ ] **Step 1: Write the failing tests**, on small changelog strings:
  - `test_sections_and_unreleased`: a file with `## [Unreleased]` (`Added`: two bullets, the second spanning two lines), `## [0.1.0] - 2026-11-03` gives two sections, and `unreleased()["Added"][1]` holds both lines.
  - `test_cut_moves_entries_and_links`: cutting `0.2.0` on `2026-11-26` with `previous_tag="v0.1.0"` gives headings `## [Unreleased]`, `## [0.2.0] - 2026-11-26`, `## [0.1.0] - 2026-11-03` in that order, the entries under `[0.2.0]`, `[Unreleased]: https://github.com/o/r/compare/v0.2.0...HEAD` and `[0.2.0]: https://github.com/o/r/compare/v0.1.0...v0.2.0`.
  - `test_cut_without_links_adds_none` and `test_cut_unbracketed_heading`: `## Unreleased` works, and a file without link references gains none (Review Focus 4).
  - `test_cut_refuses_empty`: only empty subsection headings under unreleased raises `ValueError` with the message above.
  - `test_fold_into_open_section`: `[0.2.0]` has `Added: a`; unreleased has `Fixed: b`; folding gives `[0.2.0]` with `Added: a` then `Fixed: b`, and an empty unreleased.
  - `test_insert_section_by_version`: inserting `## [0.1.1] - 2026-12-01` into a file with `[0.2.0]` and `[0.1.0]` places it between them; inserting `[0.2.0]` again raises.
  - `test_problems`: a duplicate `[0.2.0]` and `[0.1.0]` above `[0.2.0]` each give one problem with its line.
  - `test_crlf_and_bom_round_trip`: `read_text`/`write_text` on a CRLF file with a BOM, after `set_date`, keeps CRLF and the BOM.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement `ver_changelog.py`.** Work on a list of lines; a section ends at the next `## ` heading or the first link reference line (`[label]: url`).
- [ ] **Step 4: Run the tests to see them pass.**
- [ ] **Step 5: Commit** `feat: read and edit keep a changelog files for releases` with `Refs: design §7.2, §7.3, §7.5.1, C12, C17, C23, plan task 3`.

---

### Task 4: Version sources

**Files:**
- Create: `skills/abdullah-versioning/scripts/ver_sources.py`
- Test: `skills/abdullah-versioning/tests/test_sources.py`

**Interfaces:**
- Consumes: `ver_semver` (`Version`, `to_pep440`, `from_pep440`).
- Produces:
  - `Source` dataclass: `spec: str`, `path: str` (repository-relative, forward slashes; `""` for `tag`), `kind: str`, `pattern: str | None`.
  - Kinds, chosen from the file name (§9.2): `msbuild` (`Directory.Build.props`, `*.csproj`, `*.fsproj`, `*.vbproj`), `pyproject`, `python` (`*.py`), `npm` (`package.json`), `npm-lock` (`package-lock.json`), `cargo` (`Cargo.toml`), `cargo-lock` (`Cargo.lock`), `json` (any other `*.json`), `plain` (`VERSION`), `regex` (`path#pattern`), `tag` (the word `tag`).
  - `parse_source(spec: str) -> Source`.
  - `read_raw(root: Path, src: Source) -> str | None` (the text as written) and `read_version(root, src) -> Version` (PEP 440 converted for `pyproject` and `python`; raises `ValueError` with the path when unreadable).
  - `write_version(root, src, v: Version) -> None`: replaces only the version text, keeping BOM and line endings. `msbuild` with `<VersionPrefix>`/`<VersionSuffix>` writes the prefix `X.Y.Z` and the suffix `rc.1` (empty element for a final). `npm-lock` changes the top-level `"version"` and the one under `"packages": { "": {`, nothing else. `cargo-lock` changes the `[[package]]` entry whose `name` is the `Cargo.toml` package name. `pyproject` writes under `[project]` or `[tool.poetry]`.
  - `discover(root: Path) -> list[Source]` for the survey: the file names above, depth 3 at most, skipping `.git`, `node_modules`, `bin`, `obj`, `target`, `.venv`, `venv`, `dist`, `build`; a `pyproject.toml` with `dynamic = ["version"]` gives `Source("tag", "", "tag", None)` instead; `*.csproj` without `<Version>` is not a source.
  - `assembly_info(root) -> list[str]`: paths of `AssemblyInfo.cs` files with `AssemblyVersion`, reported, never written.

- [ ] **Step 1: Write the failing tests**, one fixture file per kind under a temporary folder:
  - `test_read_each_kind`: `<Version>0.1.0</Version>` in `Directory.Build.props`; `version = "0.1.0"` under `[project]`; `__version__ = '0.2.0rc1'` (→ `0.2.0-rc.1`); `package.json`; `Cargo.toml`; `.claude-plugin/plugin.json`; `VERSION` with a trailing newline; `src/app.go#const Version = "(.*)"`.
  - `test_write_keeps_every_other_byte` (Review Focus 2): for each kind, write `0.2.0-rc.1` and compare bytes with the original where only the version text differs; the props file is CRLF with a BOM, `pyproject.toml` uses `version="0.1.0"`, `package.json` is tab-indented; the Python file gets `0.2.0rc1`.
  - `test_lock_file_changes_root_entries_only` (Review Focus 1): a `package-lock.json` with `node_modules/some-lib` also at `0.1.0`: after writing `0.2.0`, the top-level and `packages[""]` versions are `0.2.0` and `some-lib` stays `0.1.0`; the same for a `Cargo.lock` with a dependency at the old version.
  - `test_version_prefix_and_suffix`: `<VersionPrefix>0.1.0</VersionPrefix><VersionSuffix></VersionSuffix>` reads `0.1.0`; writing `0.2.0-rc.1` gives `0.2.0` and `rc.1`; writing `0.2.0` empties the suffix.
  - `test_discover`: a tree with `Directory.Build.props`, `src/web/package.json`, `src/web/package-lock.json`, `node_modules/x/package.json` and a `.csproj` without `<Version>` finds exactly the first three; a dynamic `pyproject.toml` gives the `tag` source.
  - `test_unreadable_source`: a `package.json` with no `"version"` raises `ValueError` naming the path.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement `ver_sources.py`.** Locate the version span with a kind-specific regex (for JSON, confirm the value with `json.loads` first), then splice the new text into the original bytes.
- [ ] **Step 4: Run the tests to see them pass.**
- [ ] **Step 5: Commit** `feat: read and write version sources for dotnet, python, node, rust and plain files` with `Refs: design §9.2, C13, plan task 4`.

---

### Task 5: Git helpers and the fixture repository

**Files:**
- Create: `skills/abdullah-versioning/scripts/ver_git.py`, `skills/abdullah-versioning/tests/fixtures.py`
- Test: `skills/abdullah-versioning/tests/test_git.py`

**Interfaces:**
- Consumes: `ver_semver.Version`.
- Produces:
  - `git(root, *args) -> str | None` and `is_repo(root) -> bool`, copied from `docs_git.py`.
  - `current_branch(root) -> str | None` (`None` when detached or not a repository).
  - `branches(root) -> list[str]`: local names plus remote names without `origin/`, unique, sorted.
  - `tag_versions(root, tag_format: str) -> list[tuple[str, Version]]`: tags matching the format (`{version}` stands for a SemVer string), sorted by version; other tags are skipped.
  - `all_tags(root) -> list[str]`.
  - `branches_containing(root, tag: str) -> list[str]`.
  - `show(root, ref: str, path: str) -> str | None` (`git show ref:path`).
  - `remote_url(root) -> str | None` (`origin`).
  - `fixtures.Repo`: the `abdullah-docs` fixture (copy) plus `tag(name: str)` (annotated, on `HEAD`) and `detach()`.

- [ ] **Step 1: Write the failing tests**:
  - `test_tag_versions_skips_other_tags`: tags `v0.1.0`, `v0.2.0`, `plan1-pre-squash`, `v0.3.0-rc.1` with format `v{version}` give `v0.1.0, v0.2.0, v0.3.0-rc.1` in order; with format `{version}` they give nothing.
  - `test_branches_and_current`: after `branch("dev")`, `branches()` holds `dev` and `main`, `current_branch()` is `dev`; after `detach()` it is `None`.
  - `test_branches_containing`: a tag made on `main` before `dev` branched is contained in both.
  - `test_not_a_repository`: in a plain folder, `is_repo` is false and every helper returns `None` or `[]`.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement `ver_git.py` and `fixtures.py`.**
- [ ] **Step 4: Run the tests to see them pass.**
- [ ] **Step 5: Commit** `feat: add read-only git helpers and a tagging fixture for the versioning script` with `Refs: design §6.3, §9, plan task 5`.

---

### Task 6: The next-version proposal

**Files:**
- Create: `skills/abdullah-versioning/scripts/ver_plan.py`
- Test: `skills/abdullah-versioning/tests/test_plan.py`

**Interfaces:**
- Consumes: `ver_semver` (`Version`, `bump`, `next_pre`).
- Produces:
  - `Proposal` dataclass: `current: Version | None`, `next: Version`, `part: str` (`"first" | "major" | "minor" | "patch"`), `reasons: list[str]` (`"<Subsection>: <first line of bullet>"`), `judgment: list[str]` (the `Changed` bullets), `pre: str | None`.
  - `propose(current: Version | None, entries: dict[str, list[str]], *, first: Version, pre: str | None = None, major: bool = False, existing: list[Version] = ()) -> Proposal`. Rules of §5.2: no current → `first`; before 1.0.0 any of `Added`, `Changed`, `Deprecated`, `Removed` → minor, else `Fixed`/`Security` only → patch, and `major=True` still gives minor; from 1.0.0 `Removed` or `major=True` → major, `Added`, `Deprecated` or `Changed` → minor, else patch. A subsection outside Keep a Changelog's six counts as minor and goes into `judgment`. With `pre`, `next` is `next_pre(final, pre, existing)`. Raises `ValueError("[Unreleased] has no entries to release")` when `entries` is empty.

- [ ] **Step 1: Write the failing tests**:
  - `test_first_release`: `current=None`, `first=0.1.0`, `Added` → `0.1.0`, part `first`; with `pre="rc"` → `0.1.0-rc.1`.
  - `test_before_1_0`: from `0.3.0`: `Added` → `0.4.0` minor with reason `"Added: workspace export"`; only `Fixed` → `0.3.1`; `Removed` → `0.4.0`; `major=True` → `0.4.0`.
  - `test_from_1_0`: from `1.4.2`: `Removed` → `2.0.0`; `Changed` → `1.5.0` with the bullet in `judgment`; `Changed` and `major=True` → `2.0.0`; `Security` only → `1.4.3`.
  - `test_pre_release_numbering`: from `0.3.0` with `Added`, `pre="rc"`, `existing=[0.4.0-rc.1]` → `0.4.0-rc.2`.
  - `test_empty_is_refused`: `{}` raises with the message above.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement `ver_plan.py`.**
- [ ] **Step 4: Run the tests to see them pass.**
- [ ] **Step 5: Commit** `feat: propose the next version and its reasons from unreleased entries` with `Refs: design §5.2, §5.3, C2, C3, plan task 6`.

---

### Task 7: Survey and status

**Files:**
- Create: `skills/abdullah-versioning/scripts/ver_survey.py`
- Test: `skills/abdullah-versioning/tests/test_survey.py`

**Interfaces:**
- Consumes: `ver_git`, `ver_sources`, `ver_changelog`, `ver_policy.Settings`, `ver_semver`, `ver_findings`.
- Produces:
  - `ROLE_NAMES = {"production": ("main", "master", "production", "release", "trunk"), "staging": ("staging", "stage", "uat", "preprod"), "integration": ("dev", "develop", "development")}`; `SUPPORT_PATTERNS = ("support/*", "maintenance/*", "release/*.x")`.
  - `Survey` dataclass: `git: bool`, `tags: list[str]` (version tags), `tag_format: str | None` (`v{version}`, `{version}` or `<prefix>{version}`), `stray_tags: list[str]`, `non_semver: bool` (version-like tags such as `2024.05` exist and no SemVer tag does), `sources: list[tuple[str, str | None]]` (spec, raw version), `changelog: str | None`, `has_unreleased: bool`, `released: list[str]`, `roles: dict[str, str | None]`, `support: list[str]`, `layout: str | None`, `verdict: str` (`"new" | "released" | "ambiguous"`), `current: str | None`, `stops: list[str]` (§6.3 step 3, one message each), `assembly_info: list[str]`, `findings: list[Finding]`. `to_json() -> str`.
  - `survey(root: Path) -> Survey`. Production is the role-named branch that contains the latest version tag; with no tags, the first existing name from `ROLE_NAMES["production"]` (C15). Layout: staging and integration present → `dev-staging-main`; integration only → `dev-main`; neither → `main`. Verdict `released` when a version tag or a released changelog section exists, `new` when neither does (template versions do not count, §5.3), `ambiguous` with a stop otherwise.
  - `Status` dataclass: `layout`, `branch: str | None`, `role: str | None` (`production | staging | integration | release | hotfix | support | work`), `latest: Version | None` (latest final tag; on a support branch, of its line), `declared: dict[str, str]`, `changelog_latest: str | None`, `agree: bool`, `due: str | None` (§5.6: `"patch: Security"`, `"patch: Fixed"`, `"minor when the milestone is finished: Added"`, or `None`), `findings: list[Finding]`.
  - `status(root: Path, settings: Settings) -> Status`.

- [ ] **Step 1: Write the failing tests** with `fixtures.Repo`:
  - `test_new_project`: `pyproject.toml` at `0.1.0`, a changelog with only `[Unreleased]`, no tags → verdict `new`, `current` `None`, layout `main`.
  - `test_released_dev_main_project`: tags `v0.1.0`, `v0.2.0` on `main`, branch `dev`, `Directory.Build.props` and `src/web/package.json` at `0.3.0-dev`, a stray tag `plan1-pre-squash` → verdict `released`, `current` `0.2.0`, layout `dev-main`, roles `production=main, integration=dev`, `stray_tags == ["plan1-pre-squash"]`, `non_semver` false (Review Focus 3).
  - `test_default_branch_is_not_production`: same repository with `refs/remotes/origin/HEAD` pointing at `dev`: production is still `main`.
  - `test_stops`: a file at `0.3.0` with the latest tag `v0.2.0` and no `-dev` gives a "disagree" stop; tags `2024.05` and `2024.06` only give a non-SemVer stop; released changelog sections without tags give a "no tags" stop; two `package.json` files at different versions in separate folders give a monorepo stop.
  - `test_master_and_support`: production named `master`, and a branch `support/0.1.x`, are found.
  - `test_status_due`: on `dev` with `Security` unreleased → `due == "patch: Security"`; only `Added` → the minor message; empty → `None`.
  - `test_plain_folder_and_detached` (Review Focus 5): no git → `git` false, sources still read, one `warning: git` finding; a detached checkout → `branch` `None`, `role` `None`, no exception.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement `ver_survey.py`.**
- [ ] **Step 4: Run the tests to see them pass.**
- [ ] **Step 5: Commit** `feat: survey a project's versions and report its release status` with `Refs: design §5.6, §6.3, §7.1, C15, plan task 7`.

---

### Task 8: `version.py`: the read-only commands

**Files:**
- Create: `skills/abdullah-versioning/scripts/version.py`
- Test: `skills/abdullah-versioning/tests/test_cli_read.py`

**Interfaces:**
- Consumes: every `ver_*` module.
- Produces: `main(argv: list[str] | None = None) -> int`, and the commands `survey [--json]`, `status [--json]`, `plan [--pre STAGE] [--major] [--json]`, `notes X.Y.Z`, `check`, each with `--root` (default `.`) and `--policy` (default `find_policy(root)`). Module docstring states commands, options and exit codes, shown by `--help`. Human output: one `key: value` line per fact, then findings. `plan` prints `next: 0.4.0`, `part: minor`, then `reason: Added: …` lines and `judge: Changed: …` lines. `check` findings use kinds `sources` (disagree), `role` (a declared version wrong for the branch role, per the table in Step 3), `changelog` (each of `ver_changelog.problems`), `git`.

- [ ] **Step 1: Write the failing tests**, calling `version.main([...])` with captured stdout:
  - `test_survey_json_shape`: on the `test_released_dev_main_project` fixture, `survey --json` parses and has keys `verdict`, `current`, `layout`, `roles`, `sources`, `stops`.
  - `test_plan_output`: from `v0.3.0` with `Added: workspace export` prints `next: 0.4.0`, `part: minor`, `reason: Added: workspace export`; exit 0. Empty unreleased: exit 1, message on stderr.
  - `test_notes`: prints exactly the `[0.2.0]` section body.
  - `test_check_roles`: on `dev` declaring `0.3.0-dev` after `v0.2.0` → exit 0; on `dev` declaring `0.2.0` → one `error: role` finding; sources at `0.3.0-dev` and `0.2.0` → one `error: sources`; a duplicate changelog section → one `error: changelog`.
  - `test_usage_errors`: an unknown command, or `notes 1.2`, exits 2.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement the read-only commands.** The role table for `check`:

  | Branch role | The declared version must be |
  |---|---|
  | integration | a `-<dev_suffix>` version above `latest` when `dev_suffix` is set; otherwise equal to `latest` |
  | staging | a pre-release of a version above `latest`, or a final above or equal to `latest` |
  | production | equal to `latest`, or a final above it (a warning: "untagged release") |
  | support | inside the branch's `X.Y` line, at or above its latest tag |
  | release, hotfix, work | any version; only agreement is checked |
- [ ] **Step 4: Run the tests to see them pass.**
- [ ] **Step 5: Commit** `feat: add the survey, status, plan, notes and check commands` with `Refs: design §9.1, plan task 8`.

---

### Task 9: `version.py`: the writing commands and refusals

**Files:**
- Modify: `skills/abdullah-versioning/scripts/version.py`
- Test: `skills/abdullah-versioning/tests/test_cli_write.py`

**Interfaces:**
- Consumes: Task 8's `main`.
- Produces: `prepare X.Y.Z [--pre STAGE] [--date YYYY-MM-DD] [--first-major] [--allow-long-lived]`, `declare VERSION [--date YYYY-MM-DD] [--first-major] [--allow-long-lived]`, `carry X.Y.Z --from REF`. `prepare` prints the paths it wrote and, under `fold:`, `ver_changelog.fold_candidates`. Every refusal prints `version.py: refused: <reason>` on stderr and exits 1 with no file changed.

- [ ] **Step 1: Write the failing tests**:
  - `test_prepare_final`: on `release/0.2.0` after `v0.1.0`, `prepare 0.2.0 --date 2026-11-26` cuts the changelog and writes `0.2.0` into every source.
  - `test_prepare_pre_release`: `prepare 0.2.0 --pre rc` declares `0.2.0-rc.1`, and a Python source gets `0.2.0rc1`.
  - `test_declare_folds_unreleased_into_open_section` (C17): after the cut with `--pre rc`, a new `Fixed` entry under unreleased; `declare 0.2.0-rc.2` moves it into `[0.2.0]`; `declare 0.2.0 --date 2026-12-01` sets the section's date and declares `0.2.0`.
  - `test_declare_dev_after_release`: `declare 0.3.0-dev` writes the sources only; the changelog is unchanged.
  - `test_refusals`, one subtest each, every one leaving all files byte-identical: `prepare 0.1.0` when `v0.1.0` exists (not greater); `prepare 0.2.0` with empty unreleased; sources that already disagree; `declare 0.2.0-beta.1` after `v0.2.0-rc.1` (stage back); `prepare 1.0.0` without `--first-major`; `declare` on `dev` without `--allow-long-lived`; `declare 0.2.1` on `support/0.1.x` (outside its line); `prepare 0.2.0 --pre dev` (`dev` is not a pre-release stage).
  - `test_hotfix_allowed_during_rc` (C19): with `v0.2.0` and `v0.3.0-rc.1`, `prepare 0.2.1` on `hotfix/0.2.1-x` succeeds.
  - `test_carry`: on `main`, `carry 0.1.1 --from support/0.1.x` inserts that branch's `[0.1.1]` section below `[0.2.0]`; carrying it twice is refused.
  - `test_tag_source_writes_nothing`: with `sources: tag`, `prepare 0.2.0` cuts the changelog and touches no other file.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement the writing commands.** Each command computes every new file text first, runs all checks, and writes only when all pass.
- [ ] **Step 4: Run the tests to see them pass.**
- [ ] **Step 5: Commit** `feat: add the prepare, declare and carry commands with their refusals` with `Refs: design §9.1, §7.5.1, C6, C17, C19, C21, plan task 9`.

---

### Task 10: The release flows end to end

**Files:**
- Test: `skills/abdullah-versioning/tests/test_flows.py`
- Modify: the `ver_*` modules and `version.py` only where a flow test fails.

**Interfaces:**
- Consumes: `fixtures.Repo`, `version.main`. The tests play the agent: they create branches, run commands, commit, merge and tag, exactly as §7 draws each flow.

- [ ] **Step 1: Write the failing tests**, each ending with `check` exiting 0 on every long-lived branch and tags in the expected places:
  - `test_dev_staging_main`: §7.2 for `0.2.0` with one `rc.2` fix: tags `v0.2.0-rc.1`, `v0.2.0-rc.2` on `staging`, `v0.2.0` on `main`; `dev` declares `0.3.0-dev` from the first back-merge on, and its unreleased holds only work added after the cut; no tag contains `-dev`.
  - `test_dev_main`: §7.3, the prior-art flow without pre-releases, then with `rc` on the open release branch.
  - `test_main_only`: §7.4 on a repository whose only source is `.claude-plugin/plugin.json`, with no `-dev` between releases.
  - `test_hotfix_with_back_merges`: §7.5 in `dev-staging-main` while `0.3.0-rc.1` is on `staging`: `v0.2.1` on `main`; after the back-merges `staging` still declares `0.3.0-rc.1` and `dev` its `-dev`.
  - `test_back_merge_conflict_resolution`: §7.6: the back-merge conflicts in a version file; taking either side, `declare <receiving version> --allow-long-lived` and `check` resolve it.
  - `test_support_line`: §7.5.1: `support/0.1.x` from `v0.1.0` after `v0.2.0`; `v0.1.1` on the support branch; `carry` on `main` lists `[0.1.1]` below `[0.2.0]`.
- [ ] **Step 2: Run them, and fix each failure in the module responsible.**
- [ ] **Step 3: Run the whole skill suite.** Expected: OK.
- [ ] **Step 4: Commit** `test: run each release flow end to end` with `Refs: design §7, plan task 10`.

---

### Task 11: The skill content

**Files:**
- Create: `skills/abdullah-versioning/SKILL.md`, `skills/abdullah-versioning/agents/openai.yaml`, `skills/abdullah-versioning/reference/{setup,rules,layouts,hotfix,sources}.md`, `skills/abdullah-versioning/templates/{releasing,agent-section}.md`, `skills/setup-abdullah-versioning/SKILL.md`, `skills/setup-abdullah-versioning/agents/openai.yaml`
- Modify: `tests/test_skill_content.py`

**Interfaces:**
- Consumes: the commands and options of Tasks 8 and 9, named exactly.
- Produces:
  - `abdullah-versioning/SKILL.md` front matter: `name: abdullah-versioning`; `description: "Own a project's version number and releases in any language: propose the next version and which part goes up from the changelog, keep every declared version in agreement, cut releases, pre-releases and hotfixes on the project's branch layout, and say when a release is due. Use when a release, version, tag, pre-release or hotfix is asked for, after a pull request merges into the integration branch, and before changing a version file or the changelog's version sections."` Body under 200 lines: the rules that always apply (§2 anti-goals, §6.2 outward steps), step 0 (§6.1), the task table (§6.2), running the script (commands, exit codes, finding format, the Python fallback), and the release suggestion (§5.6).
  - `reference/rules.md` = §5; `layouts.md` = §7.1–§7.4, §7.6, §7.7; `hotfix.md` = §7.5, §7.5.1; `sources.md` = §9.2 and the setup's source decisions; `setup.md` = §6.3 steps 1–7.
  - `templates/releasing.md`: the policy for a new project, a fill-in of §5 and one layout section of §7, with the settings block of §8. `templates/agent-section.md`: the section of §6.4, verbatim, starting with the heading.
  - `setup-abdullah-versioning/SKILL.md`: `disable-model-invocation: true`; three steps like `setup-abdullah-docs/SKILL.md`, pointing to `reference/setup.md` and "Re-running the setup".
  - `agents/openai.yaml`: `display_name: "Abdullah Versioning"`, `short_description: "Version numbers and releases"`; the setup's `display_name: "Setup Abdullah Versioning"`, `short_description: "Set up a project for abdullah-versioning"`, `policy: allow_implicit_invocation: false`.

- [ ] **Step 1: Write the failing tests** in `tests/test_skill_content.py`, mirroring the existing ones for the docs skills:
  - `test_versioning_front_matter`, `test_setup_versioning_is_user_invoked_only`, `test_versioning_skill_is_model_invoked`.
  - `test_versioning_links_resolve` and `test_versioning_names_no_single_agent_tool` over both new folders.
  - `test_versioning_skill_stays_short`: under 200 lines.
  - `test_versioning_agent_section_matches_design`: `templates/agent-section.md` starts with `## Versioning (abdullah-versioning)` and holds the three bullets of §6.4.
  - `test_releasing_template_block_parses`: the block in `templates/releasing.md` reads with `ver_policy.read_settings` without error and names a layout.
  - `test_reference_commands_exist`: every `version.py <command>` mentioned in the skill's Markdown is one of the commands `version.py --help` lists.
- [ ] **Step 2: Run the repository tests to see them fail.**
- [ ] **Step 3: Write the content.**
- [ ] **Step 4: Run `python scripts/check_frontmatter.py --root .` and the repository tests.** Expected: both pass.
- [ ] **Step 5: Commit** `feat: add the abdullah-versioning and setup-abdullah-versioning skills` with `Refs: design §5, §6, §7, §8, plan task 11`.

---

### Task 12: Repository integration

**Files:**
- Modify: `README.md`, `.claude-plugin/plugin.json`, `docs/README.md`, `CLAUDE.md`, `AGENTS.md`, `CHANGELOG.md`, `.github/workflows/check.yml`, `skills/abdullah-docs/reference/changelog.md`, `docs/DOCUMENTATION.md` (the `examples` setting)
- Create: `docs/abdullah-versioning.md`, `docs/setup-abdullah-versioning.md`

- [ ] **Step 1: Make the edits** (§11):
  - `README.md`: `abdullah-versioning` under model-invoked and `setup-abdullah-versioning` under user-invoked, each linked to its `SKILL.md`, with one line on the problem it fixes; the "After installing" text also names `/setup-abdullah-versioning`. Change the install wording only in `.agents/install-block.md` and copy it, if it changes at all.
  - `plugin.json`: both skills in `skills`; `description` drops "and, next, versioning" for "documentation and versioning"; add `"versioning"` and `"releases"` to `keywords`. The version is not bumped here (Task 15 does).
  - `docs/abdullah-versioning.md` and `docs/setup-abdullah-versioning.md` from `.agents/writing-docs.md`; a row each in `docs/README.md`.
  - `CLAUDE.md` and `AGENTS.md`, identically: the two skills in the skills table and layout; the new test command in "Checks".
  - `.github/workflows/check.yml`: a step `Versioning skill tests` running the skill test command.
  - `CHANGELOG.md`: under `[Unreleased]` `### Added`, one line per skill.
  - `skills/abdullah-docs/reference/changelog.md`: in "After a merge from the base branch", add staging-fix branches to where `--release` applies (§10).
  - `docs/DOCUMENTATION.md`: add `docs/abdullah-versioning.md, docs/setup-abdullah-versioning.md` to `examples`.
- [ ] **Step 2: Run every check in `CLAUDE.md`** ("Checks"), plus the new skill test command, then `claude plugin validate .claude-plugin/marketplace.json --strict` and `claude plugin validate .`. Expected: all pass; the second validation's only warning is the CLAUDE.md one, plus `ICON_MISSING` in the directory checks.
- [ ] **Step 3: Commit** `docs: list the versioning skills and run their tests in ci` with `Refs: design §11, plan task 12`.

---

### Task 13: Acceptance on a real project (read-only)

The owner's earlier private project is on the owner's machine (the path is given in the session, never committed): `dev-main`, `Directory.Build.props` plus `src/web/package.json` and its lock file, seven tags from `v0.1.0` to `v0.7.0`, and a stray non-version tag.

- [ ] **Step 1: Run `survey --json` and `status`** with `--root <that project>`, on a checkout of its `dev` branch. Expected: verdict `released`, `current` `0.7.0`, layout `dev-main`, production `main` (although its default branch is `dev`), the three sources, the stray tag ignored, no stops.
- [ ] **Step 2: Run `plan`** on its current `[Unreleased]`. Show the proposal and its reasons to the owner; record whether they agree.
- [ ] **Step 3: Run `check`.** Show every finding to the owner. A false finding is a bug: fix it with a regression test in this repository, then re-run.
- [ ] **Step 4: Confirm nothing in that project changed**: `git -C <that project> status --porcelain` is empty and its tags are unchanged.

No commit unless Step 3 found a bug; then `fix: <what>` with `Refs: design §12, plan task 13`.

---

### Task 14: Acceptance on a new project

- [ ] **Step 1: Create a sample project** in the session's scratch folder (outside this repository): `git init`, a `pyproject.toml` at `0.1.0`, a `CHANGELOG.md` with two `Added` entries, no remote.
- [ ] **Step 2: Run the setup** as `setup-abdullah-versioning` would: the survey says `new`; drafts for `docs/RELEASING.md` (layout `dev-staging-main`) and the agent section are shown before writing; branches `dev` and `staging` are created.
- [ ] **Step 3: Release `0.1.0`** through §7.2: `0.1.0-rc.1` tagged on `staging`, `dev` at `0.2.0.dev0` in `pyproject.toml`, then `v0.1.0` on `main`. Every step that would leave the machine is shown as a command and not run (there is no remote).
- [ ] **Step 4: Run `check`** on `dev`, `staging` and `main`. Expected: exit 0 on each. Report the run to the owner. No commit in this repository unless a bug was found (as in Task 13).

---

### Task 15: This repository on the skill, and its release

- [ ] **Step 1: Set up this repository** with the skill, showing the drafts to the owner first: `docs/RELEASING.md` (layout `main`, source `.claude-plugin/plugin.json`, tag `v{version}`, no `-dev`), the `## Versioning (abdullah-versioning)` section in `CLAUDE.md` and `AGENTS.md`, and their "Releases" section pointing to the skill and `docs/RELEASING.md`. Add `docs/RELEASING.md` to `docs/README.md`.
- [ ] **Step 2: Run every check in `CLAUDE.md`.** Commit `docs: release this repository with abdullah-versioning` with `Refs: design §11, plan task 15`.
- [ ] **Step 3: Open the pull request** for `feature/abdullah-versioning` into `main` after the owner approves (outward step); merge after their review.
- [ ] **Step 4: Cut the release with the skill:** `plan` (expected `0.2.0`, minor, because of the two `Added` entries), the owner approves, `release/0.2.0` from `main`, `prepare 0.2.0`, pull request, merge, then the tag `v0.2.0` and a GitHub Release from `notes 0.2.0`, each outward step after the owner's approval.
- [ ] **Step 5: Confirm a managed install updates:** `claude plugin marketplace update abdullah` and `claude plugin list` show `abdullah-skills@abdullah` at `0.2.0`, and both new skills load.
