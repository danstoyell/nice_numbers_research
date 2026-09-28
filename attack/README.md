# Parallel attack, started 2026-09-26

Goal: a second nice number (explicit, or proved to exist) or a proof that 69
in base 10 is the only one. Nothing else counts.

**2026-09-27 review:** [Five next hypotheses and research priorities](NEXT_HYPOTHESES.md)
assesses these results alongside `critique/` and the earlier research and
proposes bounded intermediate tests.

**2026-09-28 follow-up:** four of the five were tested, one folder each. None
changes the picture: the two search ideas (H1, H2) and the solver idea (H5)
fail on the k-nice testbed, and the congruence question (H3) is settled the
way the model predicts, with a theorem for the modulus b+1.

| Folder | Hypothesis | Verdict |
|---|---|---|
| `h1-domains/` | H1. Exact domains of the cube's middle digits reject whole batches | **Killed.** With 2–3 free root digits the middle domains are the whole alphabet and add zero rejections; with 1 free digit they add at most 9×10⁻⁶ of the roots (threshold was 10%). 23 configurations, 5.4×10⁹ roots, all 60 known witnesses preserved. [Report](h1-domains/REPORT.md) |
| `h2-sampler/` | H2. Subset simulation with digit proposals beats uniform sampling | **Killed.** At equal budget it finds 0–0.8× as many distinct witnesses as uniform sampling, worse as the base grows; seeds collapse to 1–12% of the ancestors and no episode ever reaches the final level by conditioning. [Report](h2-sampler/REPORT.md) |
| `h3-covering/` | H3. Pandigital splits realize every residue pair the digit sum allows | **Confirmed and partly proved.** Exhaustive for every M ≤ b² coprime to b at bases 10–18 (1,057 cases, no failure); theorem with proof for M = b+1 in every base b ≥ 10; class DP for b²−1 to base 24. No congruence obstruction exists at these moduli. [Report](h3-covering/REPORT.md) |
| `h5-sat-witness/` | H5. SAT finds a first witness faster on satisfiable instances | **Killed.** Time to a first verified witness is 10⁵ times the enumerator's on thrice-nice bases 9–10 (85–285 s against 0.2–2 ms), and from twice-nice base 14 on the solver finds nothing within 400–600 s where the enumerator needs at most 0.08 s. [Report](h5-sat-witness/REPORT.md) |
| — | H4. Conditioned low-order moments cannot force a hit | Not attempted (lowest bearing on either goal). |

Five hypotheses run in parallel, one folder each. Each folder gets a
`REPORT.md` with the verdict, the numbers behind it, and code.

| Folder | Path | Hypothesis | Killed if |
|---|---|---|---|
| `p1-structure/` | 1 | A structured family of (n, b) boosts the chance of niceness by about e^(cb), like the families behind the Hadamard-668 and rank-31 records | Family size × boost stays ≪ 1 at every base ≤ 1000 |
| `p1-algorithm/` | 1 | An algorithm certifies middle digits for many candidates at once, beating edge enumeration | No gain over the edge rate on the k-nice testbed |
| `p3-analogues/` | 3 | Exact twice- and thrice-nice counts at rarer bases fall below the random model | Counts match the model |
| `p3-obstruction/` | 3 | The deficiency-2 shortfall has an arithmetic cause that could scale to a nonexistence proof | Shortfall explained or gone |
| `p2-existence/` | 2 | Some very large base provably contains a nice number | No approach closes its exponent bookkeeping |
