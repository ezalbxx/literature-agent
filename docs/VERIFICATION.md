# Verification · 2026-10-23

- 25 offline unit/integration tests passed locally on Python 3.10.
- PDF page attribution, collection isolation, duplicate imports, invalid citations, tool budgets and API errors covered.
- Research coordination: all four roles, human question selection, mode isolation, corpus invalidation and stale-write rejection covered.
- The original training-project provider credential returned HTTP 401. A newer locally configured credential was used in memory for a synthetic smoke test: native tool calling retrieved evidence and submitted three citation-checked claims; the live ReviewAgent delivered a validated artifact with three evidence claims.
- A real provider HTTP 400 exposed a thinking/forced-tool incompatibility. Added a failing adapter regression test, then explicitly disabled DeepSeek thinking for this tools adapter; the live smoke test passed after the fix. See the official provider documentation linked in README.
- These smoke tests verify connectivity, tool protocol and artifact acceptance on synthetic material, **not** research-answer quality, semantic citation support or measured accuracy.
- Offline demonstrations do not call an LLM and are not model-performance results.
- UI walkthrough completed the review → gaps → selected question → experiment → draft sequence; screenshot in this directory is explicitly an offline demonstration.
- Additional live multi-role checks encountered an intermittent provider connection failure; the adapter permits one SDK retry for transient network/429/5xx failures and reports failure instead of silently producing an answer.
- After the bounded-retry change, a complete live synthetic coordination run passed: review → gaps → explicit candidate selection → experiment → draft, with 9 handoff events and the final draft marked `results_status=not_conducted`. This remains a protocol smoke test on synthetic evidence, not validation of research novelty or scientific quality.
- Secret-pattern scan passed for the publishable working trees. Private data and environment files are excluded.
