#!/usr/bin/env python3
"""Diff every superseded manuscript revision against its replacement.

Emits, per pair:
  out/diffs/<base>.diff          the raw unified diff
  out/version-diffs.json         per-pair classification + hunk inventory
  out/version-diffs.md           a reading copy

Classification is by where the changed lines land in the NEW file: a hunk whose
changed lines sit inside a theorem/lemma/proposition environment is a statement
edit; one inside a proof is a proof edit; one confined to the bibliography is a
citation edit.
"""
import os
import pathlib
ROOT = os.environ.get("OAI_AUDIT_ROOT", "/Users/dereky/oai-math")
REPO = pathlib.Path(ROOT) / "repo" / "preprints"
OUT = pathlib.Path(ROOT) / "out"

import json
import pathlib
import re
import subprocess
import sys
from collections import Counter



ENV_BEGIN = re.compile(r"\\begin\{(theorem|lemma|proposition|corollary|conjecture|"
                       r"definition|remark|claim|assumption|hypothesis|proof|"
                       r"abstract|thebibliography|equation|align|itemize|enumerate)\*?\}")
ENV_END = re.compile(r"\\end\{(theorem|lemma|proposition|corollary|conjecture|"
                     r"definition|remark|claim|assumption|hypothesis|proof|"
                     r"abstract|thebibliography|equation|align|itemize|enumerate)\*?\}")
STMT = {"theorem", "lemma", "proposition", "corollary", "conjecture", "claim"}
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


_CACHE = {}


def env_at(path, lineno):
    """Innermost open environment at 1-indexed lineno of `path`."""
    key = str(path)
    if key not in _CACHE:
        try:
            _CACHE[key] = path.read_text(encoding="utf-8", errors="replace").split("\n")
        except OSError:
            _CACHE[key] = []
    lines = _CACHE[key]
    stack = []
    for i, ln in enumerate(lines[:lineno], 1):
        for m in ENV_BEGIN.finditer(ln):
            stack.append(m.group(1))
        for m in ENV_END.finditer(ln):
            if stack and stack[-1] == m.group(1):
                stack.pop()
            elif m.group(1) in stack:
                stack.remove(m.group(1))
    return stack[-1] if stack else None


def classify(hunks):
    cats = Counter()
    for h in hunks:
        if h["env"] in STMT:
            cats["statement"] += 1
        elif h["env"] == "proof":
            cats["proof"] += 1
        elif h["env"] == "thebibliography" or h["bib"]:
            cats["citation"] += 1
        elif h["env"] in ("abstract",):
            cats["abstract"] += 1
        else:
            cats["body"] += 1
    return cats


def main():
    data = json.loads((OUT / "site_data.json").read_text(encoding="utf-8"))
    (OUT / "diffs").mkdir(parents=True, exist_ok=True)
    report = []

    for s in data["superseded"]:
        cur = s["current"]
        for old in s["older_versions"]:
            a, b = REPO / old / "build", REPO / cur / "build"
            if not a.is_dir() or not b.is_dir():
                continue
            raw = subprocess.run(
                ["diff", "-ru", "--exclude=*.pdf", "--exclude=*.aux", "--exclude=*.log",
                 "--exclude=*.out", str(a), str(b)],
                capture_output=True, text=True).stdout
            slug = re.sub(r"[^A-Za-z0-9-]+", "-", s["base"])[:80]
            (OUT / "diffs" / f"{slug}.diff").write_text(raw, encoding="utf-8")

            files, hunks, cur_file = [], [], None
            for ln in raw.split("\n"):
                if ln.startswith("+++ "):
                    cur_file = ln[4:].split("\t")[0].strip()
                    continue
                if ln.startswith("--- "):
                    continue
                m = HUNK.match(ln)
                if m and cur_file:
                    ln_new = int(m.group(3))
                    n_new = int(m.group(4) or 1)
                    hunks.append({
                        "file": cur_file.replace(str(b) + "/", ""),
                        "line": ln_new,
                        "env": env_at(pathlib.Path(cur_file), ln_new),
                        "bib": (cur_file.endswith(".bib")
                                or "references" in cur_file or "bibliography" in cur_file),
                        "n": n_new,
                    })
            for h in hunks:
                if h["file"] not in files:
                    files.append(h["file"])

            add = sum(1 for l in raw.split("\n") if l.startswith("+") and not l.startswith("+++"))
            rem = sum(1 for l in raw.split("\n") if l.startswith("-") and not l.startswith("---"))
            cats = classify(hunks)
            report.append({
                "base": s["base"], "old": old, "current": cur,
                "files": files, "added": add, "removed": rem,
                "hunks": len(hunks), "categories": dict(cats),
                "unified_bytes": len(raw),
                "envs": dict(Counter(h["env"] or "(top level)" for h in hunks)),
            })

    report.sort(key=lambda r: -(r["added"] + r["removed"]))
    (OUT / "version-diffs.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = ["# What changed between revisions\n",
          "Each row diffs a superseded manuscript directory against the revision that replaced it.\n",
          "| added | removed | hunks | where the changes land | files touched |",
          "|---:|---:|---:|---|---|"]
    for r in report:
        envs = ", ".join(f"{k} x{v}" for k, v in
                         sorted(r["envs"].items(), key=lambda kv: -kv[1]))
        md.append(f"| {r['added']} | {r['removed']} | {r['hunks']} | {envs} | "
                  f"{', '.join(r['files'][:3])}{' …' if len(r['files']) > 3 else ''} |")
    (OUT / "version-diffs.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    for r in report:
        print(f"{r['added']:>5}+ {r['removed']:>5}-  hunks={r['hunks']:>3}  "
              f"{json.dumps(r['categories']):<58} {r['base'][:44]}")
    print(f"\n{len(report)} pairs, {sum(r['unified_bytes'] for r in report)} diff bytes")


if __name__ == "__main__":
    sys.exit(main())
