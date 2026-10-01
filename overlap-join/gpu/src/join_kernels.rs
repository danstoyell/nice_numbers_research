//! Device stage of the overlap join, as `CubeCL` kernels written to the
//! conventions of the client's `cubecl_backend.rs` (u32 buffers, u64 digit
//! masks in registers, every division by a comptime constant, cube-scoped
//! compaction with `plane_exclusive_sum` and two `sync_cube` barriers per
//! step, split16 or wide digit scan chosen per runtime).
//!
//! Terms (see proto.rs): n has L base-b digits; a *top* is a prefix P of its
//! top t digits (n = P*b^f0 + R_low, f0 = L - t) with a certificate mask of
//! the output digits it fixes at positions >= k; a *bottom* is R = n mod b^k
//! whose low k digits of n^2 and n^3 are distinct (its mask). The two share
//! o = t + k - L digits of n (positions f0..k-1); the lowest `pp` of those are
//! the partition value v, the rest (0 or 1 digit here) the hash key. The
//! digit-sum class of R_low mod (b-1) is the other half of the bucket key.
//!
//! Per batch of partitions (one slot per partition value v):
//! 1. [`bottom_extend_kernel`]: every *bpre* entry (r0 = R mod b^f0 with its
//!    2*f0 distinct low digits; class-sorted, uploaded once per field) is
//!    extended by v's digits at positions f0..f0+pp-1 (exact digit-array
//!    arithmetic mod b^k); if a key digit remains, the data to derive its two
//!    output digits for any key value in O(1) is packed alongside.
//! 2. [`join_kernel`]: one cube per non-empty bucket (slot, key digit, class):
//!    the bucket's tops go to shared memory; the class segment of extended
//!    entries is scanned, entries valid for this key digit are compacted into
//!    a shared queue, and each drained entry is ANDed against every top of the
//!    bucket (one 64-bit AND plus the field-edge range test per pair).
//!    Survivors (top index, r0) are staged in shared memory and flushed to a
//!    global list with one atomic per flush.
//! 3. [`mid_kernel`] (optional, `mid` > 0): a middle-digit prefilter on the
//!    survivors. From n's low k2 = k + mid digits (r0 and P mod b^(k2-f0))
//!    it computes the digits of n^2 and n^3 at positions 0..k2-1 exactly and
//!    requires them distinct and disjoint from the top certificate (used as
//!    a seed only when the host proved every certified position >= k2).
//!    Survivors are compacted to a second list, one atomic per cube-round.
//! 4. [`check_kernel`]: grid-stride over the (second) survivor list, rebuild
//!    n = P*b^f0 + r0 and run the client's own `candidate_check` on it.
#![allow(
    clippy::cast_possible_truncation,
    clippy::cast_possible_wrap,
    clippy::cast_lossless,
    clippy::too_many_arguments,
    clippy::too_many_lines,
    clippy::similar_names,
    clippy::many_single_char_names,
    clippy::collapsible_if,
    clippy::fn_params_excessive_bools
)]

use crate::client_check::candidate_check;
use cubecl::prelude::*;

/// Threads per cube for all three kernels (the client's WORKGROUP_SIZE).
pub const JOIN_WG: u32 = 256;
/// Tops held in shared memory per pass over a bucket's entries.
pub const TOP_CAP: u32 = 256;
/// Survivors staged in shared memory before a flush to the global list.
pub const SURV_SH_CAP: u32 = 1024;
/// Staged-survivor level that triggers a flush at the next barrier.
pub const SURV_FLUSH: u32 = 512;
/// Sentinel mask of an extended entry that failed its fixed positions.
pub const DEAD_MASK: u64 = 0xFFFF_FFFF_FFFF_FFFF;

/// Step 1: extend the class-sorted bpre list by each slot's partition digits.
/// Grid: x over bpre entries, y over batch slots.
#[cube(launch_unchecked)]
pub fn bottom_extend_kernel(
    bp_r: &Array<u32>,
    bp_m: &Array<u32>, // lo, hi words per entry
    vs: &Array<u32>,   // partition value per slot
    ext_m: &mut Array<u32>,  // lo, hi words per (slot, entry)
    ext_pk: &mut Array<u32>, // u2 | u3 << 8 | s2 << 16 | s3 << 24 per (slot, entry)
    nbp: u32,
    #[comptime] base: u32,
    #[comptime] f0: u32,
    #[comptime] pp: u32,
    #[comptime] k: u32,
    #[comptime] key_level: bool,
) {
    let i = ABSOLUTE_POS_X;
    let slot = CUBE_POS_Y;
    if i < nbp {
        let r0 = bp_r[i as usize];
        let mut m = (u64::cast_from(bp_m[(2u32 * i + 1u32) as usize]) << 32u64)
            | u64::cast_from(bp_m[(2u32 * i) as usize]);
        let v = vs[slot as usize];

        // Digits of R' = r0 + v * b^f0 (the key digit, if any, left at 0).
        let mut d = Array::<u32>::new(k as usize);
        let mut x = r0;
        #[unroll]
        for j in 0..f0 {
            d[j as usize] = x % base;
            x /= base;
        }
        let mut y = v;
        #[unroll]
        for j in f0..comptime!(f0 + pp) {
            d[j as usize] = y % base;
            y /= base;
        }
        #[unroll]
        for j in comptime!(f0 + pp)..k {
            d[j as usize] = 0u32;
        }

        // sq = R'^2 mod b^k and cu = R'^3 mod b^k as digit arrays: column
        // sums of digit products (each < b^2 <= 4096) plus carry, exact in u32.
        let mut sq = Array::<u32>::new(k as usize);
        let mut carry = 0u32;
        #[unroll]
        for pos in 0..k {
            let mut col = carry;
            #[unroll]
            for i2 in 0..comptime!(pos + 1) {
                col += d[i2 as usize] * d[comptime!(pos - i2) as usize];
            }
            sq[pos as usize] = col % base;
            carry = col / base;
        }
        let mut cu = Array::<u32>::new(k as usize);
        carry = 0u32;
        #[unroll]
        for pos in 0..k {
            let mut col = carry;
            #[unroll]
            for i2 in 0..comptime!(pos + 1) {
                col += sq[i2 as usize] * d[comptime!(pos - i2) as usize];
            }
            cu[pos as usize] = col % base;
            carry = col / base;
        }

        // The partition positions: two new output digits each, distinct
        // from each other and from everything certified so far.
        let mut ok = true;
        #[unroll]
        for j in f0..comptime!(f0 + pp) {
            let g2 = sq[j as usize];
            let g3 = cu[j as usize];
            let bb = (1u64 << u64::cast_from(g2)) | (1u64 << u64::cast_from(g3));
            if g2 == g3 || (m & bb) != 0u64 {
                ok = false;
            }
            m |= bb;
        }
        if !ok {
            m = DEAD_MASK;
        }
        let idx = slot * nbp + i;
        ext_m[(2u32 * idx) as usize] = u32::cast_from(m);
        ext_m[(2u32 * idx + 1u32) as usize] = u32::cast_from(m >> 32u64);
        if key_level {
            // Key digit c at position k-1: (R' + c b^(k-1))^2 has digit
            // (u2 + c * 2 d0) mod b there, the cube (u3 + c * 3 d0^2) mod b
            // (k-1 >= 1; u2, u3 are R'^2, R'^3's digits at k-1).
            let u2 = sq[comptime!(k - 1) as usize];
            let u3 = cu[comptime!(k - 1) as usize];
            let d0 = d[0];
            let s2 = (2u32 * d0) % base;
            let s3 = (3u32 * ((d0 * d0) % base)) % base;
            ext_pk[idx as usize] = u2 | (u3 << 8u32) | (s2 << 16u32) | (s3 << 24u32);
        }
    }
}

