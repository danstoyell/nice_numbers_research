//! CPU prototype of the overlap join behind the public client's chunk
//! interface: a contiguous range of n in, nice numbers out (niceonly, K = 1,
//! bases up to 64, n < 2^128, n^3 < 2^256).
//!
//! For a range [s, e) of L-digit numbers and parameters (t, k, p):
//! * top list: prefixes P of the top t digits of n that meet [s, e). A
//!   prefix is kept if the output digits of n^2 and n^3 at positions >= k
//!   that are constant on its interval (clipped to [s, e)) are distinct.
//!   Built breadth-first to depth t - p once per range ("Tlay"), then
//!   extended by p digits per partition.
//! * bottom list: residues R = n mod b^k whose low k digits of n^2 and n^3
//!   (positions 0..k-1) are distinct, enumerated depth-first from the digit
//!   0 upward; the prefix of depth f0 = L - t ("Bpre") is shared.
//! * the two lists share o = t + k - L digits of n (positions f0..k-1). The
//!   lowest p of them are the partition value v (both lists are built per v,
//!   so memory is |T|/b^p + |B|/b^p); the other o - p are the hash key,
//!   together with the digit-sum class R_low mod (b-1), R_low = R mod b^f0,
//!   since n = P*b^f0 + R_low == P + R_low (mod b-1) must be a digit-sum root.
//! * each key-equal pair is a match: one AND of the two certified-digit
//!   masks (the positions are disjoint by the cap); pairs that pass and lie
//!   in [s, e) are fully checked with the client's own get_is_nice.
//! Soundness: a nice n has distinct digits in every subset of positions, so
//! its prefix is kept, its residue is kept, its class is a root, and its
//! (P, R) pair passes the AND; every n in [s, e) is exactly one pair.
use nice_common::client_process::get_is_nice;

#[derive(Clone, Copy, Default, Debug, PartialEq, Eq)]
pub struct W4(pub [u64; 4]);

impl W4 {
    #[inline]
    pub fn mul_u128_u128(a: u128, b: u128) -> Self {
        let (a0, a1, b0, b1) = (a as u64 as u128, a >> 64, b as u64 as u128, b >> 64);
        let p00 = a0 * b0;
        let p01 = a0 * b1;
        let p10 = a1 * b0;
        let p11 = a1 * b1;
        let mid = (p00 >> 64) + (p01 as u64 as u128) + (p10 as u64 as u128);
        let hi = (mid >> 64) + (p01 >> 64) + (p10 >> 64) + (p11 as u64 as u128);
        W4([p00 as u64, mid as u64, hi as u64, ((hi >> 64) + (p11 >> 64)) as u64])
    }
    #[inline]
    pub fn mul_u128(&self, b: u128) -> Self {
        let (b0, b1) = (b as u64 as u128, b >> 64);
        let mut r = [0u64; 4];
        let mut c: u128 = 0;
        for i in 0..4 {
            c += self.0[i] as u128 * b0 + r[i] as u128;
            r[i] = c as u64;
            c >>= 64;
        }
        c = 0;
        for i in 0..3 {
            c += self.0[i] as u128 * b1 + r[i + 1] as u128;
            r[i + 1] = c as u64;
            c >>= 64;
        }
        W4(r)
    }
    #[inline]
    pub fn sub(&self, o: &W4) -> W4 {
        let mut r = [0u64; 4];
        let mut borrow = 0u64;
        for i in 0..4 {
            let (d1, b1) = self.0[i].overflowing_sub(o.0[i]);
            let (d2, b2) = d1.overflowing_sub(borrow);
            r[i] = d2;
            borrow = (b1 | b2) as u64;
        }
        W4(r)
    }
    #[inline]
    pub fn lt(&self, o: &W4) -> bool {
        for i in (0..4).rev() {
            if self.0[i] != o.0[i] {
                return self.0[i] < o.0[i];
            }
        }
        false
    }
    #[inline]
    pub fn divrem_u64(&mut self, d: u64) -> u64 {
        let mut r: u128 = 0;
        let mut i = 4;
        while i > 0 && self.0[i - 1] == 0 {
            i -= 1;
        }
        while i > 0 {
            i -= 1;
            let cur = (r << 64) | self.0[i] as u128;
            self.0[i] = (cur / d as u128) as u64;
            r = cur % d as u128;
        }
        r as u64
    }
    #[inline]
    pub fn to_u128(&self) -> u128 {
        debug_assert!(self.0[2] == 0 && self.0[3] == 0);
        (self.0[1] as u128) << 64 | self.0[0] as u128
    }
}

