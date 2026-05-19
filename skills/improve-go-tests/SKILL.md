---
name: improve-go-tests
description: Use when writing, reviewing, refactoring, or debugging Go tests, especially when failures are hard to diagnose, tests use assertion helpers, table tests are messy, cmp/diff output is missing, subtests are flaky, or errors are compared by string.
---

# Improve Go Tests

## Overview

Improve Go tests by keeping verdict logic in `Test` functions, producing diagnostic failures, and using idiomatic `testing`, table tests, subtests, helpers, and `cmp`.

## Workflow

1. Inspect the test's current failure mode before editing when possible.
2. Identify whether the problem is structure, diagnostics, comparison semantics, helper design, or flakiness.
3. Make the smallest change that improves the test's signal.
4. Run the targeted test, then the relevant package test.
5. If behavior changed, verify the test fails for the right reason before making it pass.

## Core Rules

| Situation | Prefer | Avoid |
|---|---|---|
| Checking behavior | Keep assertions and failure text in `Test...` | Assertion libraries or custom test DSLs |
| Shared setup/cleanup | Test helper with `t.Helper()` | Helper that hides product failure context |
| Shared validation | Return `error`, `cmp.Option`, or value | Passing `*testing.T` into assertion helpers |
| Scalar mismatch | `t.Errorf("Func(%q) = %v, want %v", in, got, want)` | `t.Errorf("got %v, want %v", got, want)` |
| Complex values | `cmp.Diff(want, got, opts...)` | Hand-written field-by-field comparisons |
| Multiple independent checks | `t.Error`/`t.Errorf` and keep going | `t.Fatal` for every mismatch |
| Invalid prerequisite | `t.Fatal`/`t.Fatalf` | Continuing after state is meaningless |
| Error expectations | boolean error presence, `errors.Is`, `cmpopts.EquateErrors` | Exact error string equality for error type |
| External serialization | Parse and compare semantic data | Byte/string equality for unstable output |

## Failure Messages

Every failure should usually identify:

- the function or behavior that failed
- the important input or case description
- the actual result before the expected result
- a readable diff for large values

Default formats:

```go
if got, want := Parse(input), wantValue; got != want {
	t.Errorf("Parse(%q) = %v, want %v", input, got, want)
}

if diff := cmp.Diff(want, got); diff != "" {
	t.Errorf("Build(%q) returned unexpected diff (-want +got):\n%s", input, diff)
}
```

Use `%q` for meaningful strings and `%+v` for small structs when fields matter.

## Table Tests

Use table tests when cases share the same logic. Keep the loop body simple.

- Include inputs in failure messages even when using `t.Run`.
- Do not identify failures only by row index.
- Split into separate tests when success and error cases need different logic.
- Avoid table fields that drive complex setup switches; duplicate simple setup in separate tests if it improves readability.
- Use explicit field names for non-trivial case structs.

Subtest names should be short, filter-friendly identifiers. Avoid spaces that obscure logs and avoid `/` because it has special meaning in test filters. Put long context in `desc` and print it on failure.

## Helpers

Use helpers for setup and cleanup failures:

```go
func readFile(t *testing.T, name string) string {
	t.Helper()
	data, err := os.ReadFile(name)
	if err != nil {
		t.Fatalf("read %q: %v", name, err)
	}
	return string(data)
}
```

Do not turn helpers into assertion wrappers:

```go
// Avoid: hides the call-specific context from the test body.
func assertEqual(t *testing.T, got, want Foo) { ... }
```

If shared comparison is needed, return a `cmp.Option`, `cmp.Transformer`, boolean, value, or error and let the `Test` function report the failure.

## Equality And Errors

- Use `==` for simple comparable values.
- Use `cmp.Equal` or `cmp.Diff` for slices, maps, structs, protobufs, and semantic equality.
- Use required options such as `protocmp.Transform()` for protobufs.
- Avoid `reflect.DeepEqual` in new tests; it is often sensitive to implementation details.
- Treat `cmp` as test-only code, not production logic.
- For errors, prefer `wantErr bool` when only presence matters.
- Use `errors.Is` or `cmpopts.EquateErrors` when semantic error matching matters.
- Do not compare full error strings to decide error type; only check text properties when the text itself is the contract.

## Package Choice

- Same package tests: `foo_test.go` with `package foo`; useful for unexported identifiers and compact coverage.
- External tests: `package foo_test`; useful for integration tests, public API tests, or avoiding import cycles.
- Use Go's standard `testing` package as the default framework.

## Review Checklist

Before finishing, check:

- Can a maintainer diagnose the failure without opening the test source?
- Does the failure message include input, got, and want?
- Would one failure hide other useful failures unnecessarily?
- Are subtests independently runnable?
- Are table test rows simple enough to scan?
- Are comparisons semantic and stable across dependency formatting changes?
- Are helpers only hiding setup/cleanup details, not product behavior?
