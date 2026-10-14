#!/usr/bin/env python3
"""Fold ledger.json into the compact dataset the browsable page embeds."""
import os
import pathlib
ROOT = os.environ.get("OAI_AUDIT_ROOT", "/Users/dereky/oai-math")
REPO = pathlib.Path(ROOT) / "repo"
OUT = pathlib.Path(ROOT) / "out"

import json, pathlib, re

SUB = {"0":"\u2080","1":"\u2081","2":"\u2082","3":"\u2083","4":"\u2084","5":"\u2085",
       "6":"\u2086","7":"\u2087","8":"\u2088","9":"\u2089","+":"\u208a","-":"\u208b",
       "=":"\u208c","(":"\u208d",")":"\u208e","a":"\u2090","e":"\u2091","h":"\u2095",
       "i":"\u1d62","j":"\u2c7c","k":"\u2096","l":"\u2097","m":"\u2098","n":"\u2099",
       "o":"\u2092","p":"\u209a","r":"\u1d63","s":"\u209b","t":"\u209c","u":"\u2094",
       "v":"\u1d65","x":"\u2093"}
SUP = {"0":"\u2070","1":"\u00b9","2":"\u00b2","3":"\u00b3","4":"\u2074","5":"\u2075",
       "6":"\u2076","7":"\u2077","8":"\u2078","9":"\u2079","+":"\u207a","-":"\u207b",
       "=":"\u207c","(":"\u207d",")":"\u207e","n":"\u207f","i":"\u2071"}


def _map(inner, table, marker):
    """Unicode-transcribe an <sub>/<sup> run; fall back to _x / ^x."""
    txt = re.sub(r"<[^>]+>", "", inner)
    if txt and all(c in table for c in txt):
        return "".join(table[c] for c in txt)
    return marker + txt


def clean_title(t):
    """CONTENTS.md titles carry math-typography HTML; transcribe it to plain text."""
    t = re.sub(r"<sub>(.*?)</sub>", lambda m: _map(m.group(1), SUB, "_"), t, flags=re.S)
    t = re.sub(r"<sup>(.*?)</sup>", lambda m: _map(m.group(1), SUP, "^"), t, flags=re.S)
    t = re.sub(r"</?(?:i|b|em|strong)>", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    return t.strip()


led = json.loads((OUT / "ledger.json").read_text(encoding="utf-8"))
edges = json.loads((OUT / "edges.json").read_text(encoding="utf-8"))

indeg, outdeg = {}, {}
for e in edges:
    outdeg[e["citing"]] = outdeg.get(e["citing"], 0) + 1
    indeg[e["cited"]] = indeg.get(e["cited"], 0) + 1

lean_dirs = set()
fam = led["families"]

fams = []
for fid, f in sorted(fam.items()):
    members = []
    for m in f["members"]:
        members.append({
            "d": m,
            "i": indeg.get(m, 0),
            "o": outdeg.get(m, 0),
        })
    fams.append({
        "id": fid,
        "t": clean_title(f["title"]),
        "lean": f["any_formalized"],
        "wd": f["any_withdrawn"],
        "m": members,
    })

# which papers have a Lean entry, straight from the formalization catalogue
import yaml
lean_flag = {}
d = yaml.safe_load(open(REPO / "lean/formalization.yaml"))
for src in d["sources"]:
    m = re.match(r"\.\./preprints/([^/]+)/", src.get("id", ""))
    if m: lean_flag[m.group(1)] = True

withdrawn = {w["dir"] for w in led["withdrawn"]}

data = {
    "counts": led["counts"],
    "claims": led["repo_claims"],
    "leanMeta": led["lean_meta"],
    "withdrawn": led["withdrawn"],
    "superseded": led["superseded_versions"],
    "fams": fams,
    "flags": {d_: {"lean": bool(lean_flag.get(d_)), "wd": d_ in withdrawn}
              for d_ in {m["d"] for f in fams for m in f["m"]}},
    "edges": [{"s": e["citing"], "t": e["cited"]} for e in edges],
}
(OUT / "site_data.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
print("families:", len(fams), "edges:", len(edges), "bytes:", os.path.getsize(OUT / "site_data.json"))
