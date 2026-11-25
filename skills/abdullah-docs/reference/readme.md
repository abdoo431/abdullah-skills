# Project READMEs

Every project or package has a README at its root. It tells a new reader what the thing is, how to use it, and where the rest of the documentation is.

## When to write or update one

- **Create one** for a new project or package.
- **Update it** when the public interface changes: commands, options, configuration, exported functions, API endpoints, installation steps.
- **Check it** during the done check: `pr_checklist.py` prints `public-interface: check by hand`, and lists new source files. Decide whether any of them changes what the README promises.

## How

1. For a new README, use [../templates/readme.md](../templates/readme.md). For an existing one, keep its structure and change only what is now wrong or missing.
2. Write only what the code shows: real commands, real options, real requirements. Write anything you cannot confirm as `> Needs confirmation: <question>`.
3. Keep it short. Link to the runbooks for long procedures and to the documentation map for everything else, instead of repeating them.
4. Do not hand-write generated references (API or schema docs). Link to them.
5. In a repository with several packages, the root README lists the packages and links to each package's README.