/// Flush the shared survivor stage to the global list. Must be called by the
/// whole cube at a point where no thread is still appending (after a
/// barrier); `sc` is the stage count read after that barrier.
#[cube]
fn flush_survivors(
    s_t: &SharedMemory<u32>,
    s_r: &SharedMemory<u32>,
    s_cnt: &mut SharedMemory<Atomic<u32>>,
    s_base: &mut SharedMemory<u32>,
    surv: &mut Array<u32>,
    surv_count: &mut Array<Atomic<u32>>,
    surv_cap: u32,
    sc: u32,
) {
    let mut n = sc;
    if n > SURV_SH_CAP {
        n = SURV_SH_CAP; // the rest went straight to the global list
    }
    if UNIT_POS_X == 0u32 {
        s_base[0] = surv_count[0].fetch_add(n);
    }
    sync_cube();
    let gb = s_base[0];
    let mut i = UNIT_POS_X;
    while i < n {
        let g = gb + i;
        if g < surv_cap {
            surv[(2u32 * g) as usize] = s_t[i as usize];
            surv[(2u32 * g + 1u32) as usize] = s_r[i as usize];
        }
        i += CUBE_DIM_X;
    }
    sync_cube();
    if UNIT_POS_X == 0u32 {
        s_cnt[0].store(0u32);
    }
}

/// Step 2: one cube per work item (slot, bucket, top-list range); cubes
/// grid-stride over the work list. See the module docs.
#[cube(launch_unchecked)]
pub fn join_kernel(
    ext_m: &Array<u32>,
    ext_pk: &Array<u32>,
    bp_r: &Array<u32>,
    seg: &Array<u32>,  // class segment offsets into bpre (b entries)
    work: &Array<u32>, // slot, bucket, tl start, tl end per item
    tl: &Array<u32>,   // top indices grouped by bucket
    top_m: &Array<u32>, // lo, hi certificate words per top
    top_r: &Array<u32>, // rlo, rhi: r0 range inside [s, e) per top
    surv: &mut Array<u32>, // top index, r0 per survivor
    surv_count: &mut Array<Atomic<u32>>,
    stats: &mut Array<u32>, // per work item: bucket entries (verification)
    nwork: u32,
    nbp: u32,
    surv_cap: u32,
    #[comptime] base: u32,
    #[comptime] key_level: bool,
    #[comptime] key_at_zero: bool, // the key digit is n's digit 0 (f0 = p = 0, k = 1)
    #[comptime] with_stats: bool,
) {
    let m1 = comptime!(base - 1);
    let mut q_lo = SharedMemory::<u32>::new(comptime!((2 * JOIN_WG) as usize));
    let mut q_hi = SharedMemory::<u32>::new(comptime!((2 * JOIN_WG) as usize));
    let mut q_r = SharedMemory::<u32>::new(comptime!((2 * JOIN_WG) as usize));
    let mut t_lo = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_hi = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_rlo = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_rhi = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_id = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut plane_tot = SharedMemory::<u32>::new(comptime!(JOIN_WG as usize));
    let mut s_t = SharedMemory::<u32>::new(comptime!(SURV_SH_CAP as usize));
    let mut s_r = SharedMemory::<u32>::new(comptime!(SURV_SH_CAP as usize));
    let mut s_cnt = SharedMemory::<Atomic<u32>>::new(1usize);
    let mut s_base = SharedMemory::<u32>::new(1usize);
    let my_plane = UNIT_POS_X / PLANE_DIM;
    let num_planes = CUBE_DIM_X / PLANE_DIM;

    if UNIT_POS_X == 0u32 {
        s_cnt[0].store(0u32);
    }
    sync_cube();

    let mut w = CUBE_POS_X;
    while w < nwork {
        let slot = work[(4u32 * w) as usize];
        let bx = work[(4u32 * w + 1u32) as usize];
        let ts = work[(4u32 * w + 2u32) as usize];
        let te = work[(4u32 * w + 3u32) as usize];
        let dkey = bx / m1;
        let cls = bx - dkey * m1;
        let cs = seg[cls as usize];
        let ce = seg[(cls + 1u32) as usize];
        let ebase = slot * nbp;

        let mut tc = ts;
        while tc < te {
            let mut nt = te - tc;
            if nt > TOP_CAP {
                nt = TOP_CAP;
            }
            if UNIT_POS_X < nt {
                let t = tl[(tc + UNIT_POS_X) as usize];
                t_lo[UNIT_POS_X as usize] = top_m[(2u32 * t) as usize];
                t_hi[UNIT_POS_X as usize] = top_m[(2u32 * t + 1u32) as usize];
                t_rlo[UNIT_POS_X as usize] = top_r[(2u32 * t) as usize];
                t_rhi[UNIT_POS_X as usize] = top_r[(2u32 * t + 1u32) as usize];
                t_id[UNIT_POS_X as usize] = t;
            }
            sync_cube();

            let mut valid_total = 0u32;
            let mut qn = 0u32;
            let mut tile = cs;
            loop {
                // Produce: this thread's entry of the tile, if it is in the
                // bucket (valid for this key digit).
                let e = tile + UNIT_POS_X;
                let mut pf = 0u32;
                let mut m = 0u64;
                let mut r0 = 0u32;
                if e < ce {
                    let gi = ebase + e;
                    m = (u64::cast_from(ext_m[(2u32 * gi + 1u32) as usize]) << 32u64)
                        | u64::cast_from(ext_m[(2u32 * gi) as usize]);
                    if key_level {
                        let pk = ext_pk[gi as usize];
                        let u2 = pk & 255u32;
                        let u3 = (pk >> 8u32) & 255u32;
                        let s2 = (pk >> 16u32) & 255u32;
                        let s3 = pk >> 24u32;
                        let mut g2 = (u2 + dkey * s2) % base;
                        let mut g3 = (u3 + dkey * s3) % base;
                        if key_at_zero {
                            // Position 0 is not linear in the new digit.
                            g2 = (dkey * dkey) % base;
                            g3 = (g2 * dkey) % base;
                        }
                        let bb = (1u64 << u64::cast_from(g2)) | (1u64 << u64::cast_from(g3));
                        if g2 != g3 && (m & bb) == 0u64 {
                            pf = 1u32;
                            m |= bb;
                        }
                    } else {
                        if m != DEAD_MASK {
                            pf = 1u32;
                        }
                    }
                    r0 = bp_r[e as usize];
                }

                let idx_in_plane = plane_exclusive_sum(pf);
                let tot = plane_sum(pf);
                if UNIT_POS_PLANE == 0u32 {
                    plane_tot[my_plane as usize] = tot;
                }
                // Barrier 1: plane totals visible; last drain's reads and
                // survivor appends are complete.
                sync_cube();

                let sc = s_cnt[0].load();
                if sc >= SURV_FLUSH {
                    flush_survivors(
                        &s_t, &s_r, &mut s_cnt, &mut s_base, surv, surv_count, surv_cap, sc,
                    );
                }

                let mut base_off = qn;
                let mut incoming = 0u32;
                let mut p = 0u32;
                while p < num_planes {
                    let t = plane_tot[p as usize];
                    if p < my_plane {
                        base_off += t;
                    }
                    incoming += t;
                    p += 1u32;
                }
                if pf != 0u32 {
                    let dst = (base_off + idx_in_plane) as usize;
                    q_lo[dst] = u32::cast_from(m);
                    q_hi[dst] = u32::cast_from(m >> 32u64);
                    q_r[dst] = r0;
                }
                qn += incoming;
                valid_total += incoming;
                let done = tile + CUBE_DIM_X >= ce;
                // Barrier 2: queue writes visible to the drain.
                sync_cube();

                let mut take = 0u32;
                if qn >= CUBE_DIM_X {
                    take = CUBE_DIM_X;
                } else if done {
                    take = qn;
                }
                if UNIT_POS_X < take {
                    let s = (qn - take + UNIT_POS_X) as usize;
                    let mlo = q_lo[s];
                    let mhi = q_hi[s];
                    let rr = q_r[s];
                    let mut j = 0u32;
                    while j < nt {
                        let ju = j as usize;
                        if ((mlo & t_lo[ju]) | (mhi & t_hi[ju])) == 0u32
                            && rr >= t_rlo[ju]
                            && rr < t_rhi[ju]
                        {
                            let at = s_cnt[0].fetch_add(1u32);
                            if at < SURV_SH_CAP {
                                s_t[at as usize] = t_id[ju];
                                s_r[at as usize] = rr;
                            } else {
                                let g = surv_count[0].fetch_add(1u32);
                                if g < surv_cap {
                                    surv[(2u32 * g) as usize] = t_id[ju];
                                    surv[(2u32 * g + 1u32) as usize] = rr;
                                }
                            }
                        }
                        j += 1u32;
                    }
                }
                qn -= take;
                if done && qn == 0u32 {
                    break;
                }
                tile += CUBE_DIM_X;
            }
            if with_stats {
                if tc == ts && UNIT_POS_X == 0u32 {
                    stats[w as usize] = valid_total;
                }
            }
            tc += TOP_CAP;
            // The next top chunk (or work item) overwrites the shared tops.
            sync_cube();
        }
        w += CUBE_COUNT_X;
    }
    sync_cube();
    let sc = s_cnt[0].load();
    if sc > 0u32 {
        flush_survivors(
            &s_t, &s_r, &mut s_cnt, &mut s_base, surv, surv_count, surv_cap, sc,
        );
    }
}

