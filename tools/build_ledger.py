#!/usr/bin/env python3
"""Build a verification + dependency ledger for the openai/math corpus.

Inputs (all from the sparse clone at REPO):
  CONTENTS.md                      family -> member manuscripts
  lean/formalization.yaml          paper -> Lean declarations, review status
  history.md                       withdrawals / revisions log
  preprints/*/README.md            per-paper withdrawal notices, dates
  preprints/*/build/**/*.{tex,bib} cross-references between papers

Two independent cross-reference signals are used, because they disagree:
  (a) the full URL  .../preprints/<DIR>/<file>.pdf
  (b) the cite key  OAI:<DIR>
"""
import os
import pathlib
ROOT = os.environ.get("OAI_AUDIT_ROOT", "/Users/dereky/oai-math")
REPO = pathlib.Path(ROOT) / "repo"
OUT = pathlib.Path(ROOT) / "out"

import json
import pathlib
import re
import sys
from collections import defaultdict

import yaml



FAMILY_RE = re.compile(r"^\*\*(\d{3})\.\s+(.*?)\.\*\*\s*(.*)$")
MEMBER_RE = re.compile(r"&emsp;\[(.*?)\]\((preprints/[^)]+)\)")
WITHDRAWN_RE = re.compile(r"withdraw", re.I)
XREF_URL_RE = re.compile(r"preprints/([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+\.pdf)")
XREF_KEY_RE = re.compile(r"OAI:([A-Za-z0-9._-]+)")
DATE_SUFFIX_RE = re.compile(
    r"-(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"-\d{1,2}-\d{4}$"
)
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def parse_contents():
    fams, cur = {}, None
    for line in (REPO / "CONTENTS.md").read_text(encoding="utf-8").splitlines():
        m = FAMILY_RE.match(line)
        if m:
            cur = {"id": m.group(1), "title": m.group(2).strip(),
                   "blurb": m.group(3).strip(), "members": []}
            fams[m.group(1)] = cur
            continue
        if cur is None:
            continue
        for _t, path in MEMBER_RE.findall(line):
            cur["members"].append(path.split("/")[1])
    return fams


def parse_lean():
    d = yaml.safe_load((REPO / "lean/formalization.yaml").read_text(encoding="utf-8"))
    formalized = {}
    for src in d.get("sources", []):
        m = re.match(r"\.\./preprints/([^/]+)/", src.get("id", ""))
        if m:
            formalized[m.group(1)] = {"title": src.get("title", "")}
    for r in d.get("related_formalizations", []):
        m = re.match(r"\.\./preprints/([^/]+)/", r.get("id", ""))
        if m:
            formalized.setdefault(m.group(1), {"title": "(related)"})
    return {
        "formalized_dirs": formalized,
        "n_declarations": len(d.get("status", {}).get("main_results", [])),
        "n_sources": len(d.get("sources", [])),
        "n_related": len(d.get("related_formalizations", [])),
        "review_status": d.get("review", {}).get("status"),
        "scope": d.get("status", {}).get("scope"),
        "automation": d.get("automation", {}),
    }


def parse_history():
    txt = (REPO / "history.md").read_text(encoding="utf-8")
    withdrawn, dates, section = [], [], None
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith("**Withdrawals"):
            section = "w"; continue
        if s.startswith("**Fixes") or s.startswith("**Additional"):
            section = "f"; continue
        if s.startswith("## "):
            dates.append(s[3:]); section = None; continue
        if section == "w" and s.startswith("- "):
            withdrawn.append(s[2:].strip())
    return {"withdrawn_titles": withdrawn, "log_dates": dates}


def paper_readmes():
    out = {}
    for rd in sorted((REPO / "preprints").iterdir()):
        if not rd.is_dir():
            continue
        f, rec = rd / "README.md", {"withdrawn": False, "notice_date": None, "title": rd.name}
        if f.exists():
            txt = f.read_text(encoding="utf-8", errors="replace")
            first = txt.split("\n", 1)[0] if txt else ""
            if WITHDRAWN_RE.search(first):
                rec["withdrawn"] = True
            d = re.search(r"\*\*Withdrawn on ([^*]+)\.\*\*", txt)
            if d:
                rec["notice_date"] = d.group(1).strip()
            t = re.match(r"#\s*\[?(?:Withdrawal notice:\s*)?(.*?)\]?\(paper\.pdf\)", txt)
            if t:
                rec["title"] = t.group(1).strip()
        out[rd.name] = rec
    return out


def build_edges(dirs, redirect):
    """Directed edges: (citing, cited) -> signal counts.

    Direction is the whole point -- in-degree is what says a result is
    load-bearing -- so the key is never sorted. A citation to a superseded
    revision is redirected to the revision that replaced it: same result,
    corrected text.
    """
    def canon(d):
        return redirect.get(d, d)

    known = set(dirs)
    edges = defaultdict(lambda: {"url": 0, "key": 0})
    for d in dirs:
        build = REPO / "preprints" / d / "build"
        if not build.exists():
            continue
        for f in build.rglob("*"):
            if f.suffix not in (".tex", ".bib") or not f.is_file():
                continue
            txt = f.read_text(encoding="utf-8", errors="replace")
            for tgt, _ in set(XREF_URL_RE.findall(txt)):
                src, dst = canon(d), canon(tgt)
                if tgt in known and src != dst:
                    edges[(src, dst)]["url"] += 1
            for tgt in set(XREF_KEY_RE.findall(txt)):
                src, dst = canon(d), canon(tgt)
                if tgt in known and src != dst:
                    edges[(src, dst)]["key"] += 1
    return edges


