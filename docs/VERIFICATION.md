# Verification · 2026-10-23

- 25 offline unit/integration tests passed locally on Python 3.10.
- PDF page attribution, collection isolation, duplicate imports, invalid citations, tool budgets and API errors covered.
- Research coordination: all four roles, human question selection, mode isolation, corpus invalidation and stale-write rejection covered.
- The original training-project provider credential returned HTTP 401. A newer locally configured credential was used in memory for a synthetic smoke test: native tool calling retrieved evidence and submitted three citation-checked claims; the live ReviewAgent delivered a validated artifact with three evidence claims.
- A real provider HTTP 400 exposed a thinking/forced-tool incompatibility. Added a failing adapter regression test, then explicitly disabled DeepSeek thinking for this tools adapter; the live smoke test passed after the fix. See the official provider documentation linked in README.
- These smoke tests verify connectivity, tool protocol and artifact acceptance on synthetic material, **not** research-answer quality, semantic citation support or measured accuracy.
- Offline demonstrations do not call an LLM and are not model-performance results.
- Secret-pattern scan passed for the publishable working trees. Private data and environment files are excluded.