/// Step 2, v2: as [`join_kernel`], but each thread evaluates `ept` class
/// entries per tile and holds `ept` bucket entries per drain (the queue keeps
/// entry indices, 4 bytes, and the drain re-reads the entry from global
/// memory, which the tile just touched); the top's range bounds are read only
/// on the rare path where the AND passes.
#[cube(launch_unchecked)]
pub fn join_kernel_v2(
    ext_m: &Array<u32>,
    ext_pk: &Array<u32>,
    bp_r: &Array<u32>,
    seg: &Array<u32>,
    work: &Array<u32>,
    tl: &Array<u32>,
    top_m: &Array<u32>,
    top_r: &Array<u32>,
    surv: &mut Array<u32>,
    surv_count: &mut Array<Atomic<u32>>,
    stats: &mut Array<u32>,
    nwork: u32,
    nbp: u32,
    surv_cap: u32,
    #[comptime] base: u32,
    #[comptime] key_level: bool,
    #[comptime] key_at_zero: bool,
    #[comptime] with_stats: bool,
    #[comptime] ept: u32,
    #[comptime] exp: u32, // experiments: 0 normal, 1 no top loop, 2 count survivors only
) {
    let m1 = comptime!(base - 1);
    let wave = comptime!(ept * JOIN_WG);
    let mut xcount = 0u32;
    let mut q_e = SharedMemory::<u32>::new(comptime!((2 * ept * JOIN_WG) as usize));
    let mut t_lo = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_hi = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_rlo = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_rhi = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_id = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut plane_tot = SharedMemory::<u32>::new(64usize);
    let mut s_t = SharedMemory::<u32>::new(comptime!(SURV_SH_CAP as usize));
    let mut s_r = SharedMemory::<u32>::new(comptime!(SURV_SH_CAP as usize));
    let mut s_cnt = SharedMemory::<Atomic<u32>>::new(1usize);
    let mut s_base = SharedMemory::<u32>::new(1usize);
    let my_plane = UNIT_POS_X / PLANE_DIM;
    let num_planes = CUBE_DIM_X / PLANE_DIM;

    if UNIT_POS_X == 0u32 {
        s_cnt[0].store(0u32);
    }
    sync_cube();

    let mut w = CUBE_POS_X;
    while w < nwork {
        let slot = work[(4u32 * w) as usize];
        let bx = work[(4u32 * w + 1u32) as usize];
        let ts = work[(4u32 * w + 2u32) as usize];
        let te = work[(4u32 * w + 3u32) as usize];
        let dkey = bx / m1;
        let cls = bx - dkey * m1;
        let cs = seg[cls as usize];
        let ce = seg[(cls + 1u32) as usize];
        let ebase = slot * nbp;

        let mut tc = ts;
        while tc < te {
            let mut nt = te - tc;
            if nt > TOP_CAP {
                nt = TOP_CAP;
            }
            if UNIT_POS_X < nt {
                let t = tl[(tc + UNIT_POS_X) as usize];
                t_lo[UNIT_POS_X as usize] = top_m[(2u32 * t) as usize];
                t_hi[UNIT_POS_X as usize] = top_m[(2u32 * t + 1u32) as usize];
                t_rlo[UNIT_POS_X as usize] = top_r[(2u32 * t) as usize];
                t_rhi[UNIT_POS_X as usize] = top_r[(2u32 * t + 1u32) as usize];
                t_id[UNIT_POS_X as usize] = t;
            }
            sync_cube();

            let mut valid_total = 0u32;
            let mut qn = 0u32;
            let mut tile = cs;
            loop {
                // Produce: `ept` entries of the tile per thread.
                let mut flags = Array::<u32>::new(ept as usize);
                let mut mine = 0u32;
                #[unroll]
                for j in 0..ept {
                    let e = tile + UNIT_POS_X + comptime!(j * JOIN_WG);
                    let mut pf = 0u32;
                    if e < ce {
                        let gi = ebase + e;
                        let m = (u64::cast_from(ext_m[(2u32 * gi + 1u32) as usize]) << 32u64)
                            | u64::cast_from(ext_m[(2u32 * gi) as usize]);
                        if key_level {
                            let pk = ext_pk[gi as usize];
                            let mut g2 = ((pk & 255u32) + dkey * ((pk >> 16u32) & 255u32)) % base;
                            let mut g3 = (((pk >> 8u32) & 255u32) + dkey * (pk >> 24u32)) % base;
                            if key_at_zero {
                                g2 = (dkey * dkey) % base;
                                g3 = (g2 * dkey) % base;
                            }
                            let bb = (1u64 << u64::cast_from(g2)) | (1u64 << u64::cast_from(g3));
                            if g2 != g3 && (m & bb) == 0u64 {
                                pf = 1u32;
                            }
                        } else {
                            if m != DEAD_MASK {
                                pf = 1u32;
                            }
                        }
                    }
                    flags[j as usize] = pf;
                    mine += pf;
                }
                let idx_in_plane = plane_exclusive_sum(mine);
                let tot = plane_sum(mine);
                if UNIT_POS_PLANE == 0u32 {
                    plane_tot[my_plane as usize] = tot;
                }
                // Barrier 1.
                sync_cube();

                let sc = s_cnt[0].load();
                if sc >= SURV_FLUSH {
                    flush_survivors(
                        &s_t, &s_r, &mut s_cnt, &mut s_base, surv, surv_count, surv_cap, sc,
                    );
                }

                let mut base_off = qn;
                let mut incoming = 0u32;
                let mut p = 0u32;
                while p < num_planes {
                    let t = plane_tot[p as usize];
                    if p < my_plane {
                        base_off += t;
                    }
                    incoming += t;
                    p += 1u32;
                }
                let mut dst = base_off + idx_in_plane;
                #[unroll]
                for j in 0..ept {
                    if flags[j as usize] != 0u32 {
                        q_e[dst as usize] = tile + UNIT_POS_X + comptime!(j * JOIN_WG);
                        dst += 1u32;
                    }
                }
                qn += incoming;
                valid_total += incoming;
                let done = tile + wave >= ce;
                // Barrier 2.
                sync_cube();

                let mut take = 0u32;
                if qn >= wave {
                    take = wave;
                } else if done {
                    take = qn;
                }
                if take > 0u32 {
                    let first = qn - take;
                    let mut mlo = Array::<u32>::new(ept as usize);
                    let mut mhi = Array::<u32>::new(ept as usize);
                    let mut rr = Array::<u32>::new(ept as usize);
                    #[unroll]
                    for j in 0..ept {
                        let sl = UNIT_POS_X + comptime!(j * JOIN_WG);
                        // An empty slot keeps an all-ones mask: it never passes.
                        mlo[j as usize] = 0xFFFF_FFFFu32;
                        mhi[j as usize] = 0xFFFF_FFFFu32;
                        // Outside every top's [rlo, rhi) (rhi <= b^f0 < 2^32):
                        // an empty slot never passes, even against a zero mask.
                        rr[j as usize] = 0xFFFF_FFFFu32;
                        if sl < take {
                            let e = q_e[(first + sl) as usize];
                            let gi = ebase + e;
                            let mut m = (u64::cast_from(ext_m[(2u32 * gi + 1u32) as usize]) << 32u64)
                                | u64::cast_from(ext_m[(2u32 * gi) as usize]);
                            if key_level {
                                let pk = ext_pk[gi as usize];
                                let mut g2 = ((pk & 255u32) + dkey * ((pk >> 16u32) & 255u32)) % base;
                                let mut g3 = (((pk >> 8u32) & 255u32) + dkey * (pk >> 24u32)) % base;
                                if key_at_zero {
                                    g2 = (dkey * dkey) % base;
                                    g3 = (g2 * dkey) % base;
                                }
                                m |= (1u64 << u64::cast_from(g2)) | (1u64 << u64::cast_from(g3));
                            }
                            mlo[j as usize] = u32::cast_from(m);
                            mhi[j as usize] = u32::cast_from(m >> 32u64);
                            rr[j as usize] = bp_r[e as usize];
                        }
                    }
                    // Threads past `take` hold only never-passing slots.
                    if UNIT_POS_X < take && comptime!(exp != 1) {
                        let mut jt = 0u32;
                        while jt < nt {
                            let tlo = t_lo[jt as usize];
                            let thi = t_hi[jt as usize];
                            #[unroll]
                            for j in 0..ept {
                                if ((mlo[j as usize] & tlo) | (mhi[j as usize] & thi)) == 0u32 {
                                    let r0 = rr[j as usize];
                                    if r0 >= t_rlo[jt as usize] && r0 < t_rhi[jt as usize] {
                                        if comptime!(exp == 2) {
                                            xcount += 1u32;
                                        } else {
                                        let at = s_cnt[0].fetch_add(1u32);
                                        if at < SURV_SH_CAP {
                                            s_t[at as usize] = t_id[jt as usize];
                                            s_r[at as usize] = r0;
                                        } else {
                                            let g = surv_count[0].fetch_add(1u32);
                                            if g < surv_cap {
                                                surv[(2u32 * g) as usize] = t_id[jt as usize];
                                                surv[(2u32 * g + 1u32) as usize] = r0;
                                            }
                                        }
                                        }
                                    }
                                }
                            }
                            jt += 1u32;
                        }
                    }
                }
                qn -= take;
                if done && qn == 0u32 {
                    break;
                }
                tile += wave;
            }
            if with_stats {
                if tc == ts && UNIT_POS_X == 0u32 {
                    stats[w as usize] = valid_total;
                }
            }
            tc += TOP_CAP;
            sync_cube();
        }
        w += CUBE_COUNT_X;
    }
    sync_cube();
    let sc = s_cnt[0].load();
    if sc > 0u32 {
        flush_survivors(
            &s_t, &s_r, &mut s_cnt, &mut s_base, surv, surv_count, surv_cap, sc,
        );
    }
    if comptime!(exp == 2) {
        if xcount > 0u32 {
            surv_count[0].fetch_add(xcount);
        }
    }
}

