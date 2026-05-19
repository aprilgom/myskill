---
name: initialize
description: Use when initializing a repository for Codex, creating or updating AGENTS.md, setting repository contribution conventions, or handling an init-style project setup request.
---

# Initialize Repository Context

Use this skill when the user asks to initialize a repository, create `AGENTS.md`, update repo guidance, or run an init-style setup for future Codex sessions. The output should be a contributor guide for the current repository, not a generic template.

## AGENTS.md Requirements

- Title the document `Repository Guidelines`.
- Use Markdown headings for structure.
- Keep the file concise; 200-400 words is the target unless the repository genuinely needs more detail.
- Write short, direct, repository-specific instructions.
- Provide concrete examples where useful, such as commands, paths, naming patterns, branch names, or test commands.
- Use a professional, instructional tone.
- Adapt the structure to the project: add relevant sections and omit sections that do not apply.
- If the guide would become long, keep `AGENTS.md` as the short entry point and split detailed material into linked Markdown files in the repository, preferably under `docs/`.

## Recommended Sections

- `Project Structure & Module Organization`: source code, tests, assets, generated files, and package boundaries.
- `Build, Test, and Development Commands`: key local commands and a brief explanation of each.
- `Coding Style & Naming Conventions`: formatting tools, language idioms, naming patterns, and CLI/API naming rules.
- `Testing Guidelines`: framework, test naming, test data strategy, and how to run focused tests.
- `Commit & Pull Request Guidelines`: commit, branch, and PR conventions plus PR evidence requirements.
- `Quality Gates`: local hooks, pre-push checks, CI workflows, and manual quality commands when they are present.
- Optional sections when relevant: `Security & Configuration Tips`, `Architecture Overview`, or `Agent-Specific Instructions`.

## Splitting Long Guidance

Split content only when the repository complexity justifies it or the `AGENTS.md` draft would exceed roughly 500-600 words.

- Keep high-frequency guidance in `AGENTS.md`: project map, core build/test commands, contribution conventions, and critical safety notes.
- Move deep details into linked files: architecture walkthroughs, long setup instructions, release procedures, test matrices, package-by-package rules, or generated asset policies.
- Use relative Markdown links from `AGENTS.md`, for example `[docs/agent-architecture.md](docs/agent-architecture.md)`.
- Do not create extra documents just to satisfy a template; every linked file must have a clear purpose and be based on observed repository facts.

## Workflow

1. Inspect the repository before writing guidance.
   - Check project manifests, README, test files, build files, and existing docs.
   - Check for quality automation such as `.pre-commit-config.yaml`, `.husky/`, `lefthook.yml`, `.lintstagedrc`, `Makefile`, `justfile`, package scripts, task runners, `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `CircleCI`, Buildkite, or `.git/hooks/`.
   - Check recent Git history for existing commit conventions when available.
   - Preserve existing project-specific conventions when they conflict with these defaults.
2. Create or update the root `AGENTS.md`.
   - Follow the requirements and recommended sections above.
   - Prefer observed repository facts over assumptions.
3. If the guidance is too long, split details into linked Markdown files.
   - Keep `AGENTS.md` concise and link to the detail files.
   - Prefer `docs/agent-*.md` names for Codex-facing supplemental guides.
4. Apply these default contribution conventions unless the repository already defines different ones.
   - Use this precedence: existing documented policy, then clear Git history pattern, then these defaults.
   - Commit subjects use Conventional Commits: `<type>(<scope>): <description>`.
   - Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `build`, and `chore`.
   - Commit and pull request title descriptions are written in Korean.
   - Branches use the same type and optional scope, followed by a short kebab-case English description for URL readability: `<type>/<scope>/<description>` or `<type>/<description>`.
   - Pull request titles use the same Conventional Commit subject format as the primary commit they introduce.
5. Include examples when adding the convention section.
   - Commit/PR examples: `feat(cli): JPEG 품질 플래그 추가`, `fix(vectorize): 투명 영역 건너뛰기`, `docs: 빌드 워크플로 문서화`.
   - Branch examples: `feat/cli/jpeg-quality-flag`, `fix/vectorize/transparent-regions`, `docs/build-workflow`.
6. Document quality gates when present.
   - Include setup and manual run commands that are visible in the repository, for example `pre-commit install`, `pre-commit run --all-files`, `npm run prepare`, `lefthook install`, `make lint`, `just test`, `npm run typecheck`, or `go test ./...`.
   - Summarize where checks run: pre-commit, pre-push, commit-msg, local task runner, CI, release workflow, or required PR check.
   - Summarize what the checks cover, such as formatting, linting, type checking, tests, static analysis, secret scanning, dependency audits, generated-file guards, large-file guards, license checks, or commit message validation.
   - Mention bypass or failure-handling policy only if the repository documents one; otherwise say checks should pass before pushing or opening a PR.
   - If no automation exists but project tooling is visible, ask the user which quality gate tools and enforcement points to add before creating files or commands.
   - Keep the question short and concrete: propose 2-4 fitting options based on the repository, such as pre-commit, pre-push, CI workflow, task runner target, formatter, linter, type checker, test command, secret scanner, dependency audit, generated-file guard, or commit message checker.
   - If the user only wants documentation, list suitable quality gate categories as recommendations without inventing exact commands or CI behavior.
   - Do not invent hook managers, CI providers, install commands, required checks, or quality tool behavior that is not visible in the repository.
7. Validate the result.
   - Re-read `AGENTS.md`.
   - Confirm every relative link resolves when supplemental files are created.
   - Confirm referenced paths and commands exist or were actually verified.
   - Do not invent scripts, package commands, or CI behavior that is not visible in the repository.

## Output

Report:

- The `AGENTS.md` path created or changed.
- Any supplemental guide paths created or changed.
- The main repository-specific guidance added.
- The contribution conventions added or preserved.
- Any quality gate guidance added, preserved, or recommended.
- Any commands run for verification.
