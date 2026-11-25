# abdullah-docs v0.1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish the `abdullah-docs` and `setup-abdullah-docs` agent skills in the public repository `abdoo431/abdullah-skills`, installable in Claude Code, Codex and any Agent Skills agent.

**Architecture:** Two skill folders under `skills/`. `abdullah-docs` (model-invoked) holds the procedure, the default policy, templates and three stdlib-Python CLI scripts built on five small shared modules. `setup-abdullah-docs` (user-invoked) is a thin entry point into the setup procedure that `abdullah-docs` owns. The repository root carries the plugin manifests, the install wording, human-facing docs pages, maintainer scripts and a GitHub Actions check.

**Tech Stack:** Python 3.10+ standard library only (`argparse`, `subprocess`, `re`, `fnmatch`, `dataclasses`, `unittest`), git, Markdown, the Agent Skills `SKILL.md` format, Claude Code plugin manifests, GitHub Actions.

**Reviews:** every task's review, and the final whole-branch review, run on Claude Fable 5.2 (`claude-fable-5-2`) as an advisor, each in a fresh context. The implementer acts on its findings or records why not.

**Spec:** [docs/design/2026-11-25-abdullah-docs-design.md](../design/2026-11-25-abdullah-docs-design.md). Section numbers below (§, D, C) refer to it.

## Global Constraints

- Python 3.10 or later, standard library only. Every script runs as `python <path>/script.py`, works from any current directory, and finds sibling modules and templates relative to its own file (`Path(__file__).resolve().parent`), inserting that directory into `sys.path` itself.
- Cross-platform: Windows and Linux. Read text as UTF-8 with `errors="replace"`, accept `\r\n` and `\n`, and print repository paths with forward slashes.
- Script exit codes: 0 clean, 1 findings of severity `error`, 2 usage error. Warnings never change the exit code.
- Finding format, one per line: `path:line: severity: kind: message`, with `severity` either `error` or `warning`, and `line` 1 when a finding has no line.
- Checks never modify files. Only `new_adr.py` writes: the new ADR and its index row. Scripts never run `git fetch`.
- All documentation in English. No paths on the owner's machine, no private project names, no personal data in any committed file.
- `SKILL.md` front matter: `name` equals the folder name; `description` is a non-empty string; quote any value containing `: `.
- `setup-abdullah-docs` has `disable-model-invocation: true` and, in `agents/openai.yaml`, `policy.allow_implicit_invocation: false`. `abdullah-docs` has neither.
- Procedure text names no tool of one agent. A dependency on another skill reads: call the Skill tool with `<name>`.
- No symlinks committed inside the repository.
- The repository: `abdoo431/abdullah-skills`, public, MIT. Plugin name `abdullah-skills`, marketplace name `abdullah`, one version in `.claude-plugin/plugin.json`, first release `v0.1.0`.
- Git in this repository: work on `feature/abdullah-docs-v1`; Conventional Commits (`feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`), lower-case imperative summary, no trailing period, and a `Refs:` line naming the design section or task. `main` is created at publication (Task 12).
- Execute this plan in an agent session whose working directory is this repository's working copy. Another project's git hooks must not govern this repository.

## Review Focus

1. **CRLF files.** A Markdown file saved with Windows line endings gives the same findings, with the same line numbers, as its LF copy. Test in Task 2.
2. **Unusual link syntax.** `[a](<docs/my file.md>)`, `[a](docs/x.md "Title")`, `[a](docs/my%20file.md)` and reference-style `[a]: docs/x.md` resolve to the right file; links inside fenced or inline code are ignored. Tests in Task 2.
3. **No git, no remote, unfetched base.** In a plain folder, or a repository whose `origin/main` does not exist, every script still checks local files and prints one `warning: base` finding instead of failing. Tests in Tasks 3, 4 and 5.
4. **Changelog heading variants.** `## [Unreleased]`, `## Unreleased` and `## [unreleased]` are all the unreleased section; a changelog with none of them is one error, not a crash. Test in Task 6.
5. **Project ADR conventions.** Three-digit numbers, a list index, an index with no rows yet, and a project's own `0000-template.md` all work; an index in any other shape is refused with a message naming the file. Tests in Task 4.

---

## File Structure

```
abdullah-skills/
├── README.md  LICENSE  CHANGELOG.md  CONTRIBUTING.md  CLAUDE.md  AGENTS.md  .gitignore
├── .agents/install-block.md  .agents/writing-docs.md
├── .agents/adr/README.md  .agents/adr/0001-*.md  .agents/adr/0002-*.md
├── .claude-plugin/plugin.json  .claude-plugin/marketplace.json
├── .github/workflows/check.yml
├── docs/DOCUMENTATION.md                 this repository's own policy (lean)
├── docs/README.md                        this repository's documentation map
├── docs/abdullah-docs.md  docs/setup-abdullah-docs.md
├── docs/design/2026-11-25-abdullah-docs-design.md
├── docs/plans/2026-11-25-abdullah-docs.md
├── scripts/check_frontmatter.py  scripts/link_skills.py
├── tests/test_check_frontmatter.py  tests/test_link_skills.py
└── skills/
    ├── abdullah-docs/
    │   ├── SKILL.md  agents/openai.yaml
    │   ├── reference/setup.md  policy-default.md  adr.md  changelog.md  incident.md  runbook.md  readme.md  decisions.md
    │   ├── templates/adr-full.md  adr-short.md  incident.md  runbook.md  readme.md  changelog.md  docs-map.md  agent-section.md
    │   ├── scripts/docs_findings.py  docs_policy.py  docs_markdown.py  docs_git.py  docs_adr.py
    │   ├── scripts/new_adr.py  check_docs.py  pr_checklist.py
    │   └── tests/fixtures.py  test_*.py
    └── setup-abdullah-docs/SKILL.md  agents/openai.yaml
```

Skill tests run with `python -m unittest discover -s skills/abdullah-docs/tests -t skills/abdullah-docs`; repository tests with `python -m unittest discover -s tests`. Each test module inserts `skills/abdullah-docs/scripts` (or `scripts/`) into `sys.path`.

---

### Task 1: Repository scaffold and the front matter check

**Files:**
- Create: `.gitignore` (`__pycache__/`, `*.pyc`, `.venv/`), `.gitattributes`, `LICENSE` (MIT, `Copyright (c) 2026 <holder>`)
- Create: `scripts/check_frontmatter.py`
- Test: `tests/test_check_frontmatter.py`

**Interfaces:**
- Produces: `check_frontmatter.py --root <repo>`, exit 0 and `All SKILL.md front matter parses.` when clean, else one `path: message` line per problem and exit 1. Function `check_skill(path: Path) -> list[str]`.

- [ ] **Step 1: Initialise the repository**