/// Division by an invariant 64-bit divisor with a precomputed reciprocal
/// (N. Moller and T. Granlund, "Improved division by invariant integers",
/// IEEE Trans. Computers 60 (2011), Algorithm 4), replacing __udivti3.
#[derive(Clone, Copy, Debug)]
pub struct Div64 {
    d: u64,
    dn: u64,
    shift: u32,
    v: u64,
}

impl Div64 {
    pub fn new(d: u64) -> Self {
        let shift = d.leading_zeros();
        let dn = d << shift;
        let v = (u128::MAX / dn as u128 - (1u128 << 64)) as u64;
        Div64 { d, dn, shift, v }
    }
    /// (u1:u0) / dn with u1 < dn -> (q, r)
    #[inline(always)]
    fn div2by1(&self, u1: u64, u0: u64) -> (u64, u64) {
        let q = (self.v as u128 * u1 as u128).wrapping_add((u1 as u128) << 64 | u0 as u128);
        let mut q1 = ((q >> 64) as u64).wrapping_add(1);
        let q0 = q as u64;
        let mut r = u0.wrapping_sub(q1.wrapping_mul(self.dn));
        if r > q0 {
            q1 = q1.wrapping_sub(1);
            r = r.wrapping_add(self.dn);
        }
        if r >= self.dn {
            q1 += 1;
            r -= self.dn;
        }
        (q1, r)
    }
    /// x /= d in place, returns x mod d.
    #[inline]
    pub fn divrem_w4(&self, x: &mut W4) -> u64 {
        let mut i = 4;
        while i > 0 && x.0[i - 1] == 0 {
            i -= 1;
        }
        if i == 0 {
            return 0;
        }
        let sh = self.shift;
        // normalized dividend limbs, most significant first
        let mut r: u64 = if sh == 0 { 0 } else { x.0[i - 1] >> (64 - sh) };
        while i > 0 {
            i -= 1;
            let lo = if sh == 0 { x.0[i] } else { (x.0[i] << sh) | if i > 0 { x.0[i - 1] >> (64 - sh) } else { 0 } };
            let (q, rr) = self.div2by1(r, lo);
            x.0[i] = q;
            r = rr;
        }
        r >> sh
    }
    #[inline]
    pub fn divrem_u128(&self, x: u128) -> (u128, u64) {
        let mut w = W4([x as u64, (x >> 64) as u64, 0, 0]);
        let r = self.divrem_w4(&mut w);
        (w.to_u128(), r)
    }
    pub fn divisor(&self) -> u64 {
        self.d
    }
}

#[derive(Default, Clone, Debug)]
pub struct Counters {
    pub top_calls: u64,
    pub tlay_calls: u64,
    pub bpre_calls: u64,
    pub tlay: u64,
    pub tops: u64,
    pub bottom_calls: u64,
    pub bottoms: u64,
    pub lookups: u64,
    pub matches: u64,
    pub out_of_range: u64,
    pub survivors: u64,
    pub hits: Vec<u128>,
    pub partitions: u64,
    pub sec_tlay: f64,
    pub sec_bottom: f64,
    pub sec_top_ext: f64,
    pub sec_join: f64,
}

pub struct Base {
    pub b: u32,
    pub l: u32,
    pub s2: u32,
    pub s3: u32,
    pub m1: u32,
    pub roots: Vec<u32>,
    pow: Vec<u128>,
    poww: Vec<W4>,
    pow64: Vec<u64>,
    chd: u32,
    rch: u64,
    dpow: Vec<Div64>,
}

fn ndig_u128(mut x: u128, b: u32) -> u32 {
    let mut n = 0;
    while x > 0 {
        x /= b as u128;
        n += 1;
    }
    n
}

