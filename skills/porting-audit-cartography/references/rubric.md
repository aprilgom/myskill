# Porting Audit Rubric

This rubric scores source-to-target port evidence. Automated scripts provide a heuristic baseline; manual review remains required for semantic parity and expert-only judgment.

| Category | Evidence Criteria | Points |
| --- | --- | ---: |
| API surface parity | Source public items are mapped to target exported APIs or documented target-language equivalents. | 15 |
| Core behavior parity | Main runtime behavior, data contracts, and decision logic match source-observable behavior. | 25 |
| Edge cases and error semantics | Boundary cases, exact error messages/types, byte offsets, JSON/TOML shape, and validation failures are covered. | 15 |
| Lifecycle, concurrency, and platform semantics | RAII/Close, async/cancellation, file locking, OS-specific behavior, and build tags are equivalent. | 12 |
| Dependency and responsibility boundary fidelity | Registered workspace dependencies are imported from expected target packages, dependency grade direction is valid, and local reimplementation exceptions are explicit. | 13 |
| Test coverage ported from source behavior | Source tests or behavior slices have focused target tests with comparable assertions. | 12 |
| Integration/build quality | Focused tests, repo tests, lint/porting-rule checks, and build constraints are clean or failures are explained. | 8 |

Grade bands:

- 90-100: near complete; only minor idiomatic or documentation gaps.
- 75-89: substantially ported; some edge cases, parser breadth, or tests remain.
- 50-74: usable partial port; important source behavior is absent.
- 25-49: skeleton or narrow behavior slice only.
- 0-24: effectively unported.

Failure modes:

- Claiming dependency correctness when the registry reports `unknown mapping`.
- Counting copied local helpers as parity when a lower-level port exists.
- Treating standard-library replacement as semantic proof without behavior tests.
- Hiding extraction gaps from the final score.

## Score JSON Schema

`scripts/score.py` emits this stable shape:

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601 timestamp",
  "source": "source package root",
  "target": "target package root",
  "score": 0,
  "grade": "grade band",
  "mode": "heuristic baseline; manual-review gap remains for semantic parity",
  "categories": {
    "dependency_responsibility_boundary": {
      "score": 0,
      "max": 13,
      "rationale": "why this category was scored",
      "evidence": ["path or extracted fact"],
      "gaps": ["manual-review gap or missing evidence"]
    }
  },
  "findings": [{"severity": "P2", "title": "Finding", "evidence": "fact", "fix": "bounded fix"}],
  "risks": [{"severity": "P2", "risk": "Risk", "evidence": "fact"}],
  "extraction_gaps": ["unsupported or manual-review-only evidence"],
  "actions": [{"priority": 100, "effort": "M", "impact": "H", "action": "ROI-ranked next step"}]
}
```

## Dependency Registry Shape

```json
{
  "rust_to_go": {
    "andex-utils-absolute-path": "andex-go2/utils/absolute-path"
  },
  "standard_replacements": {
    "serde_json": "encoding/json"
  },
  "external_replacements": {
    "notify": "github.com/fsnotify/fsnotify"
  },
  "allowed_local_reimplementations": {
    "execpolicy": ["shlex"]
  }
}
```