/// Step 1+ (v3): extension fused with bucketization. One cube per
/// (class c, slot): its bpre segment is extended by the slot's partition
/// digits exactly as in [`bottom_extend_kernel`] (the extended entries are
/// written to `ext_m`/`ext_pk` as there), and each surviving entry's two
/// key-position digits are stepped through every key value d incrementally
/// (+s2, +s3 mod b); the entry's index goes onto the (slot, d, c) list for
/// every d where they are distinct and new. List layout per slot:
/// `slot*b*nbp + b*seg[c] + d*len(c) + i`; counts at `(slot*b + d)*m1 + c`.
#[cube(launch_unchecked)]
pub fn bucket_kernel(
    bp_r: &Array<u32>,
    bp_m: &Array<u32>,
    seg: &Array<u32>,
    vs: &Array<u32>,
    ext_m: &mut Array<u32>,
    ext_pk: &mut Array<u32>,
    lists: &mut Array<u32>,
    counts: &mut Array<u32>,
    nbp: u32,
    #[comptime] base: u32,
    #[comptime] f0: u32,
    #[comptime] pp: u32,
    #[comptime] k: u32,
    #[comptime] key_level: bool,
    #[comptime] key_at_zero: bool,
) {
    let m1 = comptime!(base - 1);
    let nkeys = comptime!(if key_level { base } else { 1 });
    let mut s_cnt = SharedMemory::<Atomic<u32>>::new(64usize);
    let c = CUBE_POS_X;
    let slot = CUBE_POS_Y;
    if UNIT_POS_X < 64u32 {
        s_cnt[UNIT_POS_X as usize].store(0u32);
    }
    sync_cube();
    let cs = seg[c as usize];
    let ce = seg[(c + 1u32) as usize];
    let clen = ce - cs;
    let lbase = slot * base * nbp + base * cs;
    let v = vs[slot as usize];
    let mut i = cs + UNIT_POS_X;
    while i < ce {
        let r0 = bp_r[i as usize];
        let mut m = (u64::cast_from(bp_m[(2u32 * i + 1u32) as usize]) << 32u64)
            | u64::cast_from(bp_m[(2u32 * i) as usize]);
        let mut d = Array::<u32>::new(k as usize);
        let mut x = r0;
        #[unroll]
        for j in 0..f0 {
            d[j as usize] = x % base;
            x /= base;
        }
        let mut y = v;
        #[unroll]
        for j in f0..comptime!(f0 + pp) {
            d[j as usize] = y % base;
            y /= base;
        }
        #[unroll]
        for j in comptime!(f0 + pp)..k {
            d[j as usize] = 0u32;
        }
        let mut sq = Array::<u32>::new(k as usize);
        let mut carry = 0u32;
        #[unroll]
        for pos in 0..k {
            let mut col = carry;
            #[unroll]
            for i2 in 0..comptime!(pos + 1) {
                col += d[i2 as usize] * d[comptime!(pos - i2) as usize];
            }
            sq[pos as usize] = col % base;
            carry = col / base;
        }
        let mut cu = Array::<u32>::new(k as usize);
        carry = 0u32;
        #[unroll]
        for pos in 0..k {
            let mut col = carry;
            #[unroll]
            for i2 in 0..comptime!(pos + 1) {
                col += sq[i2 as usize] * d[comptime!(pos - i2) as usize];
            }
            cu[pos as usize] = col % base;
            carry = col / base;
        }
        let mut ok = true;
        #[unroll]
        for j in f0..comptime!(f0 + pp) {
            let g2 = sq[j as usize];
            let g3 = cu[j as usize];
            let bb = (1u64 << u64::cast_from(g2)) | (1u64 << u64::cast_from(g3));
            if g2 == g3 || (m & bb) != 0u64 {
                ok = false;
            }
            m |= bb;
        }
        if !ok {
            m = DEAD_MASK;
        }
        let idx = slot * nbp + i;
        ext_m[(2u32 * idx) as usize] = u32::cast_from(m);
        ext_m[(2u32 * idx + 1u32) as usize] = u32::cast_from(m >> 32u64);
        if key_level {
            let u2 = sq[comptime!(k - 1) as usize];
            let u3 = cu[comptime!(k - 1) as usize];
            let d0 = d[0];
            let s2 = (2u32 * d0) % base;
            let s3 = (3u32 * ((d0 * d0) % base)) % base;
            ext_pk[idx as usize] = u2 | (u3 << 8u32) | (s2 << 16u32) | (s3 << 24u32);
            if ok {
                // Key digit dk: (u2 + dk s2, u3 + dk s3) mod b, stepped.
                let mut g2 = u2;
                let mut g3 = u3;
                let mut dk = 0u32;
                while dk < nkeys {
                    let mut a2 = g2;
                    let mut a3 = g3;
                    if key_at_zero {
                        a2 = (dk * dk) % base;
                        a3 = (a2 * dk) % base;
                    }
                    let bb = (1u64 << u64::cast_from(a2)) | (1u64 << u64::cast_from(a3));
                    if a2 != a3 && (m & bb) == 0u64 {
                        let at = s_cnt[dk as usize].fetch_add(1u32);
                        lists[(lbase + dk * clen + at) as usize] = i;
                    }
                    g2 += s2;
                    if g2 >= base {
                        g2 -= base;
                    }
                    g3 += s3;
                    if g3 >= base {
                        g3 -= base;
                    }
                    dk += 1u32;
                }
            }
        } else {
            if ok {
                let at = s_cnt[0].fetch_add(1u32);
                lists[(lbase + at) as usize] = i;
            }
        }
        i += CUBE_DIM_X;
    }
    sync_cube();
    if UNIT_POS_X < nkeys {
        counts[((slot * nkeys + UNIT_POS_X) * m1 + c) as usize] = s_cnt[UNIT_POS_X as usize].load();
    }
}

