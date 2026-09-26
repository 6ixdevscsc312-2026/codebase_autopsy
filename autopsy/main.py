"""
main.py
Codebase Autopsy — orchestrates the full pipeline:
  1. Walk the repo, parse every module (ingest.py)
  2. Build the dependency graph, find cycles (graph.py)
  3. For each module with a docstring, ask Bob 2.0 to judge declared vs
     observed behavior (bob_client.py)
  4. Rank modules by drift score, print a report

Usage:
    python -m autopsy.main <repo_path> [--mock]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from autopsy.ingest import ModuleInfo, walk_repo
from autopsy.graph import build_graph
from autopsy.bob_client import BobClient, BobError


ANALYSIS_PROMPT_TEMPLATE = """You are auditing a Python module for architectural drift:
places where a module's declared purpose (its docstring) no longer matches
what the code actually does.

Module docstring: "{docstring}"

Function/class summary:
{summary}

Judge whether the module's actual behavior (based on the functions, their
names, and what they call) matches its declared docstring purpose.

Respond ONLY with JSON, no other text, in this exact shape:
{{"declared_purpose": "<one line>", "observed_behavior": "<one line>",
  "drift_score": <integer 0-10, 0=perfect match, 10=totally contradicts>,
  "evidence": ["<short evidence string>", ...]}}
"""


def summarize_module(m: ModuleInfo) -> str:
    lines = []
    for fn in m.functions:
        doc = f" - {fn.docstring}" if fn.docstring else ""
        calls = f" [calls: {', '.join(sorted(set(fn.calls))[:6])}]" if fn.calls else ""
        lines.append(f"def {fn.name}(){doc}{calls}")
    for cls in m.classes:
        doc = f" - {cls.docstring}" if cls.docstring else ""
        lines.append(f"class {cls.name}{doc} (methods: {', '.join(cls.methods)})")
    return "\n".join(lines) if lines else "(no functions or classes)"


def analyze_module(client: BobClient, repo_root: str, m: ModuleInfo) -> dict | None:
    """Ask Bob to judge one module. Returns parsed verdict dict, or None if
    the module has no docstring (nothing to compare against) or on failure."""
    if not m.docstring:
        return None

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        docstring=m.docstring,
        summary=summarize_module(m),
    )

    try:
        full_path = os.path.join(repo_root, m.path)
        result = client.run(prompt, file_refs=[full_path])
    except BobError as e:
        print(f"  [warn] Bob call failed for {m.path}: {e}", file=sys.stderr)
        return None

    try:
        verdict = json.loads(result.last_message)
    except json.JSONDecodeError:
        print(f"  [warn] Could not parse verdict JSON for {m.path}: {result.last_message[:200]}",
              file=sys.stderr)
        return None

    verdict["path"] = m.path
    return verdict


def run_autopsy(repo_path: str, mock: bool = False, max_modules: int | None = None) -> dict:
    """max_modules caps how many modules get sent to Bob for analysis —
    each one is a real bob run call. Important on a public web deployment
    where a stranger could otherwise point this at a huge repo and burn
    through the whole Bobcoin budget in one request."""
    print(f"Scanning {repo_path} ...")
    modules = walk_repo(repo_path)
    print(f"  {len(modules)} Python modules found")

    graph = build_graph(modules)
    cycles = graph.find_cycles()

    client = BobClient(mock=mock)

    verdicts = []
    candidates = [m for m in modules if m.docstring]
    truncated = False
    if max_modules is not None and len(candidates) > max_modules:
        candidates = candidates[:max_modules]
        truncated = True
    print(f"  {len(candidates)} modules have docstrings worth checking for drift")

    for m in candidates:
        print(f"  Analyzing {m.path} ...")
        v = analyze_module(client, repo_path, m)
        if v:
            v["in_degree"] = graph.in_degree(m.path)
            verdicts.append(v)

    verdicts.sort(key=lambda v: v.get("drift_score", 0), reverse=True)

    return {
        "repo": repo_path,
        "module_count": len(modules),
        "import_cycles": cycles,
        "verdicts": verdicts,
        "analysis_truncated": truncated,
    }


def print_report(report: dict) -> None:
    print("\n" + "=" * 60)
    print(f"CODEBASE AUTOPSY REPORT — {report['repo']}")
    print("=" * 60)
    print(f"Modules scanned: {report['module_count']}")

    if report["import_cycles"]:
        print(f"\n⚠ {len(report['import_cycles'])} import cycle(s):")
        for c in report["import_cycles"]:
            print("   " + " -> ".join(c))
    else:
        print("\n✓ No import cycles")

    print("\nTop drift offenders (declared purpose vs. actual behavior):")
    for v in report["verdicts"][:10]:
        score = v.get("drift_score", "?")
        bar = "█" * int(score) if isinstance(score, int) else ""
        print(f"\n  [{score:>2}] {v['path']}  {bar}")
        print(f"       declared: {v.get('declared_purpose', '?')}")
        print(f"       observed: {v.get('observed_behavior', '?')}")
        for ev in v.get("evidence", []):
            print(f"         - {ev}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Codebase Autopsy")
    parser.add_argument("repo_path", help="Path to the repo to analyze")
    parser.add_argument("--mock", action="store_true",
                         help="Use mock Bob responses (no BOB_API_KEY / bob CLI needed)")
    args = parser.parse_args()

    report = run_autopsy(args.repo_path, mock=args.mock)
    print_report(report)
