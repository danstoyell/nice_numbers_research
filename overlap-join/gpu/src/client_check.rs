//! VERBATIM COPY of the client's full-check device function `candidate_check`
//! from common/src/cubecl_backend.rs (wasabipesto/nice @ fe1b0b8, lines 358-811).
//! It is private (`fn`, not `pub fn`) in nice_common, so it cannot be called
//! from outside the crate; in a merge the copy is deleted and the join's check
//! kernel calls the original. Nothing below the separator line is edited.
//!
//! Copyright (c) 2024 wasabipesto. Used under the MIT License of
//! https://github.com/wasabipesto/nice (see LICENSE there).
#![allow(
    clippy::cast_possible_truncation,
    clippy::cast_possible_wrap,
    clippy::cast_lossless,
    clippy::used_underscore_binding
)]
use cubecl::prelude::*;
use nice_common::cubecl_backend::NICEONLY_STRIDE;

// ------------------------------- verbatim ---------------------------------
/// Shared per-candidate check: the low-digit modular prefilter, then the
/// full square/cube distinct-digit scan, appending hits (or, in probe
/// builds, prefilter survivors) to the output buffer. Factored out of
/// `niceonly_kernel` so the plain and plane-compacted enumeration paths run
/// the identical body.
// `collapsible_if`: `has_prefilter` is comptime and `ok` is runtime; the
// cube macro wants them in separate `if`s so the outer one folds away.
#[cube]
#[allow(
    clippy::too_many_arguments,
    clippy::too_many_lines,
    clippy::similar_names,
    clippy::many_single_char_names,
    clippy::collapsible_if,
    clippy::fn_params_excessive_bools
)]
pub fn candidate_check(
    n_lo: u64,
    n_hi: u64,
    sv_s: &mut SharedMemory<u32>,
    svb: u32,
    nice_out: &mut Array<u32>,
    nice_count: &mut Array<Atomic<u32>>,
    nice_cap: u32,
    #[comptime] base: u32,
    #[comptime] limbs: u32,
    #[comptime] chunk_digits: u32,
    #[comptime] chunk_div: u32,
    #[comptime] wide_chunk: bool,
    #[comptime] pre_limbs: u32,
    #[comptime] pre_chunk_digits: u32,
    #[comptime] pre_chunk_div: u32,
    #[comptime] probe: bool,
) {
    let sq_limbs = comptime!(2 * limbs);
    let cu_limbs = comptime!(3 * limbs);
    let two_masks = comptime!(base > 64);
    let has_prefilter = comptime!(pre_limbs > 0);

    let mut ok = true;
    // Low-digit modular prefilter: are the lowest
    // `pre_limbs * pre_chunk_digits` digits of n² and n³ all distinct?
    // Fixed-length and branch-free — lanes only save work when their
    // whole group is killed, and this kills ~98% of candidates. Held
    // as digit-chunks of base `pre_chunk_div < 2^16` so the truncated
    // multiplies stay in u32 (`x^k mod b^p == (x mod b^p)^k mod b^p`).
    if has_prefilter {
        if ok {
            // v = n's u32 limbs; a[r] = successive `mod pre_chunk_div`
            // chunks peeled off by the same split16 step the digit scan
            // uses.
            let mut v = Array::<u32>::new(limbs as usize);
            #[unroll]
            for i in 0..limbs {
                let shift = comptime!(((i & 1) * 32) as u64);
                if comptime!(i < 2) {
                    v[i as usize] = u32::cast_from(n_lo >> shift);
                } else {
                    v[i as usize] = u32::cast_from(n_hi >> shift);
                }
            }
            let mut a = Array::<u32>::new(pre_limbs as usize);
            #[unroll]
            for rr in 0..pre_limbs {
                let mut rem = 0u32;
                #[unroll]
                for i in 0..limbs {
                    let idx = comptime!(limbs - 1 - i);
                    let vi = v[idx as usize];
                    // Plain paired `%` here, unlike the digit scan: the
                    // mul-sub form of these four prefilter sites
                    // miscompiles under naga's MSL backend (survivors
                    // diverge from the host mirror on Apple GPUs, caught
                    // by the probe test), and the prefilter runs once per
                    // candidate so the pairing costs nothing measurable.
                    let c1 = (rem << 16u32) | (vi >> 16u32);
                    let q1 = c1 / pre_chunk_div;
                    let c2 = ((c1 % pre_chunk_div) << 16u32) | (vi & 0xFFFFu32);
                    rem = c2 % pre_chunk_div;
                    v[idx as usize] = (q1 << 16u32) | (c2 / pre_chunk_div);
                }
                a[rr as usize] = rem;
            }

            // sq = a², cu = sq·a, truncated schoolbook over digit-chunks —
            // dropping products at or above chunk `pre_limbs` is exactly
            // reduction mod pre_chunk_div^pre_limbs.
            let mut psq = Array::<u32>::new(pre_limbs as usize);
            #[unroll]
            for i in 0..pre_limbs {
                psq[i as usize] = 0u32;
            }
            #[unroll]
            for i in 0..pre_limbs {
                let mut carry = 0u32;
                #[unroll]
                for j in 0..comptime!(pre_limbs - i) {
                    let k = comptime!(i + j);
                    let t = a[i as usize] * a[j as usize] + psq[k as usize] + carry;
                    psq[k as usize] = t % pre_chunk_div;
                    carry = t / pre_chunk_div;
                }
            }
            let mut pcu = Array::<u32>::new(pre_limbs as usize);
            #[unroll]
            for i in 0..pre_limbs {
                pcu[i as usize] = 0u32;
            }
            #[unroll]
            for i in 0..pre_limbs {
                let mut carry = 0u32;
                #[unroll]
                for j in 0..comptime!(pre_limbs - i) {
                    let k = comptime!(i + j);
                    let t = psq[i as usize] * a[j as usize] + pcu[k as usize] + carry;
                    pcu[k as usize] = t % pre_chunk_div;
                    carry = t / pre_chunk_div;
                }
            }

            // Duplicate scan over both values' chunks; every chunk holds
            // exactly pre_chunk_digits real digits, leading zeros included
            // (that is what the host's digit-count guarantee buys).
            let mut p0 = 0u64;
            let mut p1 = 0u64;
            let mut dup = 0u64;
            let mut src: u32 = 0u32;
            while src < 2u32 {
                #[unroll]
                for i in 0..pre_limbs {
                    let mut c = if src == 0u32 {
                        psq[i as usize]
                    } else {
                        pcu[i as usize]
                    };
                    #[unroll]
                    for _k in 0..pre_chunk_digits {
                        let d = c % base;
                        c /= base;
                        if two_masks {
                            if d < 64u32 {
                                let bit = 1u64 << u64::cast_from(d);
                                dup |= p0 & bit;
                                p0 |= bit;
                            } else {
                                let bit = 1u64 << u64::cast_from(d - 64u32);
                                dup |= p1 & bit;
                                p1 |= bit;
                            }
                        } else {
                            let bit = 1u64 << u64::cast_from(d);
                            dup |= p0 & bit;
                            p0 |= bit;
                        }
                    }
                }
                src += 1u32;
            }
            if dup != 0u64 {
                ok = false;
            }
        }
    }

    // Full check: unique digits of n² and n³ together must number
    // exactly `base`. Same limb multiply and chunked scan as the
    // detailed kernel, but the scan bails at the first duplicate —
    // almost no candidate survives its n² scan. A probe build skips
    // it and reports the prefilter's survivors instead, which is the
    // only way a device test can see the filter itself (an
    // over-rejecting prefilter agrees with the CPU on any range
    // without a nice number in it — the v3.2.14 bug class).
    let mut m0 = 0u64;
    let mut m1 = 0u64;
    if ok && !probe {
        let mut nl = Array::<u32>::new(limbs as usize);
        #[unroll]
        for i in 0..limbs {
            let shift = comptime!(((i & 1) * 32) as u64);
            if comptime!(i < 2) {
                nl[i as usize] = u32::cast_from(n_lo >> shift);
            } else {
                nl[i as usize] = u32::cast_from(n_hi >> shift);
            }
        }
        let mut sq = Array::<u32>::new(sq_limbs as usize);
        #[unroll]
        for i in 0..sq_limbs {
            sq[i as usize] = 0u32;
        }
        #[unroll]
        for i in 0..limbs {
            let mut carry = 0u64;
            #[unroll]
            for jj in 0..limbs {
                let k = comptime!(i + jj);
                let t = u64::cast_from(nl[i as usize]) * u64::cast_from(nl[jj as usize])
                    + u64::cast_from(sq[k as usize])
                    + carry;
                sq[k as usize] = u32::cast_from(t);
                carry = t >> 32u64;
            }
            sq[comptime!(i + limbs) as usize] = u32::cast_from(carry);
        }

        // Scan n² first; n³ is only multiplied out if n² had no
        // duplicate (the same ordering worth 20-27% in the CUDA
        // kernel — the cube multiply is usually dead work). Straight-line
        // like the hand kernels: the sq scan reads a sq_limbs window, and
        // the cube is built directly in the scratch and destroyed by its
        // scan — no cu array, no extra copies, no runtime pass branch.
        // (The pass-loop version cost ~30% whole-kernel at bases without a
        // prefilter, where every candidate takes this path.)
        #[unroll]
        for i in 0..sq_limbs {
            sv_s[(svb + u32::cast_from(i)) as usize] = sq[i as usize];
        }
        let mut top: i32 = comptime!(sq_limbs as i32 - 1).runtime();
        while top >= 0 {
            if sv_s[(svb + u32::cast_from(top)) as usize] != 0u32 {
                break;
            }
            top -= 1;
        }
        while top >= 0 && ok {
            let mut rem = 0u32;
            if wide_chunk {
                let mut rem64 = 0u64;
                let mut i: i32 = top;
                while i >= 0 {
                    let cur =
                        (rem64 << 32u64) | u64::cast_from(sv_s[(svb + u32::cast_from(i)) as usize]);
                    // Quotient once, remainder by mul-sub: `%` would
                    // lower as a second independent multiply-high
                    // correction sequence (the hand kernels avoid it
                    // the same way).
                    let q = cur / u64::cast_from(chunk_div);
                    sv_s[(svb + u32::cast_from(i)) as usize] = u32::cast_from(q);
                    rem64 = cur - q * u64::cast_from(chunk_div);
                    i -= 1;
                }
                rem = u32::cast_from(rem64); // rem < chunk_div < 2^31
            } else {
                let mut i: i32 = top;
                while i >= 0 {
                    let vi = sv_s[(svb + u32::cast_from(i)) as usize];
                    let c1 = (rem << 16u32) | (vi >> 16u32);
                    let q1 = c1 / chunk_div;
                    let r1 = c1 - q1 * chunk_div;
                    let c2 = (r1 << 16u32) | (vi & 0xFFFFu32);
                    let q2 = c2 / chunk_div;
                    rem = c2 - q2 * chunk_div;
                    sv_s[(svb + u32::cast_from(i)) as usize] = (q1 << 16u32) | q2;
                    i -= 1;
                }
            }
            while top >= 0 {
                if sv_s[(svb + u32::cast_from(top)) as usize] != 0u32 {
                    break;
                }
                top -= 1;
            }

            let mut chunk = rem;
            let mut dup = 0u64;
            if top >= 0 {
                // Interior chunk: all chunk_digits digits, zeros included.
                #[unroll]
                for _k in 0..chunk_digits {
                    let cq = chunk / base;
                    let d = chunk - cq * base;
                    chunk = cq;
                    if two_masks {
                        if d < 64u32 {
                            let bit = 1u64 << u64::cast_from(d);
                            dup |= m0 & bit;
                            m0 |= bit;
                        } else {
                            let bit = 1u64 << u64::cast_from(d - 64u32);
                            dup |= m1 & bit;
                            m1 |= bit;
                        }
                    } else {
                        let bit = 1u64 << u64::cast_from(d);
                        dup |= m0 & bit;
                        m0 |= bit;
                    }
                }
            } else {
                // Most significant chunk: digits until zero.
                while chunk != 0u32 {
                    let cq = chunk / base;
                    let d = chunk - cq * base;
                    chunk = cq;
                    if two_masks {
                        if d < 64u32 {
                            let bit = 1u64 << u64::cast_from(d);
                            dup |= m0 & bit;
                            m0 |= bit;
                        } else {
                            let bit = 1u64 << u64::cast_from(d - 64u32);
                            dup |= m1 & bit;
                            m1 |= bit;
                        }
                    } else {
                        let bit = 1u64 << u64::cast_from(d);
                        dup |= m0 & bit;
                        m0 |= bit;
                    }
                }
            }
            if dup != 0u64 {
                ok = false;
            }
        }

        if ok {
            // cu = sq * n, built directly in the scratch and consumed there.
            #[unroll]
            for i in 0..cu_limbs {
                sv_s[(svb + u32::cast_from(i)) as usize] = 0u32;
            }
            #[unroll]
            for i in 0..sq_limbs {
                let mut carry = 0u64;
                #[unroll]
                for jj in 0..limbs {
                    let k = comptime!(i + jj);
                    let t = u64::cast_from(sq[i as usize]) * u64::cast_from(nl[jj as usize])
                        + u64::cast_from(sv_s[(svb + k) as usize])
                        + carry;
                    sv_s[(svb + k) as usize] = u32::cast_from(t);
                    carry = t >> 32u64;
                }
                sv_s[(svb + comptime!(i + limbs)) as usize] = u32::cast_from(carry);
            }
            let mut topc: i32 = comptime!(cu_limbs as i32 - 1).runtime();
            while topc >= 0 {
                if sv_s[(svb + u32::cast_from(topc)) as usize] != 0u32 {
                    break;
                }
                topc -= 1;
            }
            while topc >= 0 && ok {
                let mut rem = 0u32;
                if wide_chunk {
                    let mut rem64 = 0u64;
                    let mut i: i32 = topc;
                    while i >= 0 {
                        let cur = (rem64 << 32u64)
                            | u64::cast_from(sv_s[(svb + u32::cast_from(i)) as usize]);
                        // Quotient once, remainder by mul-sub: `%` would
                        // lower as a second independent multiply-high
                        // correction sequence (the hand kernels avoid it
                        // the same way).
                        let q = cur / u64::cast_from(chunk_div);
                        sv_s[(svb + u32::cast_from(i)) as usize] = u32::cast_from(q);
                        rem64 = cur - q * u64::cast_from(chunk_div);
                        i -= 1;
                    }
                    rem = u32::cast_from(rem64); // rem < chunk_div < 2^31
                } else {
                    let mut i: i32 = topc;
                    while i >= 0 {
                        let vi = sv_s[(svb + u32::cast_from(i)) as usize];
                        let c1 = (rem << 16u32) | (vi >> 16u32);
                        let q1 = c1 / chunk_div;
                        let r1 = c1 - q1 * chunk_div;
                        let c2 = (r1 << 16u32) | (vi & 0xFFFFu32);
                        let q2 = c2 / chunk_div;
                        rem = c2 - q2 * chunk_div;
                        sv_s[(svb + u32::cast_from(i)) as usize] = (q1 << 16u32) | q2;
                        i -= 1;
                    }
                }
                while topc >= 0 {
                    if sv_s[(svb + u32::cast_from(topc)) as usize] != 0u32 {
                        break;
                    }
                    topc -= 1;
                }

                let mut chunk = rem;
                let mut dup = 0u64;
                if topc >= 0 {
                    // Interior chunk: all chunk_digits digits, zeros included.
                    #[unroll]
                    for _k in 0..chunk_digits {
                        let cq = chunk / base;
                        let d = chunk - cq * base;
                        chunk = cq;
                        if two_masks {
                            if d < 64u32 {
                                let bit = 1u64 << u64::cast_from(d);
                                dup |= m0 & bit;
                                m0 |= bit;
                            } else {
                                let bit = 1u64 << u64::cast_from(d - 64u32);
                                dup |= m1 & bit;
                                m1 |= bit;
                            }
                        } else {
                            let bit = 1u64 << u64::cast_from(d);
                            dup |= m0 & bit;
                            m0 |= bit;
                        }
                    }
                } else {
                    // Most significant chunk: digits until zero.
                    while chunk != 0u32 {
                        let cq = chunk / base;
                        let d = chunk - cq * base;
                        chunk = cq;
                        if two_masks {
                            if d < 64u32 {
                                let bit = 1u64 << u64::cast_from(d);
                                dup |= m0 & bit;
                                m0 |= bit;
                            } else {
                                let bit = 1u64 << u64::cast_from(d - 64u32);
                                dup |= m1 & bit;
                                m1 |= bit;
                            }
                        } else {
                            let bit = 1u64 << u64::cast_from(d);
                            dup |= m0 & bit;
                            m0 |= bit;
                        }
                    }
                }
                if dup != 0u64 {
                    ok = false;
                }
            }
        }
    }

    if ok {
        let mut u = u32::cast_from(m0).count_ones() + u32::cast_from(m0 >> 32u64).count_ones();
        if two_masks {
            u += u32::cast_from(m1).count_ones() + u32::cast_from(m1 >> 32u64).count_ones();
        }
        if probe || u == base {
            let pos = nice_count[0].fetch_add(1u32);
            if pos < nice_cap {
                let o = NICEONLY_STRIDE * pos;
                nice_out[o as usize] = u32::cast_from(n_lo);
                nice_out[(o + 1u32) as usize] = u32::cast_from(n_lo >> 32u64);
                nice_out[(o + 2u32) as usize] = u32::cast_from(n_hi);
                nice_out[(o + 3u32) as usize] = u32::cast_from(n_hi >> 32u64);
            }
        }
    }
}