/// Step 2 (v3): one cube per work item over the dense (slot, d, c) list
/// built by [`bucket_kernel`]; `ept` entries per thread per wave, every
/// thread runs every wave (uniform), survivors staged and flushed per wave.
#[cube(launch_unchecked)]
pub fn join_kernel_v3(
    ext_m: &Array<u32>,
    ext_pk: &Array<u32>,
    bp_r: &Array<u32>,
    seg: &Array<u32>,
    lists: &Array<u32>,
    counts: &Array<u32>,
    work: &Array<u32>,
    tl: &Array<u32>,
    top_m: &Array<u32>,
    top_r: &Array<u32>,
    surv: &mut Array<u32>,
    surv_count: &mut Array<Atomic<u32>>,
    stats: &mut Array<u32>,
    nwork: u32,
    nbp: u32,
    surv_cap: u32,
    #[comptime] base: u32,
    #[comptime] key_level: bool,
    #[comptime] key_at_zero: bool,
    #[comptime] with_stats: bool,
    #[comptime] ept: u32,
    #[comptime] exp: u32, // experiments: 0 normal, 1 no AND loop, 2 AND loop without the survivor walk
) {
    let mut xcount = 0u32;
    let m1 = comptime!(base - 1);
    let nkeys = comptime!(if key_level { base } else { 1 });
    let wave = comptime!(ept * JOIN_WG);
    let mut t_lo = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_hi = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_rlo = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_rhi = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut t_id = SharedMemory::<u32>::new(comptime!(TOP_CAP as usize));
    let mut s_t = SharedMemory::<u32>::new(comptime!(SURV_SH_CAP as usize));
    let mut s_r = SharedMemory::<u32>::new(comptime!(SURV_SH_CAP as usize));
    let mut s_cnt = SharedMemory::<Atomic<u32>>::new(1usize);
    let mut s_base = SharedMemory::<u32>::new(1usize);

    if UNIT_POS_X == 0u32 {
        s_cnt[0].store(0u32);
    }
    sync_cube();

    let mut w = CUBE_POS_X;
    while w < nwork {
        let slot = work[(4u32 * w) as usize];
        let bx = work[(4u32 * w + 1u32) as usize];
        let ts = work[(4u32 * w + 2u32) as usize];
        let te = work[(4u32 * w + 3u32) as usize];
        let dkey = bx / m1;
        let cls = bx - dkey * m1;
        let cs = seg[cls as usize];
        let clen = seg[(cls + 1u32) as usize] - cs;
        let mut ne = counts[((slot * nkeys + dkey) * m1 + cls) as usize];
        if comptime!(exp == 3) {
            ne = 0u32;
        }
        let lbase = slot * base * nbp + base * cs + dkey * clen;
        let ebase = slot * nbp;
        if with_stats {
            if UNIT_POS_X == 0u32 {
                stats[w as usize] = ne;
            }
        }

        let mut tc = ts;
        if comptime!(exp == 3 || exp == 4) {
            tc = te;
            xcount += ne + ebase + lbase;
        }
        while tc < te {
            let mut nt = te - tc;
            if nt > TOP_CAP {
                nt = TOP_CAP;
            }
            if UNIT_POS_X < nt {
                let t = tl[(tc + UNIT_POS_X) as usize];
                t_lo[UNIT_POS_X as usize] = top_m[(2u32 * t) as usize];
                t_hi[UNIT_POS_X as usize] = top_m[(2u32 * t + 1u32) as usize];
                t_rlo[UNIT_POS_X as usize] = top_r[(2u32 * t) as usize];
                t_rhi[UNIT_POS_X as usize] = top_r[(2u32 * t + 1u32) as usize];
                t_id[UNIT_POS_X as usize] = t;
            }
            sync_cube();

            let mut ws = 0u32;
            while ws < ne {
                let mut mlo = Array::<u32>::new(ept as usize);
                let mut mhi = Array::<u32>::new(ept as usize);
                let mut rr = Array::<u32>::new(ept as usize);
                // Per-slot validity: an empty slot must never pass, whatever
                // the top's mask (a top may certify nothing at small t).
                let mut vv = Array::<u32>::new(ept as usize);
                #[unroll]
                for j in 0..ept {
                    let sl = ws + UNIT_POS_X + comptime!(j * JOIN_WG);
                    mlo[j as usize] = 0xFFFF_FFFFu32;
                    mhi[j as usize] = 0xFFFF_FFFFu32;
                    rr[j as usize] = 0u32;
                    vv[j as usize] = 0u32;
                    if sl < ne {
                        vv[j as usize] = 0xFFFF_FFFFu32;
                        let e = lists[(lbase + sl) as usize];
                        let gi = ebase + e;
                        let mut m = (u64::cast_from(ext_m[(2u32 * gi + 1u32) as usize]) << 32u64)
                            | u64::cast_from(ext_m[(2u32 * gi) as usize]);
                        if key_level {
                            let pk = ext_pk[gi as usize];
                            let mut g2 = ((pk & 255u32) + dkey * ((pk >> 16u32) & 255u32)) % base;
                            let mut g3 = (((pk >> 8u32) & 255u32) + dkey * (pk >> 24u32)) % base;
                            if key_at_zero {
                                g2 = (dkey * dkey) % base;
                                g3 = (g2 * dkey) % base;
                            }
                            m |= (1u64 << u64::cast_from(g2)) | (1u64 << u64::cast_from(g3));
                        }
                        mlo[j as usize] = u32::cast_from(m);
                        mhi[j as usize] = u32::cast_from(m >> 32u64);
                        rr[j as usize] = bp_r[e as usize];
                    }
                }
                // Branch-free AND over a chunk of up to 32 tops into a pass
                // bitmask per entry, then only the (rare) set bits are
                // walked: the survivor path diverges once per chunk, not
                // once per top.
                let mut jc = 0u32;
                if comptime!(exp == 1) {
                    jc = nt;
                }
                while jc < nt {
                    let mut cend = jc + 32u32;
                    if cend > nt {
                        cend = nt;
                    }
                    let mut pm = Array::<u32>::new(ept as usize);
                    #[unroll]
                    for j in 0..ept {
                        pm[j as usize] = 0u32;
                    }
                    let mut jt = jc;
                    let mut bit = 1u32;
                    while jt < cend {
                        let tlo = t_lo[jt as usize];
                        let thi = t_hi[jt as usize];
                        #[unroll]
                        for j in 0..ept {
                            let z = (mlo[j as usize] & tlo) | (mhi[j as usize] & thi);
                            pm[j as usize] |= select(z == 0u32, bit, 0u32);
                        }
                        bit <<= 1u32;
                        jt += 1u32;
                    }
                    if comptime!(exp == 2) {
                        #[unroll]
                        for j in 0..ept {
                            xcount += pm[j as usize].count_ones();
                            pm[j as usize] = 0u32;
                        }
                    }
                    #[unroll]
                    for j in 0..ept {
                        let mut x = pm[j as usize] & vv[j as usize];
                        let r0 = rr[j as usize];
                        while x != 0u32 {
                            let jt2 = jc + x.trailing_zeros();
                            x &= x - 1u32;
                            if r0 >= t_rlo[jt2 as usize] && r0 < t_rhi[jt2 as usize] {
                                let at = s_cnt[0].fetch_add(1u32);
                                if at < SURV_SH_CAP {
                                    s_t[at as usize] = t_id[jt2 as usize];
                                    s_r[at as usize] = r0;
                                } else {
                                    let g = surv_count[0].fetch_add(1u32);
                                    if g < surv_cap {
                                        surv[(2u32 * g) as usize] = t_id[jt2 as usize];
                                        surv[(2u32 * g + 1u32) as usize] = r0;
                                    }
                                }
                            }
                        }
                    }
                    jc += 32u32;
                }
                sync_cube();
                let sc = s_cnt[0].load();
                if sc >= SURV_FLUSH {
                    flush_survivors(
                        &s_t, &s_r, &mut s_cnt, &mut s_base, surv, surv_count, surv_cap, sc,
                    );
                    sync_cube();
                }
                ws += wave;
            }
            tc += TOP_CAP;
            sync_cube();
        }
        w += CUBE_COUNT_X;
    }
    sync_cube();
    let sc = s_cnt[0].load();
    if sc > 0u32 {
        flush_survivors(
            &s_t, &s_r, &mut s_cnt, &mut s_base, surv, surv_count, surv_cap, sc,
        );
    }
    if comptime!(exp >= 2) {
        if xcount > 0u32 {
            surv_count[0].fetch_add(xcount);
        }
    }
}

