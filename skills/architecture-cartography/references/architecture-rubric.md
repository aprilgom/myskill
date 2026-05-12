# Architecture Cartography Rubric

Total: 100 points.

This rubric evaluates whether a repository's architecture is understandable, changeable, and locally verifiable. It is not a code style review. Use automatic scanner evidence as a baseline, then adjust only when human judgment has concrete evidence.

## A. Module Boundaries & Ownership - 20

- 18-20: Clear bounded modules, obvious ownership, stable public entrypoints, limited shared dumping grounds.
- 14-17: Mostly clear modules with some ambiguous shared areas.
- 8-13: Modules exist but boundaries are porous or ownership is unclear.
- 0-7: Structure is mostly file-type buckets, framework residue, or large mixed-responsibility areas.

Evidence:
- top-level source modules
- package/workspace boundaries
- public index/API files
- shared/common/util density
- files with mixed concern names

## B. Dependency Direction & Coupling - 20

- 18-20: Dependencies flow in one direction, domain code is not coupled to adapters/UI, shared dependencies are deliberate.
- 14-17: A few hotspots, but coupling is understandable.
- 8-13: Cross-layer imports, deep relative imports, or high fan-in/fan-out files create change risk.
- 0-7: Circular or bidirectional dependencies dominate important paths.

Evidence:
- import graph fan-in/fan-out
- relative import depth
- cross-layer imports between UI/API/domain/infra/data
- package manager workspace graph hints

## C. API & Data Contract Clarity - 15

- 14-15: External and internal contracts are typed, versioned, colocated with validation, and easy to find.
- 10-13: Main contracts are present but not consistently organized.
- 5-9: Contracts are implicit in handlers, ORM calls, or tests.
- 0-4: Data shape and API behavior require reading scattered implementation.

Evidence:
- OpenAPI, GraphQL, protobuf, JSON schema, zod/io-ts/pydantic, DTO/model files
- migrations and schema ownership
- request/response validation locations

## D. Runtime & Deployment Shape - 10

- 9-10: Runtime topology, services, environment boundaries, and deploy artifacts are explicit.
- 7-8: Main runtime is clear with minor gaps.
- 4-6: Some deploy files exist, but service relationships or env boundaries are unclear.
- 0-3: Runtime shape is discoverable only by tribal knowledge.

Evidence:
- Dockerfile, compose, Kubernetes, Terraform, serverless, Procfile
- service entrypoints and process definitions
- env examples and CI deploy hints

## E. Testability & Change Isolation - 15

- 14-15: Tests map to modules, boundary contracts have tests, and changes can be verified locally.
- 10-13: Reasonable test structure with gaps around integration boundaries.
- 5-9: Tests exist but are sparse, centralized, or disconnected from architecture boundaries.
- 0-4: Meaningful architecture changes cannot be verified from local tests.

Evidence:
- test-to-source ratio
- colocated tests
- contract/integration/e2e markers
- module-specific verification commands in docs or package scripts

## F. Architecture Documentation & Decisions - 10

- 9-10: Architecture docs, ADRs, diagrams, and decision history are current enough to guide changes.
- 7-8: Docs exist but omit some important decisions or diagrams.
- 4-6: Fragmented docs or stale diagrams.
- 0-3: No useful architecture map or decision record.

Evidence:
- `ARCHITECTURE.md`, `docs/architecture*`
- `docs/adr/*`, `adr/*`
- Mermaid diagrams and C4-style diagrams
- modification recency relative to source changes

## G. Evolution Risk & Complexity Hotspots - 10

- 9-10: Complexity hotspots are small, named, and bounded.
- 7-8: Some large files or config sprawl but clear mitigation paths.
- 4-6: Several high-risk files or generic modules concentrate unrelated behavior.
- 0-3: God files, shared dumping grounds, and config sprawl make changes risky.

Evidence:
- large files over 300/600 lines
- generic names: common, shared, utils, helpers, manager, service
- config file count and placement
- generated/vendor/migration boundaries

## Manual Adjustment Rules

Adjust the automatic baseline when:
- the scanner flags a dependency as risky but local conventions make it intentional and documented
- the scanner misses framework-specific boundaries that are obvious from repo structure
- generated code inflates file size or import counts
- a legacy module has explicit containment and migration tests
- critical runtime or contract knowledge exists in docs the scanner only counted shallowly

Record adjustment rationale when changing the score by 5+ points or crossing a grade band.

## ROI Actions

Actions should be small enough to execute without a rewrite. Prefer:
- add or update an architecture map for the highest-change area
- extract a public entrypoint for a module
- add a boundary/contract test around a risky dependency
- move validation/schema definitions next to API edges
- split a god file by externally visible responsibilities
- document an accepted cross-layer dependency with an ADR

Effort:
- S: less than 1 hour
- M: 1-4 hours
- L: 4+ hours

Priority:
- `impact_score / effort_hours`
