# openai-math-audit

An independent reading of [openai/math](https://github.com/openai/math), the 719-manuscript
mathematics collection OpenAI published on 6 October 2026.

Nothing here checks whether a theorem is true. What it does is put the repository's own
artifacts side by side and see whether they agree: the manuscript map, the Lean formalization
catalogue, the cross-references between papers, the changelog, and the per-paper withdrawal
notices.

Data as read: 15 October 2026.

## Findings

**1. Lean coverage and structural load are nearly disjoint.**
Cross-references extracted from the LaTeX sources join the 719 manuscripts with 591 directed
citations. The graph is mostly empty: 223 manuscripts cite nothing in the collection and are
cited by nothing, while one paper is cited 16 times. Of the twenty most-cited manuscripts,
**one** has a Lean entry. The single most-cited paper, cited by 16 others, has none.

If a result in this collection is wrong, the blast radius follows the citation graph, and the
citation graph is the part with the least machine checking.

**2. The formalization catalogue grades its own work "unchecked".**
`lean/formalization.yaml` carries `review: status: unchecked`, `status.scope: "Partial
progress."`, and `automation.methods: [agent]`. A Lean entry means a compiler accepted a
declaration that a comparator config points at. It does not mean anyone checked that the
declaration states the theorem the paper claims. "Formalized" and "verified" are different
claims, and the repository makes only the weaker one.

**3. One coverage number, three denominators.**
`README.md` and `history.md` both say 300 of 719 top-line results are formalized, about 42%.
The catalogue enumerates 173 `sources` plus 30 `related_formalizations`. The family map
resolves to 135 of 372 families containing at least one formalized member. Each is a
defensible reading and none is stated next to the others.

**4. The withdrawals were removed cleanly enough to be hard to notice.**
A sign error in a stabilization-trace argument withdrew three manuscripts. Searching every
`.tex`, `.bib` and `.md` file in the tree finds zero references to them from any surviving
manuscript; they are absent from `CONTENTS.md` and `overview.tex`. Only the flat changelog in
`history.md` records that the Hodge/K3 line lost three results.

The withdrawn sources are still recoverable. Their `build/` directories were deleted from the
working tree, but the archived revision each notice cites is present in the object store:

```
git ls-tree -r adc7f1241b42e322a6451854ab7e4b4c146bf78a \
  -- preprints/Algebraicity-of-Weil-classes-on-split-abelian-eightfolds-September-18-2026
```

That makes the withdrawal reasoning checkable against the text it withdraws. Nobody appears to
have done it. **This is the largest open opportunity in the corpus.**

**5. Thirteen revisions are real mathematics; fourteen are bookkeeping.**
Corrections land as a new dated directory beside the old one, so the working tree carries 27
superseded revisions. Diffing each pair separates them cleanly. See [FINDINGS.md](FINDINGS.md).

## The ledger

[`index.html`](index.html) is a browsable ledger: all 372 families, searchable and filterable
by Lean coverage, citation load, and withdrawal status. It is a single self-contained file.

## Data

| File | Contents |
|---|---|
| `data/ledger.json` | Per-family and per-manuscript status: Lean entry, withdrawal, citation degree |
| `data/edges.json` | 644 directed citations, with which signal found each one |
| `data/revision-diffs.json` | Per-pair diff inventory and hunk classification |
| `data/revision-classes.json` | Each revision labelled substantive or citation-bump |
| `data/site_data.json` | The ledger page's embedded dataset |
| `diffs/*.diff` | The 27 raw unified diffs |

## Reproducing

```sh
git clone --depth 1 --filter=blob:none --no-checkout https://github.com/openai/math.git repo
cd repo
git sparse-checkout init --no-cone
git sparse-checkout set '/*.md' '/*.tex' '/lean/formalization.yaml' \
                        '/preprints/*/README.md' '/preprints/*/build/**'
git checkout                      # ~227 MB, no PDFs

python3 tools/build_ledger.py     # parse map + catalogue + changelog, extract citations
python3 tools/make_site_data.py   # fold into the page dataset
python3 tools/diff_versions.py    # diff every superseded revision, classify hunks
python3 tools/classify_revisions.py
python3 tools/show_hunks.py <base-substring> [statement|proof|body|citation]
```

`build_ledger.py` expects the clone at `/Users/dereky/oai-math/repo`; change `REPO` at the top
of the file. Only `PyYAML` is required beyond the standard library.

## Limits

- Nothing here is a proof check. A Lean entry is a compiler accepting a declaration, not a
  verified theorem.
- Citation counts measure references, not dependence. A paper cited 18 times may be cited once
  and referred to afterwards.
- The hunk classifier keys on the enclosing LaTeX environment, so a citation repointed inside a
  proof reads as a proof edit. The substantive/citation split in `revision-classes.json` was
  hand-checked against the raw diffs; individual hunk labels were not.
- Three manuscript directories carry no `build/` tree: the withdrawn papers, whose sources were
  removed from the working copy.
- Citations pointing at a superseded revision are redirected to the revision that replaced it.
  That merge drops 53 edges, most of them self-loops created when a superseded directory cites
  its own replacement.

## Source and licence

Derived from [openai/math](https://github.com/openai/math), Apache-2.0. The manuscript titles,
directory names, changelog text and LaTeX excerpts reproduced here come from that repository.
No PDFs are redistributed. This project's own code and prose are Apache-2.0; see [LICENSE](LICENSE).

Not affiliated with OpenAI.