Run: `git init -b feature/abdullah-docs-v1` in the working copy. Then ask the owner which name and email this public repository's commits carry, and which name goes in `LICENSE` and in the plugin manifests' `author` and `owner` fields. Recommend GitHub's noreply address for the email (`<id>+<login>@users.noreply.github.com`, with `<id>` from `gh api user --jq .id`), because the global git email is personal. Set the answers with `git config user.name` and `git config user.email` in this repository only, before the first commit. Below, `<holder>` is the name the owner chose for `LICENSE` and the manifests. Add `.gitattributes` with `* text=auto eol=lf`.
Expected: `git status` lists `docs/` as untracked; `git config user.name` and `git config user.email` print the owner's choice.

- [ ] **Step 2: Write the failing tests** in `tests/test_check_frontmatter.py`, each building a skill folder in a temporary directory:
  - `test_valid_skill_passes`: front matter `name: demo` and `description: Does a thing.` in `skills/demo/SKILL.md` gives `[]`.
  - `test_missing_front_matter`: a file with no `---` block gives one problem containing `no front matter`.
  - `test_missing_description`: gives one problem containing `` `description` ``.
  - `test_name_must_match_folder`: `name: other` in `skills/demo/` gives one problem containing `does not match folder`.
  - `test_unquoted_colon_space`: `description: Use when: always` gives one problem containing `quote`.
  - `test_quoted_value_with_colon_passes`: `description: "Use when: always"` gives `[]`.
  - `test_cli_exit_codes`: the CLI exits 0 on a clean root and 1 with a bad skill.

- [ ] **Step 3: Run them to see them fail**

Run: `python -m unittest discover -s tests -v`
Expected: errors, `No module named 'check_frontmatter'`.

- [ ] **Step 4: Implement `check_skill(path: Path) -> list[str]` and `main(argv: list[str] | None = None) -> int` in `scripts/check_frontmatter.py`**

Parse only the block between the first two `---` lines, one `key: value` per line (a stdlib parser; no YAML library). A value is quoted if it starts with `"` or `'`. Walk every `SKILL.md` under `<root>/skills`.

- [ ] **Step 5: Run the tests to see them pass**

Run: `python -m unittest discover -s tests -v`
Expected: 7 tests OK.

- [ ] **Step 6: Commit**

```bash
git add .gitignore .gitattributes LICENSE scripts/check_frontmatter.py tests/test_check_frontmatter.py docs/design docs/plans
git commit -m "chore: add repository scaffold and the skill front matter check" -m "Refs: design §11, plan task 1"
```

---

### Task 2: Pure modules: findings, policy settings, Markdown

**Files:**
- Create: `skills/abdullah-docs/scripts/docs_findings.py`, `docs_policy.py`, `docs_markdown.py`
- Test: `skills/abdullah-docs/tests/test_findings.py`, `test_policy.py`, `test_markdown.py`

**Interfaces:**
- Produces:
  - `docs_findings.Finding(path: str, line: int, severity: str, kind: str, message: str)`, a frozen dataclass; `format_finding(f: Finding) -> str`; `exit_code(findings: Iterable[Finding]) -> int`; `warning(...)` and `error(...)` constructors with the same parameters minus `severity`.
  - `docs_policy.Settings` dataclass with defaults `profile="lean"`, `adr_dir="docs/adr"`, `changelog="CHANGELOG.md"`, `base=None`, `history=[]`, `pairs=[]` (list of `(str, str)`), `examples=[]` (globs of files whose backticked paths are examples, so the code-path check skips them), `specs="docs/superpowers/specs"`, `plans="docs/superpowers/plans"`. `read_settings(policy: Path | None) -> Settings`. `find_policy(root: Path) -> Path | None` (tries `docs/DOCUMENTATION.md`, then `DOCUMENTATION.md`, then `CONTRIBUTING.md` when it has a `## Documentation` heading, design §6.1). Every script that takes `--policy` uses `find_policy(root)` when the flag is absent. Constant `AGENT_SECTION_HEADING = "## Documentation (abdullah-docs)"`.
  - `docs_markdown.Link(line: int, target: str, anchor: str | None)`; `links(text: str) -> list[Link]`; `code_paths(text: str) -> list[tuple[int, str]]`; `heading_slugs(text: str) -> set[str]`; `is_repo_path(token: str) -> bool`; `split_lines(text: str) -> list[str]` (handles `\r\n`).

- [ ] **Step 1: Write the failing tests**

`test_findings.py`:
  - `format_finding(error("a/b.md", 3, "adr-index", "missing row"))` equals `"a/b.md:3: error: adr-index: missing row"`.
  - `exit_code([warning(...)])` is 0; `exit_code([warning(...), error(...)])` is 1; `exit_code([])` is 0.

`test_policy.py`:
  - A policy containing `Documentation profile: full` and the block below gives `profile == "full"`, `adr_dir == ".agents/adr"`, `base == "origin/main"`, `history == ["docs/plans/**", "conversations/**"]`, `pairs == [("specs/*-design.md", "specs/*-design.en.md")]`:
    ````
    ```abdullah-docs
    adr-dir: .agents/adr
    base: origin/main
    history: docs/plans/**, conversations/**
    pairs: specs/*-design.md:specs/*-design.en.md
    ```
    ````
  - `read_settings(None)` returns the defaults; a policy without a block keeps the defaults but reads the profile line; an unknown key is ignored.
  - `find_policy` prefers `docs/DOCUMENTATION.md` over `DOCUMENTATION.md`, falls back to a `CONTRIBUTING.md` with a `## Documentation` heading, and returns `None` otherwise (a `CONTRIBUTING.md` without the heading is not a policy).
  - `examples: skills/**, README.md` gives `examples == ["skills/**", "README.md"]`.

`test_markdown.py`:
  - `links("See [x](docs/a.md#part) and [y](https://e.com).")` is `[Link(1, "docs/a.md", "part")]`: URLs (`http:`, `https:`, `mailto:`) are excluded.
  - Angle brackets, titles and `%20`: `[a](<docs/my file.md>)`, `[a](docs/x.md "T")`, `[a](docs/my%20file.md)` give targets `docs/my file.md`, `docs/x.md`, `docs/my file.md`.
  - Reference definitions: `[a]: docs/x.md` gives `Link(1, "docs/x.md", None)`.
  - A same-file anchor `[a](#intro)` gives `Link(1, "", "intro")`.
  - Links inside a ```` ``` ```` fence or inside `` `[a](b.md)` `` are ignored.
  - CRLF: the same text with `\r\n` gives the same links and line numbers.
  - `code_paths("Run `src/app/main.py` and `npm test`, see `docs/<name>.md` and `~/x/y.md`.")` is `[(1, "src/app/main.py")]`.
  - `is_repo_path` is true for `a/b.py` and `.github/workflows/check.yml`; false for `https://a/b.md`, `a/*.md`, `docs/<x>.md`, `/abs/p.md`, `C:/x/y.md`, `~/a/b.md`, `nofolder.md`, `a/b`.
  - `heading_slugs("# Hello World!\n## Hello World")` is `{"hello-world", "hello-world-1"}` (GitHub rules: lower case, drop punctuation except `-` and `_`, spaces to `-`, numbered duplicates).

