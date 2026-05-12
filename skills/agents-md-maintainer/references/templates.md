# AGENTS.md Templates

Use the smallest template that fits. Preserve an existing useful structure when possible.

## Minimal Root Template

```markdown
# AGENTS.md

## Project Context
- <repo purpose, main stack, or important package shape>

## Commands
- Install: `<command>`
- Test: `<command>`
- Lint/typecheck/build: `<command>`

## Navigation
- `<path>` - <why future Codex should start here>
- `<path>` - <why this area matters>

## Working Rules
- <repo-specific convention, safety boundary, or gotcha>

## Done Criteria
- <checks or manual verification expected before final response>
```

## Comprehensive Root Template

```markdown
# AGENTS.md

## Project Context
- <what this repo contains and who/what it serves>
- <primary languages, frameworks, package manager, or runtime>

## Commands
- Install: `<command>`
- Test: `<command>`
- Lint: `<command>`
- Typecheck: `<command>`
- Build: `<command>`
- Sync/generate: `<command>`

## Architecture
- `<path>` - <entrypoint, package, service, or shared module>
- `<path>` - <tests, docs, config, or generated output>
- <dependency direction or ownership rule>

## Change Boundaries
- <generated/vendor/migration/lockfile/secrets rule>
- <risky area requiring extra verification or manual review>

## Testing Notes
- <which checks matter for which changes>
- <known failure, flake, or environment prerequisite>

## Coding Conventions
- <project-specific convention that is not obvious from formatter/linter>

## Done Criteria
- <minimum verification before reporting completion>
- <what to mention if a check cannot be run>
```

## Package Or Module Template

```markdown
# AGENTS.md

## Scope
- This file applies to `<path>` and overrides repo-root guidance only where specified.

## Commands
- From repo root: `<command>`
- From this package: `<command>`

## Local Architecture
- `<path>` - <key module or entrypoint>
- `<path>` - <tests or fixtures>

## Local Rules
- <package-specific convention, generated file rule, or gotcha>

## Verification
- <checks required for changes in this package>
```

## Section Selection

Prefer these section names unless the repo already has strong conventions:

- `Project Context`
- `Commands`
- `Navigation`
- `Architecture`
- `Change Boundaries`
- `Testing Notes`
- `Working Rules`
- `Done Criteria`

Avoid sections that become dumping grounds:

- `Notes`
- `Misc`
- `Important`
- `Things to Know`