impl Base {
    /// `lo`..=`hi` must be numbers with the same digit count and the same
    /// square/cube digit counts (true inside any single field of a base).
    pub fn new(b: u32, lo: u128, hi: u128) -> Self {
        let l = ndig_u128(hi, b);
        assert_eq!(l, ndig_u128(lo, b), "range crosses a digit boundary");
        let m1 = b - 1;
        let tgt = (b as u64 * (b as u64 - 1) / 2) % m1 as u64;
        let roots = (0..m1).filter(|&r| {
            let r = r as u64;
            (r * r + r * r * r) % m1 as u64 == tgt
        }).collect();
        let mut pow = vec![1u128];
        while pow.len() < 40 {
            let last = *pow.last().unwrap();
            match last.checked_mul(b as u128) {
                Some(x) => pow.push(x),
                None => break,
            }
        }
        let mut poww = vec![W4([1, 0, 0, 0])];
        for _ in 0..60 {
            let last = *poww.last().unwrap();
            if last.0[3] >= (u64::MAX / b as u64) {
                break;
            }
            poww.push(last.mul_u128(b as u128));
        }
        let mut pow64 = vec![1u64];
        while let Some(x) = pow64.last().unwrap().checked_mul(b as u64) {
            pow64.push(x);
        }
        let chd = (pow64.len() - 1) as u32;
        let rch = pow64[chd as usize];
        let digits_w = |x: &W4| {
            let mut n = 0u32;
            while n + 1 < poww.len() as u32 && !x.lt(&poww[n as usize]) {
                n += 1;
            }
            n
        };
        let s2 = digits_w(&W4::mul_u128_u128(lo, lo));
        let s3 = digits_w(&W4::mul_u128_u128(lo, lo).mul_u128(lo));
        let hs2 = digits_w(&W4::mul_u128_u128(hi, hi));
        let hs3 = digits_w(&W4::mul_u128_u128(hi, hi).mul_u128(hi));
        assert!(s2 == hs2 && s3 == hs3, "range crosses a square/cube length boundary");
        let dpow = pow64.iter().map(|&x| Div64::new(x)).collect();
        Base { b, l, s2, s3, m1, roots, pow, poww, pow64, chd, rch, dpow }
    }