- [ ] **Step 2: Run them to see them fail**

Run: `python -m unittest discover -s skills/abdullah-docs/tests -t skills/abdullah-docs -v`
Expected: import errors for the three modules.

- [ ] **Step 3: Implement the three modules** with the signatures above. In `docs_markdown`, blank out fenced blocks and inline code spans before matching links; collect backticked tokens before blanking inline code, but skip those inside fences.

- [ ] **Step 4: Run the tests to see them pass**

Run: the command in Step 2. Expected: all OK.

- [ ] **Step 5: Commit**

```bash
git add skills/abdullah-docs/scripts skills/abdullah-docs/tests
git commit -m "feat: add finding, policy and markdown modules for the docs scripts" -m "Refs: design §9, C13, plan task 2"
```

---

### Task 3: Git helpers and the fixture repository

**Files:**
- Create: `skills/abdullah-docs/scripts/docs_git.py`, `skills/abdullah-docs/tests/fixtures.py`
- Test: `skills/abdullah-docs/tests/test_git.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `docs_git.git(root: Path, *args: str) -> str | None` (stdout, or `None` when git fails or is missing); `is_repo(root) -> bool`; `default_base(root) -> str | None` (the target of `refs/remotes/origin/HEAD`, as `origin/<name>`); `ref_exists(root, ref) -> bool`; `merge_base(root, base) -> str | None`; `changed_files(root, base) -> set[str]` (files differing between the merge base and the working tree, plus untracked files not ignored; forward slashes); `added_lines(root, base, path) -> set[int]` (line numbers in the working-tree file added since the merge base, from `git diff --unified=0`); `files_at(root, ref, directory) -> list[str]` (base names via `git ls-tree --name-only <ref> <directory>/`); `tracked_files(root, pattern) -> list[str]` (`git ls-files`, or a directory walk skipping `.git` and `node_modules` when not a repository); `commits_since(root, base) -> list[str]` (full messages, from the merge base to `HEAD`).
  - `fixtures.Repo(tmp: Path)`: `write(path: str, text: str, newline: str = "\n")`, `commit(message: str)`, `branch(name: str)`, `checkout(name: str)`, `merge(name: str)`, `root: Path`. It runs `git init -b main` and sets a local `user.name`/`user.email` and `core.autocrlf false`, so tests behave the same on Windows and Linux.
  - `added_lines` passes `--ignore-cr-at-eol`, so a file whose line endings alone changed reports no added lines.

- [ ] **Step 1: Write the failing tests** in `test_git.py` using `fixtures.Repo` in a `tempfile.TemporaryDirectory`:
  - `test_changed_files_includes_committed_uncommitted_and_untracked`: on branch `work` from `main`, one committed change, one modified file and one new untracked file all appear in `changed_files(root, "main")`; an unchanged file does not.
  - `test_added_lines_reports_new_line_numbers`: appending two lines to a 3-line file gives `{4, 5}`.
  - `test_added_lines_ignores_line_endings`: rewriting an LF file with CRLF and no other change gives `set()`.
  - `test_files_at_reads_the_base`: a file committed only on `main` after `work` branched is listed by `files_at(root, "main", "docs/adr")` and not present in the working tree.
  - `test_not_a_repository`: in a plain folder, `is_repo` is false, `git(...)` returns `None`, and `tracked_files(root, "*.md")` still lists Markdown files by walking.
  - `test_missing_ref`: `ref_exists(root, "origin/main")` is false and `merge_base(root, "origin/main")` is `None`.

- [ ] **Step 2: Run them to see them fail.** Run the skill test command. Expected: import error for `docs_git`.

- [ ] **Step 3: Implement `docs_git.py` and `fixtures.py`** with the signatures above. Call git with `subprocess.run([...], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")`, and `-c core.quotepath=off` so non-ASCII paths print plainly.

- [ ] **Step 4: Run the tests to see them pass.** Expected: all OK.

- [ ] **Step 5: Commit** `feat: add git helpers and a fixture repository for the docs scripts` with `Refs: design §3, §9, plan task 3`.

---

### Task 4: ADR module and `new_adr.py`

**Files:**
- Create: `skills/abdullah-docs/scripts/docs_adr.py`, `skills/abdullah-docs/scripts/new_adr.py`, `skills/abdullah-docs/templates/adr-full.md`, `skills/abdullah-docs/templates/adr-short.md`
- Test: `skills/abdullah-docs/tests/test_adr.py`, `test_new_adr.py`

**Interfaces:**
- Consumes: `docs_git.files_at`, `docs_git.default_base`, `docs_git.ref_exists`, `docs_policy.read_settings`, `docs_policy.find_policy`, `docs_findings`.
- Produces:
  - `docs_adr.ADR_NAME_RE = re.compile(r"^(\d{3,4})-[a-z0-9][a-z0-9-]*\.md$")`; `AdrFile(number: int, name: str)`; `adr_files(names: Iterable[str]) -> list[AdrFile]` (number 0 excluded: it is a template); `number_width(files) -> int` (width of the existing numbers, 4 when none); `next_number(local: list[AdrFile], base: list[AdrFile]) -> int`; `slugify(title: str) -> str` (lower case, runs of non-alphanumerics to `-`, trimmed, at most 60 characters, cut at a hyphen); `index_format(text: str) -> str | None` (`"table"`, `"list"` or `None`); `index_targets(text: str) -> list[tuple[int, str]]` (line and linked file name of each ADR link); `insert_index_row(text: str, number: str, name: str, title: str) -> str`, raising `IndexFormatError` when the format is neither; it mirrors the last ADR row's shape (its column count, and which cell holds the link, the title and a status word such as Accepted or Proposed), leaving other cells empty; `unrecognised_adrs(names) -> list[str]` (Markdown files that look like ADRs, matching `^(?:adr[-_])?\d+[-_ ]` in any case, but not `ADR_NAME_RE`); `project_template(adr_dir: Path) -> Path | None` (`0000-template.md`, then `template.md`); `render(template: str, number: str, title: str, today: str, numbered_h1: bool) -> str`; `status_of(text: str) -> tuple[int, str] | None` and `date_of(text: str) -> tuple[int, str] | None` (line and value of the first `Status:` or `Date:` line, with or without `- **…:**` markup).
  - `new_adr.py --root <repo> --title <title> [--adr-dir D] [--base REF] [--policy P] [--short]`: writes the ADR, updates or creates `<adr-dir>/README.md`, prints only the new file's repository path on stdout (warnings go to stderr, because the agent reads stdout), exits 0; exits 2 when the index format is refused (message names the file), when the directory holds ADR-like files it cannot number (`unrecognised_adrs`, listed in the message), or when `--title` is empty.

Templates. `adr-full.md` has the sections of the design's default policy: `# {number}. {title}`, a `- **Status:** Proposed` line, `- **Date:** {date}`, `- **Deciders:**`, `- **Related:**`, then `## Context`, `## Decision`, `## Alternatives considered` (a three-column table: Option, Pros, Cons), `## Consequences`. `adr-short.md` (C11): `# {number}. {title}`, `- **Status:** Proposed · **Date:** {date}`, then one paragraph placeholder: context, decision, why. Both keep a status and a date line, so `check_docs.py`'s header check passes for either.

`render` on a project template replaces its first `# ` line with `# {number}. {title}` when `numbered_h1` is true (the latest existing ADR's title starts with its number) or `# {title}` otherwise, replaces every `YYYY-MM-DD` and `{date}` with today, and sets the status value to `Proposed`.

- [ ] **Step 1: Write the failing tests**

`test_adr.py`:
  - `adr_files(["0001-a.md", "0000-template.md", "README.md", "012-b.md"])` gives numbers `[1, 12]`.
  - `next_number([AdrFile(42, "0042-x.md")], [AdrFile(43, "0043-y.md")])` is 44: the base wins when it is ahead (design §1).
  - `slugify("Use Postgres, not SQLite!")` is `"use-postgres-not-sqlite"`.
  - Table index: `insert_index_row` on a table whose last row is `| [0002](0002-b.md) | B | Accepted |` appends `| [0003](0003-c.md) | C | Proposed |` right after it; text after the table is untouched.
  - List index: after `- [0002](0002-b.md) B` it appends `- [0003](0003-c.md) C`.
  - Header-only table (`| ADR | Decision | Status |` and its separator, no rows) gets the row appended under the separator.
  - A 2-column table (`| [0001](0001-a.md) | A |`) gets `| [0002](0002-b.md) | B |`; a 4-column table whose last row is `| [0001](0001-a.md) | A | Accepted | 2026-01-01 |` gets `| [0002](0002-b.md) | B | Proposed |  |`.
  - `unrecognised_adrs(["ADR-0001-x.md", "0002_Title.md", "0003-ok.md", "README.md"])` is `["ADR-0001-x.md", "0002_Title.md"]`.
  - An index that is plain prose raises `IndexFormatError`.
  - `status_of` reads `- **Status:** Superseded by [0007](0007-x.md)` and `Status: Accepted`.

`test_new_adr.py` (with `fixtures.Repo`):
  - `test_numbers_after_the_base`: `main` has `0001` and `0002`; branch `work` is cut after `0001`, so locally only `0001` exists. `new_adr.py --base main --title "Pick a queue"` writes `docs/adr/0003-pick-a-queue.md` and an index row for 3.
  - `test_three_digit_numbers`: existing `001-a.md`, `002-b.md` give `003-…`.
  - `test_uses_project_template`: a project `0000-template.md` containing `## Why` gives an ADR that contains `## Why`, today's date, and `Proposed`.
  - `test_short_template`: `--short` gives a file with no `## Context` heading.
  - `test_creates_missing_index`: with no `docs/adr/` at all, it creates the folder, the ADR and a `README.md` with a table header and the row.
  - `test_refuses_unknown_index`: a prose `README.md` exits 2 with a message containing `docs/adr/README.md`, and writes no ADR.
  - `test_without_git_warns`: in a plain folder it writes `0001-…`, prints `warning: base` on stderr, and stdout holds only the path.
  - `test_refuses_unrecognised_names`: a folder holding `ADR-0001-x.md` exits 2 naming that file, and writes nothing.
  - `test_policy_adr_dir`: a policy block `adr-dir: .agents/adr` with `--policy docs/DOCUMENTATION.md` writes under `.agents/adr/`.

- [ ] **Step 2: Run them to see them fail.** Expected: import errors.

- [ ] **Step 3: Implement `docs_adr.py`, `new_adr.py` and the two templates** with the interfaces above. `new_adr.py` takes the base from `--base`, else the policy's `base`, else `docs_git.default_base`, and warns (`warning: base`) when none exists.

- [ ] **Step 4: Run the tests to see them pass.** Expected: all OK.

- [ ] **Step 5: Commit** `feat: add new_adr to number an ADR after the base and index it` with `Refs: design §9.1, C8, C11, C12, plan task 4`.

---

### Task 5: `check_docs.py`: scope, ADR checks and the agent section

**Files:**
- Create: `skills/abdullah-docs/scripts/check_docs.py`
- Test: `skills/abdullah-docs/tests/test_check_docs_adr.py`

**Interfaces:**
- Consumes: `docs_git`, `docs_policy`, `docs_adr`, `docs_findings`.
- Produces: `check_docs.py --root <repo> [--base REF] [--all] [--release] [--adr-dir D] [--changelog C] [--pairs A:B]... [--history GLOB]... [--policy P]`. Functions used by Task 6: `Context` dataclass (`root: Path`, `settings: Settings`, `base: str | None`, `scope: set[str] | None` meaning all files when `None`, `release: bool`), `build_context(args) -> tuple[Context, list[Finding]]`, `is_history(ctx, path: str) -> bool`, `severity_for(ctx, path: str) -> str`, and a check registry `CHECKS: list[Callable[[Context], list[Finding]]]` that Task 6 appends to.

Scope (C5): without `--all`, Markdown checks look at `changed_files(root, base)`; the ADR index, number and agent-section checks always run, because they are cheap and a collision comes from the base. A file is history when it matches a `--history` glob or the policy's `history`, or is an ADR whose status starts with `Superseded`. History downgrades only the content kinds (`link`, `anchor`, `code-path`) to warnings; the `adr-*` kinds stay errors everywhere, because a broken index or a dangling `Superseded by` link is always fixable. Flags override the policy block, and without `--policy` the policy comes from `find_policy`.

| Kind | Severity | Condition |
|---|---|---|
| `base` | warning | No base given or found, the ref does not exist, or the folder is not a repository. Printed once; the remaining checks run on local files |
| `adr-index` | error | An ADR file is not linked from `<adr-dir>/README.md`, or an index link names a missing file. No index file with at least one ADR is one error |
| `adr-number` | error | Two local ADRs share a number, or a local ADR's number belongs to a different file on the base. The message names both files and says to renumber the local one (C7) |
| `adr-header` | error | An ADR has no status or no date line, or a `Superseded by` link names a missing ADR |
| `adr-name` | warning | A file in the ADR folder looks like an ADR but its name cannot be numbered (`unrecognised_adrs`) |
| `agent-section` | warning | Neither `CLAUDE.md` nor `AGENTS.md` contains `AGENT_SECTION_HEADING` (C14) |

- [ ] **Step 1: Write the failing tests** in `test_check_docs_adr.py`, calling `check_docs.main([...])` and capturing stdout:
  - `test_clean_repository_exits_zero`: ADRs 0001 and 0002, both indexed with status and date, and `AGENTS.md` with the heading, run with `--base main` from a branch: exit 0, no output lines.
  - `test_missing_index_row`: an unindexed `0003-c.md` gives `error: adr-index` naming `0003-c.md`, exit 1.
  - `test_dangling_index_link`: a row for a missing `0004-d.md`, error.
  - `test_number_taken_on_base`: `main` adds `0003-other.md` after `work` branched; `work` has `0003-mine.md`. `--base main` gives `error: adr-number` naming both. This is the collision of design §1.
  - `test_local_duplicate_number`: `0002-a.md` and `0002-b.md`, error.
  - `test_missing_status_or_date`, `test_superseded_link_must_resolve`.
  - `test_superseded_adr_content_findings_are_warnings`: a superseded ADR containing a broken ordinary link exits 0 with `warning: link`, while its dangling `Superseded by` link in the same file is still `error: adr-header`.
  - `test_unrecognised_adr_name_is_warning`: `ADR-0009-x.md` in the ADR folder gives `warning: adr-name` naming it.
  - `test_agent_section_missing_is_warning`: exit 0 with `warning: agent-section`.
  - `test_unfetched_base_warns_once`: `--base origin/main` in a repository with no remote prints exactly one `warning: base` and still reports a missing index row.
  - `test_policy_block_is_read`: `--policy docs/DOCUMENTATION.md` with `adr-dir: .agents/adr` checks `.agents/adr`.

- [ ] **Step 2: Run them to see them fail.** Expected: import error for `check_docs`.

- [ ] **Step 3: Implement `check_docs.py`** with the interface and table above. Print findings sorted by path and line, then exit with `exit_code`.

- [ ] **Step 4: Run the tests to see them pass.** Expected: all OK.

- [ ] **Step 5: Commit** `feat: add check_docs with scope, adr and agent-section checks` with `Refs: design §9.2, C5, C7, C14, plan task 5`.

---

### Task 6: `check_docs.py`: links, code paths, changelog and language pairs

**Files:**
- Modify: `skills/abdullah-docs/scripts/check_docs.py` (append four checks to `CHECKS`)
- Test: `skills/abdullah-docs/tests/test_check_docs_content.py`

**Interfaces:**
- Consumes: `Context`, `severity_for`, `CHECKS` (Task 5); `docs_markdown.links`, `code_paths`, `heading_slugs`; `docs_git.added_lines`, `changed_files`.
- Produces: the finding kinds below.

| Kind | Severity | Condition |
|---|---|---|
| `link` | error | A relative link in an in-scope Markdown file points to a file that does not exist, resolved from the linking file's folder |
| `anchor` | warning | The target file exists, but its headings have no slug equal to the anchor (same-file anchors included) |
| `code-path` | error | A backticked token that `is_repo_path` accepts exists neither from the repository root nor from the file's folder. Files matching the `examples` setting are skipped, because their paths describe other projects |
| `changelog` | error | The changelog has no unreleased heading (`## [Unreleased]` or `## Unreleased`, any case); or, with a base and without `--release`, a line added since the base lies outside that section (C6). Lines outside the unreleased section are history for the link and code-path checks |
| `pair` | error | With pairs configured, an in-scope file matching one side has no counterpart; or one side changed since the base and the other did not |

The changelog section runs from the unreleased heading to the next `## ` heading.

- [ ] **Step 1: Write the failing tests** in `test_check_docs_content.py`:
  - `test_broken_link`, `test_link_relative_to_file` (`docs/a.md` linking `b.md` resolves to `docs/b.md`), `test_unknown_anchor_is_warning`, `test_link_in_fence_ignored`.
  - `test_missing_code_path` and `test_code_path_found_from_root_or_file_folder`.
  - `test_changelog_line_in_released_section`: `main` has `## [Unreleased]` then `## [0.4.0]` with entries; on `work` a line is added under `## [0.4.0]`. `--base main` gives `error: changelog` at that line. This is the misplaced entry of design §1.
  - `test_changelog_entry_moved_by_merge`: the real slip. `work` adds an entry under `## [Unreleased]` while `main` releases (renames `## [Unreleased]` to `## [0.5.0]` and adds a new empty `## [Unreleased]` above it). After `repo.merge("main")` on `work` with the result git's text merge leaves (the entry under `## [0.5.0]`; if git reports a conflict instead, write that result and commit it as the merge), `--base main` gives `error: changelog` at the entry's line.
  - `test_changelog_line_under_unreleased_passes`.
  - `test_examples_skip_code_paths`: with `examples: skills/**`, a missing backticked path in `skills/x/reference/a.md` is not reported; the same text in `docs/a.md` is.
  - `test_release_flag_skips_placement`: the same misplaced line with `--release` exits 0.
  - `test_unreleased_heading_variants`: `## Unreleased` and `## [unreleased]` pass; a changelog with neither gives one error.
  - `test_broken_link_in_released_section_is_warning`.
  - `test_pair_missing_counterpart` and `test_pair_changed_alone`: `--pairs "specs/*-design.md:specs/*-design.en.md"`; changing `specs/x-design.md` alone since the base is an error; changing both passes.
  - `test_default_scope_is_changed_files`: a broken link in a file unchanged since the base is not reported without `--all`, and is with it.
  - `test_history_glob_downgrades`: with `--history "docs/plans/**"` a broken link in a plan is a warning.
  - `test_crlf_line_numbers`: the misplaced-changelog fixture saved with CRLF reports the same line.

- [ ] **Step 2: Run them to see them fail.** Expected: the new kinds are missing.

- [ ] **Step 3: Implement the four checks** and register them in `CHECKS`.

- [ ] **Step 4: Run the full skill suite.** Run the skill test command. Expected: all OK.

- [ ] **Step 5: Commit** `feat: check links, code paths, changelog placement and language pairs` with `Refs: design §9.2, C5, C6, plan task 6`.

---

### Task 7: `pr_checklist.py`

**Files:**
- Create: `skills/abdullah-docs/scripts/pr_checklist.py`
- Test: `skills/abdullah-docs/tests/test_pr_checklist.py`

**Interfaces:**
- Consumes: `docs_git.changed_files`, `commits_since`, `default_base`; `docs_policy.read_settings`.
- Produces: `pr_checklist.py --root <repo> [--base REF] [--policy P]`, printing six lines in this order, each `- <item>: <evidence>`, and exit 0 (2 on a usage error, `warning: base` when there is no base):
  1. `spec-or-adr`: the changed files under the ADR directory, the specs directory and the plans directory, or `none changed`.
  2. `changelog`: `changed` or `not changed`, followed by `(N source files changed)`. A source file is any changed file that is not Markdown, not under `docs/`, and not a test file (item 4's definition).
  3. `public-interface`: `check by hand`, followed by the new source files, if any.
  4. `regression-test`: the changed test files (a path segment `test` or `tests`, or a name matching `*_test.*`, `*.test.*`, `test_*.*`), or `none changed`.
  5. `runbook`: new files under `docs/runbooks/`, or `none added`.
  6. `commit-refs`: `n/a (no commit uses Refs:)` when no commit since the base has a `Refs:` line, otherwise the subjects of the commits that lack one, or `all commits reference`.

- [ ] **Step 1: Write the failing tests**: one fixture branch with a source change, a test change, a new runbook, no changelog change and two commits, one with `Refs:` and one without. Assert each of the six lines exactly, including `changelog: not changed (1 source files changed)` and the subject of the commit without `Refs:`. A second test: on a branch with only Markdown changes, `changelog: not changed (0 source files changed)`.

- [ ] **Step 2: Run them to see them fail.**

- [ ] **Step 3: Implement `pr_checklist.py`.**

- [ ] **Step 4: Run the tests to see them pass.**

- [ ] **Step 5: Commit** `feat: add pr_checklist to show what the diff says about each done item` with `Refs: design §9.3, plan task 7`.

---

### Task 8: The skill content

**Files:**
- Create: `skills/abdullah-docs/SKILL.md`, `skills/abdullah-docs/agents/openai.yaml`
- Create: `skills/abdullah-docs/reference/setup.md`, `policy-default.md`, `adr.md`, `changelog.md`, `incident.md`, `runbook.md`, `readme.md`, `decisions.md`
- Create: `skills/abdullah-docs/templates/incident.md`, `runbook.md`, `readme.md`, `changelog.md`, `docs-map.md`, `agent-section.md`
- Create: `skills/setup-abdullah-docs/SKILL.md`, `skills/setup-abdullah-docs/agents/openai.yaml`
- Test: `tests/test_skill_content.py`

**Interfaces:**
- Consumes: the three scripts and their flags (Tasks 4 to 7); `AGENT_SECTION_HEADING`.
- Produces: the files the agent reads. Paths in them are relative to the skill folder.

Content each file must carry (wording is the builder's, design §13):

- `abdullah-docs/SKILL.md` front matter:
  ```yaml
  ---
  name: abdullah-docs
  description: "Keep a project's documentation traceable: ADRs, changelog, specs, runbooks, incident records and READMEs, under the project's own documentation policy. Use when writing or changing any of these, when a decision is made, before opening a pull request, and before calling a task done."
  ---
  ```
  Body, short: step 0 from design §6.1 with its four-row table and the automatic setup rule (C10: start it, write nothing before the owner approves the drafts, do not offer it again in the session after a refusal); the task table of §6.2, each row pointing to its reference file; the done check (fetch, `check_docs.py` with the flags from the policy block, `pr_checklist.py`, fix errors, report each checklist item in the final message); decision capture by pointing to `reference/decisions.md`; how to run a script (`python <this skill's folder>/scripts/<name>.py --root <repo>`), and what to do when Python is missing (do the steps by hand and say so).
- `reference/setup.md`: the eight steps of design §6.3, the re-run rule, C8 (adopt an existing layout), C12 (never overwrite a project template; show the difference and ask), C14 (always write the heading; only missing lines under it), and the exact settings block of design §9.2.
- `reference/policy-default.md`: the default policy of design §6.4 as a document a project can adopt, with the profile line, an empty settings block to fill, the profile table of §7, and the definition-of-done checklist.
- `reference/adr.md`: when to write one per profile (C11's three-part test for `lean`); numbering through `new_adr.py`; supersede and amend without deleting; renumbering after a collision (C7: file name, title line, index row, inbound links).
- `reference/changelog.md`: Keep a Changelog subsections, entries only under the unreleased section, and the boundary with `abdullah-versioning` (§10).
- `reference/incident.md`, `runbook.md`, `readme.md`: when each is written and which template to use.
- `reference/decisions.md`: the procedure of design §8.
- `templates/agent-section.md`: the section of design §6.5 with `abdoo431/abdullah-skills` and a `{policy}` placeholder.
- `templates/docs-map.md`, `changelog.md` (Keep a Changelog header and `## [Unreleased]`), `incident.md`, `runbook.md`, `readme.md`.
- `abdullah-docs/agents/openai.yaml`: `interface.display_name: "Abdullah Docs"`, `interface.short_description: "Traceable project documentation"`.
- Skill names under a plugin install carry the plugin's prefix (`abdullah-skills:abdullah-docs`, `/abdullah-skills:setup-abdullah-docs`). Every place that names a skill to invoke says so: "call the Skill tool with `abdullah-docs` (listed as `abdullah-skills:abdullah-docs` when installed as a plugin)", and the same for the setup command in the README and the docs pages.
- `setup-abdullah-docs/SKILL.md`: front matter `name: setup-abdullah-docs`, a human-facing `description` (`"Set up a project for abdullah-docs: survey it, choose lean or full, and draft its documentation policy, map, templates and agent-instructions section for your approval."`), `disable-model-invocation: true`. Body: call the Skill tool with `abdullah-docs`, then follow its `reference/setup.md` from step 1.
- `setup-abdullah-docs/agents/openai.yaml`: `display_name: "Setup Abdullah Docs"`, `short_description: "Set up a project for abdullah-docs"`, and `policy.allow_implicit_invocation: false`.

- [ ] **Step 1: Write the failing tests** in `tests/test_skill_content.py`:
  - `check_frontmatter.check_skill` returns `[]` for both skills.
  - `setup-abdullah-docs/SKILL.md` has `disable-model-invocation: true`; its `openai.yaml` has `allow_implicit_invocation: false`; `abdullah-docs` has neither.
  - Every relative link in both skills' Markdown resolves: run `check_docs.py --root <repo> --all` and assert no `link` error under `skills/`. Backticked paths there are examples of other projects' files (the repository policy in Task 9 lists `skills/**` under `examples`), so `code-path` findings are not asserted.
  - `templates/agent-section.md` starts with `AGENT_SECTION_HEADING`.
  - `reference/setup.md` contains a fenced `abdullah-docs` block that `docs_policy.read_settings` parses.
  - `abdullah-docs/SKILL.md` stays under 200 lines.

- [ ] **Step 2: Run them to see them fail.**

- [ ] **Step 3: Write the files** above.

- [ ] **Step 4: Run both suites.** Run: `python -m unittest discover -s tests -v` and the skill test command. Expected: all OK.

- [ ] **Step 5: Commit** `feat: add the abdullah-docs and setup-abdullah-docs skill content` with `Refs: design §5, §6, §7, §8, D8, C9 to C14, plan task 8`.

---

### Task 9: Repository documentation, plugin manifests and CI

**Files:**
- Create: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
- Create: `.agents/install-block.md`, `.agents/writing-docs.md`, `.agents/adr/README.md`, `.agents/adr/0001-skills-and-install-routes.md`, `.agents/adr/0002-setup-owned-by-the-model-invoked-skill.md`
- Create: `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CLAUDE.md`, `AGENTS.md`, `docs/DOCUMENTATION.md`, `docs/README.md`, `docs/abdullah-docs.md`, `docs/setup-abdullah-docs.md`
- Create: `scripts/link_skills.py`, `.github/workflows/check.yml`
- Test: `tests/test_link_skills.py`, `tests/test_repository.py`

**Interfaces:**
- Consumes: the skills (Task 8), `check_frontmatter.py` (Task 1), `check_docs.py` (Tasks 5 and 6).
- Produces: `link_skills.py [--dest DIR]... [--dry-run] [--remove]`, linking each `skills/<name>` into each destination (defaults `~/.claude/skills` and `~/.agents/skills`), a directory junction on Windows (`_winapi.CreateJunction`) and a symlink elsewhere, replacing an existing link but refusing to replace a real folder, and refusing a destination that resolves inside the repository. Prints `linked <name> -> <dest>`. `--remove` removes only the links it would create. A link is detected by `os.path.islink`, or on Windows by the reparse-point flag in `os.lstat(p).st_file_attributes` (`stat.FILE_ATTRIBUTE_REPARSE_POINT`), because `os.path.islink` is false for a junction and `os.path.isjunction` needs Python 3.12. A junction is removed with `os.rmdir`, never `shutil.rmtree`, which would delete the skill's files through it.

Exact manifest values:

```json
{ "name": "abdullah-skills", "version": "0.1.0",
  "description": "Agent skills for traceable project documentation and, next, versioning.",
  "author": { "name": "<holder>" }, "repository": "https://github.com/abdoo431/abdullah-skills",
  "license": "MIT", "keywords": ["documentation", "adr", "changelog", "skills"],
  "skills": ["./skills/abdullah-docs", "./skills/setup-abdullah-docs"] }
```

`marketplace.json`: `name: "abdullah"`, `owner: { "name": "<holder>" }`, one plugin `{ "name": "abdullah-skills", "source": "./", "description": …, "category": "documentation" }`.

Content each document must carry:

- `.agents/install-block.md`: the routes of design §11.1 with these exact commands, managed first, each marked tested or untested (all untested until Task 12): `claude plugin marketplace add abdoo431/abdullah-skills` then `claude plugin install abdullah-skills@abdullah`; `codex plugin marketplace add abdoo431/abdullah-skills` then `codex plugin add abdullah-skills@abdullah`; Copilot `copilot plugin marketplace add abdoo431/abdullah-skills` then `copilot plugin install abdullah-skills@abdullah`; `gemini skills install https://github.com/abdoo431/abdullah-skills.git --path skills`; `npx skills@latest add abdoo431/abdullah-skills`. Then: pick one route per agent, and after installing run `/setup-abdullah-docs` once per project, or let `abdullah-docs` start it.
- `README.md`: the problem (design §1, without private details), the fix, the install block copied verbatim, step 2 (run the setup), and the skill list split into user-invoked and model-invoked, each name linked to its `SKILL.md`.
- `.agents/writing-docs.md`: the page template of design §11.2.
- `docs/abdullah-docs.md`, `docs/setup-abdullah-docs.md`: pages in that template. `Common questions` is omitted until real questions exist.
- `docs/DOCUMENTATION.md`: this repository's own policy, from `reference/policy-default.md`, profile `lean`, settings block `adr-dir: .agents/adr`, `base: origin/main`, `specs: docs/design`, `plans: docs/plans`, `history: docs/plans/**, docs/design/**`, `examples: skills/**, README.md, CLAUDE.md, AGENTS.md, docs/abdullah-docs.md, docs/setup-abdullah-docs.md, .agents/install-block.md, .agents/writing-docs.md`.
- `docs/README.md`: the map of this repository's documents.
- `CLAUDE.md` and `AGENTS.md`, identical: the layout; every skill listed in the README and in `plugin.json`; install wording copied from `.agents/install-block.md`; run `claude plugin validate . --strict` after touching a manifest; run both test suites and `check_docs.py --all --policy docs/DOCUMENTATION.md` before a pull request; bump `version` in `plugin.json` for every release; the section of design §6.5 for this repository itself.
- `.agents/adr/0001`: the layout and the install routes (D7, design §11), with mattpocock/skills as prior art. `0002`: why the setup procedure lives in the model-invoked skill (C9). Both written with `new_adr.py`.
- `CHANGELOG.md`: Keep a Changelog, `## [Unreleased]` with the `Added` entries for both skills.
- `CONTRIBUTING.md`: report a problem as an issue with what you ran, what the skill did and what you expected.
- `.github/workflows/check.yml`: on pull requests and pushes to `main`, a matrix of Python 3.10 and 3.12 on `ubuntu-latest` and `windows-latest`; run the front matter check, both test suites, and `check_docs.py --root . --all --policy docs/DOCUMENTATION.md`. `actions/checkout` with `fetch-depth: 0`, so the tests' git calls see history.

- [ ] **Step 1: Write the failing tests**:
  - `tests/test_link_skills.py`: with `--dest` set to two temporary folders, both receive one entry per skill that resolves to `skills/<name>`; a second run replaces links without error; a real folder at a target is refused with exit 1 and left intact; a destination inside the repository is refused; `--remove` deletes the links and leaves every file under `skills/` in place.
  - `tests/test_repository.py`: `plugin.json` parses, its `skills` list equals the folders under `skills/`, and its `version` equals the latest released version in `CHANGELOG.md` (the first `## [X.Y.Z]` heading), or, while only `[Unreleased]` exists, is `0.1.0` (design §11.3: plugin installs update only when this version changes); every skill is linked from `README.md`; `CLAUDE.md` and `AGENTS.md` are byte-identical; every command in `.agents/install-block.md` appears verbatim in `README.md`; `check_docs.py --root . --all --policy docs/DOCUMENTATION.md` exits 0.

- [ ] **Step 2: Run them to see them fail.**

- [ ] **Step 3: Write `link_skills.py`, the manifests, the documents and the workflow.** Create the two repository ADRs with `python skills/abdullah-docs/scripts/new_adr.py --root . --policy docs/DOCUMENTATION.md --title "…"` (the first real use of the script).

- [ ] **Step 4: Verify**

Run: `python -m unittest discover -s tests -v`, the skill test command, and `claude plugin validate . --strict`.
Expected: all tests OK; the validation passes.

- [ ] **Step 5: Commit** `docs: add the readme, install routes, docs pages, plugin manifests and ci` with `Refs: design §11, D7, plan task 9`.

---

### Task 10: Acceptance on a mature project (read-only)

**Files:**
- Test: `skills/abdullah-docs/tests/` (a regression fixture for each false positive fixed)
- Modify: the scripts, only for false positives found here

**Interfaces:**
- Consumes: all three scripts.
- Produces: a findings report for the owner, and regression tests.

The project is a private repository on the owner's machine (C15); the owner gives its path at execution time, written below as `<mature>`. Nothing in it changes. Its name and paths appear in no committed file, and fixtures reproduce a false positive with neutral names. Its default branch is `<mature-base>` (ask the owner).

- [ ] **Step 1: Run the full check on the mature project**

Run: `git -C <mature> fetch origin`, then `python skills/abdullah-docs/scripts/check_docs.py --root <mature> --all --base <mature-base>` with the flags its documentation policy implies (its ADR folder, its language pairs, and its never-edited and plan folders as `--history`). Read the policy first to derive them.
Expected: it finishes; every finding is either a real problem or a false positive.

- [ ] **Step 2: Sort the findings** into real problems and false positives, and show the owner the list with one line on each. A false positive is a finding on text that is correct.

- [ ] **Step 3: For each false positive, write a failing regression test** with a neutral fixture, then fix the script, then run the skill suite. Expected: all OK.

- [ ] **Step 4: Check numbering against a branch cut before the latest ADR**

Run, in a throwaway clone under the system temp folder: `git clone --no-checkout <mature> <tmp>/mature`, check out a commit before the latest ADR on `<mature-base>` as branch `test/numbering`, then `new_adr.py --root <tmp>/mature --base <mature-base> --title "Numbering check"`.
Expected: the number is one more than the highest ADR on `<mature-base>`. Delete the clone.

- [ ] **Step 5: Commit** each fix with its test, `fix: <what the false positive was>` with `Refs: design §12, C15, plan task 10`.

---

### Task 11: Acceptance on a project with no documentation

**Files:**
- Modify: `skills/abdullah-docs/reference/*.md`, `SKILL.md`, only for gaps found here

**Interfaces:**
- Consumes: the whole skill.
- Produces: a report for the owner: what the setup proposed, the drafts it showed before writing, and the questions it asked.

- [ ] **Step 1: Make a sample project** under the system temp folder: `git init`, a small Python web API (an `app/` package with two modules, `requirements.txt` naming one web framework and one database driver, a `Makefile` with `run` and `test`, one test file), and three commits. No `docs/`, no `CHANGELOG.md`, no `CLAUDE.md`, no `AGENTS.md`.

- [ ] **Step 2: Run the skill as an agent without skill support would, in two phases.** Commit the sample project first, so `git status` is clean.
  - Phase 1: start a fresh subagent with a fresh context and tell it: "In <sample>, add a changelog entry for the `test` target. Read `<repo>/skills/abdullah-docs/SKILL.md` and follow it. Stop at the first point where you need the owner's answer or approval, and report exactly what you would ask and the drafts you would show." This is ordinary work in a project with no setup, so the skill must start the setup on its own (D8).
  - Check: `git -C <sample> status --porcelain` prints nothing (nothing was written before approval), and the report holds the profile question, the drafts, and the question of which agent file to create.
  - Phase 2: resume the same subagent with the answers: profile `lean`, drafts approved as shown, create `CLAUDE.md`.

- [ ] **Step 3: Check the result**

Expected, each checked by reading the sample project:
- Phase 1 wrote nothing and asked the three questions above;
- the `lean` skeleton exists: `docs/DOCUMENTATION.md` with `Documentation profile: lean` and a settings block, `docs/README.md`, `docs/adr/README.md` and its template, `CHANGELOG.md` with `## [Unreleased]`, a build-run-test runbook;
- retroactive ADRs for the framework and the database, each saying it was recorded retroactively, with nothing the code does not show;
- `CLAUDE.md` created after asking which file to create, with the heading `## Documentation (abdullah-docs)`;
- a list of `Needs confirmation` questions;
- `check_docs.py --root <sample> --all --policy docs/DOCUMENTATION.md` exits 0.

- [ ] **Step 4: Fix any gap** in the reference files or `SKILL.md`, re-run Steps 2 and 3 on a fresh copy of the sample, and commit `fix: <the gap>` with `Refs: design §6.3, §12, plan task 11`.

---

### Task 12: Publish v0.1.0 and run the install routes

**Files:**
- Modify: `.agents/install-block.md`, `README.md` (mark each route tested or untested), `CHANGELOG.md` (move `[Unreleased]` to `## [0.1.0] - <date>`)

**Interfaces:**
- Consumes: the finished repository.
- Produces: the public repository, tag `v0.1.0`, a GitHub release, and tested install routes.

- [ ] **Step 1: Stop for the owner's review.** List every file that will be published (`git ls-files`), and search the tracked files (`git grep -n -i`) for the mature project's name, for machine paths (`Users`, drive letters) and for the owner's email address, which the owner supplies at this step and which is never written to a file, to show none is committed. Search the history too, because deleted content and commit metadata are published with it: `git log --all --format="%an %ae %cn %ce%n%B"` and `git log -p --all`, for the same strings. Every author and committer must be the name and email the owner chose in Task 1. Wait for the owner's explicit approval. Publishing cannot be fully undone.

- [ ] **Step 2: Finalise the release**: move the changelog entries to `## [0.1.0] - <today>`, commit `chore: release v0.1.0` with `Refs: design §11.3, D9, plan task 12`, and create `main` at this commit: `git branch main`.

- [ ] **Step 3: Publish**

Run: `gh repo create abdoo431/abdullah-skills --public --description "Agent skills for traceable project documentation" --source . --remote origin`, then `git push -u origin main feature/abdullah-docs-v1`, `gh repo edit abdoo431/abdullah-skills --default-branch main`, `git tag -a v0.1.0 -m "v0.1.0"`, `git push origin v0.1.0`, and `gh release create v0.1.0 --title "v0.1.0" --notes-file <the 0.1.0 changelog section>`.
Expected: `gh repo view abdoo431/abdullah-skills --json url` prints the URL; the Check workflow passes on `main`.

- [ ] **Step 4: Run the install routes** that this machine has (Claude Code, Codex, `npx skills`; Copilot and Gemini are not installed). Before each, run `python scripts/link_skills.py --remove` so the skills are not installed twice.
  - Codex: run `codex --help` first. The plugin commands in the install block need a Codex with a `plugin` subcommand; if the installed version lacks it, ask the owner whether to upgrade Codex, and otherwise mark the route untested.
  - skills.sh: run `npx skills@latest add --help` first and use its non-interactive flags (an agent choice and a yes-to-all flag), because the default asks questions interactively. Record the exact command used in the install block. For each route: install, confirm the agent lists `abdullah-docs` and `setup-abdullah-docs`, then uninstall unless the owner wants to keep it.
Expected: each run route loads both skills.

- [ ] **Step 5: Record the results**: mark each route tested (with the date and agent version) or untested in `.agents/install-block.md` and `README.md`, commit on a branch `docs/install-routes-tested`, open a pull request into `main`, and give the owner its link and the repository's link.
