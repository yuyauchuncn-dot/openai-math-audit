#!/usr/bin/env python3
"""Coarse per-revision characterisation, for the ones a citation bump cannot explain."""
import os
import pathlib
ROOT = os.environ.get("OAI_AUDIT_ROOT", "/Users/dereky/oai-math")
REPO = pathlib.Path(ROOT) / "repo" / "preprints"
OUT = pathlib.Path(ROOT) / "out"

import json, pathlib, re, subprocess
from collections import Counter


recs = json.loads((OUT / "version-diffs.json").read_text(encoding="utf-8"))
BIBENTRY = re.compile(r"^\+(?:@\w+\{)")
CITEKEY = re.compile(r"OAI:[A-Za-z0-9._-]+")

rows = []
for r in recs:
    a, b = REPO / r["old"] / "build", REPO / r["current"] / "build"
    raw = subprocess.run(["diff", "-ru", "--exclude=*.pdf", str(a), str(b)],
                         capture_output=True, text=True).stdout
    # split per file so .bib churn doesn't dominate
    chunks, cur = {}, None
    for ln in raw.split("\n"):
        if ln.startswith("+++ "):
            cur = ln[4:].split("\t")[0].replace(str(b) + "/", ""); chunks[cur] = []
        elif cur and (ln.startswith("+") or ln.startswith("-")) and not ln.startswith(("+++", "---")):
            chunks[cur].append(ln)
    prose = {k: v for k, v in chunks.items()
             if not (k.endswith(".bib") or "references" in k)}
    bib = {k: v for k, v in chunks.items() if k not in prose}
    add_notes = sum(1 for v in prose.values() for l in v if l.startswith("+") and not l.startswith("+++"))
    del_notes = sum(1 for v in prose.values() for l in v if l.startswith("-"))
    newrefs = sum(1 for v in bib.values() for l in v if BIBENTRY.match(l))
    newkeys = sum(1 for v in bib.values() for l in v if l.startswith("+") and CITEKEY.search(l))
    cats = r["categories"]
    stmt = cats.get("statement", 0)
    # a "statement" hunk that only repoints a citation is not a statement edit
    stmt_real = 0
    for v in prose.values():
        pass
    substantive = add_notes > 4 or del_notes > 4
    rows.append({
        "base": r["base"], "old": r["old"], "current": r["current"],
        "add_prose": add_notes, "del_prose": del_notes,
        "add_bib_lines": sum(1 for v in bib.values() for l in v if l.startswith("+")),
        "new_bib_entries": newrefs, "repointed_cites": newkeys,
        "hunks": r["hunks"], "envs": r["envs"], "files": r["files"],
        "kind": "substantive" if substantive else "citation-bump",
    })

rows.sort(key=lambda x: -x["add_prose"])
(OUT / "revision-classes.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

print(f"{'prose+':>6} {'prose-':>6} {'newrefs':>7} {'repoint':>7}  kind           base")
for r in rows:
    print(f"{r['add_prose']:>6} {r['del_prose']:>6} {r['new_bib_entries']:>7} "
          f"{r['repointed_cites']:>7}  {r['kind']:<14} {r['base'][:46]}")
print()
print("citation-bump:", sum(1 for r in rows if r["kind"] == "citation-bump"),
      " substantive:", sum(1 for r in rows if r["kind"] == "substantive"))
print("new external bib entries across substantive:",
      sum(r["new_bib_entries"] for r in rows if r["kind"] == "substantive"))