// ---------------------------------------------------------------------------
// Device-side top certification (optional stage 0; JOIN_DEVTOPS=1)
// ---------------------------------------------------------------------------

/// One power's share of the top certificate, the device form of
/// `Base::cert`'s inner loop: x and y are the power of the interval's two
/// endpoints (`nl` u32 limbs, destroyed), `sp` its digit count. Positions
/// >= c0 = max(cap, ndig(y - x)) are scanned least significant first in
/// lockstep; a position where the digits differ resets the run, so what
/// is left at the top is exactly the digits `cert` certifies (from the top
/// down to the first disagreement), with `dup` set if two of them repeat.
/// Returns the run mask; `c0` and `dup` via the out-arrays.
#[cube]
fn cert_power(
    x: &mut Array<u32>,
    y: &mut Array<u32>,
    pw: &Array<u32>,
    out_c0: &mut Array<u32>,
    out_dup: &mut Array<u32>,
    #[comptime] nl: u32,
    #[comptime] nl3: u32,
    #[comptime] sp: u32,
    #[comptime] cap: u32,
    #[comptime] base: u32,
    #[comptime] chunk_digits: u32,
    #[comptime] chunk_div: u32,
) -> u64 {
    // d = y - x (y >= x)
    let mut d = Array::<u32>::new(nl as usize);
    let mut borrow = 0u32;
    #[unroll]
    for j in 0..nl {
        let yj = y[j as usize];
        let xj = x[j as usize];
        let t = yj - xj - borrow;
        let mut nb = 0u32;
        if yj < xj || (yj == xj && borrow != 0u32) {
            nb = 1u32;
        }
        d[j as usize] = t;
        borrow = nb;
    }
    // ndig(d): smallest i with b^i > d, binary search over the power table.
    let mut lo = 0u32;
    let mut hi = sp.runtime();
    while lo < hi {
        let mid = (lo + hi) >> 1u32;
        // d < b^mid ?
        let mut lt = false;
        let mut eq = true;
        #[unroll]
        for jj in 0..nl3 {
            let j = comptime!(nl3 - 1 - jj);
            let pj = pw[(mid * nl3 + j) as usize];
            let mut dj = 0u32;
            if comptime!(j < nl) {
                dj = d[j as usize];
            }
            if eq {
                if dj < pj {
                    lt = true;
                    eq = false;
                } else if dj > pj {
                    eq = false;
                }
            }
        }
        if lt {
            hi = mid;
        } else {
            lo = mid + 1u32;
        }
    }
    let mut c0 = lo;
    if c0 < cap {
        c0 = cap.runtime();
    }
    let mut run = 0u64;
    let mut dup = 0u32;
    let passes = comptime!((sp + chunk_digits - 1) / chunk_digits);
    #[unroll]
    for pass in 0..passes {
        let mut rx = 0u32;
        let mut ry = 0u32;
        #[unroll]
        for jj in 0..nl {
            let j = comptime!(nl - 1 - jj);
            let vx = x[j as usize];
            let c1 = (rx << 16u32) | (vx >> 16u32);
            let q1 = c1 / chunk_div;
            let r1 = c1 - q1 * chunk_div;
            let c2 = (r1 << 16u32) | (vx & 0xFFFFu32);
            let q2 = c2 / chunk_div;
            rx = c2 - q2 * chunk_div;
            x[j as usize] = (q1 << 16u32) | q2;
            let vy = y[j as usize];
            let e1 = (ry << 16u32) | (vy >> 16u32);
            let s1 = e1 / chunk_div;
            let t1 = e1 - s1 * chunk_div;
            let e2 = (t1 << 16u32) | (vy & 0xFFFFu32);
            let s2 = e2 / chunk_div;
            ry = e2 - s2 * chunk_div;
            y[j as usize] = (s1 << 16u32) | s2;
        }
        #[unroll]
        for q in 0..chunk_digits {
            let pos = comptime!(pass * chunk_digits + q);
            let dx = rx % base;
            rx /= base;
            let dy = ry % base;
            ry /= base;
            if comptime!(pos < sp) {
                if pos >= c0 {
                    if dx != dy {
                        run = 0u64;
                        dup = 0u32;
                    } else {
                        let bit = 1u64 << u64::cast_from(dx);
                        if (run & bit) != 0u64 {
                            dup = 1u32;
                        }
                        run |= bit;
                    }
                }
            }
        }
    }
    out_c0[0] = c0;
    out_dup[0] = dup;
    run
}

