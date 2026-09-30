/-
  NiceCore.lean
  =============

  Machine-checked versions of three elementary results from the nice-number
  research repository (direction D4), in Lean 4 core — no Mathlib, no `sorry`,
  no `native_decide` — written in the style of, and on the digit definitions of,
  Brian Haskin's `NiceNumbers.lean` (https://github.com/Janzert/nice-numbers-lean).

  §A  Haskin's definitions and lemmas that the rest uses, copied verbatim, so the
      file checks on its own.  Delete §A to append §B–§E to his file.

  §B  **The batch digit formula** (Lemma 1 of attack/middle-digits/REPORT.md).
      For `n = c + b^k·m`, the digit at position `P` of `n³` is
      `(A mod b^(P+1)) / b^P` with
      `A = c³ mod b^(P+1) + (3c² mod b^(P+1-k))·m·b^k
           + (3c mod b^(P+1-2k))·m²·b^(2k) + (1 mod b^(P+1-3k))·m³·b^(3k)`,
      i.e. `⌊b·{x₀ + θ₁m + θ₂m² + θ₃m³}⌋` — for every `P`, no hypothesis `P ≥ k`
      (`batch_cube_digit`; the square: `batch_square_digit`).  Corollaries:
      digits below `k` are constant along a batch, for every exponent
      (`batch_low_digit_const`); for `P + 1 ≤ 2k` the digit depends on `m` only
      through `(3c² mod b^(P+1-k))·m mod b^(P+1-k)` (`batch_cube_rotation_only`,
      and `batch_square_rotation_only` with `2c`); for `P + 1 ≤ 3k` the cubic
      term drops (`batch_cube_quadratic`).

  §C  **Subset sums of an interval** (Lemma 1 of attack/h3-covering/REPORT.md),
      as an iff: for `r ≤ m`, `σ` is the sum of an `r`-subset of
      `{u,…,u+m-1}` iff `r·u + tri r ≤ σ ≤ r·u + tri r + r·(m-r)`
      (`subset_sums_iff`).  The new half is `subset_bounds`, the converse of
      Haskin's `pick_sum` that his NOTES list as missing.

  §D  **Covering modulo `b+1`** (Theorem 1 of the H3 report), as an iff: under
      the report's class-size hypothesis, a residue pair mod `b+1` is realised
      by a pandigital split with non-zero leading digits iff it passes the
      digit-sum test (`cover_b_plus_one`, `realised_compatible`,
      `cover_b_plus_one_iff`).

  §E  **The Corollary, for every base `b ≥ 10`** (`cover_nice_lengths`), with
      the bases the inequality misses settled by kernel-checked certificates
      (`certOK`, `realised_of_cert`), and its form for candidates:
      `cover_candidate` — for every `b ≥ 10` and every `n` whose square and cube
      have `b` digits between them, the residue pairs mod `b+1` of pandigital
      splits with those lengths are exactly the pairs the digit sum permits.
      The report's inequality (even `b ≥ 28`, odd `b ≥ 21`) is proved with the
      odd threshold lowered to 17, both thresholds sharp (`cover_cond_large`,
      `cover_cond_twentysix_fails`, `cover_cond_fifteen_fails`).

  Check with `lean NiceCore.lean` from this directory (the `lean-toolchain` file
  pins v4.33.0, Haskin's version).  The `#print axioms` block at the end should
  list only `propext`, `Classical.choice`, `Quot.sound`, or a subset.
-/

set_option linter.unusedVariables false

namespace Nice

/-- Number of base-`b` digits of `x`; zero has none. -/
def numDigits (b x : Nat) : Nat :=
  if h : 1 < b ∧ 0 < x then numDigits b (x / b) + 1 else 0
decreasing_by exact Nat.div_lt_self h.2 h.1

theorem numDigits_zero (b : Nat) : numDigits b 0 = 0 := by rw [numDigits]; simp

theorem eq_zero_of_numDigits_eq_zero {b x : Nat} (hb : 1 < b)
    (h : numDigits b x = 0) : x = 0 := by
  rcases Nat.eq_zero_or_pos x with h0 | h0
  · exact h0
  · rw [numDigits, dif_pos ⟨hb, h0⟩] at h; omega

/-- `numDigits b x = k+1` means exactly `b^k ≤ x < b^(k+1)`. -/
theorem bounds_of_numDigits {b : Nat} (hb : 1 < b) :
    ∀ x k, numDigits b x = k + 1 → b ^ k ≤ x ∧ x < b ^ (k + 1) := by
  intro x
  induction x using Nat.strongRecOn with
  | _ x ih =>
    intro k hk
    have hx : 0 < x := by
      rcases Nat.eq_zero_or_pos x with rfl | h
      · rw [numDigits_zero] at hk; omega
      · exact h
    rw [numDigits, dif_pos ⟨hb, hx⟩] at hk
    have hkk : numDigits b (x / b) = k := by omega
    have hdm : b * (x / b) + x % b = x := Nat.div_add_mod x b
    have hmod : x % b < b := Nat.mod_lt _ (by omega)
    match k with
    | 0 =>
      have h0 : x / b = 0 := eq_zero_of_numDigits_eq_zero hb hkk
      rw [h0, Nat.mul_zero, Nat.zero_add] at hdm
      refine ⟨by rw [Nat.pow_zero]; omega, ?_⟩
      rw [Nat.pow_one]; omega
    | (j+1) =>
      have hlt : x / b < x := Nat.div_lt_self hx hb
      have hIH := ih (x / b) hlt j hkk
      refine ⟨?_, ?_⟩
      · calc b ^ (j+1) = b ^ j * b := rfl
          _ ≤ (x / b) * b := Nat.mul_le_mul_right b hIH.1
          _ ≤ x := Nat.div_mul_le_self x b
      · calc x < b * (x / b) + b := by omega
          _ = b * (x / b + 1) := by rw [Nat.mul_add, Nat.mul_one]
          _ ≤ b * b ^ (j+1) := Nat.mul_le_mul_left b (by omega)
          _ = b ^ (j+1+1) := (Nat.mul_comm b (b^(j+1))).trans (Nat.pow_succ b (j+1)).symm

/-- The base-`b` digits of `x`, least significant first. -/
def digits (b x : Nat) : List Nat :=
  if h : 1 < b ∧ 0 < x then x % b :: digits b (x / b) else []
decreasing_by exact Nat.div_lt_self h.2 h.1

theorem digits_zero (b : Nat) : digits b 0 = [] := by rw [digits]; simp

theorem digits_step {b x : Nat} (hb : 1 < b) (hx : 0 < x) :
    digits b x = x % b :: digits b (x / b) := by rw [digits, dif_pos ⟨hb, hx⟩]

/-- Occurrences of `v` in `l`.  Core's `List.count` would do; this keeps the
section self-contained and reduces in the kernel. -/
def occ (v : Nat) : List Nat → Nat
  | [] => 0
  | a :: l => (if a = v then 1 else 0) + occ v l

theorem occ_cons_self (v : Nat) (l : List Nat) : occ v (v :: l) = 1 + occ v l := by
  show (if v = v then 1 else 0) + occ v l = 1 + occ v l
  rw [if_pos rfl]

theorem occ_append (v : Nat) : ∀ l1 l2 : List Nat,
    occ v (l1 ++ l2) = occ v l1 + occ v l2 := by
  intro l1
  induction l1 with
  | nil => intro l2; show occ v l2 = 0 + occ v l2; omega
  | cons a t ih =>
    intro l2
    show (if a = v then 1 else 0) + occ v (t ++ l2)
        = ((if a = v then 1 else 0) + occ v t) + occ v l2
    rw [ih]
    omega

/-- `n` is **`(e1,e2)`-pandigital in base `b`**: the base-`b` digits of `n^e1`
and of `n^e2`, taken together, contain every value `< b` exactly once.  This is
the definition an exhaustive search tests for; §1-§3 above use only its two
numerical consequences. -/
def Pandigital (b e1 e2 n : Nat) : Prop :=
  ∀ v, v < b → occ v (digits b (n ^ e1) ++ digits b (n ^ e2)) = 1

/-- Value of a digit list, least significant digit first. -/
def valOf (b : Nat) : List Nat → Nat
  | [] => 0
  | d :: ds => d + b * valOf b ds

/-- Congruence as divisibility of the (truncated) difference. -/
theorem dvd_sub_iff_mod_eq {b x y : Nat} (hb : 0 < b) (hyx : y ≤ x) :
    b ∣ x - y ↔ x % b = y % b := by
  constructor
  · rintro ⟨k, hk⟩
    have hx : x = y + b * k := by omega
    rw [hx, Nat.add_mul_mod_self_left]
  · intro h
    have hdx : b * (x / b) + x % b = x := Nat.div_add_mod x b
    have hdy : b * (y / b) + y % b = y := Nat.div_add_mod y b
    have hq : y / b ≤ x / b := Nat.div_le_div_right hyx
    obtain ⟨t, ht⟩ : ∃ t, x / b = y / b + t := ⟨x / b - y / b, by omega⟩
    have hmul : b * (y / b + t) = b * (y / b) + b * t := Nat.mul_add b _ _
    rw [ht] at hdx
    exact ⟨t, by omega⟩

/-- Cancelling a common summand under `%`. -/
theorem mod_add_cancel {b c u v : Nat} (hb : 0 < b) (h : (u + c) % b = (v + c) % b) :
    u % b = v % b := by
  rcases Nat.le_total u v with hle | hle
  · have h1' : u + c ≤ v + c := by omega
    have hd : b ∣ v + c - (u + c) := (dvd_sub_iff_mod_eq hb h1').mpr h.symm
    have he : v + c - (u + c) = v - u := by omega
    rw [he] at hd
    exact ((dvd_sub_iff_mod_eq hb hle).mp hd).symm
  · have h1' : v + c ≤ u + c := by omega
    have hd : b ∣ u + c - (v + c) := (dvd_sub_iff_mod_eq hb h1').mpr h
    have he : u + c - (v + c) = u - v := by omega
    rw [he] at hd
    exact (dvd_sub_iff_mod_eq hb hle).mp hd

theorem occ_nil (v : Nat) : occ v [] = 0 := rfl

/-- `[s, s+1, …, s+n-1]`. -/
def run (s : Nat) : Nat → List Nat
  | 0 => []
  | n + 1 => s :: run (s + 1) n

/-- `p(p-1)/2`, without the division. -/
def tri : Nat → Nat
  | 0 => 0
  | p + 1 => tri p + p

theorem run_length (s n : Nat) : (run s n).length = n := by
  induction n generalizing s with
  | zero => rfl
  | succ k ih => show (run (s+1) k).length + 1 = k + 1; rw [ih]

theorem run_sum (s : Nat) : ∀ n, (run s n).sum = n * s + tri n := by
  intro n
  induction n generalizing s with
  | zero => simp [run, tri]
  | succ k ih =>
    show s + (run (s+1) k).sum = _
    rw [ih (s+1)]
    show s + (k * (s+1) + tri k) = (k+1) * s + (tri k + k)
    rw [Nat.mul_succ, Nat.succ_mul]
    omega

/-- `run` splits at any point. -/
theorem run_add (s m : Nat) : ∀ n, run s (m + n) = run s m ++ run (s + m) n := by
  intro n
  induction m generalizing s with
  | zero => simp [run]
  | succ k ih =>
    show run s (k + 1 + n) = _
    have : k + 1 + n = (k + n) + 1 := by omega
    rw [this]
    show s :: run (s+1) (k + n) = (s :: run (s+1) k) ++ run (s + (k+1)) n
    rw [ih (s+1)]
    show s :: (run (s+1) k ++ run (s + 1 + k) n) = s :: (run (s+1) k ++ run (s + (k+1)) n)
    rw [show s + 1 + k = s + (k+1) from by omega]

theorem run_succ (s n : Nat) : run s (n + 1) = run s n ++ [s + n] := by
  have h := run_add s n 1
  simpa [run] using h

/-- Split `run s (p+q)` into a `p`-element sublist and its `q`-element
complement, so that the first has sum `p·s + tri p + ν`. -/
def pick : Nat → Nat → Nat → Nat → List Nat × List Nat
  | s, 0,     q,     _ => ([], run s q)
  | s, p + 1, 0,     _ => (run s (p + 1), [])
  | s, p + 1, q + 1, ν =>
      if q + 1 ≤ ν then
        (((pick s p (q + 1) (ν - (q + 1))).1) ++ [s + p + q + 1],
         (pick s p (q + 1) (ν - (q + 1))).2)
      else
        ((pick s (p + 1) q ν).1,
         ((pick s (p + 1) q ν).2) ++ [s + p + q + 1])
termination_by _ p q _ => p + q

theorem pick_len1 (s p q ν : Nat) : (pick s p q ν).1.length = p := by
  induction s, p, q, ν using pick.induct with
  | case1 s q ν => simp [pick]
  | case2 s p ν => simp [pick, run_length]
  | case3 s p q ν h ih => rw [pick]; simp [h, ih]
  | case4 s p q ν h ih => rw [pick]; simp [h, ih]

theorem pick_len2 (s p q ν : Nat) : (pick s p q ν).2.length = q := by
  induction s, p, q, ν using pick.induct with
  | case1 s q ν => simp [pick, run_length]
  | case2 s p ν => simp [pick]
  | case3 s p q ν h ih => rw [pick]; simp [h, ih]
  | case4 s p q ν h ih => rw [pick]; simp [h, ih]

theorem pick_occ (v : Nat) : ∀ s p q ν,
    occ v (pick s p q ν).1 + occ v (pick s p q ν).2 = occ v (run s (p + q)) := by
  intro s p q ν
  induction s, p, q, ν using pick.induct with
  | case1 s q ν => rw [pick]; simp [occ_nil]
  | case2 s p ν => rw [pick]; simp [occ_nil]
  | case3 s p q ν h ih =>
    rw [pick, if_pos h]
    show occ v ((pick s p (q+1) (ν - (q+1))).1 ++ [s + p + q + 1])
        + occ v (pick s p (q+1) (ν - (q+1))).2 = _
    rw [occ_append, show p + 1 + (q + 1) = (p + (q+1)) + 1 from by omega, run_succ,
        occ_append, ← ih, show s + (p + (q+1)) = s + p + q + 1 from by omega]
    omega
  | case4 s p q ν h ih =>
    rw [pick, if_neg h]
    show occ v (pick s (p+1) q ν).1
        + occ v ((pick s (p+1) q ν).2 ++ [s + p + q + 1]) = _
    rw [occ_append, show p + 1 + (q + 1) = ((p+1) + q) + 1 from by omega, run_succ,
        occ_append, ← ih, show s + ((p+1) + q) = s + p + q + 1 from by omega]
    omega

theorem pick_sum_total : ∀ s p q ν,
    (pick s p q ν).1.sum + (pick s p q ν).2.sum = (run s (p + q)).sum := by
  intro s p q ν
  induction s, p, q, ν using pick.induct with
  | case1 s q ν => rw [pick]; simp
  | case2 s p ν => rw [pick]; simp
  | case3 s p q ν h ih =>
    rw [pick, if_pos h]
    show ((pick s p (q+1) (ν - (q+1))).1 ++ [s + p + q + 1]).sum
        + (pick s p (q+1) (ν - (q+1))).2.sum = _
    rw [List.sum_append, show p + 1 + (q + 1) = (p + (q+1)) + 1 from by omega, run_succ,
        List.sum_append, ← ih, show s + (p + (q+1)) = s + p + q + 1 from by omega]
    simp; omega
  | case4 s p q ν h ih =>
    rw [pick, if_neg h]
    show (pick s (p+1) q ν).1.sum
        + ((pick s (p+1) q ν).2 ++ [s + p + q + 1]).sum = _
    rw [List.sum_append, show p + 1 + (q + 1) = ((p+1) + q) + 1 from by omega, run_succ,
        List.sum_append, ← ih, show s + ((p+1) + q) = s + p + q + 1 from by omega]
    simp; omega

/-- **Subset-sum contiguity.**  The `p`-element sublists of a run of `p+q`
consecutive integers realise every sum from the minimum to the minimum plus
`p·q`, with no gaps — this is the one combinatorial fact Theorem 5 needs. -/
theorem pick_sum : ∀ s p q ν, ν ≤ p * q →
    (pick s p q ν).1.sum = p * s + tri p + ν := by
  intro s p q ν
  induction s, p, q, ν using pick.induct with
  | case1 s q ν => intro h; rw [pick]; simp [tri]; omega
  | case2 s p ν =>
    intro h
    simp only [Nat.mul_zero, Nat.le_zero_eq] at h
    subst h
    rw [pick]
    show (run s (p+1)).sum = _
    rw [run_sum]
    simp only [Nat.succ_eq_add_one]
    omega
  | case3 s p q ν h ih =>
    intro hν
    simp only [Nat.succ_eq_add_one] at hν
    have hexp : (p + 1) * (q + 1) = p * (q + 1) + (q + 1) := Nat.succ_mul p (q+1)
    have hle : ν - (q + 1) ≤ p * (q + 1) := by omega
    rw [pick, if_pos h]
    show ((pick s p (q+1) (ν - (q+1))).1 ++ [s + p + q + 1]).sum = _
    rw [List.sum_append, ih hle]
    show p * s + tri p + (ν - (q+1)) + (s + p + q + 1 + 0) = (p+1) * s + (tri p + p) + ν
    rw [Nat.succ_mul]
    omega
  | case4 s p q ν h ih =>
    intro _
    have hle : ν ≤ (p + 1) * q := by
      rcases Nat.eq_zero_or_pos q with rfl | hq
      · omega
      · have : q ≤ (p+1) * q := Nat.le_mul_of_pos_left q (by omega)
        omega
    rw [pick, if_neg h]
    exact ih hle

/-- The value at index `m`, read through `drop` so that no `Fin` is needed. -/
def nth (l : List Nat) (m : Nat) : Nat := (l.drop m).headD 0

theorem nth_ne_zero : ∀ (l : List Nat), occ 0 l = 0 → ∀ m, m < l.length → nth l m ≠ 0 := by
  intro l
  induction l with
  | nil => intro _ m hm; exact absurd hm (by simp)
  | cons x xs ih =>
    intro h0 m hm
    have hx : x ≠ 0 ∧ occ 0 xs = 0 := by
      have : (if x = 0 then 1 else 0) + occ 0 xs = 0 := h0
      by_cases hx0 : x = 0
      · rw [if_pos hx0] at this; omega
      · exact ⟨hx0, by rw [if_neg hx0] at this; omega⟩
    cases m with
    | zero => show (x :: xs).headD 0 ≠ 0; exact hx.1
    | succ i => exact ih hx.2 i (by simpa using hm)

theorem nth_append_left : ∀ (l1 : List Nat) (l2 : List Nat) (m : Nat), m < l1.length →
    nth (l1 ++ l2) m = nth l1 m := by
  intro l1
  induction l1 with
  | nil => intro l2 m hm; exact absurd hm (by simp)
  | cons x xs ih =>
    intro l2 m hm
    cases m with
    | zero => rfl
    | succ i => exact ih l2 i (by simpa using hm)

theorem nth_append_right : ∀ (l1 : List Nat) (l2 : List Nat) (m : Nat), l1.length ≤ m →
    nth (l1 ++ l2) m = nth l2 (m - l1.length) := by
  intro l1
  induction l1 with
  | nil => intro l2 m _; rfl
  | cons x xs ih =>
    intro l2 m hm
    cases m with
    | zero => exact absurd hm (by simp)
    | succ i =>
      have h : xs.length ≤ i := by simpa using hm
      show nth (xs ++ l2) i = nth l2 (i + 1 - (xs.length + 1))
      rw [ih l2 i h]
      congr 1
      omega

/-- Dropping the zeros of a list: same sum, same non-zero values. -/
def dropZeros : List Nat → List Nat
  | [] => []
  | x :: xs => if x = 0 then dropZeros xs else x :: dropZeros xs

theorem dropZeros_occ_zero : ∀ l : List Nat, occ 0 (dropZeros l) = 0 := by
  intro l
  induction l with
  | nil => rfl
  | cons x xs ih =>
    show occ 0 (if x = 0 then dropZeros xs else x :: dropZeros xs) = 0
    by_cases h : x = 0
    · rw [if_pos h]; exact ih
    · rw [if_neg h]; show (if x = 0 then 1 else 0) + occ 0 (dropZeros xs) = 0
      rw [if_neg h]; omega

theorem dropZeros_occ {v : Nat} (hv : v ≠ 0) : ∀ l : List Nat, occ v (dropZeros l) = occ v l := by
  intro l
  induction l with
  | nil => rfl
  | cons x xs ih =>
    show occ v (if x = 0 then dropZeros xs else x :: dropZeros xs)
        = (if x = v then 1 else 0) + occ v xs
    by_cases h : x = 0
    · rw [if_pos h, ih, if_neg (by omega : ¬ x = v)]; omega
    · rw [if_neg h]; show (if x = v then 1 else 0) + occ v (dropZeros xs) = _
      rw [ih]

theorem dropZeros_sum : ∀ l : List Nat, (dropZeros l).sum = l.sum := by
  intro l
  induction l with
  | nil => rfl
  | cons x xs ih =>
    show (if x = 0 then dropZeros xs else x :: dropZeros xs).sum = x + xs.sum
    by_cases h : x = 0
    · rw [if_pos h, ih, h]; omega
    · rw [if_neg h]; show x + (dropZeros xs).sum = _; rw [ih]

theorem mem_of_occ_pos : ∀ (l : List Nat) (t : Nat), 0 < occ t l → t ∈ l := by
  intro l
  induction l with
  | nil => intro t h; exact absurd h (by simp [occ_nil])
  | cons x xs ih =>
    intro t h
    by_cases hx : x = t
    · exact hx ▸ List.mem_cons_self
    · refine List.mem_cons_of_mem _ (ih t ?_)
      have hh : occ t (x :: xs) = (if x = t then 1 else 0) + occ t xs := rfl
      rw [if_neg hx] at hh
      omega

theorem occ_run_lt : ∀ n s v, v < s → occ v (run s n) = 0 := by
  intro n
  induction n with
  | zero => intro s v _; rfl
  | succ k ih =>
    intro s v hv
    show (if s = v then 1 else 0) + occ v (run (s+1) k) = 0
    rw [if_neg (by omega), ih (s+1) v (by omega)]

/-- Every value below `b` occurs exactly once in `run 0 b`. -/
theorem occ_run : ∀ n s v, s ≤ v → v < s + n → occ v (run s n) = 1 := by
  intro n
  induction n with
  | zero => intro s v h1' h2'; omega
  | succ k ih =>
    intro s v h1' h2'
    show (if s = v then 1 else 0) + occ v (run (s+1) k) = 1
    by_cases h : s = v
    · rw [if_pos h, occ_run_lt k (s+1) v (by omega)]
    · rw [if_neg h, ih (s+1) v (by omega) (by omega)]

/-- Digit `i` of `x` in base `b`, counting from the least significant. -/
def slot (b i x : Nat) : Nat := x / b ^ i % b

/-- A slot sees only the low `i+1` digits: this is the p-adic boundary, stated. -/
theorem slot_of_mod {b i x y : Nat} (h : x % b ^ (i + 1) = y % b ^ (i + 1)) :
    slot b i x = slot b i y := by
  have hp : b ^ (i + 1) = b ^ i * b := Nat.pow_succ b i
  show x / b ^ i % b = y / b ^ i % b
  rw [← Nat.mod_mul_right_div_self x (b ^ i) b, ← Nat.mod_mul_right_div_self y (b ^ i) b,
      ← hp, h]

/-- Hence `n mod b^(i+1)` pins slot `i` of `n^e` — two slots per digit of `n`. -/
theorem slot_pow_of_mod {b i x y e : Nat} (h : x % b ^ (i + 1) = y % b ^ (i + 1)) :
    slot b i (x ^ e) = slot b i (y ^ e) := by
  refine slot_of_mod ?_
  rw [Nat.pow_mod, h, ← Nat.pow_mod]

/-! ## §B  The batch digit formula — Lemma 1 of the middle-digit report

A search batch fixes the top and bottom digits of a root and frees a block of
digits at positions `k, k+1, …`.  Writing `c` for the root with the free block
zeroed, the batch is `n(m) = c + b^k·m`.  Lemma 1 says that the digit of `n(m)³`
at any position `P` is `⌊b·{x₀ + θ₁m + θ₂m² + θ₃m³}⌋`, where

    x₀ = (c³ mod b^(P+1)) / b^(P+1)
    θ₁ = (3c² mod b^(P+1-k)) / b^(P+1-k)
    θ₂ = (3c mod b^(P+1-2k)) / b^(P+1-2k)     (0 if P+1 ≤ 2k)
    θ₃ = 1 / b^(P+1-3k)                       (0 if P+1 ≤ 3k).

Multiplying through by `b^(P+1)` turns this into a statement about one natural
number,

    A = c³ mod b^(P+1) + (3c² mod b^(P+1-k))·m·b^k
          + (3c mod b^(P+1-2k))·m²·b^(2k) + (1 mod b^(P+1-3k))·m³·b^(3k),

namely `A = b^(P+1)·(x₀ + θ₁m + θ₂m² + θ₃m³)`, and the digit is
`⌊b·{A/b^(P+1)}⌋ = (A mod b^(P+1)) / b^P` (`slot_eq_mod_div`).  The four
coefficient residues use truncated subtraction on purpose: when `P+1 ≤ j·k`
the modulus is `b^0 = 1`, the residue is `0`, and that is exactly the report's
"else 0".  So one formula covers every zone, and **no hypothesis `P ≥ k` is
needed**: below `k` the formula still holds and says the digit is constant.

The whole proof is one engine, `mul_pow_mod_tail`: a term `a·b^j` seen modulo
`b^N` depends on `a` only modulo `b^(N-j)`. -/

/-- A slot is `⌊b·{x/b^(i+1)}⌋`, written in ℕ: the residue mod `b^(i+1)`, divided
by `b^i`. -/
theorem slot_eq_mod_div (b i x : Nat) : slot b i x = x % b ^ (i + 1) / b ^ i := by
  show x / b ^ i % b = _
  rw [Nat.pow_succ, Nat.mod_mul_right_div_self]

/-- **The engine.**  Modulo `b^N`, the term `a·b^j` sees `a` only modulo `b^(N-j)`.
With truncated subtraction this is uniform: if `j ≥ N` both sides are `0`. -/
theorem mul_pow_mod_tail (b a j N : Nat) :
    a * b ^ j % b ^ N = a % b ^ (N - j) * b ^ j % b ^ N := by
  obtain ⟨w, hw⟩ : b ^ N ∣ b ^ (N - j) * b ^ j := by
    rw [← Nat.pow_add]; exact Nat.pow_dvd_pow b (by omega)
  have hsplit : a * b ^ j
      = a % b ^ (N - j) * b ^ j + b ^ N * (w * (a / b ^ (N - j))) := by
    have ha := Nat.mod_add_div a (b ^ (N - j))
    calc a * b ^ j = (a % b ^ (N - j) + b ^ (N - j) * (a / b ^ (N - j))) * b ^ j := by
          rw [ha]
      _ = a % b ^ (N - j) * b ^ j + (b ^ (N - j) * b ^ j) * (a / b ^ (N - j)) := by
          rw [Nat.add_mul, Nat.mul_assoc, Nat.mul_comm (a / _) (b ^ j), ← Nat.mul_assoc]
      _ = a % b ^ (N - j) * b ^ j + b ^ N * (w * (a / b ^ (N - j))) := by
          rw [hw, Nat.mul_assoc]
  rw [hsplit, Nat.add_mul_mod_self_left]

/-- Two coefficients that agree modulo `b^(N-j)` give the same term modulo `b^N`. -/
theorem mul_pow_congr {b a a' j N : Nat} (h : a % b ^ (N - j) = a' % b ^ (N - j)) :
    a * b ^ j % b ^ N = a' * b ^ j % b ^ N := by
  rw [mul_pow_mod_tail b a, mul_pow_mod_tail b a', h]

theorem add_mod_congr {n x x' y y' : Nat} (hx : x % n = x' % n) (hy : y % n = y' % n) :
    (x + y) % n = (x' + y') % n := by
  rw [Nat.add_mod, hx, hy, ← Nat.add_mod]

/-- The binomial expansion of a batch cube, in ℕ. -/
theorem batch_cube_expand (c y m : Nat) :
    (c + y * m) ^ 3 = c ^ 3 + 3 * c ^ 2 * m * y + 3 * c * m ^ 2 * y ^ 2 + m ^ 3 * y ^ 3 := by
  grind

theorem batch_square_expand (c y m : Nat) :
    (c + y * m) ^ 2 = c ^ 2 + 2 * c * m * y + m ^ 2 * y ^ 2 := by
  grind

/-- Reducing a coefficient before multiplying by `m` changes nothing modulo the
tail. -/
theorem coeff_mod_mul (a m B : Nat) : a % B * m % B = a * m % B := Nat.mod_mul_mod a m B

/--
**Lemma 1, cube, as a congruence.**  Modulo `b^N`, the cube of the batch root
`c + b^k·m` equals the four-term polynomial in `m` whose coefficients are the
residues `c³ mod b^N`, `3c² mod b^(N-k)`, `3c mod b^(N-2k)` and `1 mod b^(N-3k)`.
No hypothesis on `N` or `k`.
-/
theorem batch_cube_mod (b c k m N : Nat) :
    (c + b ^ k * m) ^ 3 % b ^ N
      = (c ^ 3 % b ^ N
          + (3 * c ^ 2 % b ^ (N - k)) * m * b ^ k
          + (3 * c % b ^ (N - 2 * k)) * m ^ 2 * b ^ (2 * k)
          + (1 % b ^ (N - 3 * k)) * m ^ 3 * b ^ (3 * k)) % b ^ N := by
  have h2 : (b ^ k) ^ 2 = b ^ (2 * k) := by rw [← Nat.pow_mul, Nat.mul_comm]
  have h3 : (b ^ k) ^ 3 = b ^ (3 * k) := by rw [← Nat.pow_mul, Nat.mul_comm]
  rw [batch_cube_expand, h2, h3]
  refine add_mod_congr (add_mod_congr (add_mod_congr ?_ ?_) ?_) ?_
  · rw [Nat.mod_mod]
  · refine mul_pow_congr ?_
    rw [coeff_mod_mul]
  · refine mul_pow_congr ?_
    rw [coeff_mod_mul]
  · refine mul_pow_congr ?_
    rw [coeff_mod_mul, Nat.one_mul]

/-- **Lemma 1, square, as a congruence.** -/
theorem batch_square_mod (b c k m N : Nat) :
    (c + b ^ k * m) ^ 2 % b ^ N
      = (c ^ 2 % b ^ N
          + (2 * c % b ^ (N - k)) * m * b ^ k
          + (1 % b ^ (N - 2 * k)) * m ^ 2 * b ^ (2 * k)) % b ^ N := by
  have h2 : (b ^ k) ^ 2 = b ^ (2 * k) := by rw [← Nat.pow_mul, Nat.mul_comm]
  rw [batch_square_expand, h2]
  refine add_mod_congr (add_mod_congr ?_ ?_) ?_
  · rw [Nat.mod_mod]
  · refine mul_pow_congr ?_
    rw [coeff_mod_mul]
  · refine mul_pow_congr ?_
    rw [coeff_mod_mul, Nat.one_mul]

/--
**Lemma 1 (cube).**  The digit at position `P` of `(c + b^k·m)³` is
`⌊b·{A/b^(P+1)}⌋ = (A mod b^(P+1)) / b^P`, where `A = b^(P+1)·(x₀ + θ₁m + θ₂m² + θ₃m³)`
is the four-term polynomial of the report.  Every position `P`, every `k`, every
`m`, every base.
-/
theorem batch_cube_digit (b c k m P : Nat) :
    slot b P ((c + b ^ k * m) ^ 3)
      = (c ^ 3 % b ^ (P + 1)
          + (3 * c ^ 2 % b ^ (P + 1 - k)) * m * b ^ k
          + (3 * c % b ^ (P + 1 - 2 * k)) * m ^ 2 * b ^ (2 * k)
          + (1 % b ^ (P + 1 - 3 * k)) * m ^ 3 * b ^ (3 * k)) % b ^ (P + 1) / b ^ P := by
  rw [slot_eq_mod_div, batch_cube_mod]

/-- **Lemma 1 (square).** -/
theorem batch_square_digit (b c k m P : Nat) :
    slot b P ((c + b ^ k * m) ^ 2)
      = (c ^ 2 % b ^ (P + 1)
          + (2 * c % b ^ (P + 1 - k)) * m * b ^ k
          + (1 % b ^ (P + 1 - 2 * k)) * m ^ 2 * b ^ (2 * k)) % b ^ (P + 1) / b ^ P := by
  rw [slot_eq_mod_div, batch_square_mod]

/-- The digit really is determined by the four residues: two batches whose
residues agree have the same digit at `P` for every `m`.  (Stated for the cube;
this is the form "depends only on these terms" takes.) -/
theorem batch_cube_digit_of_residues {b c c' k m P : Nat}
    (h0 : c ^ 3 % b ^ (P + 1) = c' ^ 3 % b ^ (P + 1))
    (h1 : 3 * c ^ 2 % b ^ (P + 1 - k) = 3 * c' ^ 2 % b ^ (P + 1 - k))
    (h2 : 3 * c % b ^ (P + 1 - 2 * k) = 3 * c' % b ^ (P + 1 - 2 * k)) :
    slot b P ((c + b ^ k * m) ^ 3) = slot b P ((c' + b ^ k * m) ^ 3) := by
  rw [batch_cube_digit, batch_cube_digit, h0, h1, h2]

/-! ### Corollaries: the zones -/

/-- **Below the free block the digits are constant along the batch**, for every
exponent: position `P < k` sees `n` only modulo `b^(P+1)`, which `b^k·m` does not
touch. -/
theorem batch_low_digit_const {b c k m P : Nat} (e : Nat) (hP : P < k) :
    slot b P ((c + b ^ k * m) ^ e) = slot b P (c ^ e) := by
  refine slot_pow_of_mod ?_
  obtain ⟨w, hw⟩ : b ^ (P + 1) ∣ b ^ k := Nat.pow_dvd_pow b (by omega)
  rw [hw, Nat.mul_assoc, Nat.add_mul_mod_self_left]

/-- **The rotation zone** `P + 1 ≤ 2k` (so `k ≤ P < 2k` is its interesting part):
the quadratic and cubic terms vanish modulo `b^(P+1)`, and the digit is the
coding of the rotation `m ↦ (3c² mod b^(P+1-k))·m mod b^(P+1-k)`. -/
theorem batch_cube_rotation {b c k m P : Nat} (hP : P + 1 ≤ 2 * k) :
    slot b P ((c + b ^ k * m) ^ 3)
      = (c ^ 3 % b ^ (P + 1)
          + (3 * c ^ 2 % b ^ (P + 1 - k)) * m % b ^ (P + 1 - k) * b ^ k)
          % b ^ (P + 1) / b ^ P := by
  rw [batch_cube_digit]
  have e2 : P + 1 - 2 * k = 0 := by omega
  have e3 : P + 1 - 3 * k = 0 := by omega
  rw [e2, e3]
  simp only [Nat.pow_zero, Nat.mod_one, Nat.zero_mul, Nat.add_zero]
  congr 1
  exact add_mod_congr rfl (mul_pow_congr (by rw [Nat.mod_mod]))

/-- **Hence in the rotation zone the digit depends on `m` only through
`(3c² mod b^(P+1-k))·m mod b^(P+1-k)`** — the statement in the D4 brief. -/
theorem batch_cube_rotation_only {b c k m m' P : Nat} (hP : P + 1 ≤ 2 * k)
    (h : (3 * c ^ 2 % b ^ (P + 1 - k)) * m % b ^ (P + 1 - k)
        = (3 * c ^ 2 % b ^ (P + 1 - k)) * m' % b ^ (P + 1 - k)) :
    slot b P ((c + b ^ k * m) ^ 3) = slot b P ((c + b ^ k * m') ^ 3) := by
  rw [batch_cube_rotation hP, batch_cube_rotation hP, h]

/-- The same two statements for the square: slope `2c`. -/
theorem batch_square_rotation {b c k m P : Nat} (hP : P + 1 ≤ 2 * k) :
    slot b P ((c + b ^ k * m) ^ 2)
      = (c ^ 2 % b ^ (P + 1)
          + (2 * c % b ^ (P + 1 - k)) * m % b ^ (P + 1 - k) * b ^ k)
          % b ^ (P + 1) / b ^ P := by
  rw [batch_square_digit]
  have e2 : P + 1 - 2 * k = 0 := by omega
  rw [e2]
  simp only [Nat.pow_zero, Nat.mod_one, Nat.zero_mul, Nat.add_zero]
  congr 1
  exact add_mod_congr rfl (mul_pow_congr (by rw [Nat.mod_mod]))

theorem batch_square_rotation_only {b c k m m' P : Nat} (hP : P + 1 ≤ 2 * k)
    (h : (2 * c % b ^ (P + 1 - k)) * m % b ^ (P + 1 - k)
        = (2 * c % b ^ (P + 1 - k)) * m' % b ^ (P + 1 - k)) :
    slot b P ((c + b ^ k * m) ^ 2) = slot b P ((c + b ^ k * m') ^ 2) := by
  rw [batch_square_rotation hP, batch_square_rotation hP, h]

/-- **The quadratic zone** `P + 1 ≤ 3k`: the cubic term vanishes, and the digit
is the coding of a quadratic sequence in `m`. -/
theorem batch_cube_quadratic {b c k m P : Nat} (hP : P + 1 ≤ 3 * k) :
    slot b P ((c + b ^ k * m) ^ 3)
      = (c ^ 3 % b ^ (P + 1)
          + (3 * c ^ 2 % b ^ (P + 1 - k)) * m * b ^ k
          + (3 * c % b ^ (P + 1 - 2 * k)) * m ^ 2 * b ^ (2 * k)) % b ^ (P + 1) / b ^ P := by
  rw [batch_cube_digit]
  have e3 : P + 1 - 3 * k = 0 := by omega
  rw [e3]
  simp only [Nat.pow_zero, Nat.mod_one, Nat.zero_mul, Nat.add_zero]

/-! ### Non-vacuity and sharpness

The formula is an identity, so the guard here is different from an
impossibility theorem's: the witnesses check that it computes the right digit
on real numbers (69 in base 10, and a base-30 batch where every residue is
genuinely reduced), that the rotation zone really rotates (the digit is *not*
constant along the batch), and that the moduli are sharp — shrinking the tail
modulus `b^(P+1-k)` by one factor of `b` gives a wrong digit. -/

/-- `69 = 9 + 10·6`, `69³ = 328509`: the formula reads every digit of the cube
correctly, one batch of the only known nice number. -/
theorem sixtynine_batch_digits : ∀ P, P < 6 →
    slot 10 P ((9 + 10 ^ 1 * 6) ^ 3)
      = (9 ^ 3 % 10 ^ (P + 1)
          + (3 * 9 ^ 2 % 10 ^ (P + 1 - 1)) * 6 * 10 ^ 1
          + (3 * 9 % 10 ^ (P + 1 - 2 * 1)) * 6 ^ 2 * 10 ^ (2 * 1)
          + (1 % 10 ^ (P + 1 - 3 * 1)) * 6 ^ 3 * 10 ^ (3 * 1)) % 10 ^ (P + 1) / 10 ^ P := by
  decide

/-- The six digits it reads are `9,0,5,8,2,3` — those of `328509`. -/
theorem sixtynine_cube_slots :
    (List.range 6).map (fun P => slot 10 P (69 ^ 3)) = [9, 0, 5, 8, 2, 3] := by decide

/-- A base-30 batch with `k = 2` and a middle position `P = 8` (the nice-number
root length there is 6, so the cube's middle third is positions 6–11), with
`c = (20·30² + 7·30 + 3)·30³ + 17·30 + 11` chosen so that every coefficient residue is a genuine
reduction.  The formula agrees with the cube for all 30 values of the free digit. -/
theorem base_thirty_batch : ∀ m, m < 30 →
    slot 30 8 ((491751521 + 30 ^ 2 * m) ^ 3)
      = (491751521 ^ 3 % 30 ^ 9
          + (3 * 491751521 ^ 2 % 30 ^ 7) * m * 30 ^ 2
          + (3 * 491751521 % 30 ^ 5) * m ^ 2 * 30 ^ 4
          + (1 % 30 ^ 3) * m ^ 3 * 30 ^ 6) % 30 ^ 9 / 30 ^ 8 := by
  decide +kernel

/-- …and there every residue is a real reduction, not the identity. -/
theorem base_thirty_batch_reduces :
    491751521 ^ 3 ≠ 491751521 ^ 3 % 30 ^ 9 ∧ 3 * 491751521 ^ 2 ≠ 3 * 491751521 ^ 2 % 30 ^ 7
      ∧ 3 * 491751521 ≠ 3 * 491751521 % 30 ^ 5 := by decide

/-- **The rotation zone rotates**: at base 10, `k = 2`, position `P = 2`, the digit
of `(c + 100m)³` takes several values as `m` varies, so `batch_cube_rotation_only`
is not the statement that the digit is constant. -/
theorem rotation_zone_moves :
    (List.range 10).map (fun m => slot 10 2 ((13 + 10 ^ 2 * m) ^ 3))
      = [1, 8, 5, 2, 9, 6, 3, 0, 7, 4] := by decide

/-- **The tail modulus is sharp.**  Shrinking `b^(P+1-k)` to `b^(P-k)` in the
linear coefficient gives the wrong digit: same batch as `rotation_zone_moves`,
`m = 1`. -/
theorem batch_tail_sharp :
    slot 10 2 ((13 + 10 ^ 2 * 1) ^ 3)
      ≠ (13 ^ 3 % 10 ^ 3 + (3 * 13 ^ 2 % 10 ^ (2 - 2)) * 1 * 10 ^ 2) % 10 ^ 3 / 10 ^ 2 := by
  decide

/-- **The zone boundary is sharp**: the rotation form needs `P + 1 ≤ 2k`.  At
`P = 2k-1+1 = 2k` (here `k = 1`, `P = 2`) the quadratic term is live and the
rotation-only formula is wrong. -/
theorem rotation_zone_boundary_sharp :
    slot 10 2 ((9 + 10 ^ 1 * 6) ^ 3)
      ≠ (9 ^ 3 % 10 ^ 3 + (3 * 9 ^ 2 % 10 ^ (3 - 1)) * 6 % 10 ^ (3 - 1) * 10 ^ 1)
          % 10 ^ 3 / 10 ^ 2 := by
  decide

/-! ## §C  Subset sums of an interval — Lemma 1 of the H3 covering report

**Lemma.**  For `r ≤ m`, the sums of the `r`-element subsets of
`{u, u+1, …, u+m-1}` are *exactly* the integers from `ru + r(r-1)/2` to
`ru + r(2m-r-1)/2`, an interval of `r(m-r) + 1` values.

A subset is written in the file's own vocabulary: a list `l` with
`occ v l ≤ occ v (run u m)` for every `v`, i.e. no repeated value and nothing
outside the interval.  `tri r` is `r(r-1)/2` (`two_mul_tri`), so the interval is
`[r·u + tri r, r·u + tri r + r·(m-r)]` (`subset_sum_top` converts the upper end
to the report's form).

The *every value is attained* half is Haskin's `pick_sum` (§A), whose staircase
`pick` is the report's "raise the largest raisable element" step unrolled.  His
NOTES record the converse as missing ("`pick_sum` gives only the inclusion.
Same induction, other direction").  It is `subset_bounds` below, by induction on
`m`: either the top element `u+m-1` is absent, or it is present and removing it
leaves an `(r-1)`-subset of the shorter interval.  The same induction also gives
`r ≤ m`, the pigeonhole the lower bound needs. -/

/-- `l` with its first copy of `v` removed. -/
def dropOne (v : Nat) : List Nat → List Nat
  | [] => []
  | a :: l => if a = v then l else a :: dropOne v l

theorem dropOne_spec (v : Nat) : ∀ l : List Nat, 0 < occ v l →
    (dropOne v l).length + 1 = l.length ∧ (dropOne v l).sum + v = l.sum ∧
    ∀ w, occ w (dropOne v l) + (if v = w then 1 else 0) = occ w l := by
  intro l
  induction l with
  | nil => intro h; exact absurd h (by simp [occ_nil])
  | cons a t ih =>
    intro h
    by_cases hav : a = v
    · subst hav
      refine ⟨?_, ?_, ?_⟩
      · show (if a = a then t else a :: dropOne a t).length + 1 = t.length + 1
        rw [if_pos rfl]
      · show (if a = a then t else a :: dropOne a t).sum + a = (a :: t).sum
        rw [if_pos rfl, List.sum_cons]; omega
      · intro w
        show occ w (if a = a then t else a :: dropOne a t) + _
            = (if a = w then 1 else 0) + occ w t
        rw [if_pos rfl]; omega
    · have h' : 0 < occ v t := by
        have : occ v (a :: t) = (if a = v then 1 else 0) + occ v t := rfl
        rw [if_neg hav] at this; omega
      obtain ⟨h1, h2, h3⟩ := ih h'
      refine ⟨?_, ?_, ?_⟩
      · show (if a = v then t else a :: dropOne v t).length + 1 = t.length + 1
        rw [if_neg hav]; simp only [List.length_cons]; omega
      · show (if a = v then t else a :: dropOne v t).sum + v = (a :: t).sum
        rw [if_neg hav, List.sum_cons, List.sum_cons]; omega
      · intro w
        show occ w (if a = v then t else a :: dropOne v t) + _
            = (if a = w then 1 else 0) + occ w t
        rw [if_neg hav]
        show ((if a = w then 1 else 0) + occ w (dropOne v t)) + _ = _
        have := h3 w; omega

theorem eq_nil_of_occ_zero : ∀ l : List Nat, (∀ v, occ v l = 0) → l = []
  | [], _ => rfl
  | a :: t, h => by have := h a; rw [occ_cons_self] at this; omega

theorem occ_run_succ (u m v : Nat) :
    occ v (run u (m + 1)) = occ v (run u m) + (if u + m = v then 1 else 0) := by
  rw [run_succ, occ_append]
  show occ v (run u m) + ((if u + m = v then 1 else 0) + 0) = _
  omega

/-- **The converse of `pick_sum`.**  An `r`-subset of `{u, …, u+m-1}` has
`r ≤ m` and its sum lies in `[r·u + tri r, r·u + tri r + r·(m-r)]`. -/
theorem subset_bounds (u : Nat) : ∀ m (l : List Nat), (∀ v, occ v l ≤ occ v (run u m)) →
    l.length ≤ m ∧ l.length * u + tri l.length ≤ l.sum ∧
      l.sum ≤ l.length * u + tri l.length + l.length * (m - l.length) := by
  intro m
  induction m with
  | zero =>
    intro l hl
    have hnil : l = [] := eq_nil_of_occ_zero l (fun v => by
      have h := hl v
      have h0 : occ v (run u 0) = 0 := rfl
      omega)
    subst hnil
    simp [tri]
  | succ m ih =>
    intro l hl
    by_cases htop : occ (u + m) l = 0
    · have hl' : ∀ v, occ v l ≤ occ v (run u m) := by
        intro v
        have h := hl v
        rw [occ_run_succ] at h
        by_cases hv : u + m = v
        · subst hv; omega
        · rw [if_neg hv] at h; omega
      obtain ⟨h1, h2, h3⟩ := ih l hl'
      refine ⟨by omega, h2, ?_⟩
      have : l.length * (m - l.length) ≤ l.length * (m + 1 - l.length) :=
        Nat.mul_le_mul_left _ (by omega)
      omega
    · obtain ⟨hl1, hl2, hl3⟩ := dropOne_spec (u + m) l (by omega)
      have hl' : ∀ v, occ v (dropOne (u + m) l) ≤ occ v (run u m) := by
        intro v
        have h := hl v
        have h' := hl3 v
        rw [occ_run_succ] at h
        by_cases hv : u + m = v
        · rw [if_pos hv] at h h'; omega
        · rw [if_neg hv] at h h'; omega
      obtain ⟨h1, h2, h3⟩ := ih _ hl'
      generalize hr' : (dropOne (u + m) l).length = r' at h1 h2 h3 hl1
      have hr : l.length = r' + 1 := by omega
      rw [hr]
      refine ⟨by omega, ?_, ?_⟩
      · show (r' + 1) * u + (tri r' + r') ≤ l.sum
        rw [Nat.succ_mul]; omega
      · show l.sum ≤ (r' + 1) * u + (tri r' + r') + (r' + 1) * (m + 1 - (r' + 1))
        rw [show m + 1 - (r' + 1) = m - r' from by omega, Nat.succ_mul, Nat.succ_mul]
        omega

/--
**Lemma 1 (subset sums of an interval).**  For `r ≤ m`, a value `σ` is the sum of
some `r`-element subset of `{u, …, u+m-1}` **iff**
`r·u + tri r ≤ σ ≤ r·u + tri r + r·(m-r)`.
-/
theorem subset_sums_iff (u r m σ : Nat) (hr : r ≤ m) :
    (∃ l : List Nat, l.length = r ∧ (∀ v, occ v l ≤ occ v (run u m)) ∧ l.sum = σ)
      ↔ r * u + tri r ≤ σ ∧ σ ≤ r * u + tri r + r * (m - r) := by
  constructor
  · rintro ⟨l, hlen, hsub, hsum⟩
    obtain ⟨-, h2, h3⟩ := subset_bounds u m l hsub
    rw [hlen, hsum] at h2 h3
    exact ⟨h2, h3⟩
  · rintro ⟨h1, h2⟩
    refine ⟨(pick u r (m - r) (σ - (r * u + tri r))).1, pick_len1 _ _ _ _, ?_, ?_⟩
    · intro v
      have h := pick_occ v u r (m - r) (σ - (r * u + tri r))
      rw [show r + (m - r) = m from by omega] at h
      omega
    · rw [pick_sum _ _ _ _ (by omega)]; omega

/-- `tri r = r(r-1)/2`. -/
theorem two_mul_tri : ∀ r, 2 * tri r = r * (r - 1)
  | 0 => rfl
  | r + 1 => by
    show 2 * (tri r + r) = (r + 1) * (r + 1 - 1)
    rw [Nat.mul_add, two_mul_tri r, Nat.add_sub_cancel]
    cases r with
    | zero => rfl
    | succ s => rw [Nat.add_sub_cancel]; grind

/-- The upper end in the report's form: `2·(r·u + tri r + r·(m-r)) = 2ru + r(2m-r-1)`. -/
theorem subset_sum_top (u r m : Nat) (hr : r ≤ m) :
    2 * (r * u + tri r + r * (m - r)) = 2 * r * u + r * (2 * m - r - 1) := by
  obtain ⟨q, rfl⟩ : ∃ q, m = r + q := ⟨m - r, by omega⟩
  cases r with
  | zero => simp [tri]
  | succ s =>
    have h1 : s + 1 + q - (s + 1) = q := by omega
    have h2 : 2 * (s + 1 + q) - (s + 1) - 1 = s + 2 * q := by omega
    have ht := two_mul_tri (s + 1)
    rw [Nat.add_sub_cancel] at ht
    rw [h1, h2, Nat.mul_add, Nat.mul_add, ht]
    grind

/-! ### Non-vacuity, and where the hypothesis bites -/

/-- The 2-subsets of `{0,1,2,3}` have sums exactly `1, …, 5`: `5` is attained… -/
theorem subset_sums_attained :
    ∃ l : List Nat, l.length = 2 ∧ (∀ v, occ v l ≤ occ v (run 0 4)) ∧ l.sum = 5 :=
  (subset_sums_iff 0 2 4 5 (by omega)).mpr (by decide)

/-- …and `6` is not, although `2 + 4` would give it if a value could repeat
or leave the interval. -/
theorem subset_sums_gap :
    ¬ ∃ l : List Nat, l.length = 2 ∧ (∀ v, occ v l ≤ occ v (run 0 4)) ∧ l.sum = 6 := by
  intro h
  have := (subset_sums_iff 0 2 4 6 (by omega)).mp h
  revert this; decide

/-- **`r ≤ m` is load-bearing.**  At `r = 3`, `m = 2` the arithmetic side holds for
`σ = tri 3 = 3`, but no 3-subset of a 2-element interval exists. -/
theorem subset_sums_needs_room :
    (3 * 0 + tri 3 ≤ 3 ∧ 3 ≤ 3 * 0 + tri 3 + 3 * (2 - 3)) ∧
      ¬ ∃ l : List Nat, l.length = 3 ∧ (∀ v, occ v l ≤ occ v (run 0 2)) ∧ l.sum = 3 := by
  refine ⟨by decide, ?_⟩
  rintro ⟨l, hlen, hsub, -⟩
  have := (subset_bounds 0 2 l hsub).1
  omega

/-! ## §D  Covering modulo `b+1` — Theorem 1 and its Corollary in the H3 report

The H3 report asks whether a congruence modulo `M` coprime to `b` can exclude a
candidate that the digit-sum congruence admits.  Theorem 1 answers it for
`M = b+1`: with `T = b(b-1)/2`, every pair `(x, y)` of residues mod `b+1` with
`x + y ≡ T (mod gcd(2, b-1))` is the pair `(X mod b+1, Y mod b+1)` of a
**pandigital split** — digit lists `X` of length `s` and `Y` of length `c`,
`s + c = b`, that together use each digit `0, …, b-1` exactly once, both with a
non-zero leading digit.

This is a statement about *pairs*; Haskin's `sieve_complete` is about the sum
`X + Y` modulo `b^j - 1`, so neither implies the other.

The proof is the report's.  Because `b ≡ -1 (mod b+1)`, a word's residue is its
even-position digit sum minus its odd-position digit sum (`weave_val`), so it is
decided by which digits sit at even positions.  With the digits of a word taken
from an interval, the even-position sums fill an interval of consecutive
integers (Lemma 1 of §C, i.e. `pick_sum`), long enough to reach every needed
residue.  For odd `b` only half the residues are reachable from one digit set,
and a parity swap of one digit between the words reaches the other half.

`Realised b s c x y` is the conclusion.  It states pandigitality as
`occ v (d1 ++ d2) = occ v (run 0 b)` for **every** `v`, which says both "each
digit below `b` once" (Haskin's form, `realised_pandigital`) and "no other
value". -/

/-! ### Words from two digit classes -/

/-- Interleave two lists: `weave [e₀,e₁,…] [o₀,o₁,…] = [e₀,o₀,e₁,o₁,…]`.  The first
list fills the even positions of a little-endian digit word, the second the odd
ones. -/
def weave : List Nat → List Nat → List Nat
  | [], os => os
  | e :: es, [] => e :: es
  | e :: es, o :: os => e :: o :: weave es os

theorem weave_length : ∀ E O : List Nat, (weave E O).length = E.length + O.length
  | [], O => by simp [weave]
  | e :: es, [] => by simp [weave]
  | e :: es, o :: os => by
    show (weave es os).length + 1 + 1 = (es.length + 1) + (os.length + 1)
    rw [weave_length es os]; omega

theorem weave_occ (v : Nat) : ∀ E O : List Nat, occ v (weave E O) = occ v E + occ v O
  | [], O => by show occ v O = 0 + occ v O; omega
  | e :: es, [] => by show occ v (e :: es) = occ v (e :: es) + 0; omega
  | e :: es, o :: os => by
    show (if e = v then 1 else 0) + ((if o = v then 1 else 0) + occ v (weave es os))
        = ((if e = v then 1 else 0) + occ v es) + ((if o = v then 1 else 0) + occ v os)
    rw [weave_occ v es os]; omega

/-- **The residue of a word mod `b+1`.**  Since `b ≡ -1`, the value of the woven
word plus its odd-position digit sum is its even-position digit sum, mod `b+1`.
(Needs the two classes to have the sizes of a genuine word: `|O| ≤ |E| ≤ |O|+1`.) -/
theorem weave_val (b : Nat) : ∀ E O : List Nat, O.length ≤ E.length →
    E.length ≤ O.length + 1 → (valOf b (weave E O) + O.sum) % (b + 1) = E.sum % (b + 1)
  | [], [], _, _ => rfl
  | [], _ :: _, h1, _ => by simp at h1
  | [e], [], _, _ => by
    show (e + b * 0 + 0) % (b + 1) = (e + 0) % (b + 1)
    rw [Nat.mul_zero]
  | e :: _ :: _, [], _, h2 => by simp at h2
  | e :: es, o :: os, h1, h2 => by
    have ih := weave_val b es os (by simp at h1; omega) (by simp at h2; omega)
    show (e + b * (o + b * valOf b (weave es os)) + (o :: os).sum) % (b + 1)
        = (e :: es).sum % (b + 1)
    rw [List.sum_cons, List.sum_cons]
    cases b with
    | zero => simp [Nat.mod_one]
    | succ b' =>
      have hid : e + (b' + 1) * (o + (b' + 1) * valOf (b' + 1) (weave es os)) + (o + os.sum)
          = (e + (valOf (b' + 1) (weave es os) + os.sum))
            + (b' + 1 + 1) * (o + b' * valOf (b' + 1) (weave es os)) := by grind
      rw [hid, Nat.add_mul_mod_self_left]
      exact add_mod_congr rfl ih

theorem weave_nth_even : ∀ (i : Nat) (E O : List Nat), i < E.length → i ≤ O.length →
    nth (weave E O) (2 * i) = nth E i
  | 0, [], _, h, _ => by simp at h
  | 0, e :: es, [], _, _ => rfl
  | 0, e :: es, o :: os, _, _ => rfl
  | i + 1, [], _, h, _ => by simp at h
  | i + 1, e :: es, [], _, h => by simp at h
  | i + 1, e :: es, o :: os, h1, h2 => by
    rw [show 2 * (i + 1) = 2 * i + 1 + 1 from by omega]
    exact weave_nth_even i es os (by simp at h1; omega) (by simp at h2; omega)

theorem weave_nth_odd : ∀ (i : Nat) (E O : List Nat), i < O.length → i < E.length →
    nth (weave E O) (2 * i + 1) = nth O i
  | _, _, [], h, _ => by simp at h
  | _, [], _ :: _, _, h => by simp at h
  | 0, e :: es, o :: os, _, _ => rfl
  | i + 1, e :: es, o :: os, h1, h2 => by
    rw [show 2 * (i + 1) + 1 = 2 * i + 1 + 1 + 1 from by omega]
    exact weave_nth_odd i es os (by simp at h1; omega) (by simp at h2; omega)

/-! ### Keeping `0` off the leading slot

The report's Lemma 2: the class holding the leading position has at least two
positions, so if it holds `0`, put `0` somewhere else.  `front0` moves every `0`
of a list to its front; the leading slot reads the list's *last* element. -/

def front0 (l : List Nat) : List Nat := List.replicate (occ 0 l) 0 ++ dropZeros l

theorem dropZeros_length_add : ∀ l : List Nat, (dropZeros l).length + occ 0 l = l.length
  | [] => rfl
  | x :: xs => by
    have ih := dropZeros_length_add xs
    show (if x = 0 then dropZeros xs else x :: dropZeros xs).length
        + ((if x = 0 then 1 else 0) + occ 0 xs) = xs.length + 1
    by_cases h : x = 0
    · rw [if_pos h, if_pos h]; omega
    · rw [if_neg h, if_neg h]; simp only [List.length_cons]; omega

theorem occ_replicate_zero (v : Nat) : ∀ n, occ v (List.replicate n 0) = if v = 0 then n else 0
  | 0 => by by_cases h : v = 0 <;> simp [h, occ_nil]
  | n + 1 => by
    rw [List.replicate_succ]
    show (if 0 = v then 1 else 0) + occ v (List.replicate n 0) = _
    rw [occ_replicate_zero v n]
    by_cases h : v = 0
    · subst h; simp; omega
    · rw [if_neg (fun h' => h h'.symm), if_neg h, if_neg h]

theorem sum_replicate_zero : ∀ n, (List.replicate n 0).sum = 0
  | 0 => rfl
  | n + 1 => by rw [List.replicate_succ, List.sum_cons, sum_replicate_zero n]

theorem front0_length (l : List Nat) : (front0 l).length = l.length := by
  rw [front0, List.length_append, List.length_replicate]
  have := dropZeros_length_add l
  omega

theorem front0_occ (v : Nat) (l : List Nat) : occ v (front0 l) = occ v l := by
  rw [front0, occ_append, occ_replicate_zero]
  by_cases h : v = 0
  · subst h; rw [if_pos rfl, dropZeros_occ_zero]; omega
  · rw [if_neg h, dropZeros_occ h]; omega

theorem front0_sum (l : List Nat) : (front0 l).sum = l.sum := by
  rw [front0, List.sum_append, sum_replicate_zero, dropZeros_sum]; omega

theorem front0_last (l : List Nat) (h : occ 0 l < l.length) :
    nth (front0 l) (l.length - 1) ≠ 0 := by
  have hd := dropZeros_length_add l
  rw [front0, nth_append_right _ _ _ (by rw [List.length_replicate]; omega),
      List.length_replicate]
  exact nth_ne_zero _ (dropZeros_occ_zero l) _ (by omega)

/-- The word with even-position digits `E` and odd-position digits `O`. -/
def word (E O : List Nat) : List Nat := weave (front0 E) (front0 O)

/-- **Lemma 2 of the report, and the residue.**  A word built from classes of the
right sizes has those digits, the residue `ΣE - ΣO` mod `b+1`, and a non-zero
leading digit as soon as each class holds `0` at most once. -/
theorem word_spec (b : Nat) (E O : List Nat) (h1 : O.length ≤ E.length)
    (h2 : E.length ≤ O.length + 1) (hO : 2 ≤ O.length) (h0E : occ 0 E ≤ 1)
    (h0O : occ 0 O ≤ 1) :
    (word E O).length = E.length + O.length ∧
    (∀ v, occ v (word E O) = occ v E + occ v O) ∧
    (valOf b (word E O) + O.sum) % (b + 1) = E.sum % (b + 1) ∧
    nth (word E O) (E.length + O.length - 1) ≠ 0 := by
  have hlE := front0_length E
  have hlO := front0_length O
  refine ⟨?_, ?_, ?_, ?_⟩
  · rw [word, weave_length, hlE, hlO]
  · intro v; rw [word, weave_occ, front0_occ, front0_occ]
  · have h := weave_val b (front0 E) (front0 O) (by omega) (by omega)
    rw [front0_sum, front0_sum] at h
    exact h
  · rcases Nat.lt_or_ge O.length E.length with hlt | hge
    · rw [show E.length + O.length - 1 = 2 * O.length from by omega, word,
          weave_nth_even _ _ _ (by omega) (by omega),
          show O.length = E.length - 1 from by omega]
      exact front0_last E (by omega)
    · rw [show E.length + O.length - 1 = 2 * (O.length - 1) + 1 from by omega, word,
          weave_nth_odd _ _ _ (by omega) (by omega)]
      exact front0_last O (by omega)

/-! ### The conclusion, and how two words produce it -/

/-- **`(x, y)` is realised**: some pandigital split of lengths `(s, c)` with non-zero
leading digits has residues `x` and `y` modulo `b+1`. -/
def Realised (b s c x y : Nat) : Prop :=
  ∃ d1 d2 : List Nat, d1.length = s ∧ d2.length = c ∧
    (∀ v, occ v (d1 ++ d2) = occ v (run 0 b)) ∧
    nth d1 (s - 1) ≠ 0 ∧ nth d2 (c - 1) ≠ 0 ∧
    valOf b d1 % (b + 1) = x ∧ valOf b d2 % (b + 1) = y

/-- The digit-sum condition `x + y ≡ T (mod gcd(2, b-1))`: no condition for even
`b`, a parity condition for odd `b`. -/
def Compatible (b x y : Nat) : Prop := b % 2 = 0 ∨ (x + y) % 2 = tri b % 2

instance (b x y : Nat) : Decidable (Compatible b x y) := by unfold Compatible; infer_instance

/-- `Realised` contains Haskin's form of pandigitality. -/
theorem realised_pandigital {b s c x y : Nat} (h : Realised b s c x y) :
    ∃ d1 d2 : List Nat, d1.length = s ∧ d2.length = c ∧
      (∀ v, v < b → occ v (d1 ++ d2) = 1) ∧ nth d1 (s - 1) ≠ 0 ∧ nth d2 (c - 1) ≠ 0 ∧
      valOf b d1 % (b + 1) = x ∧ valOf b d2 % (b + 1) = y := by
  obtain ⟨d1, d2, h1, h2, h3, h4, h5, h6, h7⟩ := h
  exact ⟨d1, d2, h1, h2, fun v hv => by rw [h3, occ_run b 0 v (by omega) (by omega)],
    h4, h5, h6, h7⟩

theorem target_of_word {n V O E x : Nat} (hn : 0 < n) (hw : (V + O) % n = E % n)
    (hx : (x + O) % n = E % n) (hxn : x < n) : V % n = x := by
  rw [mod_add_cancel hn (hw.trans hx.symm), Nat.mod_eq_of_lt hxn]

/-- Two pairs of digit classes with the right sizes, partitioning `{0,…,b-1}`, and
the right residues, give a realised pair. -/
theorem realised_of_classes {b s c x y : Nat} (hsc : s + c = b) (hs : 4 ≤ s) (hc : 4 ≤ c)
    (hx : x < b + 1) (hy : y < b + 1) (EX OX EY OY : List Nat)
    (hEX : EX.length = (s + 1) / 2) (hOX : OX.length = s / 2)
    (hEY : EY.length = (c + 1) / 2) (hOY : OY.length = c / 2)
    (hocc : ∀ v, (occ v EX + occ v OX) + (occ v EY + occ v OY) = occ v (run 0 b))
    (hrx : (x + OX.sum) % (b + 1) = EX.sum % (b + 1))
    (hry : (y + OY.sum) % (b + 1) = EY.sum % (b + 1)) :
    Realised b s c x y := by
  have h01 : occ 0 (run 0 b) = 1 := occ_run b 0 0 (by omega) (by omega)
  have h0 := hocc 0
  obtain ⟨l1, o1, v1, n1⟩ :=
    word_spec b EX OX (by omega) (by omega) (by omega) (by omega) (by omega)
  obtain ⟨l2, o2, v2, n2⟩ :=
    word_spec b EY OY (by omega) (by omega) (by omega) (by omega) (by omega)
  refine ⟨word EX OX, word EY OY, by rw [l1]; omega, by rw [l2]; omega, ?_, ?_, ?_, ?_, ?_⟩
  · intro v; rw [occ_append, o1, o2, hocc]
  · rw [show s - 1 = EX.length + OX.length - 1 from by omega]; exact n1
  · rw [show c - 1 = EY.length + OY.length - 1 from by omega]; exact n2
  · exact target_of_word (by omega) v1 hrx hx
  · exact target_of_word (by omega) v2 hry hy

/-! ### Hitting a residue with an interval of even-position sums -/

theorem double_hit_key {b K z t : Nat} (ht : t % (b + 1) = (z + 2 * K * b) % (b + 1)) :
    (2 * K + t) % (b + 1) = z % (b + 1) := by
  rw [Nat.add_mod, ht, ← Nat.add_mod]
  have : 2 * K + (z + 2 * K * b) = z + (b + 1) * (2 * K) := by grind
  rw [this, Nat.add_mul_mod_self_left]

/-- Even `b`: `2` is invertible mod `b+1`, and `b+1` consecutive values of `ν`
reach every residue of `2(K+ν)`. -/
theorem hit_even {b : Nat} (hb : b % 2 = 0) (K z : Nat) :
    ∃ ν, ν ≤ b ∧ (2 * (K + ν)) % (b + 1) = z % (b + 1) := by
  obtain ⟨t, htdef⟩ : ∃ t, t = (z + 2 * K * b) % (b + 1) := ⟨_, rfl⟩
  have htlt : t < b + 1 := htdef ▸ Nat.mod_lt _ (by omega)
  have ht : t % (b + 1) = (z + 2 * K * b) % (b + 1) := by rw [htdef, Nat.mod_mod]
  rcases Nat.mod_two_eq_zero_or_one t with h | h
  · refine ⟨t / 2, by omega, ?_⟩
    rw [show 2 * (K + t / 2) = 2 * K + t from by omega]
    exact double_hit_key ht
  · refine ⟨(t + b + 1) / 2, by omega, ?_⟩
    rw [show 2 * (K + (t + b + 1) / 2) = (2 * K + t) + (b + 1) from by omega,
        Nat.add_mod_right]
    exact double_hit_key ht

/-- Odd `b`: `2(K+ν)` reaches every *even* residue mod the even number `b+1`,
with `ν ≤ (b-1)/2`. -/
theorem hit_odd {b : Nat} (hb : b % 2 = 1) (K z : Nat) (hz : z % 2 = 0) :
    ∃ ν, 2 * ν ≤ b ∧ (2 * (K + ν)) % (b + 1) = z % (b + 1) := by
  obtain ⟨t, htdef⟩ : ∃ t, t = (z + 2 * K * b) % (b + 1) := ⟨_, rfl⟩
  have htlt : t < b + 1 := htdef ▸ Nat.mod_lt _ (by omega)
  have ht : t % (b + 1) = (z + 2 * K * b) % (b + 1) := by rw [htdef, Nat.mod_mod]
  have ht2 : t % 2 = 0 := by
    have hdvd : 2 ∣ b + 1 := ⟨(b + 1) / 2, by omega⟩
    rw [htdef, Nat.mod_mod_of_dvd _ hdvd, Nat.mul_assoc]
    omega
  refine ⟨t / 2, by omega, ?_⟩
  rw [show 2 * (K + t / 2) = 2 * K + t from by omega]
  exact double_hit_key ht

/-- **One word.**  Take the digits of a word to be a list `A` (kept at odd
positions) together with the interval `{u, …, u+m-1}`, `m = e + q`, of which `e`
go to even positions.  If there is room — `e·q ≥ b` for even `b`, or
`e·q ≥ (b-1)/2` and the right parity for odd `b` — the word can be given residue
`x`. -/
theorem word_of_room {b u e q m x : Nat} (A : List Nat) (hm : e + q = m)
    (hroom : (b % 2 = 0 ∧ b ≤ e * q) ∨
      (b % 2 = 1 ∧ (b - 1) / 2 ≤ e * q ∧ (x + (A.sum + (run u m).sum)) % 2 = 0)) :
    ∃ E O : List Nat, E.length = e ∧ O.length = A.length + q ∧
      (∀ v, occ v E + occ v O = occ v A + occ v (run u m)) ∧
      (x + O.sum) % (b + 1) = E.sum % (b + 1) := by
  subst hm
  obtain ⟨ν, hν, hmod⟩ : ∃ ν, ν ≤ e * q ∧ (2 * (e * u + tri e + ν)) % (b + 1)
      = (x + (A.sum + (run u (e + q)).sum)) % (b + 1) := by
    rcases hroom with ⟨hb, hr⟩ | ⟨hb, hr, hp⟩
    · obtain ⟨ν, h1, h2⟩ := hit_even hb (e * u + tri e) (x + (A.sum + (run u (e + q)).sum))
      exact ⟨ν, by omega, h2⟩
    · obtain ⟨ν, h1, h2⟩ := hit_odd hb (e * u + tri e) _ hp
      exact ⟨ν, by omega, h2⟩
  refine ⟨(pick u e q ν).1, A ++ (pick u e q ν).2, pick_len1 _ _ _ _, ?_, ?_, ?_⟩
  · rw [List.length_append, pick_len2]
  · intro v; rw [occ_append, ← pick_occ v u e q ν]; omega
  · have hs := pick_sum u e q ν hν
    have ht := pick_sum_total u e q ν
    refine mod_add_cancel (c := (pick u e q ν).1.sum) (by omega) ?_
    rw [List.sum_append]
    have : x + (A.sum + (pick u e q ν).2.sum) + (pick u e q ν).1.sum
        = x + (A.sum + (run u (e + q)).sum) := by omega
    rw [this, ← hmod, hs]
    congr 1
    omega

theorem occ_run_split {u m n w : Nat} (v : Nat) (hw : w = u + m) :
    occ v (run u m) + occ v (run w n) = occ v (run u (m + n)) := by
  subst hw; rw [run_add, occ_append]

theorem sum_run_split {u m n w : Nat} (hw : w = u + m) :
    (run u m).sum + (run w n).sum = (run u (m + n)).sum := by
  subst hw; rw [run_add, List.sum_append]

/-! ### Theorem 1 -/

/-- The hypothesis of Theorem 1: for even `b`, `e·o ≥ b` and `e'·o' ≥ b`; for odd
`b`, `e(o-1) ≥ (b-1)/2` and `e'(o'-1) ≥ (b-1)/2`, where `e = ⌈s/2⌉`, `o = ⌊s/2⌋`
count the even and odd positions of the first word and `e'`, `o'` those of the
second. -/
def CoverCond (b s c : Nat) : Prop :=
  (b % 2 = 0 → b ≤ (s + 1) / 2 * (s / 2) ∧ b ≤ (c + 1) / 2 * (c / 2)) ∧
  (b % 2 = 1 → (b - 1) / 2 ≤ (s + 1) / 2 * (s / 2 - 1) ∧
                (b - 1) / 2 ≤ (c + 1) / 2 * (c / 2 - 1))

instance (b s c : Nat) : Decidable (CoverCond b s c) := by unfold CoverCond; infer_instance

/--
**Theorem 1 (covering modulo `b+1`).**  If `s + c = b`, both words have at least
four digits, and the class sizes satisfy `CoverCond`, then every pair `(x, y)` of
residues modulo `b+1` with `x + y ≡ T (mod gcd(2, b-1))` is realised by a
pandigital split with non-zero leading digits.
-/
theorem cover_b_plus_one {b s c : Nat} (hsc : s + c = b) (hs : 4 ≤ s) (hc : 4 ≤ c)
    (hcond : CoverCond b s c) {x y : Nat} (hx : x < b + 1) (hy : y < b + 1)
    (hxy : Compatible b x y) : Realised b s c x y := by
  have hrs := run_sum 0 s
  have hrb := run_sum 0 b
  have htot : (run 0 s).sum + (run s c).sum = (run 0 b).sum := by
    rw [sum_run_split (by omega : s = 0 + s), hsc]
  rcases Nat.mod_two_eq_zero_or_one b with hbe | hbo
  · -- even `b`: the interval split `{0,…,s-1} | {s,…,b-1}` does everything
    obtain ⟨h1, h2⟩ := hcond.1 hbe
    obtain ⟨EX, OX, lEX, lOX, oX, rX⟩ :=
      word_of_room (b := b) (u := 0) (e := (s + 1) / 2) (q := s / 2) (m := s) (x := x) []
        (by omega) (Or.inl ⟨hbe, h1⟩)
    obtain ⟨EY, OY, lEY, lOY, oY, rY⟩ :=
      word_of_room (b := b) (u := s) (e := (c + 1) / 2) (q := c / 2) (m := c) (x := y) []
        (by omega) (Or.inl ⟨hbe, h2⟩)
    refine realised_of_classes hsc hs hc hx hy EX OX EY OY lEX (by simpa using lOX) lEY
      (by simpa using lOY) (fun v => ?_) rX rY
    have hdec := occ_run_split (n := c) v (by omega : s = 0 + s)
    rw [hsc] at hdec
    have := oX v; have := oY v; rw [occ_nil] at *
    omega
  · obtain ⟨h1, h2⟩ := hcond.2 hbo
    have h1' : (b - 1) / 2 ≤ (s + 1) / 2 * (s / 2) :=
      Nat.le_trans h1 (Nat.mul_le_mul_left _ (by omega))
    have h2' : (b - 1) / 2 ≤ (c + 1) / 2 * (c / 2) :=
      Nat.le_trans h2 (Nat.mul_le_mul_left _ (by omega))
    have hxy' : (x + y) % 2 = tri b % 2 := by
      rcases hxy with h | h
      · omega
      · exact h
    by_cases hpar : (x + tri s) % 2 = 0
    · -- the parity of `x` matches the interval split: use it
      obtain ⟨EX, OX, lEX, lOX, oX, rX⟩ :=
        word_of_room (b := b) (u := 0) (e := (s + 1) / 2) (q := s / 2) (m := s) (x := x) []
          (by omega) (Or.inr ⟨hbo, h1', by simp; omega⟩)
      obtain ⟨EY, OY, lEY, lOY, oY, rY⟩ :=
        word_of_room (b := b) (u := s) (e := (c + 1) / 2) (q := c / 2) (m := c) (x := y) []
          (by omega) (Or.inr ⟨hbo, h2', by simp; omega⟩)
      refine realised_of_classes hsc hs hc hx hy EX OX EY OY lEX (by simpa using lOX) lEY
        (by simpa using lOY) (fun v => ?_) rX rY
      have hdec := occ_run_split (n := c) v (by omega : s = 0 + s)
      rw [hsc] at hdec
      have := oX v; have := oY v; rw [occ_nil] at *
      omega
    · rcases Nat.mod_two_eq_zero_or_one s with hse | hso
      · -- `s` even: `{0,…,s-2} ∪ {s}` and `{s-1} ∪ {s+1,…,b-1}`
        have hts : tri s = tri (s - 1) + (s - 1) := by
          obtain ⟨s', rfl⟩ : ∃ s', s = s' + 1 := ⟨s - 1, by omega⟩
          rfl
        have hr0 := run_sum 0 (s - 1)
        have htot' : (run 0 (s - 1)).sum + ((run (s - 1) 1).sum + ((run s 1).sum
            + (run (s + 1) (c - 1)).sum)) = (run 0 b).sum := by
          rw [sum_run_split (n := c - 1) (by omega : s + 1 = s + 1),
            sum_run_split (n := 1 + (c - 1)) (by omega : s = s - 1 + 1),
            sum_run_split (n := 1 + (1 + (c - 1))) (by omega : s - 1 = 0 + (s - 1)),
            show s - 1 + (1 + (1 + (c - 1))) = b from by omega]
        have hs1 : (run s 1).sum = s := by simp [run]
        have hs2 : (run (s - 1) 1).sum = s - 1 := by simp [run]
        obtain ⟨EX, OX, lEX, lOX, oX, rX⟩ :=
          word_of_room (b := b) (u := 0) (e := (s + 1) / 2) (q := s / 2 - 1) (m := s - 1)
            (x := x) [s] (by omega)
            (Or.inr ⟨hbo, h1, by simp only [List.sum_cons, List.sum_nil]; omega⟩)
        obtain ⟨EY, OY, lEY, lOY, oY, rY⟩ :=
          word_of_room (b := b) (u := s + 1) (e := (c + 1) / 2) (q := c / 2 - 1) (m := c - 1)
            (x := y) [s - 1] (by omega)
            (Or.inr ⟨hbo, h2, by simp only [List.sum_cons, List.sum_nil]; omega⟩)
        refine realised_of_classes hsc hs hc hx hy EX OX EY OY lEX
          (by simp at lOX; omega) lEY (by simp at lOY; omega) (fun v => ?_) rX rY
        have e1 : occ v [s] = occ v (run s 1) := rfl
        have e2 : occ v [s - 1] = occ v (run (s - 1) 1) := rfl
        have d1 := occ_run_split (n := c - 1) v (by omega : s + 1 = s + 1)
        have d2 := occ_run_split (n := 1 + (c - 1)) v (by omega : s = s - 1 + 1)
        have d3 := occ_run_split (n := 1 + (1 + (c - 1))) v (by omega : s - 1 = 0 + (s - 1))
        rw [show s - 1 + (1 + (1 + (c - 1))) = b from by omega] at d3
        have := oX v; have := oY v
        omega
      · -- `s` odd: `{1,…,s}` and `{0} ∪ {s+1,…,b-1}`
        have hr1 := run_sum 1 s
        have htot' : (run 0 1).sum + ((run 1 s).sum + (run (s + 1) (c - 1)).sum)
            = (run 0 b).sum := by
          rw [sum_run_split (n := c - 1) (by omega : s + 1 = 1 + s),
            sum_run_split (n := s + (c - 1)) (by omega : 1 = 0 + 1),
            show 1 + (s + (c - 1)) = b from by omega]
        have h01 : (run 0 1).sum = 0 := rfl
        obtain ⟨EX, OX, lEX, lOX, oX, rX⟩ :=
          word_of_room (b := b) (u := 1) (e := (s + 1) / 2) (q := s / 2) (m := s) (x := x) []
            (by omega) (Or.inr ⟨hbo, h1', by simp; omega⟩)
        obtain ⟨EY, OY, lEY, lOY, oY, rY⟩ :=
          word_of_room (b := b) (u := s + 1) (e := (c + 1) / 2) (q := c / 2 - 1) (m := c - 1)
            (x := y) [0] (by omega)
            (Or.inr ⟨hbo, h2, by simp only [List.sum_cons, List.sum_nil]; omega⟩)
        refine realised_of_classes hsc hs hc hx hy EX OX EY OY lEX (by simpa using lOX) lEY
          (by simp at lOY; omega) (fun v => ?_) rX rY
        have e1 : occ v [0] = occ v (run 0 1) := rfl
        have d1 := occ_run_split (n := c - 1) v (by omega : s + 1 = 1 + s)
        have d2 := occ_run_split (n := s + (c - 1)) v (by omega : 1 = 0 + 1)
        rw [show 1 + (s + (c - 1)) = b from by omega] at d2
        have := oX v; have := oY v; rw [occ_nil] at *
        omega

/-! ### The converse: the parity condition is necessary

For odd `b` the modulus `b+1` is even and `b ≡ 1 (mod 2)`, so a word is congruent
to its digit sum mod 2, and the two digit sums add to `T = tri b`.  So
`Compatible` is exactly the set of realisable pairs, and Theorem 1 is an iff. -/

theorem valOf_mod_two {b : Nat} (hb : b % 2 = 1) : ∀ d : List Nat, valOf b d % 2 = d.sum % 2
  | [] => rfl
  | a :: t => by
    have ih := valOf_mod_two hb t
    show (a + b * valOf b t) % 2 = (a + t.sum) % 2
    rw [Nat.add_mod, Nat.mul_mod, hb, Nat.one_mul, Nat.mod_mod, ih, ← Nat.add_mod]

/-- Lists with the same occurrence counts have the same sum. -/
theorem sum_eq_of_occ : ∀ l l' : List Nat, (∀ v, occ v l = occ v l') → l.sum = l'.sum
  | [], l', h => by
    rw [eq_nil_of_occ_zero l' (fun v => by rw [← h v]; rfl)]
  | a :: t, l', h => by
    have ha : 0 < occ a l' := by rw [← h a, occ_cons_self]; omega
    obtain ⟨-, hs, ho⟩ := dropOne_spec a l' ha
    have ih := sum_eq_of_occ t (dropOne a l') (fun w => by
      have h1 := h w
      have h2 := ho w
      have h3 : occ w (a :: t) = (if a = w then 1 else 0) + occ w t := rfl
      omega)
    rw [List.sum_cons, ih]; omega

/-- **Necessity.**  A realised pair satisfies the digit-sum condition. -/
theorem realised_compatible {b s c x y : Nat} (h : Realised b s c x y) : Compatible b x y := by
  rcases Nat.mod_two_eq_zero_or_one b with hb | hb
  · exact Or.inl hb
  · right
    obtain ⟨d1, d2, -, -, hocc, -, -, hx, hy⟩ := h
    have hsum : (d1 ++ d2).sum = (run 0 b).sum := sum_eq_of_occ _ _ hocc
    rw [List.sum_append, run_sum] at hsum
    have hdvd : 2 ∣ b + 1 := ⟨(b + 1) / 2, by omega⟩
    have h1 : x % 2 = d1.sum % 2 := by
      rw [← hx, Nat.mod_mod_of_dvd _ hdvd, valOf_mod_two hb]
    have h2 : y % 2 = d2.sum % 2 := by
      rw [← hy, Nat.mod_mod_of_dvd _ hdvd, valOf_mod_two hb]
    omega

/-- **Theorem 1 as a biconditional.**  Under its hypotheses, a pair of residues
mod `b+1` is realised by a pandigital split **iff** it satisfies the digit-sum
condition. -/
theorem cover_b_plus_one_iff {b s c : Nat} (hsc : s + c = b) (hs : 4 ≤ s) (hc : 4 ≤ c)
    (hcond : CoverCond b s c) {x y : Nat} (hx : x < b + 1) (hy : y < b + 1) :
    Realised b s c x y ↔ Compatible b x y :=
  ⟨realised_compatible, cover_b_plus_one hsc hs hc hcond hx hy⟩

/-! ## §E  The Corollary — every base `b ≥ 10`

**Corollary (report).**  With `s + c = b`, `s ≥ (2b-2)/5` and `c ≥ s`, the
hypothesis of Theorem 1 holds for every even `b ≥ 28` and every odd `b ≥ 21`;
the bases below are settled by computation.

**Formalised.**  `cover_cond_large` proves the inequality for even `b ≥ 28` and
odd `b ≥ 17` — the odd threshold of the report is not sharp, and 17 is (at
`b = 15`, `s = 6` the condition fails: `cover_cond_fifteen_fails`); the even
threshold 28 is sharp (`cover_cond_twentysix_fails`).  The remaining bases are
settled by **kernel-checked certificates**: for each base a list of one or two
digit partitions `{0,…,b-1} = S_X ⊔ S_Y` and, for every residue, an explicit
choice of even-position digits realising it.  `certOK` checks a certificate by
evaluation and `realised_of_cert` proves the checker sound, so the certificates
themselves need not be trusted; they were found by a greedy search.

`candidate_lengths` shows the digit lengths of any candidate (`numDigits` of
`n²` and `n³` summing to `b`) satisfy `2b ≤ 5s + 1` and `5s ≤ 2b + 2`, which
pins `s` in every base, and `cover_candidate` is the headline: **for every base
`b ≥ 10` and every candidate `n`, the residue pairs mod `b+1` of pandigital
splits with the lengths of `n²` and `n³` are exactly the pairs the digit sum
permits** — so no congruence mod `b+1` can rule out a candidate the digit-sum
test admits. -/

/-! ### The inequality for large bases -/

theorem cover_cond_large {b s c : Nat} (hsc : s + c = b) (h5 : 2 * b ≤ 5 * s + 2)
    (hle : s ≤ c) (hb : (b % 2 = 0 ∧ 28 ≤ b) ∨ (b % 2 = 1 ∧ 17 ≤ b)) :
    CoverCond b s c := by
  have hmono : (s + 1) / 2 * (s / 2) ≤ (c + 1) / 2 * (c / 2) :=
    Nat.mul_le_mul (by omega) (by omega)
  have hmono' : (s + 1) / 2 * (s / 2 - 1) ≤ (c + 1) / 2 * (c / 2 - 1) :=
    Nat.mul_le_mul (by omega) (by omega)
  obtain ⟨a, ha⟩ : ∃ a, s = 2 * a ∨ s = 2 * a + 1 := ⟨s / 2, by omega⟩
  refine ⟨fun he => ?_, fun ho => ?_⟩
  · have key : b ≤ (s + 1) / 2 * (s / 2) := by
      rcases ha with rfl | rfl
      · rw [show (2 * a + 1) / 2 = a from by omega, show 2 * a / 2 = a from by omega]
        have : 6 * a ≤ a * a := Nat.mul_le_mul_right a (by omega)
        omega
      · rw [show (2 * a + 1 + 1) / 2 = a + 1 from by omega,
            show (2 * a + 1) / 2 = a from by omega, Nat.succ_mul]
        have : 5 * a ≤ a * a := Nat.mul_le_mul_right a (by omega)
        omega
    exact ⟨key, Nat.le_trans key hmono⟩
  · have key : (b - 1) / 2 ≤ (s + 1) / 2 * (s / 2 - 1) := by
      rcases ha with rfl | rfl
      · rw [show (2 * a + 1) / 2 = a from by omega, show 2 * a / 2 = a from by omega]
        obtain ⟨t, rfl⟩ : ∃ t, a = t + 1 := ⟨a - 1, by omega⟩
        rw [Nat.add_sub_cancel, Nat.succ_mul]
        have : 3 * t ≤ t * t := Nat.mul_le_mul_right t (by omega)
        omega
      · rw [show (2 * a + 1 + 1) / 2 = a + 1 from by omega,
            show (2 * a + 1) / 2 = a from by omega]
        obtain ⟨t, rfl⟩ : ∃ t, a = t + 1 := ⟨a - 1, by omega⟩
        rw [Nat.add_sub_cancel, show t + 1 + 1 = t + 2 from rfl, Nat.add_mul]
        rcases Nat.lt_or_ge t 3 with ht | ht
        · have : t = 2 := by omega
          subst this; omega
        · have : 3 * t ≤ t * t := Nat.mul_le_mul_right t ht
          omega
    exact ⟨key, Nat.le_trans key hmono'⟩

/-- The even threshold 28 is sharp: at `b = 26`, `s = 10` (which satisfies
`2b ≤ 5s + 2` and `s ≤ c`) the condition fails. -/
theorem cover_cond_twentysix_fails : 2 * 26 ≤ 5 * 10 + 2 ∧ 10 ≤ 16 ∧ ¬ CoverCond 26 10 16 := by
  decide

/-- The odd threshold 17 is sharp: at `b = 15`, `s = 6` the condition fails. -/
theorem cover_cond_fifteen_fails : 2 * 15 ≤ 5 * 6 + 2 ∧ 6 ≤ 9 ∧ ¬ CoverCond 15 6 9 := by
  decide

/-! ### Certificates for the small bases -/

/-- Split `l` by a mask: the `true` positions and the `false` positions. -/
def selMask : List Bool → List Nat → List Nat × List Nat
  | [], ds => ([], ds)
  | _ :: _, [] => ([], [])
  | m :: ms, d :: ds =>
    if m then (d :: (selMask ms ds).1, (selMask ms ds).2)
    else ((selMask ms ds).1, d :: (selMask ms ds).2)

theorem selMask_spec (v : Nat) : ∀ (ms : List Bool) (l : List Nat),
    occ v (selMask ms l).1 + occ v (selMask ms l).2 = occ v l ∧
    (selMask ms l).1.length + (selMask ms l).2.length = l.length
  | [], ds => by simp [selMask, occ_nil]
  | _ :: _, [] => by simp [selMask, occ_nil]
  | m :: ms, d :: ds => by
    obtain ⟨h1, h2⟩ := selMask_spec v ms ds
    cases m
    · show occ v (selMask ms ds).1 + ((if d = v then 1 else 0) + occ v (selMask ms ds).2)
          = (if d = v then 1 else 0) + occ v ds ∧
        (selMask ms ds).1.length + ((selMask ms ds).2.length + 1) = ds.length + 1
      omega
    · show ((if d = v then 1 else 0) + occ v (selMask ms ds).1) + occ v (selMask ms ds).2
          = (if d = v then 1 else 0) + occ v ds ∧
        ((selMask ms ds).1.length + 1) + (selMask ms ds).2.length = ds.length + 1
      omega

/-- One word: the mask picks `e` digits of `S` for the even positions, and the
residue `r` is right. -/
def maskOK (b e : Nat) (S : List Nat) (mr : List Bool × Nat) : Bool :=
  decide ((selMask mr.1 S).1.length = e) && decide (mr.2 < b + 1) &&
  decide ((mr.2 + (selMask mr.1 S).2.sum) % (b + 1) = (selMask mr.1 S).1.sum % (b + 1))

/-- A certificate entry: digit sets `S_X`, `S_Y` and the masks realising some
residues of each word. -/
abbrev Part := List Nat × List Nat × List (List Bool × Nat) × List (List Bool × Nat)

def partOK (b s c : Nat) (P : Part) : Bool :=
  decide (P.1.length = s) && decide (P.2.1.length = c) &&
  (P.1 ++ P.2.1).all (fun a => decide (a < b)) &&
  (List.range b).all (fun v => decide (occ v (P.1 ++ P.2.1) = 1)) &&
  P.2.2.1.all (maskOK b ((s + 1) / 2) P.1) && P.2.2.2.all (maskOK b ((c + 1) / 2) P.2.1)

/-- The whole check: every entry valid, and every compatible pair covered by one
entry. -/
def certOK (b s c : Nat) (cert : List Part) : Bool :=
  cert.all (partOK b s c) &&
  (List.range (b + 1)).all (fun x => (List.range (b + 1)).all (fun y =>
    !decide (b % 2 = 0 ∨ (x + y) % 2 = tri b % 2) ||
      cert.any (fun P => P.2.2.1.any (fun mr => decide (mr.2 = x)) &&
                          P.2.2.2.any (fun mr => decide (mr.2 = y)))))

/-- Nothing at or above `s + n` occurs in `run s n`. -/
theorem occ_run_ge : ∀ n s v, s + n ≤ v → occ v (run s n) = 0 := by
  intro n
  induction n with
  | zero => intro _ _ _; rfl
  | succ k ih =>
    intro s v hs
    show (if s = v then 1 else 0) + occ v (run (s + 1) k) = 0
    rw [if_neg (by omega), ih (s + 1) v (by omega)]

theorem occ_eq_run_of_perm {b : Nat} {l : List Nat} (hlt : ∀ a ∈ l, a < b)
    (h1 : ∀ v, v < b → occ v l = 1) : ∀ v, occ v l = occ v (run 0 b) := by
  intro v
  by_cases hv : v < b
  · rw [h1 v hv, occ_run b 0 v (by omega) (by omega)]
  · rw [occ_run_ge b 0 v (by omega)]
    rcases Nat.eq_zero_or_pos (occ v l) with h | h
    · exact h
    · exact absurd (hlt v (mem_of_occ_pos l v h)) hv

/-- **The checker is sound.** -/
theorem realised_of_cert {b s c : Nat} (cert : List Part) (hsc : s + c = b) (hs : 4 ≤ s)
    (hc : 4 ≤ c) (hok : certOK b s c cert = true) {x y : Nat} (hx : x < b + 1)
    (hy : y < b + 1) (hxy : Compatible b x y) : Realised b s c x y := by
  simp only [certOK, Bool.and_eq_true, List.all_eq_true] at hok
  obtain ⟨hparts, hcov⟩ := hok
  have hc' := hcov x (List.mem_range.mpr hx) y (List.mem_range.mpr hy)
  have hcomp : decide (b % 2 = 0 ∨ (x + y) % 2 = tri b % 2) = true := decide_eq_true hxy
  rw [hcomp] at hc'
  simp only [Bool.not_true, Bool.false_or, List.any_eq_true, Bool.and_eq_true,
    decide_eq_true_eq] at hc'
  obtain ⟨P, hP, ⟨mx, hmx, hmxe⟩, ⟨my, hmy, hmye⟩⟩ := hc'
  have hpart := hparts P hP
  simp only [partOK, Bool.and_eq_true, List.all_eq_true, decide_eq_true_eq] at hpart
  obtain ⟨⟨⟨⟨⟨hl1, hl2⟩, hlt⟩, hone⟩, hxs⟩, hys⟩ := hpart
  have hmxok := hxs mx hmx
  have hmyok := hys my hmy
  simp only [maskOK, Bool.and_eq_true, decide_eq_true_eq] at hmxok hmyok
  obtain ⟨⟨hex, -⟩, hrx⟩ := hmxok
  obtain ⟨⟨hey, -⟩, hry⟩ := hmyok
  rw [hmxe] at hrx
  rw [hmye] at hry
  have hperm := occ_eq_run_of_perm hlt (fun v hv => hone v (List.mem_range.mpr hv))
  obtain ⟨-, hlenX⟩ := selMask_spec 0 mx.1 P.1
  obtain ⟨-, hlenY⟩ := selMask_spec 0 my.1 P.2.1
  refine realised_of_classes hsc hs hc hx hy _ _ _ _ hex (by omega) hey (by omega)
    (fun v => ?_) hrx hry
  rw [(selMask_spec v mx.1 P.1).1, (selMask_spec v my.1 P.2.1).1, ← occ_append, hperm v]

/-! ### The certificates

Each entry is `(S_X, S_Y, masks for X, masks for Y)`; a mask marks the digits of
`S_X` (or `S_Y`) placed at even positions and carries the residue mod `b+1` that
choice gives.  They were found by a greedy search and are checked below by
`certOK`, so nothing about how they were found matters. -/

/-- Certificate for base 10, lengths (4, 6): 2 digit partitions. -/
def cert10 : List (List Nat × List Nat × List (List Bool × Nat) × List (List Bool × Nat)) := [
  ([0, 1, 2, 4], [3, 5, 6, 7, 8, 9],
    [([true, false, false, true], 1),
      ([false, true, false, true], 3),
      ([false, false, true, true], 5),
      ([true, true, false, false], 6),
      ([true, false, true, false], 8),
      ([false, true, true, false], 10)],
    [([true, false, false, true, false, true], 0),
      ([true, true, true, false, false, false], 1),
      ([true, false, false, false, true, true], 2),
      ([true, true, false, true, false, false], 3),
      ([false, true, false, true, false, true], 4),
      ([true, true, false, false, true, false], 5),
      ([false, true, false, false, true, true], 6),
      ([true, true, false, false, false, true], 7),
      ([false, false, true, false, true, true], 8),
      ([true, false, true, false, false, true], 9),
      ([false, false, false, true, true, true], 10)]),
  ([1, 2, 3, 4], [0, 5, 6, 7, 8, 9],
    [([true, false, false, true], 0),
      ([false, true, false, true], 2),
      ([false, false, true, true], 4),
      ([true, true, false, false], 7),
      ([true, false, true, false], 9)],
    [([true, true, false, true, false, false], 0),
      ([false, true, true, true, false, false], 1),
      ([true, true, false, false, true, false], 2),
      ([false, true, true, false, true, false], 3),
      ([true, true, false, false, false, true], 4),
      ([false, true, true, false, false, true], 5),
      ([true, false, true, false, false, true], 6),
      ([false, true, false, true, false, true], 7),
      ([true, false, false, true, false, true], 8),
      ([true, true, true, false, false, false], 9),
      ([true, false, false, false, true, true], 10)])]

/-- Certificate for base 12, lengths (5, 7): 2 digit partitions. -/
def cert12 : List (List Nat × List Nat × List (List Bool × Nat) × List (List Bool × Nat)) := [
  ([0, 1, 2, 4, 7], [3, 5, 6, 8, 9, 10, 11],
    [([false, true, true, true, false], 0),
      ([true, true, false, false, true], 2),
      ([true, false, true, false, true], 4),
      ([true, true, true, false, false], 5),
      ([false, true, true, false, true], 6),
      ([true, false, false, true, true], 8),
      ([true, true, false, true, false], 9),
      ([false, true, false, true, true], 10),
      ([true, false, true, true, false], 11),
      ([false, false, true, true, true], 12)],
    [([true, true, false, true, false, true, false], 0),
      ([true, false, false, false, true, true, true], 1),
      ([true, true, false, true, false, false, true], 2),
      ([false, true, false, true, false, true, true], 3),
      ([true, true, false, false, true, false, true], 4),
      ([true, true, true, true, false, false, false], 5),
      ([true, true, false, false, false, true, true], 6),
      ([true, true, true, false, true, false, false], 7),
      ([true, false, true, false, false, true, true], 8),
      ([true, true, true, false, false, true, false], 9),
      ([true, false, false, true, true, false, true], 10),
      ([true, true, true, false, false, false, true], 11),
      ([true, false, false, true, false, true, true], 12)]),
  ([0, 1, 2, 3, 5], [4, 6, 7, 8, 9, 10, 11],
    [([true, true, false, false, true], 1),
      ([true, false, true, false, true], 3),
      ([false, true, false, true, true], 7)],
    [([true, false, false, false, true, true, true], 0),
      ([true, true, true, false, false, false, true], 1),
      ([false, true, false, true, false, true, true], 2),
      ([true, true, false, true, false, false, true], 3),
      ([false, true, false, false, true, true, true], 4),
      ([true, true, false, false, true, false, true], 5),
      ([false, false, true, false, true, true, true], 6),
      ([true, true, false, false, false, true, true], 7),
      ([true, true, true, true, false, false, false], 8),
      ([true, false, true, false, false, true, true], 9),
      ([true, true, true, false, true, false, false], 10),
      ([true, false, false, true, false, true, true], 11),
      ([true, true, true, false, false, true, false], 12)])]

/-- Certificate for base 13, lengths (5, 8): 2 digit partitions. -/
def cert13 : List (List Nat × List Nat × List (List Bool × Nat) × List (List Bool × Nat)) := [
  ([0, 1, 2, 3, 4], [5, 6, 7, 8, 9, 10, 11, 12],
    [([true, true, false, false, true], 0),
      ([true, false, true, false, true], 2),
      ([true, false, false, true, true], 4),
      ([false, true, false, true, true], 6),
      ([false, false, true, true, true], 8),
      ([true, true, true, false, false], 10),
      ([true, true, false, true, false], 12)],
    [([true, true, true, false, true, false, false, false], 0),
      ([true, true, true, false, false, true, false, false], 2),
      ([true, true, true, false, false, false, true, false], 4),
      ([true, true, true, false, false, false, false, true], 6),
      ([true, true, false, true, false, false, false, true], 8),
      ([true, true, false, false, true, false, false, true], 10),
      ([true, true, true, true, false, false, false, false], 12)]),
  ([0, 1, 2, 3, 5], [4, 6, 7, 8, 9, 10, 11, 12],
    [([true, true, false, false, true], 1),
      ([true, false, true, false, true], 3),
      ([true, false, false, true, true], 5),
      ([false, true, false, true, true], 7),
      ([true, true, true, false, false], 9),
      ([true, true, false, true, false], 11),
      ([true, false, true, true, false], 13)],
    [([true, true, true, false, false, true, false, false], 1),
      ([true, true, true, false, false, false, true, false], 3),
      ([true, true, true, false, false, false, false, true], 5),
      ([true, true, false, true, false, false, false, true], 7),
      ([true, true, false, false, true, false, false, true], 9),
      ([true, true, true, true, false, false, false, false], 11),
      ([true, true, true, false, true, false, false, false], 13)])]

/-- Certificate for base 14, lengths (6, 8): 1 digit partitions. -/
def cert14 : List (List Nat × List Nat × List (List Bool × Nat) × List (List Bool × Nat)) := [
  ([0, 1, 2, 3, 5, 9], [4, 6, 7, 8, 10, 11, 12, 13],
    [([true, true, false, false, false, true], 0),
      ([true, true, true, false, false, false], 1),
      ([true, false, true, false, false, true], 2),
      ([true, true, false, true, false, false], 3),
      ([true, false, false, true, false, true], 4),
      ([true, false, true, true, false, false], 5),
      ([false, true, false, true, false, true], 6),
      ([true, true, false, false, true, false], 7),
      ([true, false, false, false, true, true], 8),
      ([true, false, true, false, true, false], 9),
      ([false, true, false, false, true, true], 10),
      ([true, false, false, true, true, false], 11),
      ([false, false, true, false, true, true], 12),
      ([false, true, false, true, true, false], 13),
      ([false, false, false, true, true, true], 14)],
    [([true, true, true, false, false, true, false, false], 0),
      ([true, false, true, false, false, false, true, true], 1),
      ([true, true, true, false, false, false, true, false], 2),
      ([true, false, false, true, false, false, true, true], 3),
      ([true, true, true, false, false, false, false, true], 4),
      ([true, false, false, false, true, true, false, true], 5),
      ([true, true, false, true, false, false, false, true], 6),
      ([true, false, false, false, true, false, true, true], 7),
      ([true, true, false, false, true, false, true, false], 8),
      ([true, true, true, true, false, false, false, false], 9),
      ([true, true, false, false, true, false, false, true], 10),
      ([false, true, false, false, true, false, true, true], 11),
      ([true, true, false, false, false, true, false, true], 12),
      ([true, true, true, false, true, false, false, false], 13),
      ([true, true, false, false, false, false, true, true], 14)])]

/-- Certificate for base 15, lengths (6, 9): 2 digit partitions. -/
def cert15 : List (List Nat × List Nat × List (List Bool × Nat) × List (List Bool × Nat)) := [
  ([0, 1, 2, 3, 4, 5], [6, 7, 8, 9, 10, 11, 12, 13, 14],
    [([true, false, false, true, false, true], 1),
      ([true, false, false, false, true, true], 3),
      ([false, true, false, false, true, true], 5),
      ([true, true, true, false, false, false], 7),
      ([true, true, false, true, false, false], 9),
      ([true, true, false, false, true, false], 11),
      ([true, true, false, false, false, true], 13),
      ([true, false, true, false, false, true], 15)],
    [([true, true, true, false, true, false, false, false, true], 0),
      ([true, true, true, false, false, true, false, false, true], 2),
      ([true, true, true, false, false, false, true, false, true], 4),
      ([true, true, true, true, true, false, false, false, false], 6),
      ([true, true, true, true, false, true, false, false, false], 8),
      ([true, true, true, true, false, false, true, false, false], 10),
      ([true, true, true, true, false, false, false, true, false], 12),
      ([true, true, true, true, false, false, false, false, true], 14)]),
  ([0, 1, 2, 3, 4, 6], [5, 7, 8, 9, 10, 11, 12, 13, 14],
    [([true, false, true, false, false, true], 0),
      ([true, false, false, true, false, true], 2),
      ([true, false, false, false, true, true], 4),
      ([true, true, true, false, false, false], 6),
      ([true, true, false, true, false, false], 8),
      ([true, true, false, false, true, false], 10),
      ([true, false, true, false, true, false], 12),
      ([true, true, false, false, false, true], 14)],
    [([true, true, true, false, false, true, false, false, true], 1),
      ([true, true, true, false, false, false, true, false, true], 3),
      ([true, true, true, true, true, false, false, false, false], 5),
      ([true, true, true, true, false, true, false, false, false], 7),
      ([true, true, true, true, false, false, true, false, false], 9),
      ([true, true, true, true, false, false, false, true, false], 11),
      ([true, true, true, true, false, false, false, false, true], 13),
      ([true, true, true, false, true, false, false, false, true], 15)])]

/-- Certificate for base 18, lengths (7, 11): 1 digit partitions. -/
def cert18 : List (List Nat × List Nat × List (List Bool × Nat) × List (List Bool × Nat)) := [
  ([1, 4, 5, 6, 11, 13, 17], [0, 2, 3, 7, 8, 9, 10, 12, 14, 15, 16],
    [([false, true, false, true, true, false, true], 0),
      ([true, true, false, false, true, true, false], 1),
      ([false, true, true, false, false, true, true], 2),
      ([true, false, true, false, true, true, false], 3),
      ([true, true, true, false, true, false, false], 4),
      ([true, false, false, true, true, true, false], 5),
      ([true, true, false, true, true, false, false], 6),
      ([false, true, true, true, false, false, true], 7),
      ([true, true, true, false, false, true, false], 8),
      ([true, true, false, false, true, false, true], 9),
      ([true, true, false, true, false, true, false], 10),
      ([true, false, true, false, true, false, true], 11),
      ([true, false, true, true, false, true, false], 12),
      ([true, true, true, true, false, false, false], 13),
      ([false, true, true, true, true, false, false], 14),
      ([true, false, true, false, false, true, true], 15),
      ([true, true, true, false, false, false, true], 16),
      ([true, false, false, true, false, true, true], 17),
      ([true, true, false, true, false, false, true], 18)],
    [([true, true, true, true, true, true, false, false, false, false, false], 0),
      ([true, true, true, true, false, false, false, true, false, true, false], 1),
      ([true, true, true, true, true, false, true, false, false, false, false], 2),
      ([true, true, true, true, false, false, false, true, false, false, true], 3),
      ([true, true, true, true, false, true, true, false, false, false, false], 4),
      ([true, true, true, true, false, false, false, false, true, true, false], 5),
      ([true, true, true, true, true, false, false, true, false, false, false], 6),
      ([true, true, true, true, false, false, false, false, true, false, true], 7),
      ([true, true, true, true, false, true, false, true, false, false, false], 8),
      ([true, true, true, true, false, false, false, false, false, true, true], 9),
      ([true, true, true, true, true, false, false, false, true, false, false], 10),
      ([true, true, true, false, true, false, false, false, false, true, true], 11),
      ([true, true, true, true, true, false, false, false, false, true, false], 12),
      ([true, true, true, false, false, true, false, false, false, true, true], 13),
      ([true, true, true, true, true, false, false, false, false, false, true], 14),
      ([true, true, true, false, false, false, true, false, false, true, true], 15),
      ([true, true, true, true, false, true, false, false, false, false, true], 16),
      ([true, true, true, false, false, false, false, true, true, false, true], 17),
      ([true, true, true, true, false, false, true, false, false, false, true], 18)])]

/-- Certificate for base 20, lengths (8, 12): 1 digit partitions. -/
def cert20 : List (List Nat × List Nat × List (List Bool × Nat) × List (List Bool × Nat)) := [
  ([1, 2, 6, 8, 11, 12, 14, 16], [0, 3, 4, 5, 7, 9, 10, 13, 15, 17, 18, 19],
    [([true, false, true, false, false, true, false, true], 0),
      ([true, true, true, false, false, false, false, true], 1),
      ([true, false, false, true, true, false, false, true], 2),
      ([true, true, false, false, true, true, false, false], 3),
      ([true, false, true, false, false, false, true, true], 4),
      ([true, true, false, true, false, false, false, true], 5),
      ([true, true, true, true, false, false, false, false], 6),
      ([true, true, false, false, true, false, true, false], 7),
      ([true, false, false, true, false, false, true, true], 8),
      ([true, true, false, false, false, true, true, false], 9),
      ([true, false, false, false, true, true, false, true], 10),
      ([true, true, false, false, true, false, false, true], 11),
      ([true, true, true, false, true, false, false, false], 12),
      ([true, true, false, false, false, true, false, true], 13),
      ([true, true, true, false, false, true, false, false], 14),
      ([true, false, true, false, true, false, true, false], 15),
      ([true, true, false, true, true, false, false, false], 16),
      ([true, true, false, false, false, false, true, true], 17),
      ([true, true, true, false, false, false, true, false], 18),
      ([true, false, true, false, true, false, false, true], 19),
      ([false, false, true, false, true, true, false, true], 20)],
    [([true, true, true, true, false, true, false, false, false, false, true, false], 0),
      ([true, true, true, true, true, false, true, false, false, false, false, false], 1),
      ([true, true, true, true, false, true, false, false, false, false, false, true], 2),
      ([true, true, true, false, true, false, false, false, false, false, true, true], 3),
      ([true, true, true, true, false, false, true, false, false, false, false, true], 4),
      ([true, true, true, true, false, true, true, false, false, false, false, false], 5),
      ([true, true, true, true, false, false, false, true, false, true, false, false], 6),
      ([true, true, true, true, true, false, false, true, false, false, false, false], 7),
      ([true, true, true, true, false, false, false, true, false, false, true, false], 8),
      ([true, true, true, false, true, true, true, false, false, false, false, false], 9),
      ([true, true, true, true, false, false, false, true, false, false, false, true], 10),
      ([true, true, true, true, true, false, false, false, true, false, false, false], 11),
      ([true, true, true, true, false, false, false, false, true, false, true, false], 12),
      ([true, true, true, true, false, false, true, true, false, false, false, false], 13),
      ([true, true, true, true, false, false, false, false, true, false, false, true], 14),
      ([true, true, true, true, true, false, false, false, false, true, false, false], 15),
      ([true, true, true, true, false, false, false, false, false, true, true, false], 16),
      ([true, true, true, true, true, false, false, false, false, false, true, false], 17),
      ([true, true, true, true, false, false, false, false, false, true, false, true], 18),
      ([true, true, true, true, true, false, false, false, false, false, false, true], 19),
      ([true, true, true, true, true, true, false, false, false, false, false, false], 20)])]

/-- Certificate for base 22, lengths (9, 13): 1 digit partitions. -/
def cert22 : List (List Nat × List Nat × List (List Bool × Nat) × List (List Bool × Nat)) := [
  ([2, 6, 10, 11, 12, 13, 14, 16, 19], [0, 1, 3, 4, 5, 7, 8, 9, 15, 17, 18, 20, 21],
    [([true, false, false, false, true, false, true, true, true], 0),
      ([true, true, false, true, false, false, true, false, true], 1),
      ([true, true, true, true, true, false, false, false, false], 2),
      ([true, true, true, false, false, false, false, true, true], 3),
      ([true, true, true, true, false, true, false, false, false], 4),
      ([true, true, false, true, false, false, false, true, true], 5),
      ([true, true, true, true, false, false, true, false, false], 6),
      ([true, true, false, false, true, false, false, true, true], 7),
      ([true, true, true, false, true, false, true, false, false], 8),
      ([true, true, false, false, false, true, false, true, true], 9),
      ([true, true, true, true, false, false, false, true, false], 10),
      ([true, true, false, false, false, false, true, true, true], 11),
      ([true, true, true, false, true, false, false, true, false], 12),
      ([true, false, true, true, false, false, false, true, true], 13),
      ([true, true, true, false, false, true, false, true, false], 14),
      ([true, false, true, false, true, false, false, true, true], 15),
      ([true, true, true, true, false, false, false, false, true], 16),
      ([true, false, true, false, false, true, false, true, true], 17),
      ([true, true, true, false, true, false, false, false, true], 18),
      ([true, false, true, false, false, false, true, true, true], 19),
      ([true, true, true, false, false, true, false, false, true], 20),
      ([true, false, false, true, false, false, true, true, true], 21),
      ([true, true, true, false, false, false, true, false, true], 22)],
    [([true, true, true, true, true, true, false, false, false, false, false, false, true], 0),
      ([true, true, true, true, true, false, true, true, false, false, false, false, false], 1),
      ([true, true, true, true, true, false, true, false, false, false, false, false, true], 2),
      ([true, true, true, true, true, false, false, false, false, false, false, true, true], 3),
      ([true, true, true, true, true, false, false, true, false, false, false, false, true], 4),
      ([true, true, true, true, false, true, true, true, false, false, false, false, false], 5),
      ([true, true, true, true, false, true, true, false, false, false, false, false, true], 6),
      ([true, true, true, true, false, true, false, false, false, false, false, true, true], 7),
      ([true, true, true, true, true, false, false, false, true, true, false, false, false], 8),
      ([true, true, true, true, false, false, true, false, false, false, false, true, true], 9),
      ([true, true, true, true, true, false, false, false, true, false, true, false, false], 10),
      ([true, true, true, true, true, true, false, false, true, false, false, false, false], 11),
      ([true, true, true, true, false, true, false, false, true, true, false, false, false], 12),
      ([true, true, true, true, true, false, true, false, true, false, false, false, false], 13),
      ([true, true, true, true, true, false, false, false, true, false, false, true, false], 14),
      ([true, true, true, true, true, true, false, false, false, true, false, false, false], 15),
      ([true, true, true, true, true, false, false, false, true, false, false, false, true], 16),
      ([true, true, true, true, true, true, false, false, false, false, true, false, false], 17),
      ([true, true, true, true, true, false, false, false, false, true, false, true, false], 18),
      ([true, true, true, true, true, false, true, false, false, false, true, false, false], 19),
      ([true, true, true, true, true, true, true, false, false, false, false, false, false], 20),
      ([true, true, true, true, true, true, false, false, false, false, false, true, false], 21),
      ([true, true, true, true, true, true, false, true, false, false, false, false, false], 22)])]

theorem cert10_ok : certOK 10 4 6 cert10 = true := by decide +kernel
theorem cert12_ok : certOK 12 5 7 cert12 = true := by decide +kernel
theorem cert13_ok : certOK 13 5 8 cert13 = true := by decide +kernel
theorem cert14_ok : certOK 14 6 8 cert14 = true := by decide +kernel
theorem cert15_ok : certOK 15 6 9 cert15 = true := by decide +kernel
theorem cert18_ok : certOK 18 7 11 cert18 = true := by decide +kernel
theorem cert20_ok : certOK 20 8 12 cert20 = true := by decide +kernel
theorem cert22_ok : certOK 22 9 13 cert22 = true := by decide +kernel

/-! ### The Corollary -/

/--
**Corollary (covering modulo `b+1` for the nice-number lengths).**  For every base
`b ≥ 10` and lengths `s + c = b` with `2b ≤ 5s + 1` and `5s ≤ 2b + 2` — the
lengths every candidate has (`candidate_lengths`) — every pair of residues mod
`b+1` allowed by the digit sum is realised by a pandigital split with non-zero
leading digits.
-/
theorem cover_nice_lengths {b s c : Nat} (hb : 10 ≤ b) (hsc : s + c = b)
    (h1 : 2 * b ≤ 5 * s + 1) (h2 : 5 * s ≤ 2 * b + 2) {x y : Nat} (hx : x < b + 1)
    (hy : y < b + 1) (hxy : Compatible b x y) : Realised b s c x y := by
  by_cases hL : (b % 2 = 0 ∧ 28 ≤ b) ∨ (b % 2 = 1 ∧ 17 ≤ b)
  · exact cover_b_plus_one hsc (by omega) (by omega)
      (cover_cond_large hsc (by omega) (by omega) hL) hx hy hxy
  · have hs : s = (2 * b + 2) / 5 := by omega
    subst hs
    -- the bases below the thresholds that have nice-number lengths at all
    have key : ∀ b, b < 28 → 10 ≤ b ∧ 2 * b ≤ 5 * ((2 * b + 2) / 5) + 1 ∧
        ¬((b % 2 = 0 ∧ 28 ≤ b) ∨ (b % 2 = 1 ∧ 17 ≤ b)) →
        b ∈ [10, 12, 13, 14, 15, 18, 20, 22, 24] := by
      decide
    have hmem := key b (by omega) ⟨hb, h1, hL⟩
    simp only [List.mem_cons, List.not_mem_nil, or_false] at hmem
    rcases hmem with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
    · obtain rfl : c = 6 := by omega
      exact realised_of_cert cert10 rfl (by omega) (by omega) cert10_ok hx hy hxy
    · obtain rfl : c = 7 := by omega
      exact realised_of_cert cert12 rfl (by omega) (by omega) cert12_ok hx hy hxy
    · obtain rfl : c = 8 := by omega
      exact realised_of_cert cert13 rfl (by omega) (by omega) cert13_ok hx hy hxy
    · obtain rfl : c = 8 := by omega
      exact realised_of_cert cert14 rfl (by omega) (by omega) cert14_ok hx hy hxy
    · obtain rfl : c = 9 := by omega
      exact realised_of_cert cert15 rfl (by omega) (by omega) cert15_ok hx hy hxy
    · obtain rfl : c = 11 := by omega
      exact realised_of_cert cert18 rfl (by omega) (by omega) cert18_ok hx hy hxy
    · obtain rfl : c = 12 := by omega
      exact realised_of_cert cert20 rfl (by omega) (by omega) cert20_ok hx hy hxy
    · obtain rfl : c = 13 := by omega
      exact realised_of_cert cert22 rfl (by omega) (by omega) cert22_ok hx hy hxy
    · obtain rfl : c = 14 := by omega
      exact cover_b_plus_one rfl (by omega) (by omega) (by decide) hx hy hxy

/-! ### Candidates: the lengths of `n²` and `n³` -/

/-- **The lengths of a candidate.**  If `n²` and `n³` have `b` base-`b` digits
between them, `s = numDigits b (n²)` satisfies `2b ≤ 5s + 1` and `5s ≤ 2b + 2`.
Both from `n⁶ = (n²)³ = (n³)²` and Haskin's `bounds_of_numDigits`. -/
theorem candidate_lengths {b n : Nat} (hb : 1 < b)
    (h : numDigits b (n ^ 2) + numDigits b (n ^ 3) = b) :
    2 * b ≤ 5 * numDigits b (n ^ 2) + 1 ∧ 5 * numDigits b (n ^ 2) ≤ 2 * b + 2 := by
  have hn : 0 < n := by
    rcases Nat.eq_zero_or_pos n with rfl | hn
    · simp [numDigits_zero] at h; omega
    · exact hn
  have hs0 : numDigits b (n ^ 2) ≠ 0 := fun h0 =>
    absurd (eq_zero_of_numDigits_eq_zero hb h0) (Nat.pos_iff_ne_zero.mp (Nat.pow_pos hn))
  have hc0 : numDigits b (n ^ 3) ≠ 0 := fun h0 =>
    absurd (eq_zero_of_numDigits_eq_zero hb h0) (Nat.pos_iff_ne_zero.mp (Nat.pow_pos hn))
  obtain ⟨s', hs'⟩ : ∃ s', numDigits b (n ^ 2) = s' + 1 := ⟨_, (Nat.succ_pred_eq_of_ne_zero hs0).symm⟩
  obtain ⟨c', hc'⟩ : ∃ c', numDigits b (n ^ 3) = c' + 1 := ⟨_, (Nat.succ_pred_eq_of_ne_zero hc0).symm⟩
  obtain ⟨hs1, hs2⟩ := bounds_of_numDigits hb _ _ hs'
  obtain ⟨hc1, hc2⟩ := bounds_of_numDigits hb _ _ hc'
  have e23 : (n ^ 2) ^ 3 = (n ^ 3) ^ 2 := by rw [← Nat.pow_mul, ← Nat.pow_mul]
  have hA : b ^ (s' * 3) < b ^ ((c' + 1) * 2) := by
    rw [Nat.pow_mul, Nat.pow_mul]
    calc (b ^ s') ^ 3 ≤ (n ^ 2) ^ 3 := Nat.pow_le_pow_left hs1 3
      _ = (n ^ 3) ^ 2 := e23
      _ < (b ^ (c' + 1)) ^ 2 := Nat.pow_lt_pow_left hc2 (by omega)
  have hB : b ^ (c' * 2) < b ^ ((s' + 1) * 3) := by
    rw [Nat.pow_mul, Nat.pow_mul]
    calc (b ^ c') ^ 2 ≤ (n ^ 3) ^ 2 := Nat.pow_le_pow_left hc1 2
      _ = (n ^ 2) ^ 3 := e23.symm
      _ < (b ^ (s' + 1)) ^ 3 := Nat.pow_lt_pow_left hs2 (by omega)
  have hA' := (Nat.pow_lt_pow_iff_right hb).mp hA
  have hB' := (Nat.pow_lt_pow_iff_right hb).mp hB
  omega

/--
**Covering modulo `b+1`, for every candidate in every base `b ≥ 10`.**  If `n²`
and `n³` have `b` digits between them, a pair `(x, y)` of residues mod `b+1` is
the residue pair of a pandigital split with the digit lengths of `n²` and `n³`
(leading digits non-zero) **iff** it passes the digit-sum test.  So no
congruence modulo `b+1` rules out any candidate the digit sum admits.
-/
theorem cover_candidate {b n x y : Nat} (hb : 10 ≤ b)
    (h : numDigits b (n ^ 2) + numDigits b (n ^ 3) = b) (hx : x < b + 1) (hy : y < b + 1) :
    Realised b (numDigits b (n ^ 2)) (numDigits b (n ^ 3)) x y ↔ Compatible b x y := by
  obtain ⟨h1, h2⟩ := candidate_lengths (by omega) h
  exact ⟨realised_compatible, cover_nice_lengths hb h h1 h2 hx hy⟩

/-! ### Non-vacuity, and where each hypothesis bites -/

/-- **The conclusion at 69.**  `69² = 4761` and `69³ = 328509` are a pandigital
split in base 10; their residues mod 11 are `(9, 5)`. -/
theorem sixtynine_realised : Realised 10 4 6 9 5 := by
  refine ⟨[1, 6, 7, 4], [9, 0, 5, 8, 2, 3], rfl, rfl, ?_, by decide, by decide,
    by decide, by decide⟩
  exact occ_eq_run_of_perm (by decide) (by decide)

theorem sixtynine_split_values :
    valOf 10 [1, 6, 7, 4] = 69 ^ 2 ∧ valOf 10 [9, 0, 5, 8, 2, 3] = 69 ^ 3 := by decide

/-- 69 is a candidate, so `cover_candidate` applies to base 10 with its lengths. -/
theorem sixtynine_lengths : 4 + 6 = 10 ∧ 2 * 10 ≤ 5 * 4 + 1 ∧ 5 * 4 ≤ 2 * 10 + 2 := by decide

/-- **Theorem 1's hypothesis fires** at base 17 (odd) and base 24 (even), where no
certificate is used… -/
theorem cover_cond_fires : CoverCond 17 7 10 ∧ CoverCond 24 10 14 := by decide

/-- …**and fails at base 10**, so the certificates are not decoration. -/
theorem cover_cond_ten_fails : ¬ CoverCond 10 4 6 := by decide

/-- **The word lengths are load-bearing.**  With a 2-digit first word at base 10
(lengths `(2, 8)`, outside the nice-number band), the compatible pair `(0, 0)` is
not realised: `d₀ + 10d₁ ≡ d₀ - d₁ (mod 11)` vanishes only for `d₀ = d₁`. -/
theorem two_digit_word_fails : Compatible 10 0 0 ∧ ¬ Realised 10 2 8 0 0 := by
  refine ⟨Or.inl rfl, ?_⟩
  rintro ⟨d1, d2, hl1, -, hocc, -, -, hx, -⟩
  match d1, hl1 with
  | [a, a'], _ =>
    have hv : valOf 10 [a, a'] = a + 10 * (a' + 10 * 0) := rfl
    rw [hv] at hx
    have ha : a < 10 := by
      have h1 := hocc a
      rw [occ_append, occ_cons_self] at h1
      by_cases hlt : a < 10
      · exact hlt
      · rw [occ_run_ge 10 0 a (by omega)] at h1; omega
    have ha' : a' < 10 := by
      have h1 := hocc a'
      have h2 : occ a' ([a, a'] ++ d2) = (if a = a' then 1 else 0) + (1 + occ a' d2) := by
        rw [occ_append]; show (if a = a' then 1 else 0) + ((if a' = a' then 1 else 0) + 0)
          + occ a' d2 = _
        rw [if_pos rfl]; omega
      rw [h2] at h1
      by_cases hlt : a' < 10
      · exact hlt
      · rw [occ_run_ge 10 0 a' (by omega)] at h1; omega
    have hne : a ≠ a' := by
      intro he
      subst he
      have h1 := hocc a
      rw [occ_append, occ_cons_self, occ_cons_self, occ_run 10 0 a (by omega) (by omega)] at h1
      omega
    omega

/-- **The parity condition is load-bearing** (odd base 13): `(0, 0)` is realised,
`(0, 1)` is not. -/
theorem base_thirteen_parity : Realised 13 5 8 0 0 ∧ ¬ Realised 13 5 8 0 1 := by
  refine ⟨cover_nice_lengths (by omega) rfl (by omega) (by omega) (by omega) (by omega)
    (by decide), fun h => ?_⟩
  have := realised_compatible h
  revert this; decide

end Nice

#print axioms Nice.slot_eq_mod_div
#print axioms Nice.mul_pow_mod_tail
#print axioms Nice.batch_cube_mod
#print axioms Nice.batch_square_mod
#print axioms Nice.batch_cube_digit
#print axioms Nice.batch_square_digit
#print axioms Nice.batch_cube_digit_of_residues
#print axioms Nice.batch_low_digit_const
#print axioms Nice.batch_cube_rotation
#print axioms Nice.batch_cube_rotation_only
#print axioms Nice.batch_square_rotation_only
#print axioms Nice.batch_cube_quadratic
#print axioms Nice.sixtynine_batch_digits
#print axioms Nice.base_thirty_batch
#print axioms Nice.rotation_zone_moves
#print axioms Nice.batch_tail_sharp
#print axioms Nice.rotation_zone_boundary_sharp
#print axioms Nice.subset_bounds
#print axioms Nice.subset_sums_iff
#print axioms Nice.two_mul_tri
#print axioms Nice.subset_sum_top
#print axioms Nice.subset_sums_attained
#print axioms Nice.subset_sums_gap
#print axioms Nice.subset_sums_needs_room
#print axioms Nice.weave_val
#print axioms Nice.word_spec
#print axioms Nice.word_of_room
#print axioms Nice.cover_b_plus_one
#print axioms Nice.realised_compatible
#print axioms Nice.cover_b_plus_one_iff
#print axioms Nice.cover_cond_large
#print axioms Nice.cover_cond_twentysix_fails
#print axioms Nice.cover_cond_fifteen_fails
#print axioms Nice.realised_of_cert
#print axioms Nice.cert10_ok
#print axioms Nice.cert22_ok
#print axioms Nice.cover_nice_lengths
#print axioms Nice.candidate_lengths
#print axioms Nice.cover_candidate
#print axioms Nice.sixtynine_realised
#print axioms Nice.cover_cond_fires
#print axioms Nice.cover_cond_ten_fails
#print axioms Nice.two_digit_word_fails
#print axioms Nice.base_thirteen_parity
