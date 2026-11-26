# Version sources

A source is a place the project declares its version. The policy's `sources` lists them, comma-separated; `version.py` writes all of them at once and keeps every other byte of each file.

| Source | Where the version is |
|---|---|
| `Directory.Build.props`, `*.csproj`, `*.fsproj`, `*.vbproj` | `<Version>`; or `<VersionPrefix>` with `<VersionSuffix>` when the project uses that pair |
| `pyproject.toml` | `version` under `[project]`, or under `[tool.poetry]` |
| A Python file | `__version__ = "…"` (name the file in `sources`) |
| `package.json`, with `package-lock.json` | `"version"`; the lock file at its top level and under `packages[""]`, nothing else |
| `Cargo.toml`, with `Cargo.lock` | `version` under `[package]`; the package's own entry in the lock file |
| `.claude-plugin/plugin.json` and other JSON manifests | `"version"` at the top level |
| `VERSION` | the whole file |
| `path#regex` | Any other language: one capture group in a pattern the owner approves, for example `src/app.go#const Version = "(.*)"` |
| `tag` | No file: the version is the latest tag (`setuptools-scm`, `hatch-vcs`, MinVer, `git describe`) |

Source paths are relative to the repository root and must stay inside it.

## Forms

Tags and the changelog always use SemVer (`0.2.0-rc.1`). Python sources get the PEP 440 form of the same version, so packaging tools accept and order it:

| SemVer | PEP 440 |
|---|---|
| `0.2.0-alpha.1` | `0.2.0a1` |
| `0.2.0-beta.1` | `0.2.0b1` |
| `0.2.0-rc.1` | `0.2.0rc1` |
| `0.3.0-dev` | `0.3.0.dev0` |

.NET, npm, Cargo and JSON manifests take SemVer as it is.

## Choosing sources during the setup

- `version.py survey` lists every source it found (up to three folders deep, skipping `node_modules`, `bin`, `obj`, `target`, virtual environments and build output) with the version each declares.
- **One version in several files** (a .NET backend and a web front end): list them all; they must agree.
- **Several unrelated versions** (a monorepo with independently versioned packages): stop; it is not supported.
- **A `.csproj` with no `<Version>`** is not a source: .NET treats it as `1.0.0`, a template default, not a release.
- **`dynamic = ["version"]` in `pyproject.toml`**: the version comes from tags; the source is `tag` and no file is written.
- **`AssemblyInfo.cs`** with a four-part `AssemblyVersion` is reported but never written: propose moving the version to `Directory.Build.props`.
- **Another language:** ask the owner for the file and confirm a `path#regex` pattern that captures exactly the version.
