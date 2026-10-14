#!/usr/bin/env python3
"""Print selected hunks of one version diff.

usage: show_hunks.py <base-substring> [env ...] [--max N] [--ctx N]

env filters: statement | proof | citation | body | top
Prints the raw unified hunk for each match, newest-file line numbers shown.
"""
import os
import pathlib
ROOT = os.environ.get("OAI_AUDIT_ROOT", "/Users/dereky/oai-math")
REPO = pathlib.Path(ROOT) / "repo" / "preprints"
OUT = pathlib.Path(ROOT) / "out"

import json, pathlib, re, subprocess, sys
from collections import Counter


ENV = r"(theorem|lemma|proposition|corollary|conjecture|definition|remark|claim|assumption|hypothesis|proof|abstract|thebibliography|equation|align|itemize|enumerate)"
BEGIN = re.compile(r"\\begin\{" + ENV + r"\*?\}")
END = re.compile(r"\\end\{" + ENV + r"\*?\}")
STMT = {"theorem", "lemma", "proposition", "corollary", "conjecture", "claim"}
CATS = {"statement": STMT,
        "proof": {"proof"},
        "citation": {"thebibliography"},
        "abstract": {"abstract"},
        "body": {"definition", "remark", "equation", "align", "itemize", "enumerate",
                 "assumption", "hypothesis", "top", None},
        "top": {"top", None}}


def matches(env, want):
    for w in want:
        if w in CATS:
            if env in CATS[w]:
                return True
        elif env == w:
            return True
    return False
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_C = {}
INCLUDE_BIB = False


def env_at(p, n):
    if str(p) not in _C:
        try: _C[str(p)] = p.read_text(encoding="utf-8", errors="replace").split("\n")
        except OSError: _C[str(p)] = []
    stack = []
    for ln in _C[str(p)][:n]:
        for m in BEGIN.finditer(ln): stack.append(m.group(1))
        for m in END.finditer(ln):
            if stack and stack[-1] == m.group(1): stack.pop()
            elif m.group(1) in stack: stack.remove(m.group(1))
    return stack[-1] if stack else "top"


def main():
    argv = sys.argv[1:]
    base, want, mx = None, [], 400
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--max":
            mx = int(argv[i + 1]); i += 2; continue
        if base is None:
            base = a
        else:
            want.append(a)
        i += 1
    want = set(want) or None
    global INCLUDE_BIB
    INCLUDE_BIB = "--all" in argv

    recs = json.loads((OUT / "version-diffs.json").read_text(encoding="utf-8"))
    hit = [r for r in recs if base.lower() in r["base"].lower()]
    if not hit:
        print("no match"); return 1
    r = hit[0]
    a, b = REPO / r["old"] / "build", REPO / r["current"] / "build"
    raw = subprocess.run(["diff", "-ru", "--exclude=*.pdf", "--exclude=*.aux",
                          "--exclude=*.log", "--exclude=*.out", str(a), str(b)],
                         capture_output=True, text=True).stdout
    print(f"### {r['base']}\n    {r['old']}  ->  {r['current']}")
    print(f"    {r['added']}+ {r['removed']}-  hunks={r['hunks']}  {json.dumps(r['categories'])}\n")

    cur, block, shown = None, [], 0
    def flush():
        nonlocal block, shown
        if not block: return
        head, body = block[0], block[1:]
        m = HUNK.match(head)
        if m and cur:
            env = env_at(pathlib.Path(cur), int(m.group(3)))
            if want is None or matches(env, want):
                short = cur.split("/build/")[-1]
                if not INCLUDE_BIB and (short.endswith(".bib") or "references" in short):
                    if not any(ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))
                               and re.search(r"\\\\[a-zA-Z]|\\\\begin|theorem|lemma|proof", ln)
                               for ln in body):
                        block = []
                        return
                shown += 1
                print(f"--- {short}  line {m.group(3)}  [{env}]  ({m.group(0)})")
                for ln in body[:mx]: print(ln)
                print()
        block = []
    for ln in raw.split("\n"):
        if ln.startswith("+++ "):
            flush(); cur = ln[4:].split("\t")[0].strip(); continue
        if ln.startswith("--- ") or ln.startswith("diff -ru"):
            flush(); continue
        if HUNK.match(ln):
            flush(); block = [ln]; continue
        if block: block.append(ln)
    flush()
    print(f"[{shown} hunk(s) shown]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
