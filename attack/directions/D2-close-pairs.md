# D2. Haskin's +46σ "close pairs" anomaly: reproduce or refute

## Goal

Obtain the precise definition of the statistic behind Brian Haskin's "+46σ
close-pairs" figure, reproduce it on public and independent data, and decide
whether it survives the exact-edge model.

## Why it matters

Everything measured in this project says the random-digit model is right to
within a percent (near misses at 3–6 missing digits, exact k = 2, 3 hits, the
domain statistics of the middle digits). A 46σ anomaly, if it refers to
square–cube digit statistics and is not a modelling artifact, would be the
first evidence of a real obstruction, and the only lead toward a uniqueness
proof. If it is an artifact, saying so precisely closes the last open signal.

## What is known

- The repository owner asked for the definition in
  [nice-numbers-lean issue #1](https://github.com/Janzert/nice-numbers-lean/issues/1)
  ("which exponent pair and which bases your +46σ close-pairs figure refers
  to"). No answer had arrived at the time of writing. The article series
  "Nice Numbers And The Middle Digit Wall" at janzert.com (three parts) is
  where the figure appears; it could not be read from this environment.
- The public API's `numbers` field lists every near miss with at most two
  missing digits for bases 22–49 ([snapshot in p3-obstruction](../p3-obstruction/data/)).
  Our own exact recomputation covers bases 10–35 (`critique/scripts/histogram.c`),
  and the k-nice testbeds give complete exact solution sets.
- Known ways to get tens of sigma that mean nothing: comparing 10⁸–10⁹
  events with the naive model (the edges alone move it by 12–15%, which is
  "hundreds of sigma" at those counts; the exact-edge model M1 removes it,
  [experiments §2](../../critique/experiments.md)); treating dependent events
  as independent (consecutive roots share almost all their edge structure;
  near misses cluster); multiple testing across bases and statistics.

## Plan

1. Get the definition: from the reply to issue #1, or from the articles
   (an agent with web access to janzert.com should read Parts 1–3 and quote
   the statistic and the data it was computed on).
2. Recompute the statistic exactly on the data it was defined on, then on
   our independent data (bases 10–35 recomputed, the public `numbers` field
   for 22–49, and the twice/thrice-nice solution sets).
3. Compute its expectation under three models: naive uniform strings; M1
   (exact edges, uniform middle); the Monte Carlo with exact edges of
   `attack/p3-obstruction/scripts/model_mc.py`. Report the z-score under each,
   with a correct variance (bootstrap over roots if the events are
   dependent).
4. If the excess survives M1 and the variance correction: characterize which
   configurations produce it, test whether it grows with rarity (deficiency
   3, 2, 1, 0), and test the same statistic on the k-nice testbeds where the
   full solution sets are known.

## Deliverables

A note with the definition, the reproduction on each data set, the three
model expectations with honest error bars, and a verdict.

## Stop rules

- Explained by edges or by dependence: close, and say which.
- Survives both with ≥ 5σ on independent data: this becomes the top priority
  of the whole project; report immediately.

## Pitfalls

Do not guess the definition; two plausible readings ("pairs of consecutive
roots both near-nice" and "pairs of digits that collide") give different
statistics. Do not compare against the naive model only.
