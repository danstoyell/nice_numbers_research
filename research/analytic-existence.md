# Can existing digit-distribution theorems settle existence?

Reviewed 2026-09-24. This is a literature applicability check, not a proof
that no applicable theorem exists.

James Maynard's *Primes and polynomials with restricted digits*, Theorem
1.2, gives asymptotic counts for polynomial values omitting a digit in
sufficiently large fixed bases, subject to local conditions. Its proof
uses Fourier factorization across independent digit positions. The
paper takes the digit length to infinity with the base fixed; implicit
constants may depend on the base. [Primary paper](https://arxiv.org/pdf/1510.07711)

That theorem does not immediately yield a nice number. We need a joint
condition on two powers of the same integer, all digits pairwise distinct,
and total digit length exactly equal to the varying base. Distinctness
couples digit positions, so the factorization used for fixed allowed-digit
sets is unavailable in its stated form. Growing the length with a fixed
base also eventually violates the nice-number length condition.

*Squares with a positive proportion of preassigned digits* proves
asymptotics with a limited proportion of digits prescribed. It imposes
local compatibility assumptions; even its conjectured optimal proportion
for the relevant square theorem is one-half. It does not control the cube
of the same root or prohibit repetitions among all the unassigned digits.
[Primary paper](https://webusers.imj-prg.fr/~cathy.swaenepoel/article_squares_AM.pdf)

These results support investigating analytic methods, but applying either
as an existence proof here would be unjustified. A successful argument
would need quantitative joint square/cube estimates for a permutation
constraint, uniform enough as the base and digit length grow together.
No such estimate has been established in this investigation.
