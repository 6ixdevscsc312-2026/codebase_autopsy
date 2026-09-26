# Problem & Solution Statement

## Problem

Codebases drift. A module's docstring and folder name describe what it's
*supposed* to do, but over months of quick fixes and feature creep, the
actual behavior quietly diverges — a "pure math utility" module starts
doing file I/O, a "presentation layer" file starts hitting the database
directly, a "just logging" helper triggers business logic. Nobody
schedules time to notice this; it's discovered the hard way, usually by a
new hire trying to understand the code, or a reviewer surprised by a
side effect in a PR that "only touches formatting."

This falls squarely in the developer workflows IBM Bob 2.0 targets —
**onboarding** and **code review** — where too much time and effort go
into rebuilding a mental model of a codebase that nobody wrote down.

## Solution: Codebase Autopsy

Codebase Autopsy is a CLI tool that audits a Python repository for
**architectural drift**: places where declared intent (docstrings) and
observed behavior (actual code) have pulled apart.

It combines two layers of analysis:

1. **Static structural analysis** (no AI): walks the repo with Python's
   `ast` module, builds a module-level dependency graph, and detects real
   issues like import cycles — fast, deterministic, and free.
2. **IBM Bob 2.0 reasoning**: for every module with a docstring, Bob
   (via Bob Shell, `bob run`) is given the module's declared purpose and
   its actual functions/calls, and asked to judge whether the code still
   matches its stated contract. This is where Bob's repo-aware
   understanding does the work a regex or linter can't — judging *intent*
   vs *behavior*, not just syntax.

The output is a ranked **drift report**: which modules have wandered
furthest from what they claim to be, with evidence, so a team can triage
tech debt or brief a new hire on what to actually watch out for — instead
of trusting stale docstrings.

## Why this matters

- **Onboarding**: new developers get an honest map of the codebase
  instead of an aspirational one.
- **Code review**: reviewers can flag "this file no longer does what its
  docstring says" as a real, scored finding instead of a vague hunch.
- **Tech debt triage**: teams can prioritize refactors by drift score
  instead of gut feeling.
