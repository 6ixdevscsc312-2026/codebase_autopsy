# Submission Form Text (ready to paste)

## Submission Title (max 50 chars)

```
Codebase Autopsy
```
(16 characters — well under the 50 limit, room to add a subtitle if you want, e.g. "Codebase Autopsy: Drift Detector")

## Short Description (summary) — 255 char max, 50 char min

```
Codebase Autopsy uses IBM Bob 2.0 to audit repos for architectural drift, flagging modules whose real behavior no longer matches their declared docstring purpose — before it costs a new hire or reviewer hours to find out the hard way.
```
(232 characters)

## Long Description (what is your idea?) — 100 words min, 600 characters min

```
Codebase Autopsy is a CLI tool that audits a Python repository for architectural drift: places where a module's declared purpose (its docstring) has quietly diverged from what the code actually does. A "pure math utility" module that starts writing files. A "logging helper" that starts triggering business logic. Nobody schedules time to notice this — it's usually discovered the hard way, during onboarding or a code review surprise.

The tool combines two layers of analysis. First, plain static analysis: it walks the repo with Python's ast module, builds a module-level dependency graph, and detects real structural issues like import cycles — fast, deterministic, no AI needed. Second, and most importantly, IBM Bob 2.0 reasoning: for every module with a docstring, we call Bob Shell (bob run --format json) with the module's declared purpose plus a summary of its actual functions and calls, referencing the real file directly with @path so Bob reasons over genuine repo context rather than a text blob we constructed. Bob returns a structured verdict — declared purpose, observed behavior, a 0-10 drift score, and supporting evidence — which we use to produce a ranked drift report.

This directly targets the developer workflows the hackathon calls out: onboarding (new hires get an honest map of the codebase instead of an aspirational one) and code review (reviewers get a scored, evidence-backed finding instead of a vague hunch). It's a small, focused tool that shows off Bob's actual repo-aware reasoning rather than wrapping a generic LLM call.
```
(1,432 characters / ~215 words — comfortably over both minimums)

## GitHub link

Paste your public repo URL once you've pushed and set visibility to public.