    #[inline]
    fn ndig_w(&self, x: &W4) -> u32 {
        // smallest i with b^i > x
        let (mut lo, mut hi) = (0usize, self.poww.len() - 1);
        while lo < hi {
            let mid = (lo + hi) / 2;
            if x.lt(&self.poww[mid]) {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        lo as u32
    }

    /// floor(x / b^c).
    #[inline]
    fn shift_down(&self, mut x: W4, mut c: u32) -> W4 {
        while c >= self.chd {
            self.dpow[self.chd as usize].divrem_w4(&mut x);
            c -= self.chd;
        }
        if c > 0 {
            self.dpow[c as usize].divrem_w4(&mut x);
        }
        x
    }

    /// Digits of x (LSD first), exactly `len` of them (x < b^len).
    #[inline]
    fn digits_w(&self, mut x: W4, len: u32, out: &mut [u8; 48]) {
        let b = self.b as u64;
        let mut n = 0usize;
        while x.0[2] != 0 || x.0[3] != 0 {
            let mut r = self.dpow[self.chd as usize].divrem_w4(&mut x);
            for _ in 0..self.chd {
                out[n] = (r % b) as u8;
                r /= b;
                n += 1;
            }
        }
        let mut q = x.to_u128();
        while q >> 64 != 0 {
            let (hi, r0) = self.dpow[self.chd as usize].divrem_u128(q);
            let mut r = r0;
            for _ in 0..self.chd {
                out[n] = (r % b) as u8;
                r /= b;
                n += 1;
            }
            q = hi;
        }
        let mut r = q as u64;
        while (n as u32) < len {
            out[n] = (r % b) as u8;
            r /= b;
            n += 1;
        }
    }

    /// Certified-digit mask of positions >= cap of n^2 and n^3 constant on
    /// [a, e]; None if two certified digits coincide.
    pub fn cert(&self, a: u128, e: u128, cap: u32) -> Option<u64> {
        let a2 = W4::mul_u128_u128(a, a);
        let e2 = W4::mul_u128_u128(e, e);
        let a3 = a2.mul_u128(a);
        let e3 = e2.mul_u128(e);
        let mut mask = 0u64;
        let mut dx = [0u8; 48];
        let mut dy = [0u8; 48];
        for (x, y, sp) in [(a2, e2, self.s2), (a3, e3, self.s3)] {
            let c0 = cap.max(self.ndig_w(&y.sub(&x)));
            if c0 >= sp {
                continue;
            }
            let len = sp - c0;
            let qx = self.shift_down(x, c0);
            let qy = self.shift_down(y, c0);
            self.digits_w(qx, len, &mut dx);
            self.digits_w(qy, len, &mut dy);
            for i in (0..len as usize).rev() {
                if dx[i] != dy[i] {
                    break;
                }
                let bit = 1u64 << dx[i];
                if mask & bit != 0 {
                    return None;
                }
                mask |= bit;
            }
        }
        Some(mask)
    }

    /// Top prefixes of depth `depth` meeting [s, e_incl] that pass, cap `cap`.
    pub fn top_layer(&self, s: u128, e_incl: u128, depth: u32, cap: u32, ctr: &mut Counters) -> Vec<(u128, u64)> {
        let b = self.b as u128;
        let mut level: Vec<(u128, u64)> = vec![(0, 0)];
        for j in 1..=depth {
            let w = self.pow[(self.l - j) as usize];
            let (plo, phi) = (s / w, e_incl / w);
            let mut next = Vec::new();
            for &(par, _) in &level {
                let first = (par * b).max(plo);
                let last = (par * b + b - 1).min(phi);
                let mut p = first;
                while p <= last {
                    ctr.top_calls += 1;
                    let a = (p * w).max(s);
                    let e = (p * w + w - 1).min(e_incl);
                    if let Some(m) = self.cert(a, e, cap) {
                        next.push((p, m));
                    }
                    p += 1;
                }
            }
            level = next;
        }
        level
    }

    /// Bottom residues from `node` (depth j) to depth k, positions
    /// [f0, f0+pp) forced to the digits of v.
    #[allow(clippy::too_many_arguments)]
    pub fn bot_dfs(&self, r: u128, mask: u64, j: u32, k: u32, f0: u32, pp: u32, v: u128, out: &mut Vec<(u64, u64)>, ctr: &mut Counters) {
        self.bot_dfs_keyed(r, mask, j, k, f0, pp, v, None, out, ctr)
    }

    /// As bot_dfs; with `needed`, digits at the key positions (>= f0+pp) are
    /// kept only if the partial key (positions f0+pp..=j) occurs among the
    /// partition's top prefixes: needed[i] marks the key values mod b^i.
    #[allow(clippy::too_many_arguments)]
    pub fn bot_dfs_keyed(&self, r: u128, mask: u64, j: u32, k: u32, f0: u32, pp: u32, v: u128, needed: Option<&[Vec<bool>]>, out: &mut Vec<(u64, u64)>, ctr: &mut Counters) {
        if j == k {
            out.push((r as u64, mask));
            return;
        }
        let b = self.b as u128;
        let (dlo, dhi) = if j >= f0 && j < f0 + pp {
            let d = (v / self.pow[(j - f0) as usize]) % b;
            (d, d)
        } else {
            (0, b - 1)
        };
        let (mut u2, mut u3, mut s2, mut s3) = (0u128, 0u128, 0u128, 0u128);
        if j > 0 {
            let r2 = r * r;
            let r3 = r2 * r;
            u2 = (r2 / self.pow[j as usize]) % b;
            u3 = (r3 / self.pow[j as usize]) % b;
            let r0 = r % b;
            s2 = 2 * r0 % b;
            s3 = 3 * (r0 * r0 % b) % b;
        }
        let pj = self.pow[j as usize];
        for d in dlo..=dhi {
            ctr.bottom_calls += 1;
            let (g2, g3) = if j == 0 { (d * d % b, d * d % b * d % b) } else { ((u2 + d * s2) % b, (u3 + d * s3) % b) };
            if g2 == g3 {
                continue;
            }
            let (m2, m3) = (1u64 << g2, 1u64 << g3);
            if mask & (m2 | m3) != 0 {
                continue;
            }
            let rn = r + d * pj;
            if let Some(nd) = needed {
                let kp = f0 + pp;
                if j >= kp {
                    let partial = (rn / self.pow[kp as usize]) as usize;
                    if !nd[(j - kp + 1) as usize][partial] {
                        continue;
                    }
                }
            }
            self.bot_dfs_keyed(rn, mask | m2 | m3, j + 1, k, f0, pp, v, needed, out, ctr);
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct JoinParams {
    pub t: u32,
    pub k: u32,
    pub p: u32,
}

/// The join over [s, e) restricted to the partition values in `parts`
/// (None = all b^p of them). Returns counters (hits included).
pub fn join_range(base: &Base, s: u128, e: u128, jp: JoinParams, parts: Option<&[u128]>, record: Option<&mut Vec<u128>>) -> Counters {
    let mut ctr = Counters::default();
    let mut record = record;
    let l = base.l;
    let (t, k, pp) = (jp.t, jp.k, jp.p);
    assert!(t + k > l && t <= l && k < l, "need t+k>L, t<=L, k<L (L={l})");
    let f0 = l - t;
    let o = t + k - l;
    assert!(pp <= o);
    assert!(base.pow.len() as u32 > 3 * k, "bottom arithmetic must fit u128");
    let e_incl = e - 1;
    let tt = std::time::Instant::now();
    let tlay = base.top_layer(s, e_incl, t - pp, k, &mut ctr);
    ctr.tlay = tlay.len() as u64;
    let mut bpre = Vec::new();
    ctr.tlay_calls = ctr.top_calls;
    base.bot_dfs(0, 0, 0, f0, f0, 0, 0, &mut bpre, &mut ctr);
    ctr.bpre_calls = ctr.bottom_calls;
    ctr.sec_tlay = tt.elapsed().as_secs_f64();
    let nv = base.pow[pp as usize];
    let all: Vec<u128>;
    let parts = match parts {
        Some(p) => p,
        None => {
            all = (0..nv).collect();
            &all
        }
    };
    let keyspace = base.pow[(o - pp) as usize] as usize;
    let m1 = base.m1 as usize;
    let nb = keyspace * m1;
    let mut off = vec![0u32; nb + 1];
    let mut bl: Vec<(u64, u64)> = Vec::new();
    let mut sorted: Vec<(u64, u64)> = Vec::new();
    let mut tops_v: Vec<(u128, u64)> = Vec::new();
    let mut needed: Vec<Vec<bool>> = (0..=(o - pp) as usize).map(|i| vec![false; base.pow[i] as usize]).collect();
    let kdiv = base.pow[(f0 + pp) as usize] as u64;
    let lowmod = base.pow[f0 as usize] as u64;
    let pdiv = base.pow[pp as usize];
    let w_t = base.pow[f0 as usize];
    let (plo, phi) = (s / w_t, e_incl / w_t);
    for &v in parts {
        ctr.partitions += 1;
        let t0 = std::time::Instant::now();
        // tops of this partition first: an empty partition costs nothing more
        tops_v.clear();
        for &(p0, _) in &tlay {
            let p = p0 * pdiv + v;
            if p < plo || p > phi {
                continue;
            }
            ctr.top_calls += 1;
            let a = (p * w_t).max(s);
            let ee = (p * w_t + w_t - 1).min(e_incl);
            if let Some(tmask) = base.cert(a, ee, k) {
                tops_v.push((p, tmask));
            }
        }
        let t1 = std::time::Instant::now();
        ctr.sec_top_ext += (t1 - t0).as_secs_f64();
        if tops_v.is_empty() {
            continue;
        }
        // partial keys the tops need (key digits = positions f0+pp..k-1)
        for i in 1..=(o - pp) as usize {
            needed[i].iter_mut().for_each(|x| *x = false);
        }
        for &(p, _) in &tops_v {
            let key = ((p / pdiv) % keyspace as u128) as usize;
            for i in 1..=(o - pp) as usize {
                needed[i][key % base.pow[i] as usize] = true;
            }
        }
        bl.clear();
        for &(r, m) in &bpre {
            base.bot_dfs_keyed(r as u128, m, f0, k, f0, pp, v, Some(&needed), &mut bl, &mut ctr);
        }
        ctr.bottoms += bl.len() as u64;
        off.iter_mut().for_each(|x| *x = 0);
        let bkt = |r: u64| ((r / kdiv) as usize) * m1 + ((r % lowmod) % m1 as u64) as usize;
        for &(r, _) in &bl {
            off[bkt(r) + 1] += 1;
        }
        for x in 0..nb {
            off[x + 1] += off[x];
        }
        sorted.resize(bl.len(), (0, 0));
        for &(r, m) in &bl {
            let kx = bkt(r);
            sorted[off[kx] as usize] = (r % lowmod, m);
            off[kx] += 1;
        }
        for x in (1..=nb).rev() {
            off[x] = off[x - 1];
        }
        off[0] = 0;
        let t2 = std::time::Instant::now();
        ctr.sec_bottom += (t2 - t1).as_secs_f64();
        ctr.tops += tops_v.len() as u64;
        for &(p, tmask) in &tops_v {
            let key = ((p / pdiv) % keyspace as u128) as usize;
            let pc = (p % m1 as u128) as usize;
            for &root in &base.roots {
                let cls = (root as usize + m1 - pc) % m1;
                let bx = key * m1 + cls;
                ctr.lookups += 1;
                for &(rl, bm) in &sorted[off[bx] as usize..off[bx + 1] as usize] {
                    ctr.matches += 1;
                    let n = p * w_t + rl as u128;
                    if n < s || n >= e {
                        ctr.out_of_range += 1;
                        continue;
                    }
                    if tmask & bm != 0 {
                        continue;
                    }
                    ctr.survivors += 1;
                    if let Some(rec) = record.as_deref_mut() {
                        rec.push(n);
                    }
                    if get_is_nice(n, base.b) {
                        ctr.hits.push(n);
                    }
                }
            }
        }
        ctr.sec_join += t2.elapsed().as_secs_f64();
    }
    ctr
}
