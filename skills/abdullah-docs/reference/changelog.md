# Changelog entries

The changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Follow the project's own changelog rules when its policy has them.

## When to add an entry

Add one for every user-visible or behavioral change: a feature, a changed default, a fix a user would notice, a removal, a security fix. Skip pure refactors, test-only changes and internal tooling, unless the project's policy says otherwise.

## Where it goes

1. Open the changelog the policy names (default `CHANGELOG.md`). If there is none, propose one from [../templates/changelog.md](../templates/changelog.md) and write it after the owner agrees.
2. Find the unreleased section: `## [Unreleased]` (also written `## Unreleased`). Write entries only there. Never edit a released version's section.
3. Put the entry under the right subsection, creating the subsection if it is missing, in this order:
   - `### Added`: new features.
   - `### Changed`: changes to existing behavior.
   - `### Deprecated`: features that will be removed.
   - `### Removed`: features removed now.
   - `### Fixed`: bug fixes.
   - `### Security`: fixes for vulnerabilities.
4. Write one line per change, for a reader who uses the project, not for its developers. Start with what changed, not with the file that changed.
5. Link the ADR, spec, incident record or issue behind it, where the project uses such links.

## After a merge from the base branch

A merge can move the `[Unreleased]` heading, leaving this branch's entry under a version that has already shipped. `check_docs.py` reports it as `changelog: line added below the Unreleased section`. Move the entry back under `[Unreleased]`.

On the project's release and hotfix branches, and on branches that fix a release candidate on `staging`, moving entries into a version section is the point of the branch: pass `--release` to `check_docs.py` there.

## Boundary with versioning

This skill writes `[Unreleased]` entries during normal work. It does not choose version numbers, cut releases, create tags, or move `[Unreleased]` into a version section. The `abdullah-versioning` skill owns those. When it is installed and a release is asked for, call the Skill tool with `abdullah-versioning` (listed as `abdullah-skills:abdullah-versioning` when installed as a plugin). Without it, follow the project's release process.
