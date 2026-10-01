# Nice numbers research

A number n is *nice* in base b if the digits of n² and n³, written in base b,
together use every digit from 0 to b−1 exactly once. In base 10,
69² = 4761 and 69³ = 328509. No other nice number is known in any base.

This repository is an attempt to find a second nice number, or to prove that
69 is the only one.

**Status: neither has been achieved.** The evidence says a second nice number
almost certainly exists, most likely somewhere above base 100. It also says
no known search method or proof technique can reach it.

## Start here

- [PROGRESS.md](PROGRESS.md): a plain-English summary of results, search
  improvements and dead ends.
- [critique/](critique/README.md): an independent review of the first phase,
  with the random-digit model and the odds.
- [attack/](attack/README.md): a parallel test of five hypotheses plus a
  literature survey. Each folder has a `REPORT.md` with its verdict.
- [RESEARCH_LOG.md](RESEARCH_LOG.md): proofs, experiments and dead ends from
  the first phase. The detailed notes are in [research/](research/).

## Layout

| Folder | Contents |
|---|---|
| `research/` | Notes and proofs for each first-phase track |
| `scripts/`, `native/`, `tests/` | Python scripts, C ports (in progress) and verifier tests |
| `results/` | Raw outputs of first-phase experiments |
| `critique/` | Review, supporting experiments, and dated snapshots of public search data |
| `attack/` | One folder per hypothesis, each with code, results and a report |

## Running things

Most scripts need only Python 3. The enumerators need a C compiler (`clang`).
To run the exact verifier's tests:

```sh
python3 -m unittest discover -s tests
```

Each report lists the commands that reproduce its results.

## How this was made

Most of the code, proofs and reports here were written by AI agents (Claude,
by Anthropic), directed by the repository owner. The proofs are informal, not
machine-checked. Every claimed nice number was re-verified with exact integer
arithmetic.

## Related work

- The public distributed search: [wasabipesto/nice](https://github.com/wasabipesto/nice)
- Machine-checked proofs of the basic obstructions, by Brian Haskin:
  [Janzert/nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean)

## License

All code, proofs, reports and data in this repository are released under the
[MIT License](LICENSE).

A few files contain code copied or ported from other MIT-licensed projects.
Those parts keep their original copyright notices:

- `overlap-join/gpu/src/client_check.rs` (verbatim) and
  `attack/d5-client-join/client_count.c` (a C port): Copyright (c) 2024
  wasabipesto, from [wasabipesto/nice](https://github.com/wasabipesto/nice)
  ([license](https://github.com/wasabipesto/nice/blob/fe1b0b8/LICENSE)).
- `research/lean/NiceCore.lean`, §A (verbatim): Copyright (c) 2026 Brian
  Haskin, from [Janzert/nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean)
  ([license](https://github.com/Janzert/nice-numbers-lean/blob/HEAD/LICENSE)).