def main():
    fams, lean, hist = parse_contents(), parse_lean(), parse_history()
    readmes = paper_readmes()
    dirs = sorted(readmes)

    fam_of = {}
    for fid, f in fams.items():
        for m in f["members"]:
            fam_of.setdefault(m, fid)

    fdirs = set(lean["formalized_dirs"])
    withdrawn_dirs = {d for d in dirs if readmes[d]["withdrawn"]}

    # orphans = dirs on disk that the family map does not list
    orphans = [d for d in dirs if d not in fam_of]

    # superseded: same base name as a listed dir but an older date
    base_of = defaultdict(list)
    for d in dirs:
        base_of[DATE_SUFFIX_RE.sub("", d)].append(d)

    def date_key(d):
        m = re.search(r"-([A-Za-z]+)-(\d{1,2})-(\d{4})$", d)
        return (int(m.group(3)), MONTHS.index(m.group(1)), int(m.group(2))) if m else (0, 0, 0)

    superseded = []
    for base, group in base_of.items():
        if len(group) > 1:
            group = sorted(group, key=date_key)
            live = [g for g in group if g in fam_of]
            dead = [g for g in group if g not in fam_of]
            if live and dead:
                superseded.append({"base": base, "current": live[-1],
                                   "older_versions": dead})

    redirect = {}
    for s_ in superseded:
        for o_ in s_["older_versions"]:
            redirect[o_] = s_["current"]
    edges = build_edges(dirs, redirect)

    indeg, outdeg = defaultdict(int), defaultdict(int)
    for src, dst in edges:
        indeg[dst] += 1
        outdeg[src] += 1
    deg = defaultdict(int)
    for d in dirs:
        deg[d] = indeg[d] + outdeg[d]

    downstream = [
        {"citing": src, "cited": dst, **info}
        for (src, dst), info in edges.items()
        if src in withdrawn_dirs or dst in withdrawn_dirs
    ]

    fam_formalized = {fid for fid, f in fams.items() if any(m in fdirs for m in f["members"])}

    report = {
        "counts": {
            "manuscript_dirs": len(dirs),
            "families_in_contents": len(fams),
            "members_mapped": len(fam_of),
            "orphan_dirs": len(orphans),
            "orphans_withdrawn": len([o for o in orphans if o in withdrawn_dirs]),
            "papers_with_lean_entry": len(fdirs),
            "lean_main_result_declarations": lean["n_declarations"],
            "families_with_any_formalized_member": len(fam_formalized),
            "withdrawn_dirs": len(withdrawn_dirs),
            "edges": len(edges),
            "isolated_papers_no_crossrefs": sum(1 for d in dirs if indeg[d] + outdeg[d] == 0),
        },
        "repo_claims": {
            "README_formalized_pct": "~42% (300 / 719 top-line results)",
            "README_manuscripts": 719,
            "README_families": 372,
            "history_log_dates": hist["log_dates"],
            "withdrawal_notice_dates": sorted({readmes[d]["notice_date"] for d in withdrawn_dirs}),
        },
        "lean_meta": {"review_status": lean["review_status"], "scope": lean["scope"],
                      "automation": lean["automation"]},
        "withdrawn": [{"dir": d, "notice_date": readmes[d]["notice_date"],
                       "title": readmes[d]["title"]} for d in sorted(withdrawn_dirs)],
        "downstream_of_withdrawn": downstream,
        "superseded_versions": superseded,
        "orphan_dirs": orphans,
        "most_depended_on": sorted(
            ({"dir": d, "in_degree": indeg[d], "out_degree": outdeg[d],
              "family": fam_of.get(d), "lean": d in fdirs,
              "withdrawn": d in withdrawn_dirs} for d in dirs),
            key=lambda r: -r["in_degree"])[:30],
        "unformalized_high_cited": sorted(
            ({"dir": d, "family": fam_of.get(d), "in_degree": indeg[d],
              "out_degree": outdeg[d], "withdrawn": d in withdrawn_dirs}
             for d in dirs if d not in fdirs and indeg[d] > 0),
            key=lambda r: -r["in_degree"])[:50],
        "families": {k: {"title": v["title"], "n_members": len(v["members"]),
                         "members": v["members"],
                         "any_formalized": any(m in fdirs for m in v["members"]),
                         "any_withdrawn": any(m in withdrawn_dirs for m in v["members"])}
                     for k, v in fams.items()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ledger.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "edges.json").write_text(json.dumps(
        [{"citing": s_, "cited": t_, **i} for (s_, t_), i in sorted(edges.items())],
        indent=1), encoding="utf-8")

    c = report["counts"]
    print(json.dumps(c, indent=2))
    print("\nlean_meta:", json.dumps(report["lean_meta"], ensure_ascii=False))
    print("withdrawn dirs:", sorted(withdrawn_dirs))
    print("downstream of withdrawn:", len(downstream), downstream[:6])
    print("superseded version pairs:", len(superseded))
    for s in superseded[:6]:
        print("   ", s["base"][:60], "| current:", s["current"][-24:], "| older:", [o[-24:] for o in s["older_versions"]])
    print("\nTOP HUBS (in-degree), lean? family:")
    for x in report["most_depended_on"][:15]:
        print(f"   {x['in_degree']:3d}  lean={str(x['lean'])[:5]:5s} fam={str(x['family']):>4s}  {x['dir'][:62]}")


if __name__ == "__main__":
    sys.exit(main())