/// Stage 0a: certify every top prefix of every slot's partition. Grid: x
/// over the field's top layer (depth t - pp, host-built once per field),
/// y over slots. Per tlay entry (5 words): P0 lo, hi, P0 mod (b-1),
/// P0 mod b, P0 mod b^(k2-f0-pp). `fb` = s (3 limbs), e-1 (3 limbs), the P
/// range lo (2 words) and hi (2 words). Passing tops are appended per slot
/// (stride `ntlay`) and counted into their buckets, one per digit-sum root.
#[cube(launch_unchecked)]
pub fn top_kernel(
    tlay: &Array<u32>,
    vs: &Array<u32>,
    fb: &Array<u32>,
    pw: &Array<u32>,
    roots: &Array<u32>,
    top_p: &mut Array<u32>,
    top_m: &mut Array<u32>,
    top_r: &mut Array<u32>,
    top_x: &mut Array<u32>,
    top_b: &mut Array<u32>,
    top_count: &mut Array<Atomic<u32>>,
    bucket_cnt: &mut Array<Atomic<u32>>,
    ntlay: u32,
    nroots: u32,
    w: u32,
    pdiv: u32,
    pdiv_m1: u32,
    full_floor: u32, // certificate floor bound of every unclipped block (host rule)
    #[comptime] base: u32,
    #[comptime] limbs: u32,
    #[comptime] cap: u32,
    #[comptime] k2: u32,
    #[comptime] s2: u32,
    #[comptime] s3: u32,
    #[comptime] chunk_digits: u32,
    #[comptime] chunk_div: u32,
    #[comptime] key_level: bool,
    #[comptime] nb: u32,
) {
    let m1 = comptime!(base - 1);
    let nl2 = comptime!(2 * limbs);
    let nl3 = comptime!(3 * limbs);
    let i = ABSOLUTE_POS_X;
    let slot = CUBE_POS_Y;
    if i < ntlay {
        let p0 = (u64::cast_from(tlay[(5u32 * i + 1u32) as usize]) << 32u64) | u64::cast_from(tlay[(5u32 * i) as usize]);
        let v = vs[slot as usize];
        let p = p0 * u64::cast_from(pdiv) + u64::cast_from(v);
        let plo = (u64::cast_from(fb[7]) << 32u64) | u64::cast_from(fb[6]);
        let phi = (u64::cast_from(fb[9]) << 32u64) | u64::cast_from(fb[8]);
        if p >= plo && p <= phi {
            // a = p*w (< 2^96, 3 limbs), e = a + w - 1, clipped to [s, e-1].
            let t0 = (p & 0xFFFF_FFFFu64) * u64::cast_from(w);
            let t1 = (p >> 32u64) * u64::cast_from(w) + (t0 >> 32u64);
            let pw0 = u32::cast_from(t0);
            let mut a = Array::<u32>::new(limbs as usize);
            let mut e = Array::<u32>::new(limbs as usize);
            #[unroll]
            for j in 0..limbs {
                if comptime!(j == 0) {
                    a[j as usize] = pw0;
                } else if comptime!(j == 1) {
                    a[j as usize] = u32::cast_from(t1);
                } else if comptime!(j == 2) {
                    a[j as usize] = u32::cast_from(t1 >> 32u64);
                } else {
                    a[j as usize] = 0u32;
                }
            }
            let mut carry = w - 1u32;
            #[unroll]
            for j in 0..limbs {
                let t = a[j as usize] + carry;
                let mut c = 0u32;
                if t < carry {
                    c = 1u32;
                }
                e[j as usize] = t;
                carry = c;
            }
            // a = max(a, s); e = min(e, e_incl) (limbs <= 3: fb words 0..2, 3..5)
            let mut a_lt_s = false;
            let mut e_gt_e = false;
            let mut eq_a = true;
            let mut eq_e = true;
            #[unroll]
            for jj in 0..limbs {
                let j = comptime!(limbs - 1 - jj);
                let sj = fb[j as usize];
                let ej = fb[comptime!(3 + j) as usize];
                if eq_a {
                    if a[j as usize] < sj {
                        a_lt_s = true;
                        eq_a = false;
                    } else if a[j as usize] > sj {
                        eq_a = false;
                    }
                }
                if eq_e {
                    if e[j as usize] > ej {
                        e_gt_e = true;
                        eq_e = false;
                    } else if e[j as usize] < ej {
                        eq_e = false;
                    }
                }
            }
            if a_lt_s {
                #[unroll]
                for j in 0..limbs {
                    a[j as usize] = fb[j as usize];
                }
            }
            if e_gt_e {
                #[unroll]
                for j in 0..limbs {
                    e[j as usize] = fb[comptime!(3 + j) as usize];
                }
            }
            // Powers: a2 = a^2, e2 = e^2 (2L limbs), a3, e3 (3L limbs).
            let mut a2 = Array::<u32>::new(nl2 as usize);
            let mut e2 = Array::<u32>::new(nl2 as usize);
            #[unroll]
            for j in 0..nl2 {
                a2[j as usize] = 0u32;
                e2[j as usize] = 0u32;
            }
            #[unroll]
            for i1 in 0..limbs {
                let mut ca = 0u64;
                let mut ce = 0u64;
                #[unroll]
                for j in 0..limbs {
                    let kk = comptime!(i1 + j);
                    let ta = u64::cast_from(a[i1 as usize]) * u64::cast_from(a[j as usize]) + u64::cast_from(a2[kk as usize]) + ca;
                    a2[kk as usize] = u32::cast_from(ta);
                    ca = ta >> 32u64;
                    let te = u64::cast_from(e[i1 as usize]) * u64::cast_from(e[j as usize]) + u64::cast_from(e2[kk as usize]) + ce;
                    e2[kk as usize] = u32::cast_from(te);
                    ce = te >> 32u64;
                }
                a2[comptime!(i1 + limbs) as usize] = u32::cast_from(ca);
                e2[comptime!(i1 + limbs) as usize] = u32::cast_from(ce);
            }
            let mut a3 = Array::<u32>::new(nl3 as usize);
            let mut e3 = Array::<u32>::new(nl3 as usize);
            #[unroll]
            for j in 0..nl3 {
                a3[j as usize] = 0u32;
                e3[j as usize] = 0u32;
            }
            #[unroll]
            for i1 in 0..nl2 {
                let mut ca = 0u64;
                let mut ce = 0u64;
                #[unroll]
                for j in 0..limbs {
                    let kk = comptime!(i1 + j);
                    let ta = u64::cast_from(a2[i1 as usize]) * u64::cast_from(a[j as usize]) + u64::cast_from(a3[kk as usize]) + ca;
                    a3[kk as usize] = u32::cast_from(ta);
                    ca = ta >> 32u64;
                    let te = u64::cast_from(e2[i1 as usize]) * u64::cast_from(e[j as usize]) + u64::cast_from(e3[kk as usize]) + ce;
                    e3[kk as usize] = u32::cast_from(te);
                    ce = te >> 32u64;
                }
                a3[comptime!(i1 + limbs) as usize] = u32::cast_from(ca);
                e3[comptime!(i1 + limbs) as usize] = u32::cast_from(ce);
            }
            let mut c0a = Array::<u32>::new(1usize);
            let mut dupa = Array::<u32>::new(1usize);
            let mut c0b = Array::<u32>::new(1usize);
            let mut dupb = Array::<u32>::new(1usize);
            let msq = cert_power(&mut a2, &mut e2, pw, &mut c0a, &mut dupa, nl2, nl3, s2, cap, base, chunk_digits, chunk_div);
            let mcu = cert_power(&mut a3, &mut e3, pw, &mut c0b, &mut dupb, nl3, nl3, s3, cap, base, chunk_digits, chunk_div);
            if dupa[0] == 0u32 && dupb[0] == 0u32 && (msq & mcu) == 0u64 {
                let mask = msq | mcu;
                let mut floor = c0a[0];
                if c0b[0] < floor {
                    floor = c0b[0];
                }
                // Same seed rule as the host: an unclipped block uses the
                // field bound (a lower bound of its exact floor).
                if !a_lt_s && !e_gt_e {
                    floor = full_floor;
                }
                let idx = top_count[slot as usize].fetch_add(1u32);
                let g = slot * ntlay + idx;
                top_p[(2u32 * g) as usize] = u32::cast_from(p);
                top_p[(2u32 * g + 1u32) as usize] = u32::cast_from(p >> 32u64);
                top_m[(2u32 * g) as usize] = u32::cast_from(mask);
                top_m[(2u32 * g + 1u32) as usize] = u32::cast_from(mask >> 32u64);
                top_r[(2u32 * g) as usize] = a[0] - pw0;
                top_r[(2u32 * g + 1u32) as usize] = e[0] - pw0 + 1u32;
                let pmod = tlay[(5u32 * i + 4u32) as usize] * pdiv + v;
                top_x[(2u32 * g) as usize] = pmod;
                let mut seed = 0u32;
                if floor >= k2 {
                    seed = 1u32;
                }
                top_x[(2u32 * g + 1u32) as usize] = seed;
                let pc = (tlay[(5u32 * i + 2u32) as usize] * pdiv_m1 + v) % m1;
                let mut key = 0u32;
                if key_level {
                    key = tlay[(5u32 * i + 3u32) as usize];
                }
                top_b[g as usize] = pc | (key << 8u32);
                let mut r = 0u32;
                while r < nroots {
                    let cls = (roots[r as usize] + m1 - pc) % m1;
                    bucket_cnt[(slot * nb + key * m1 + cls) as usize].fetch_add(1u32);
                    r += 1u32;
                }
            }
        }
    }
}

/// Stage 0b: per slot (one cube), exclusive scan of the bucket counts into
/// offsets and fill cursors; writes every (slot, bucket) work item.
#[cube(launch_unchecked)]
pub fn top_scan_kernel(
    bucket_cnt: &Array<Atomic<u32>>,
    cursor: &mut Array<Atomic<u32>>,
    work: &mut Array<u32>,
    tl_stride: u32,
    #[comptime] nb: u32,
) {
    let per = comptime!((nb + JOIN_WG - 1) / JOIN_WG);
    let mut tot = SharedMemory::<u32>::new(comptime!(JOIN_WG as usize));
    let slot = CUBE_POS_X;
    let first = UNIT_POS_X * per;
    let mut acc = 0u32;
    #[unroll]
    for q in 0..per {
        let bx = first + q;
        if bx < nb {
            acc += bucket_cnt[(slot * nb + bx) as usize].load();
        }
    }
    tot[UNIT_POS_X as usize] = acc;
    sync_cube();
    if UNIT_POS_X == 0u32 {
        let mut run = 0u32;
        let mut t = 0u32;
        while t < CUBE_DIM_X {
            let c = tot[t as usize];
            tot[t as usize] = run;
            run += c;
            t += 1u32;
        }
    }
    sync_cube();
    let mut off = tot[UNIT_POS_X as usize] + slot * tl_stride;
    #[unroll]
    for q in 0..per {
        let bx = first + q;
        if bx < nb {
            let c = bucket_cnt[(slot * nb + bx) as usize].load();
            cursor[(slot * nb + bx) as usize].store(off);
            let wi = slot * nb + bx;
            work[(4u32 * wi) as usize] = slot;
            work[(4u32 * wi + 1u32) as usize] = bx;
            work[(4u32 * wi + 2u32) as usize] = off;
            work[(4u32 * wi + 3u32) as usize] = off + c;
            off += c;
        }
    }
}

