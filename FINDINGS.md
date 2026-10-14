# What changed between revisions

OpenAI's `history.md` records one round of corrections, dated 7 October 2026: three
withdrawals, fourteen manuscripts "revised with proof repairs", and thirteen more "updated to
cite the revised editions". The repository keeps every superseded revision on disk as a dated
directory beside its replacement, so each of those claims can be checked against the artifacts.

There are 27 such pairs. `tools/diff_versions.py` diffs each one; `diffs/*.diff` holds the raw
output.

## The split

Diffing all 27 separates them without ambiguity. Fourteen pairs change exactly two lines: the
`\date{}`, and one `\href` repointed at a revised companion paper.

```diff
-\date{September 23, 2026}
+\date{October 7, 2026}
```

```diff
-\href{.../The-rational-Hodge-conjecture-for-CM-abelian-varieties-September-30-2026/paper.pdf}{OAI:...September-30-2026},
+\href{.../The-rational-Hodge-conjecture-for-CM-abelian-varieties-October-6-2026/paper.pdf}{OAI:...October-6-2026},
```

The other thirteen change actual mathematics. Ranked by lines of prose (bibliography churn
excluded, so a paper that merely pulled in new references does not rank high on that alone):

| prose + | prose − | new external refs | manuscript |
|---:|---:|---:|---|
| 2693 | 606 | 0 | Uniform real-Lipschitz surfaces on the triangular lattice |
| 583 | 181 | 4 | The joint scaling limit of critical Ashkin–Teller currents |
| 523 | 63 | 3 | Finite ordinary minimal model programs on compact Kähler fourfolds |
| 297 | 103 | 0 | The Gaussian free field limit of integer Lipschitz heights, two-arc boundary data |
| 118 | 26 | 0 | Incompressible Box Transport and Finite Computation |
| 102 | 57 | 2 | Log abundance for compact Kähler spaces under logarithmic Iitaka subadditivity |
| 55 | 41 | 0 | Taming implies compatibility on four-manifolds |
| 52 | 4 | 0 | Termination of generalized log canonical flips on compact Kähler fourfolds |
| 33 | 23 | 0 | Conditional good minimal models for compact Kähler fourfolds |
| 22 | 11 | 0 | Numerical semiampleness of nef adjoint classes on compact Kähler manifolds |
| 8 | 6 | 0 | Gaussian free field limits of weighted integer Lipschitz heights |
| 7 | 6 | 0 | Deforming hypersymplectic four-manifolds to hyperkähler triples |
| 6 | 1 | 0 | Termination of generalized canonical flips on compact Kähler fourfolds |

Note the boundary case. `history.md` counts fourteen repairs, because it counts "removed an
obsolete introductory citation" in the exact Birch–Swinnerton-Dyer paper as a fix. That pair
changes five lines and no mathematics. The artifacts support thirteen.

## Three of the thirteen

### 1. Uniform real-Lipschitz surfaces on the triangular lattice

2693 lines added against 606 removed across five files. This is close to a rewrite.

A lemma gained a quantitative clause it did not have:

> There are also absolute `p_*, b_* > 0` such that every nonfixed positive string site has
> conditional probability at least `p_*` to have height greater than `b_*`, without any
> restriction on its distance from strand tips or Dirichlet boundary.

Its hypothesis tightened in the same pass: *"provided no prescribed new positive site is one of
those upper-bounded sites"* became *"provided neither a prescribed new positive site nor the
tested string site is one of those upper-bounded sites"*.

The proof gained the observation that makes the new clause work:

> Every string site has an oppositely sign-constrained nearest neighbor, so Lipschitzness on
> their edge bounds both heights in absolute value by one. This supplies the local anchor for
> the stated patches and also for a singleton patch at any string site, including one far from
> the tips.

This is the crux of the revision. The argument needed a uniform lower bound on a height at a
site arbitrarily far from the boundary, and the only global hypothesis available was
Lipschitzness, which by itself anchors nothing. The nearest-neighbour pairing supplies the
anchor. Once it is in place, the surrounding argument goes through.

Two further changes in the same manuscript point the same way. A lemma's uniformity clause was
rewritten and its fixed region doubled, from `𝔅_6R` to `𝔅_12R`. And the proof of that lemma was
replaced wholesale with new machinery: a filtration `ℱ_{r,s}`, explicit definitions of when a
pair of records is *open* or *live*, a forbidden-contact condition, and a scheme that updates
one of the two records at a time.

### 2. The Gaussian free field limit of integer Lipschitz heights, two-arc boundary data

297 lines added, 103 removed. A lemma's proof was replaced end to end. The old argument was
probabilistic and nested:

> choose the constant boundary residue uniformly from the four Gray residues. Require enclosing
> loops in three separated annuli, with the inner annulus `Λ_2n \ Λ_n` … annuli at radii `n`,
> `4n`, and `16n` fit inside a cut of a fixed sufficiently large multiple of `n`. … The lower
> loop estimate and `\cref{lem:gray}` give a probability at least `c_0^3` for the three-loop
> event.

The replacement is topological:

> The circuits in neighboring annuli must intersect. Their enclosed inner balls overlap, and
> each inner ball protrudes outside the other's outer ball, since `ε < 1/50`. Disjoint Jordan
> curves have disjoint or nested interiors, and these two geometric properties exclude both
> possibilities. … The resulting closed walk stays `O(r)` from the center polygon and is
> homotopic to it in the complement of the radius-`n` ball. Extracting a simple circuit with
> nonzero winding gives the required circuit between radii `n` and `2n`.

The original tried to nest three loops that never meet. The repair shows neighbouring circuits
*cannot* avoid meeting, and extracts a winding circuit from the intersections. Different idea,
not a repaired calculation.

### 3. Incompressible Box Transport and Finite Computation

118 lines added, 26 removed, three hunks. Smallest of the substantive set and the most
instructive about a failure mode.

A proposition was restated. The old version leaned on a word:

> An **effective** smooth mean-zero force `g` on `T_L^3` has an **effective** mean-zero
> potential `φ` satisfying `Δφ = div g`. Replacing `(g,p)` by `(g−∇φ, p−φ)` preserves velocity
> and makes the force solenoidal. Uniform mixed-derivative bounds, temporal `L²` bounds of their
> spatial suprema, and separately imposed time periodicity, eventual stationarity, or orderwise
> decay bounds are preserved.

"Effective" is doing no work: it is never defined, and the sentence asserts preservation of
several families of bounds without saying at what rate. The replacement names the operator,
fixes the domain, defines the norms, and states a labelled estimate:

> Let `g` be a smooth force on `[0,∞)×T_L^3` with zero spatial mean at each time. There is a
> unique smooth mean-zero potential `φ` satisfying `Δφ = div g`. Put `Qg = ∇φ` and `Pg = g − Qg`.
> Then `Pg` is solenoidal and mean zero … Use normalized spatial measure, frequencies
> `ξ_k = 2πk/L`, and norms `‖G‖_{H^s}² = Σ (1+|ξ_k|²)^s |Ĝ(k)|²` …

The downstream proof then cites that estimate by label instead of asserting bounds in prose.

## What the three have in common

None of them is an arithmetic slip. Each is a uniformity or precision failure:

- A proof that needed a bound to hold at every site, with no mechanism that delivers it at every
  site. Fixed by finding the mechanism.
- A proof whose strategy could not work, because the objects it wanted to keep apart provably
  meet. Fixed by a different strategy.
- A statement written in a vocabulary that carried no definition.

This matters for how the collection gets checked. A step-by-step verifier does not catch the
first kind: every local step is fine, and the failure is in the scope of a quantifier. It does
not catch the third either, because nothing there is false, only imprecise. Both classes need a
reader who asks whether the statement says what the proof shows.

## The withdrawn three

The sign error in the stabilization-trace argument took down three manuscripts on 6 October:
*Algebraicity of Weil classes on split abelian eightfolds*, *Algebraicity of Kuga–Satake
correspondences for K3 surfaces*, and *The rational Hodge conjecture for products of K3
surfaces*.

They were removed cleanly. No surviving manuscript cites any of them, and none appears in
`CONTENTS.md` or `overview.tex`. Only `history.md` records the loss.

Their sources are not gone. Each withdrawal notice names the revision it was withdrawn from, and
that revision is in the object store:

```sh
git ls-tree -r adc7f1241b42e322a6451854ab7e4b4c146bf78a \
  -- preprints/Algebraicity-of-Weil-classes-on-split-abelian-eightfolds-September-18-2026
# README.md, paper.pdf, build/paper.tex, build/macros.tex, build/references.tex,
# build/sections/01-introduction.tex … 12-spread.tex
```

The notice says the proof "assigns each reverse stabilization trace sign `+1`" where the correct
sign is `−1`, so the signed double-point count is `−2m` rather than zero, and the
Eliashberg–Murphy cancellation theorem invoked at that step has an unmet hypothesis. That
argument can be read against the exact text it withdraws. Doing so is the single highest-value
piece of work left in this corpus.

## Caveat on the classification

Hunk labels in `data/revision-diffs.json` come from the enclosing LaTeX environment, so a
citation repointed inside a proof is labelled a proof edit. The substantive/bump split in
`data/revision-classes.json` is by prose line count and was checked by hand against all 27 raw
diffs. Individual hunk labels were not hand-checked.
