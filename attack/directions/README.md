# Research directions for the next agents

2026-09-28, written at the end of the session that tested H1–H3 and H5 and
built the middle-digit structure theory. Each direction below has its own
file with goal, bearing on the two outcomes, what is known, a concrete plan,
deliverables, and stop rules. They are ranked by how much they could change
the picture; effort and skills are stated so agents can be matched to them.

**The picture these directions start from.** A second nice number almost
certainly exists (the random model predicts it from about base 120) and no
search can reach it; a proof either way is out of reach of current
mathematics; the cube's middle third is a wall whose structure is now
described exactly ([middle-digits](../middle-digits/REPORT.md)). See
[PROGRESS.md](../../PROGRESS.md).

| Rank | Direction | Could it change the picture? | Effort | Skills |
|---|---|---|---|---|
| 1 | [D1. Exact k = 1 calibration on (1,2)-nice numbers](D1-quasi-nice-calibration.md) | **Yes.** First exact-hit test at distinct digits; a first pass shows 55 hits against 77 expected. A shortfall that survives the refined model would be the first evidence of an obstruction; a match would be the strongest evidence yet that none exists | 1–2 sessions | C, Python, probability |
| 2 | [D2. Haskin's +46σ close-pairs anomaly](D2-close-pairs.md) | **Yes, if it is real.** Needs his definition first | 1 session | data analysis |
| 3 | [D3. A first existence theorem: fixed base, multiplicity k → ∞](D3-existence-llt.md) | **Yes**, as the first rigorous existence result in the family, with the (2,3) case conditional on an open problem | several sessions | analytic number theory (Mauduit–Rivat method) |
| 4 | [D7. Adversarial audit of the September 28 proofs](D7-audit.md) | Protects everything built on them | 1 session | mathematics, code reading |
| 5 | [D4. Machine-checked core in Lean](D4-lean-core.md) | No; makes results durable | 1–2 sessions | Lean 4 |
| 6 | [D5. The overlap join in the public search client](D5-join-in-client.md) | Only the lottery odds, ×3–25 at bases 57–64 | 2–3 sessions | Rust, GPU |
| 7 | [D6. Complete the middle-digit theory](D6-complete-wall-theory.md) | No; completeness | 1–2 sessions | analytic number theory |

**Order of work.** Run D7 early: D3, D4 and D6 build on the proofs it checks.
Run D1 now: it is cheap and the first pass already shows something worth
resolving. Run D2 as soon as Haskin answers the question in
[his issue tracker](https://github.com/Janzert/nice-numbers-lean/issues/1).

**Closed directions. Do not reopen without a new ingredient.** SAT and
constraint solving ([H5](../h5-sat-witness/REPORT.md), [critique](../../critique/experiments.md));
population samplers and hill climbing ([H2](../h2-sampler/REPORT.md));
set-valued middle-digit domains ([H1](../h1-domains/REPORT.md)); structured
root families ([p1-structure](../p1-structure/REPORT.md)); congruence
obstructions ([H3](../h3-covering/REPORT.md) and Haskin's Theorem 5);
repdigits, stretches, affine output words ([RESEARCH_LOG](../../RESEARCH_LOG.md));
any certificate for the cube's middle third built from prefixes, suffixes,
progressions or their statistics ([middle-digits](../middle-digits/REPORT.md)).
Incremental search speedups other than D5 buy 2–3 bases per factor of 10 and
cannot matter.

Files: `quasi_nice.c` and `results/quasi_nice_6_22.jsonl` are the first pass
for D1.