/// Stage 0c: every certified top onto the list of each bucket it probes.
#[cube(launch_unchecked)]
pub fn top_fill_kernel(
    top_b: &Array<u32>,
    top_count: &Array<Atomic<u32>>,
    roots: &Array<u32>,
    cursor: &mut Array<Atomic<u32>>,
    tl: &mut Array<u32>,
    ntlay: u32,
    nroots: u32,
    #[comptime] base: u32,
    #[comptime] nb: u32,
) {
    let m1 = comptime!(base - 1);
    let i = ABSOLUTE_POS_X;
    let slot = CUBE_POS_Y;
    if i < top_count[slot as usize].load() {
        let g = slot * ntlay + i;
        let b = top_b[g as usize];
        let pc = b & 255u32;
        let key = b >> 8u32;
        let mut r = 0u32;
        while r < nroots {
            let cls = (roots[r as usize] + m1 - pc) % m1;
            let at = cursor[(slot * nb + key * m1 + cls) as usize].fetch_add(1u32);
            tl[at as usize] = g;
            r += 1u32;
        }
    }
}

/// Step 3 (optional): middle-digit prefilter with compaction. See the module
/// docs. Soundness: every digit tested is a real digit of n^2 or n^3 at a
/// distinct position (the host guarantees both powers have >= k2 digits), and
/// seed digits sit at positions >= k2, so any repeat proves n is not nice.
#[cube(launch_unchecked)]
pub fn mid_kernel(
    surv: &Array<u32>,
    surv_count: &mut Array<Atomic<u32>>,
    top_m: &Array<u32>, // lo, hi certificate words per top
    top_x: &Array<u32>, // P mod b^(k2-f0), seed flag per top
    out: &mut Array<u32>,
    out_count: &mut Array<Atomic<u32>>,
    surv_cap: u32,
    out_cap: u32,
    #[comptime] base: u32,
    #[comptime] f0: u32,
    #[comptime] k2: u32,
) {
    let mut plane_tot = SharedMemory::<u32>::new(comptime!(JOIN_WG as usize));
    let mut s_base = SharedMemory::<u32>::new(1usize);
    let my_plane = UNIT_POS_X / PLANE_DIM;
    let num_planes = CUBE_DIM_X / PLANE_DIM;
    let mut count = surv_count[0].load();
    if count > surv_cap {
        count = surv_cap;
    }
    let mut rb = CUBE_POS_X * CUBE_DIM_X;
    let rstride = CUBE_COUNT_X * CUBE_DIM_X;
    while rb < count {
        let i = rb + UNIT_POS_X;
        let mut pass = 0u32;
        let mut t = 0u32;
        let mut r0 = 0u32;
        if i < count {
            t = surv[(2u32 * i) as usize];
            r0 = surv[(2u32 * i + 1u32) as usize];
            let pm = top_x[(2u32 * t) as usize];
            let mut m = 0u64;
            if top_x[(2u32 * t + 1u32) as usize] != 0u32 {
                m = (u64::cast_from(top_m[(2u32 * t + 1u32) as usize]) << 32u64)
                    | u64::cast_from(top_m[(2u32 * t) as usize]);
            }
            let mut d = Array::<u32>::new(k2 as usize);
            let mut x = r0;
            #[unroll]
            for j in 0..f0 {
                d[j as usize] = x % base;
                x /= base;
            }
            let mut y = pm;
            #[unroll]
            for j in f0..k2 {
                d[j as usize] = y % base;
                y /= base;
            }
            let mut sq = Array::<u32>::new(k2 as usize);
            let mut carry = 0u32;
            #[unroll]
            for pos in 0..k2 {
                let mut col = carry;
                #[unroll]
                for i2 in 0..comptime!(pos + 1) {
                    col += d[i2 as usize] * d[comptime!(pos - i2) as usize];
                }
                sq[pos as usize] = col % base;
                carry = col / base;
            }
            let mut ok = true;
            carry = 0u32;
            #[unroll]
            for pos in 0..k2 {
                let mut col = carry;
                #[unroll]
                for i2 in 0..comptime!(pos + 1) {
                    col += sq[i2 as usize] * d[comptime!(pos - i2) as usize];
                }
                let g3 = col % base;
                carry = col / base;
                let g2 = sq[pos as usize];
                let bb = (1u64 << u64::cast_from(g2)) | (1u64 << u64::cast_from(g3));
                if g2 == g3 || (m & bb) != 0u64 {
                    ok = false;
                }
                m |= bb;
            }
            if ok {
                pass = 1u32;
            }
        }
        let idx = plane_exclusive_sum(pass);
        let tot = plane_sum(pass);
        if UNIT_POS_PLANE == 0u32 {
            plane_tot[my_plane as usize] = tot;
        }
        sync_cube();
        let mut off = 0u32;
        let mut all = 0u32;
        let mut p = 0u32;
        while p < num_planes {
            let tp = plane_tot[p as usize];
            if p < my_plane {
                off += tp;
            }
            all += tp;
            p += 1u32;
        }
        if UNIT_POS_X == 0u32 && all > 0u32 {
            s_base[0] = out_count[0].fetch_add(all);
        }
        sync_cube();
        if pass != 0u32 {
            let g = s_base[0] + off + idx;
            if g < out_cap {
                out[(2u32 * g) as usize] = t;
                out[(2u32 * g + 1u32) as usize] = r0;
            }
        }
        rb += rstride;
    }
}

/// Step 4: grid-stride over the survivor list; rebuild n = P*b^f0 + r0 and
/// run the client's full check (probe: report every n instead).
#[cube(launch_unchecked)]
pub fn check_kernel(
    surv: &Array<u32>,
    surv_count: &mut Array<Atomic<u32>>,
    top_p: &Array<u32>, // lo, hi words of P per top
    nice_out: &mut Array<u32>,
    nice_count: &mut Array<Atomic<u32>>,
    surv_cap: u32,
    nice_cap: u32,
    w_f0: u32, // b^f0
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
    let cu_limbs = comptime!(3 * limbs);
    let sv_pad = comptime!(cu_limbs | 1);
    let mut sv_s = SharedMemory::<u32>::new(comptime!((JOIN_WG * (cu_limbs | 1)) as usize));
    let svb = UNIT_POS_X * sv_pad;
    let mut count = surv_count[0].load();
    if count > surv_cap {
        count = surv_cap;
    }
    let stride = CUBE_COUNT_X * CUBE_DIM_X;
    let mut i = ABSOLUTE_POS_X;
    while i < count {
        let t = surv[(2u32 * i) as usize];
        let r0 = surv[(2u32 * i + 1u32) as usize];
        let p_lo = u64::cast_from(top_p[(2u32 * t) as usize]);
        let p_hi = u64::cast_from(top_p[(2u32 * t + 1u32) as usize]);
        let wf = u64::cast_from(w_f0);
        // n = (p_hi 2^32 + p_lo) * w + r0 over (lo, hi) u64 halves.
        let a = p_lo * wf;
        let bq = p_hi * wf;
        let lo1 = a + (bq << 32u64);
        let mut hi = bq >> 32u64;
        if lo1 < a {
            hi += 1u64;
        }
        let lo = lo1 + u64::cast_from(r0);
        if lo < lo1 {
            hi += 1u64;
        }
        candidate_check(
            lo,
            hi,
            &mut sv_s,
            svb,
            nice_out,
            nice_count,
            nice_cap,
            base,
            limbs,
            chunk_digits,
            chunk_div,
            wide_chunk,
            pre_limbs,
            pre_chunk_digits,
            pre_chunk_div,
            probe,
        );
        i += stride;
    }
}
