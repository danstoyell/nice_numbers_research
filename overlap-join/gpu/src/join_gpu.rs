//! Host side of the GPU overlap join: per-field setup (top layer, class-sorted
//! bpre list), per-partition top lists grouped into buckets (host, 256-bit
//! certification, as in the CPU prototype), batching of partitions into
//! device launches, and the continuous host/device pipeline.
#![allow(clippy::cast_possible_truncation, clippy::cast_precision_loss)]

use crate::join_kernels::{
    JOIN_WG, bottom_extend_kernel, bucket_kernel, check_kernel, join_kernel, join_kernel_v2, join_kernel_v3, mid_kernel,
    top_fill_kernel, top_kernel, top_scan_kernel,
};
use crate::proto::{Base, Counters, JoinParams};
use anyhow::{Result, bail, ensure};
use cubecl::prelude::*;
use cubecl::server::Handle;
use nice_common::cubecl_backend::NICEONLY_STRIDE;
use nice_common::gpu_config::{chunk_constants, chunk_constants_u16, n_limbs};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::mpsc::sync_channel;
use std::time::{Duration, Instant};

/// Per-stage wall time when `JOIN_PROFILE=1` (each stage synced), in
/// microseconds: pack, upload, extend, join, check, prefilter.
pub static PROFILE_US: [std::sync::atomic::AtomicU64; 12] = [
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
    std::sync::atomic::AtomicU64::new(0),
];
fn profiling() -> bool {
    static P: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *P.get_or_init(|| std::env::var("JOIN_PROFILE").is_ok_and(|v| v == "1"))
}
/// Unsynced host-side timing of dispatcher calls (`JOIN_PROFILE=2`):
/// slots 6.. = creates, launches, flush, fence.
fn host_mark(t: &mut Instant, slot: usize) {
    if std::env::var("JOIN_PROFILE").is_ok_and(|v| v == "2") {
        PROFILE_US[slot].fetch_add(t.elapsed().as_micros() as u64, Ordering::Relaxed);
        *t = Instant::now();
    }
}
fn prof_mark<R: Runtime>(client: &ComputeClient<R>, t: &mut Instant, slot: usize) {
    if profiling() {
        cubecl::future::block_on(client.sync()).expect("sync");
        PROFILE_US[slot].fetch_add(t.elapsed().as_micros() as u64, Ordering::Relaxed);
        *t = Instant::now();
    }
}

/// Everything about a field that does not depend on the partition.
pub struct FieldSetup {
    pub base: Base,
    pub b: u32,
    pub s: u128,
    pub e: u128,
    pub jp: JoinParams,
    pub l: u32,
    pub f0: u32,
    pub o: u32,
    pub key_level: bool,
    /// b^f0: the width of one top prefix block.
    pub w: u128,
    /// b^pp: partition values.
    pub nparts: u128,
    pub keyspace: u128,
    pub m1: u32,
    pub nb: usize,
    pub plo: u128,
    pub phi: u128,
    /// Top layer at depth t - pp, built once per field.
    pub tlay: Vec<(u128, u64)>,
    /// bpre: residues mod b^f0 with distinct low f0 digits of n^2 and n^3,
    /// sorted by digit-sum class r0 mod (b-1); `seg[c]..seg[c+1]` is class c.
    pub bp_r: Vec<u32>,
    pub bp_m: Vec<u64>,
    pub seg: Vec<u32>,
    pub setup_ctr: Counters,
    pub sec_tlay: f64,
    pub sec_bpre: f64,
    /// Middle-digit prefilter depth (0 = off) and k2 = k + mid.
    pub mid: u32,
    pub k2: u32,
    /// b^(k2 - f0): tops carry P mod this for the prefilter.
    pub pmod: u128,
    /// Certificate floor of every full-width block in the field (monotone in
    /// P, so the first full block bounds them all).
    pub full_floor: u32,
}

/// One partition's tops, grouped by bucket (host output, device input).
#[derive(Default)]
pub struct PartTops {
    pub v: u32,
    pub p: Vec<u64>,
    pub m: Vec<u64>,
    pub rlo: Vec<u32>,
    pub rhi: Vec<u32>,
    /// (bucket, start, end) into `tl`, non-empty buckets only.
    pub bkt: Vec<(u32, u32, u32)>,
    pub tl: Vec<u32>,
    /// P mod b^(k2-f0) and the seed flag, per top.
    pub x: Vec<u32>,
    pub calls: u64,
    pub secs: f64,
}

impl FieldSetup {
    /// # Errors
    /// Parameters outside what the device stage supports.
    pub fn new(b: u32, s: u128, e: u128, jp: JoinParams) -> Result<Self> {
        let base = Base::new(b, s, e - 1);
        let l = base.l;
        let (t, k, pp) = (jp.t, jp.k, jp.p);
        ensure!(t + k > l && t <= l && k < l, "need t+k>L, t<=L, k<L (L={l})");
        let f0 = l - t;
        let o = t + k - l;
        ensure!(pp <= o, "p > o");
        ensure!(o - pp <= 1, "device stage supports at most one key digit (o-p = {})", o - pp);
        ensure!(b <= 64, "u64 digit masks: base <= 64");
        ensure!(u64::from(b).pow(k) < 1 << 40, "b^k too large");
        let w = base.powu(f0);
        ensure!(w < 1 << 32, "b^f0 must fit u32");
        let mut ctr = Counters::default();
        let t0 = Instant::now();
        let tlay = base.top_layer(s, e - 1, t - pp, k, &mut ctr);
        let sec_tlay = t0.elapsed().as_secs_f64();
        let t1 = Instant::now();
        let mut bpre: Vec<(u64, u64)> = Vec::new();
        base.bot_dfs(0, 0, 0, f0, f0, 0, 0, &mut bpre, &mut ctr);
        let m1 = b - 1;
        bpre.sort_unstable_by_key(|&(r, _)| (r % u64::from(m1), r));
        let mut seg = vec![0u32; m1 as usize + 1];
        for &(r, _) in &bpre {
            seg[(r % u64::from(m1)) as usize + 1] += 1;
        }
        for c in 0..m1 as usize {
            seg[c + 1] += seg[c];
        }
        let bp_r = bpre.iter().map(|&(r, _)| r as u32).collect();
        let bp_m = bpre.iter().map(|&(_, m)| m).collect();
        let sec_bpre = t1.elapsed().as_secs_f64();
        let keyspace = base.powu(o - pp);
        // Middle-digit prefilter: JOIN_MID digits above k (default 2), only
        // where both powers have >= k2 digits and P mod b^(k2-f0) fits u32.
        let want_mid: u32 = std::env::var("JOIN_MID").ok().and_then(|v| v.parse().ok()).unwrap_or(2);
        let mut mid = want_mid;
        while mid > 0 && (k + mid > base.s2 || u64::from(b).pow(k + mid - f0) >= 1 << 32 || k + mid > 12) {
            mid -= 1;
        }
        let k2 = k + mid;
        let first_full = s.div_ceil(w);
        let full_floor = if first_full * w + w - 1 <= e - 1 { base.cert_floor(first_full * w, first_full * w + w - 1, k) } else { 0 };
        Ok(Self {
            mid,
            k2,
            pmod: base.powu(k2 - f0),
            full_floor,
            b,
            s,
            e,
            jp,
            l,
            f0,
            o,
            key_level: o - pp == 1,
            w,
            nparts: base.powu(pp),
            keyspace,
            m1,
            nb: keyspace as usize * m1 as usize,
            plo: s / w,
            phi: (e - 1) / w,
            tlay,
            bp_r,
            bp_m,
            seg,
            setup_ctr: ctr,
            sec_tlay,
            sec_bpre,
            base,
        })
    }

    /// Tops of partition `v` (the proto's per-partition top extension),
    /// grouped into the buckets they probe: key digits and, per digit-sum
    /// root, the class of R_low that completes it.
    #[must_use]
    pub fn part_tops(&self, v: u32) -> PartTops {
        let t0 = Instant::now();
        let mut pt = PartTops { v, ..PartTops::default() };
        let (s, e_incl, w, k) = (self.s, self.e - 1, self.w, self.jp.k);
        for &(p0, _) in &self.tlay {
            let p = p0 * self.nparts + u128::from(v);
            if p < self.plo || p > self.phi {
                continue;
            }
            pt.calls += 1;
            let a = (p * w).max(s);
            let ee = (p * w + w - 1).min(e_incl);
            if let Some(tm) = self.base.cert(a, ee, k) {
                pt.p.push(u64::try_from(p).expect("top prefix fits u64"));
                pt.m.push(tm);
                pt.rlo.push((a - p * w) as u32);
                pt.rhi.push((ee - p * w + 1) as u32);
                // Seed the prefilter with the certificate only if every
                // certified position is >= k2 (full blocks: the field bound).
                let floor = if a == p * w && ee == p * w + w - 1 { self.full_floor } else { self.base.cert_floor(a, ee, k) };
                pt.x.push((p % self.pmod) as u32);
                pt.x.push(u32::from(floor >= self.k2));
            }
        }
        let m1 = self.m1 as usize;
        let mut cnt = vec![0u32; self.nb + 1];
        let bucket_of = |p: u64, root: u32| {
            let key = ((u128::from(p) / self.nparts) % self.keyspace) as usize;
            let pc = (p % self.m1 as u64) as usize;
            key * m1 + (root as usize + m1 - pc) % m1
        };
        for &p in &pt.p {
            for &root in &self.base.roots {
                cnt[bucket_of(p, root) + 1] += 1;
            }
        }
        for x in 0..self.nb {
            cnt[x + 1] += cnt[x];
        }
        let mut cur = cnt.clone();
        pt.tl = vec![0u32; cnt[self.nb] as usize];
        for (i, &p) in pt.p.iter().enumerate() {
            for &root in &self.base.roots {
                let bx = bucket_of(p, root);
                pt.tl[cur[bx] as usize] = i as u32;
                cur[bx] += 1;
            }
        }
        for bx in 0..self.nb {
            if cnt[bx + 1] > cnt[bx] {
                pt.bkt.push((bx as u32, cnt[bx], cnt[bx + 1]));
            }
        }
        pt.secs = t0.elapsed().as_secs_f64();
        pt
    }

    /// All partition values in order.
    #[must_use]
    pub fn all_parts(&self) -> Vec<u32> {
        (0..self.nparts as u32).collect()
    }
}

/// Which digit-scan flavor, as the client's private `wide_chunk_for`: wide on
/// CUDA/HIP, split16 on wgpu, `NICE_CUBECL_WIDE=0|1` overrides.
fn wide_chunk_for<R: Runtime>(client: &ComputeClient<R>) -> bool {
    let name = R::name(client);
    match std::env::var("NICE_CUBECL_WIDE").ok().as_deref() {
        Some("0") => false,
        Some(_) => true,
        None => name.contains("cuda") || name == "hip",
    }
}

/// A fence on everything queued so far (the client's `launch_fence`).
type LaunchFence = cubecl::future::DynFut<Result<(), cubecl::server::ServerError>>;
fn launch_fence<R: Runtime>(client: &ComputeClient<R>) -> Result<Option<LaunchFence>> {
    use std::task::{Context, Poll, Waker};
    if std::env::var("JOIN_NOFENCE").is_ok_and(|v| v == "1") {
        return Ok(None);
    }
    let mut fence = client.sync();
    let mut cx = Context::from_waker(Waker::noop());
    match fence.as_mut().poll(&mut cx) {
        Poll::Ready(r) => {
            r.map_err(|e| anyhow::anyhow!("launch fence failed: {e:?}"))?;
            Ok(None)
        }
        Poll::Pending => Ok(Some(fence)),
    }
}

/// What a launched batch leaves behind to be read later.
pub struct BatchRec {
    pub nslots: usize,
    pub ntops: usize,
    pub nwork: usize,
    pub surv_count: Handle,
    pub list2_count: Handle,
    pub stats: Option<Handle>,
    /// Host copies for verification (probe runs only).
    pub top_p: Vec<u64>,
    pub work: Vec<u32>,
    pub tl_len: Vec<u32>,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum CheckMode {
    /// Full check on the device (production).
    Check,
    /// The check kernel reports every n it would check (verification of the
    /// device-side reconstruction of n).
    Probe,
    /// No check kernel (survivors are read back by the caller).
    None,
}

/// Per-field device state.
pub struct JoinDevice<R: Runtime> {
    pub client: ComputeClient<R>,
    b: u32,
    f0: u32,
    pp: u32,
    k: u32,
    key_level: bool,
    limbs: u32,
    chunk_digits: u32,
    chunk_div: u32,
    pub wide: bool,
    w_f0: u32,
    nbp: u32,
    bp_r: Handle,
    bp_m: Handle,
    seg: Handle,
    max_slots: usize,
    ext_m: Handle,
    ext_pk: Handle,
    /// Kernel generation: 1 = tile-scan join, 2 = v1 + register blocking,
    /// 3 = bucketized lists (default). `JOIN_KERNEL`.
    pub kernel: u32,
    lists: Handle,
    counts: Handle,
    nkeys: u32,
    pub surv: Handle,
    pub surv_cap: u32,
    mid: u32,
    k2: u32,
    pub list2: Handle,
    pub list2_cap: u32,
    pub nice_out: Handle,
    pub nice_count: Handle,
    pub nice_cap: u32,
    pub check_cubes: u32,
    /// Device-side top certification (`JOIN_DEVTOPS=1`), see [`DevTops`].
    pub devtops: Option<DevTops>,
}

/// Per-field device state for stage 0 (device-side top certification):
/// the top layer with its residues, the field bounds, the power table, and
/// the per-slot top/bucket buffers the stage fills.
pub struct DevTops {
    ntlay: u32,
    nroots: u32,
    nb: u32,
    s2: u32,
    s3: u32,
    pdiv: u32,
    pdiv_m1: u32,
    full_floor: u32,
    tlay: Handle,
    fb: Handle,
    pw: Handle,
    pw_len: usize,
    roots: Handle,
    top_p: Handle,
    top_m: Handle,
    top_r: Handle,
    top_x: Handle,
    top_b: Handle,
    tl: Handle,
    work: Handle,
    cursor: Handle,
}

impl DevTops {
    fn new<R: Runtime>(client: &ComputeClient<R>, fs: &FieldSetup, max_slots: usize, limbs: u32) -> Result<Self> {
        ensure!(limbs <= 3, "device tops: n must fit 96 bits");
        let (b, pp) = (u128::from(fs.b), fs.jp.p);
        let m1 = u128::from(fs.m1);
        let pdiv = fs.nparts;
        let p0mod = fs.base.powu(fs.k2 - fs.f0 - pp);
        let mut tl = Vec::with_capacity(5 * fs.tlay.len());
        for &(p0, _) in &fs.tlay {
            let p0u = u64::try_from(p0).expect("tlay prefix fits u64");
            tl.extend_from_slice(&[p0u as u32, (p0u >> 32) as u32, (p0 % m1) as u32, (p0 % b) as u32, (p0 % p0mod) as u32]);
        }
        let limb3 = |x: u128| [x as u32, (x >> 32) as u32, (x >> 64) as u32];
        ensure!(fs.e - 1 < 1 << 96, "field end must fit 96 bits");
        let mut fb = Vec::new();
        fb.extend_from_slice(&limb3(fs.s));
        fb.extend_from_slice(&limb3(fs.e - 1));
        let (plo, phi) = (u64::try_from(fs.plo)?, u64::try_from(fs.phi)?);
        fb.extend_from_slice(&[plo as u32, (plo >> 32) as u32, phi as u32, (phi >> 32) as u32]);
        let nl3 = 3 * limbs as usize;
        let s3 = fs.base.s3;
        let mut pw = Vec::with_capacity((s3 as usize + 1) * nl3);
        for i in 0..=s3 {
            let words = fs.base.poww_words(i);
            let mut l32: Vec<u32> = words.iter().flat_map(|&w| [w as u32, (w >> 32) as u32]).collect();
            l32.resize(nl3.max(8), 0);
            ensure!(l32[nl3..].iter().all(|&x| x == 0), "b^{i} does not fit {nl3} limbs");
            pw.extend_from_slice(&l32[..nl3]);
        }
        let roots: Vec<u32> = fs.base.roots.clone();
        let nroots = roots.len() as u32;
        let ntlay = fs.tlay.len();
        let nb = fs.nb;
        let pw_len = pw.len();
        Ok(Self {
            ntlay: ntlay as u32,
            nroots,
            nb: nb as u32,
            s2: fs.base.s2,
            s3,
            pdiv: pdiv as u32,
            pdiv_m1: (pdiv % m1) as u32,
            full_floor: fs.full_floor,
            tlay: client.create(cubecl::bytes::Bytes::from_elems(tl)),
            fb: client.create(cubecl::bytes::Bytes::from_elems(fb)),
            pw: client.create(cubecl::bytes::Bytes::from_elems(pw)),
            pw_len,
            roots: client.create(cubecl::bytes::Bytes::from_elems(roots)),
            top_p: client.empty(max_slots * ntlay.max(1) * 2 * 4),
            top_m: client.empty(max_slots * ntlay.max(1) * 2 * 4),
            top_r: client.empty(max_slots * ntlay.max(1) * 2 * 4),
            top_x: client.empty(max_slots * ntlay.max(1) * 2 * 4),
            top_b: client.empty(max_slots * ntlay.max(1) * 4),
            tl: client.empty(max_slots * ntlay.max(1) * nroots as usize * 4),
            work: client.empty(max_slots * nb * 4 * 4),
            cursor: client.empty(max_slots * nb * 4),
        })
    }
}

/// What a device-tops batch leaves behind: per-slot top counts, plus the
/// usual survivor counters.
pub struct DevBatchRec {
    pub rec: BatchRec,
    pub top_count: Handle,
    pub nslots: usize,
}

impl<R: Runtime> JoinDevice<R> {
    /// Launch one batch with device-side tops: certify, bucket, extend,
    /// join, prefilter, check. Only the partition values are uploaded.
    ///
    /// # Errors
    /// Device-tops state missing, or too many slots.
    pub fn launch_batch_dev(&mut self, vs: &[u32], mode: CheckMode, with_stats: bool) -> Result<DevBatchRec> {
        let nslots = vs.len();
        ensure!(nslots > 0 && nslots <= self.max_slots, "batch of {nslots} slots (max {})", self.max_slots);
        let dt = self.devtops.as_ref().ok_or_else(|| anyhow::anyhow!("device tops not enabled"))?;
        ensure!(self.kernel == 3, "device tops need the v3 join kernel");
        let c = &self.client;
        let nbp = self.nbp as usize;
        let ntl = dt.ntlay as usize;
        let nb = dt.nb as usize;
        let nwork = nslots * nb;
        let ept: u32 = std::env::var("JOIN_EPT").ok().and_then(|v| v.parse().ok()).unwrap_or(4);
        let vs_h = c.create(cubecl::bytes::Bytes::from_elems(vs.to_vec()));
        let top_count = c.create(cubecl::bytes::Bytes::from_elems(vec![0u32; nslots]));
        let bucket_cnt = c.create(cubecl::bytes::Bytes::from_elems(vec![0u32; nslots * nb]));
        let surv_count = c.create(cubecl::bytes::Bytes::from_elems(vec![0u32; 1]));
        let list2_count = c.create(cubecl::bytes::Bytes::from_elems(vec![0u32; 1]));
        let stats = if with_stats { Some(c.create(cubecl::bytes::Bytes::from_elems(vec![0u32; nwork]))) } else { None };
        let stats_arg = stats.clone().unwrap_or_else(|| surv_count.clone());
        let stats_len = if with_stats { nwork } else { 1 };
        let tops_len = nslots.max(1) * ntl;
        let tl_len = self.max_slots * ntl * dt.nroots as usize;
        let mut tp = Instant::now();
        unsafe {
            top_kernel::launch_unchecked::<R>(
                c,
                CubeCount::Static(dt.ntlay.div_ceil(JOIN_WG).max(1), nslots as u32, 1),
                CubeDim::new_1d(JOIN_WG),
                ArrayArg::from_raw_parts(dt.tlay.clone(), 5 * ntl),
                ArrayArg::from_raw_parts(vs_h.clone(), nslots),
                ArrayArg::from_raw_parts(dt.fb.clone(), 10),
                ArrayArg::from_raw_parts(dt.pw.clone(), dt.pw_len),
                ArrayArg::from_raw_parts(dt.roots.clone(), dt.nroots as usize),
                ArrayArg::from_raw_parts(dt.top_p.clone(), 2 * self.max_slots * ntl),
                ArrayArg::from_raw_parts(dt.top_m.clone(), 2 * self.max_slots * ntl),
                ArrayArg::from_raw_parts(dt.top_r.clone(), 2 * self.max_slots * ntl),
                ArrayArg::from_raw_parts(dt.top_x.clone(), 2 * self.max_slots * ntl),
                ArrayArg::from_raw_parts(dt.top_b.clone(), self.max_slots * ntl),
                ArrayArg::from_raw_parts(top_count.clone(), nslots),
                ArrayArg::from_raw_parts(bucket_cnt.clone(), nslots * nb),
                dt.ntlay,
                dt.nroots,
                self.w_f0,
                dt.pdiv,
                dt.pdiv_m1,
                dt.full_floor,
                self.b,
                self.limbs,
                self.k,
                self.k2,
                dt.s2,
                dt.s3,
                chunk_constants_u16(self.b).0,
                chunk_constants_u16(self.b).1,
                self.key_level,
                dt.nb,
            );
            top_scan_kernel::launch_unchecked::<R>(
                c,
                CubeCount::Static(nslots as u32, 1, 1),
                CubeDim::new_1d(JOIN_WG),
                ArrayArg::from_raw_parts(bucket_cnt.clone(), nslots * nb),
                ArrayArg::from_raw_parts(dt.cursor.clone(), self.max_slots * nb),
                ArrayArg::from_raw_parts(dt.work.clone(), 4 * self.max_slots * nb),
                (ntl * dt.nroots as usize) as u32,
                dt.nb,
            );
            top_fill_kernel::launch_unchecked::<R>(
                c,
                CubeCount::Static(dt.ntlay.div_ceil(JOIN_WG).max(1), nslots as u32, 1),
                CubeDim::new_1d(JOIN_WG),
                ArrayArg::from_raw_parts(dt.top_b.clone(), self.max_slots * ntl),
                ArrayArg::from_raw_parts(top_count.clone(), nslots),
                ArrayArg::from_raw_parts(dt.roots.clone(), dt.nroots as usize),
                ArrayArg::from_raw_parts(dt.cursor.clone(), self.max_slots * nb),
                ArrayArg::from_raw_parts(dt.tl.clone(), tl_len),
                dt.ntlay,
                dt.nroots,
                self.b,
                dt.nb,
            );
        }
        prof_mark(c, &mut tp, 1);
        unsafe {
            bucket_kernel::launch_unchecked::<R>(
                c,
                CubeCount::Static(self.b - 1, nslots as u32, 1),
                CubeDim::new_1d(JOIN_WG),
                ArrayArg::from_raw_parts(self.bp_r.clone(), nbp),
                ArrayArg::from_raw_parts(self.bp_m.clone(), 2 * nbp),
                ArrayArg::from_raw_parts(self.seg.clone(), self.b as usize),
                ArrayArg::from_raw_parts(vs_h, nslots),
                ArrayArg::from_raw_parts(self.ext_m.clone(), 2 * nbp * self.max_slots),
                ArrayArg::from_raw_parts(self.ext_pk.clone(), (nbp * self.max_slots).max(1)),
                ArrayArg::from_raw_parts(self.lists.clone(), nbp * self.max_slots * self.b as usize),
                ArrayArg::from_raw_parts(self.counts.clone(), self.max_slots * self.nkeys as usize * (self.b as usize - 1)),
                self.nbp,
                self.b,
                self.f0,
                self.pp,
                self.k,
                self.key_level,
                self.key_level && self.k == 1,
            );
        }
        prof_mark(c, &mut tp, 2);
        unsafe {
            join_kernel_v3::launch_unchecked::<R>(
                c,
                CubeCount::Static((nwork as u32).min(65_535), 1, 1),
                CubeDim::new_1d(JOIN_WG),
                ArrayArg::from_raw_parts(self.ext_m.clone(), 2 * nbp * self.max_slots),
                ArrayArg::from_raw_parts(self.ext_pk.clone(), (nbp * self.max_slots).max(1)),
                ArrayArg::from_raw_parts(self.bp_r.clone(), nbp),
                ArrayArg::from_raw_parts(self.seg.clone(), self.b as usize),
                ArrayArg::from_raw_parts(self.lists.clone(), nbp * self.max_slots * self.b as usize),
                ArrayArg::from_raw_parts(self.counts.clone(), self.max_slots * self.nkeys as usize * (self.b as usize - 1)),
                ArrayArg::from_raw_parts(dt.work.clone(), 4 * self.max_slots * nb),
                ArrayArg::from_raw_parts(dt.tl.clone(), tl_len),
                ArrayArg::from_raw_parts(dt.top_m.clone(), 2 * self.max_slots * ntl),
                ArrayArg::from_raw_parts(dt.top_r.clone(), 2 * self.max_slots * ntl),
                ArrayArg::from_raw_parts(self.surv.clone(), 2 * self.surv_cap as usize),
                ArrayArg::from_raw_parts(surv_count.clone(), 1),
                ArrayArg::from_raw_parts(stats_arg, stats_len),
                nwork as u32,
                self.nbp,
                self.surv_cap,
                self.b,
                self.key_level,
                self.key_level && self.k == 1,
                with_stats,
                ept.max(1),
                0u32,
            );
        }
        prof_mark(c, &mut tp, 3);
        let (chk_list, chk_count, chk_cap) = if self.mid > 0 {
            (self.list2.clone(), list2_count.clone(), self.list2_cap)
        } else {
            (self.surv.clone(), surv_count.clone(), self.surv_cap)
        };
        if self.mid > 0 && mode != CheckMode::None {
            unsafe {
                mid_kernel::launch_unchecked::<R>(
                    c,
                    CubeCount::Static(self.check_cubes, 1, 1),
                    CubeDim::new_1d(JOIN_WG),
                    ArrayArg::from_raw_parts(self.surv.clone(), 2 * self.surv_cap as usize),
                    ArrayArg::from_raw_parts(surv_count.clone(), 1),
                    ArrayArg::from_raw_parts(dt.top_m.clone(), 2 * self.max_slots * ntl),
                    ArrayArg::from_raw_parts(dt.top_x.clone(), 2 * self.max_slots * ntl),
                    ArrayArg::from_raw_parts(self.list2.clone(), 2 * self.list2_cap as usize),
                    ArrayArg::from_raw_parts(list2_count.clone(), 1),
                    self.surv_cap,
                    self.list2_cap,
                    self.b,
                    self.f0,
                    self.k2,
                );
            }
        }
        prof_mark(c, &mut tp, 5);
        if mode != CheckMode::None {
            unsafe {
                check_kernel::launch_unchecked::<R>(
                    c,
                    CubeCount::Static(self.check_cubes, 1, 1),
                    CubeDim::new_1d(JOIN_WG),
                    ArrayArg::from_raw_parts(chk_list, 2 * chk_cap as usize),
                    ArrayArg::from_raw_parts(chk_count, 1),
                    ArrayArg::from_raw_parts(dt.top_p.clone(), 2 * self.max_slots * ntl),
                    ArrayArg::from_raw_parts(self.nice_out.clone(), self.nice_cap as usize * NICEONLY_STRIDE as usize),
                    ArrayArg::from_raw_parts(self.nice_count.clone(), 1),
                    chk_cap,
                    self.nice_cap,
                    self.w_f0,
                    self.b,
                    self.limbs,
                    self.chunk_digits,
                    self.chunk_div,
                    self.wide,
                    0u32,
                    0u32,
                    0u32,
                    mode == CheckMode::Probe,
                );
            }
        }
        prof_mark(c, &mut tp, 4);
        c.flush().map_err(|e| anyhow::anyhow!("flush failed: {e:?}"))?;
        let _ = tops_len;
        let tl_counts = Vec::new();
        Ok(DevBatchRec {
            rec: BatchRec { nslots, ntops: 0, nwork, surv_count, list2_count, stats, top_p: Vec::new(), work: Vec::new(), tl_len: tl_counts },
            top_count,
            nslots,
        })
    }

    /// The certified tops of a device-tops batch, per slot, as sorted
    /// (P, mask, rlo, rhi, P mod, seed) tuples (verification).
    ///
    /// # Errors
    /// Device read failure.
    #[allow(clippy::type_complexity)]
    pub fn read_dev_tops(&self, drec: &DevBatchRec) -> Result<Vec<Vec<(u64, u64, u32, u32, u32, u32)>>> {
        let dt = self.devtops.as_ref().ok_or_else(|| anyhow::anyhow!("device tops not enabled"))?;
        let cnt = self.read_u32(&drec.top_count)?;
        let (tp, tm, tr, tx) = (self.read_u32(&dt.top_p)?, self.read_u32(&dt.top_m)?, self.read_u32(&dt.top_r)?, self.read_u32(&dt.top_x)?);
        let ntl = dt.ntlay as usize;
        let mut out = Vec::new();
        for (slot, &c) in cnt.iter().enumerate().take(drec.nslots) {
            let mut v: Vec<_> = (0..c as usize)
                .map(|i| {
                    let g = slot * ntl + i;
                    (u64::from(tp[2 * g]) | u64::from(tp[2 * g + 1]) << 32, u64::from(tm[2 * g]) | u64::from(tm[2 * g + 1]) << 32,
                     tr[2 * g], tr[2 * g + 1], tx[2 * g], tx[2 * g + 1])
                })
                .collect();
            v.sort_unstable();
            out.push(v);
        }
        Ok(out)
    }

    /// Matches of a device-tops batch launched with stats: sum over buckets
    /// of entries x tops probing it.
    ///
    /// # Errors
    /// Device read failure.
    pub fn read_dev_matches(&self, drec: &DevBatchRec) -> Result<u64> {
        let dt = self.devtops.as_ref().ok_or_else(|| anyhow::anyhow!("device tops not enabled"))?;
        let Some(st) = &drec.rec.stats else { bail!("batch has no stats") };
        let v = self.read_u32(st)?;
        let wk = self.read_u32(&dt.work)?;
        Ok((0..drec.rec.nwork).map(|w| u64::from(v[w]) * u64::from(wk[4 * w + 3] - wk[4 * w + 2])).sum())
    }

    /// Survivors of a device-tops batch as n (unsorted): P from the device
    /// top table.
    ///
    /// # Errors
    /// Device read failure or overflow.
    pub fn read_dev_survivors(&self, drec: &DevBatchRec, second: bool) -> Result<Vec<u128>> {
        let dt = self.devtops.as_ref().ok_or_else(|| anyhow::anyhow!("device tops not enabled"))?;
        let (cnt_h, list, cap) = if second { (&drec.rec.list2_count, &self.list2, self.list2_cap) } else { (&drec.rec.surv_count, &self.surv, self.surv_cap) };
        let cnt = self.read_u32(cnt_h)?[0];
        ensure!(cnt <= cap, "survivor list overflow: {cnt} > {cap}");
        if cnt == 0 {
            return Ok(Vec::new());
        }
        let words = self.read_u32(list)?;
        let tp = self.read_u32(&dt.top_p)?;
        Ok((0..cnt as usize)
            .map(|i| {
                let t = words[2 * i] as usize;
                let p = u128::from(tp[2 * t]) | u128::from(tp[2 * t + 1]) << 32;
                p * u128::from(self.w_f0) + u128::from(words[2 * i + 1])
            })
            .collect())
    }
}

impl<R: Runtime> JoinDevice<R> {
    /// # Errors
    /// Unsupported base.
    pub fn new(client: &ComputeClient<R>, fs: &FieldSetup, max_slots: usize, surv_cap: u32, nice_cap: u32) -> Result<Self> {
        let limbs = n_limbs(fs.b).ok_or_else(|| anyhow::anyhow!("base {} has no u128 range", fs.b))?;
        let wide = wide_chunk_for(client);
        let (chunk_digits, chunk_div) = if wide { chunk_constants(fs.b) } else { chunk_constants_u16(fs.b) };
        let nbp = fs.bp_r.len();
        ensure!(nbp > 0, "empty bpre list");
        let bp_m_words: Vec<u32> = fs.bp_m.iter().flat_map(|&m| [m as u32, (m >> 32) as u32]).collect();
        let kernel: u32 = std::env::var("JOIN_KERNEL").ok().and_then(|v| v.parse().ok()).unwrap_or(3);
        // Device memory per slot: ext (12 B per entry) and, for v3, the
        // bucket lists (b index slots per entry); bounded to ~768 MB.
        let per_slot = nbp * 12 + if kernel == 3 { nbp * fs.b as usize * 4 } else { 0 };
        let max_slots = max_slots.min((768usize << 20) / per_slot.max(1)).max(1);
        let nkeys = if fs.key_level { fs.b } else { 1 };
        let slots_entries = max_slots * nbp;
        let dev = Self {
            b: fs.b,
            f0: fs.f0,
            pp: fs.jp.p,
            k: fs.jp.k,
            key_level: fs.key_level,
            limbs,
            chunk_digits,
            chunk_div,
            wide,
            w_f0: fs.w as u32,
            nbp: nbp as u32,
            bp_r: client.create(cubecl::bytes::Bytes::from_elems(fs.bp_r.clone())),
            bp_m: client.create(cubecl::bytes::Bytes::from_elems(bp_m_words)),
            seg: client.create(cubecl::bytes::Bytes::from_elems(fs.seg.clone())),
            max_slots,
            ext_m: client.empty(slots_entries * 2 * 4),
            ext_pk: client.empty(slots_entries.max(1) * 4),
            kernel,
            lists: client.empty(if kernel == 3 { slots_entries * fs.b as usize * 4 } else { 4 }),
            counts: client.empty(max_slots * nkeys as usize * (fs.b as usize - 1) * 4),
            nkeys,
            surv: client.empty(surv_cap as usize * 2 * 4),
            surv_cap,
            mid: fs.mid,
            k2: fs.k2,
            // The prefilter keeps ~6% at bases 57-64; small verification
            // runs get the full capacity (weak seeds at small bases).
            list2: client.empty(if surv_cap <= 1 << 22 { surv_cap } else { surv_cap / 4 } as usize * 2 * 4),
            list2_cap: if surv_cap <= 1 << 22 { surv_cap } else { surv_cap / 4 },
            nice_out: client.create(cubecl::bytes::Bytes::from_elems(vec![0u32; nice_cap as usize * NICEONLY_STRIDE as usize])),
            nice_count: client.create(cubecl::bytes::Bytes::from_elems(vec![0u32; 1])),
            nice_cap,
            check_cubes: 1024,
            devtops: None,
            client: client.clone(),
        };
        let mut dev = dev;
        if std::env::var("JOIN_DEVTOPS").is_ok_and(|v| v == "1") {
            dev.devtops = Some(DevTops::new(client, fs, dev.max_slots, limbs)?);
        }
        Ok(dev)
    }

    /// Launch one batch of partitions: extend, join, and (per `mode`) check.
    /// Returns immediately; nothing is read back.
    ///
    /// # Errors
    /// Too many slots, or a work list that does not fit u32.
    pub fn launch_batch(&mut self, parts: &[&PartTops], mode: CheckMode, with_stats: bool, keep_host: bool) -> Result<BatchRec> {
        let mut tp = Instant::now();
        let nslots = parts.len();
        ensure!(nslots > 0 && nslots <= self.max_slots, "batch of {nslots} slots (max {})", self.max_slots);
        let ntops: usize = parts.iter().map(|p| p.p.len()).sum();
        let mut top_p = Vec::with_capacity(2 * ntops);
        let mut top_m = Vec::with_capacity(2 * ntops);
        let mut top_r = Vec::with_capacity(2 * ntops);
        let mut top_x = Vec::with_capacity(2 * ntops);
        let mut tl = Vec::new();
        let mut work = Vec::new();
        let mut vs = Vec::with_capacity(nslots);
        let mut tbase = 0u32;
        for (slot, pt) in parts.iter().enumerate() {
            vs.push(pt.v);
            for i in 0..pt.p.len() {
                top_p.extend_from_slice(&[pt.p[i] as u32, (pt.p[i] >> 32) as u32]);
                top_m.extend_from_slice(&[pt.m[i] as u32, (pt.m[i] >> 32) as u32]);
                top_r.extend_from_slice(&[pt.rlo[i], pt.rhi[i]]);
            }
            top_x.extend_from_slice(&pt.x);
            let lbase = tl.len() as u32;
            tl.extend(pt.tl.iter().map(|&i| i + tbase));
            for &(bx, st, en) in &pt.bkt {
                work.extend_from_slice(&[slot as u32, bx, st + lbase, en + lbase]);
            }
            tbase += pt.p.len() as u32;
        }
        let nwork = work.len() / 4;
        let host_top_p: Vec<u64> = if keep_host { parts.iter().flat_map(|p| p.p.iter().copied()).collect() } else { Vec::new() };
        let tl_len = if keep_host { work.chunks(4).map(|w| w[3] - w[2]).collect() } else { Vec::new() };
        let surv_count = self.client.create(cubecl::bytes::Bytes::from_elems(vec![0u32; 1]));
        let list2_count = self.client.create(cubecl::bytes::Bytes::from_elems(vec![0u32; 1]));
        if nwork == 0 {
            return Ok(BatchRec { nslots, ntops, nwork, surv_count, list2_count, stats: None, top_p: host_top_p, work, tl_len });
        }
        let c = &self.client;
        let mut th0 = Instant::now();
        host_mark(&mut th0, 11);
        if profiling() {
            PROFILE_US[0].fetch_add(tp.elapsed().as_micros() as u64, Ordering::Relaxed);
            tp = Instant::now();
        }
        let vs_h = c.create(cubecl::bytes::Bytes::from_elems(vs));
        let top_p_h = c.create(cubecl::bytes::Bytes::from_elems(top_p));
        let top_m_h = c.create(cubecl::bytes::Bytes::from_elems(top_m));
        let top_r_h = c.create(cubecl::bytes::Bytes::from_elems(top_r));
        let top_x_h = c.create(cubecl::bytes::Bytes::from_elems(top_x));
        let tl_len_total = tl.len();
        let tl_h = c.create(cubecl::bytes::Bytes::from_elems(tl));
        let work_len = work.len();
        let work_h = c.create(cubecl::bytes::Bytes::from_elems(if keep_host { work.clone() } else { std::mem::take(&mut work) }));
        let stats = if with_stats { Some(c.create(cubecl::bytes::Bytes::from_elems(vec![0u32; nwork]))) } else { None };
        let stats_arg = stats.clone().unwrap_or_else(|| surv_count.clone());
        let stats_len = if with_stats { nwork } else { 1 };
        host_mark(&mut th0, 6);
        let mut th = Instant::now();
        let nbp = self.nbp as usize;
        // JOIN_EPT: entries per thread in join_kernel_v2 (0 = v1 kernel).
        let ept: u32 = std::env::var("JOIN_EPT").ok().and_then(|v| v.parse().ok()).unwrap_or(4);
        // JOIN_STAGES (benchmarking only): 1 = bottoms, 2 = + join, 3 = + prefilter, 4 = all.
        let stages: u32 = std::env::var("JOIN_STAGES").ok().and_then(|v| v.parse().ok()).unwrap_or(4);
        prof_mark(c, &mut tp, 1);
        if self.kernel == 3 {
            unsafe {
                bucket_kernel::launch_unchecked::<R>(
                    c,
                    CubeCount::Static(self.b - 1, nslots as u32, 1),
                    CubeDim::new_1d(JOIN_WG),
                    ArrayArg::from_raw_parts(self.bp_r.clone(), nbp),
                    ArrayArg::from_raw_parts(self.bp_m.clone(), 2 * nbp),
                    ArrayArg::from_raw_parts(self.seg.clone(), self.b as usize),
                    ArrayArg::from_raw_parts(vs_h.clone(), nslots),
                    ArrayArg::from_raw_parts(self.ext_m.clone(), 2 * nbp * self.max_slots),
                    ArrayArg::from_raw_parts(self.ext_pk.clone(), (nbp * self.max_slots).max(1)),
                    ArrayArg::from_raw_parts(self.lists.clone(), nbp * self.max_slots * self.b as usize),
                    ArrayArg::from_raw_parts(self.counts.clone(), self.max_slots * self.nkeys as usize * (self.b as usize - 1)),
                    self.nbp,
                    self.b,
                    self.f0,
                    self.pp,
                    self.k,
                    self.key_level,
                    self.key_level && self.k == 1,
                );
            }
        } else {
        unsafe {
            bottom_extend_kernel::launch_unchecked::<R>(
                c,
                CubeCount::Static(self.nbp.div_ceil(JOIN_WG), nslots as u32, 1),
                CubeDim::new_1d(JOIN_WG),
                ArrayArg::from_raw_parts(self.bp_r.clone(), nbp),
                ArrayArg::from_raw_parts(self.bp_m.clone(), 2 * nbp),
                ArrayArg::from_raw_parts(vs_h, nslots),
                ArrayArg::from_raw_parts(self.ext_m.clone(), 2 * nbp * self.max_slots),
                ArrayArg::from_raw_parts(self.ext_pk.clone(), (nbp * self.max_slots).max(1)),
                self.nbp,
                self.b,
                self.f0,
                self.pp,
                self.k,
                self.key_level,
            );
        }
        }
        prof_mark(c, &mut tp, 2);
        unsafe {
            if stages < 2 {
            } else if self.kernel == 3 {
                join_kernel_v3::launch_unchecked::<R>(
                    c,
                    CubeCount::Static((nwork as u32).min(65_535), 1, 1),
                    CubeDim::new_1d(JOIN_WG),
                    ArrayArg::from_raw_parts(self.ext_m.clone(), 2 * nbp * self.max_slots),
                    ArrayArg::from_raw_parts(self.ext_pk.clone(), (nbp * self.max_slots).max(1)),
                    ArrayArg::from_raw_parts(self.bp_r.clone(), nbp),
                    ArrayArg::from_raw_parts(self.seg.clone(), self.b as usize),
                    ArrayArg::from_raw_parts(self.lists.clone(), nbp * self.max_slots * self.b as usize),
                    ArrayArg::from_raw_parts(self.counts.clone(), self.max_slots * self.nkeys as usize * (self.b as usize - 1)),
                    ArrayArg::from_raw_parts(work_h, work_len),
                    ArrayArg::from_raw_parts(tl_h, tl_len_total),
                    ArrayArg::from_raw_parts(top_m_h.clone(), 2 * ntops),
                    ArrayArg::from_raw_parts(top_r_h, 2 * ntops),
                    ArrayArg::from_raw_parts(self.surv.clone(), 2 * self.surv_cap as usize),
                    ArrayArg::from_raw_parts(surv_count.clone(), 1),
                    ArrayArg::from_raw_parts(stats_arg, stats_len),
                    nwork as u32,
                    self.nbp,
                    self.surv_cap,
                    self.b,
                    self.key_level,
                    self.key_level && self.k == 1,
                    with_stats,
                    ept.max(1),
                    std::env::var("JOIN_EXP").ok().and_then(|v| v.parse().ok()).unwrap_or(0u32),
                );
            } else if ept == 0 || self.kernel == 1 {
                join_kernel::launch_unchecked::<R>(
                    c,
                    CubeCount::Static((nwork as u32).min(65_535), 1, 1),
                    CubeDim::new_1d(JOIN_WG),
                    ArrayArg::from_raw_parts(self.ext_m.clone(), 2 * nbp * self.max_slots),
                    ArrayArg::from_raw_parts(self.ext_pk.clone(), (nbp * self.max_slots).max(1)),
                    ArrayArg::from_raw_parts(self.bp_r.clone(), nbp),
                    ArrayArg::from_raw_parts(self.seg.clone(), self.b as usize),
                    ArrayArg::from_raw_parts(work_h, work_len),
                    ArrayArg::from_raw_parts(tl_h, tl_len_total),
                    ArrayArg::from_raw_parts(top_m_h.clone(), 2 * ntops),
                    ArrayArg::from_raw_parts(top_r_h, 2 * ntops),
                    ArrayArg::from_raw_parts(self.surv.clone(), 2 * self.surv_cap as usize),
                    ArrayArg::from_raw_parts(surv_count.clone(), 1),
                    ArrayArg::from_raw_parts(stats_arg, stats_len),
                    nwork as u32,
                    self.nbp,
                    self.surv_cap,
                    self.b,
                    self.key_level,
                    self.key_level && self.k == 1,
                    with_stats,
                );
            } else {
                join_kernel_v2::launch_unchecked::<R>(
                    c,
                    CubeCount::Static((nwork as u32).min(65_535), 1, 1),
                    CubeDim::new_1d(JOIN_WG),
                    ArrayArg::from_raw_parts(self.ext_m.clone(), 2 * nbp * self.max_slots),
                    ArrayArg::from_raw_parts(self.ext_pk.clone(), (nbp * self.max_slots).max(1)),
                    ArrayArg::from_raw_parts(self.bp_r.clone(), nbp),
                    ArrayArg::from_raw_parts(self.seg.clone(), self.b as usize),
                    ArrayArg::from_raw_parts(work_h, work_len),
                    ArrayArg::from_raw_parts(tl_h, tl_len_total),
                    ArrayArg::from_raw_parts(top_m_h.clone(), 2 * ntops),
                    ArrayArg::from_raw_parts(top_r_h, 2 * ntops),
                    ArrayArg::from_raw_parts(self.surv.clone(), 2 * self.surv_cap as usize),
                    ArrayArg::from_raw_parts(surv_count.clone(), 1),
                    ArrayArg::from_raw_parts(stats_arg, stats_len),
                    nwork as u32,
                    self.nbp,
                    self.surv_cap,
                    self.b,
                    self.key_level,
                    self.key_level && self.k == 1,
                    with_stats,
                    ept,
                    std::env::var("JOIN_EXP").ok().and_then(|v| v.parse().ok()).unwrap_or(0u32),
                );
            }
        }
        prof_mark(c, &mut tp, 3);
        // The list the full check reads: the prefilter's output, or the join's.
        let (chk_list, chk_count, chk_cap) = if self.mid > 0 {
            (self.list2.clone(), list2_count.clone(), self.list2_cap)
        } else {
            (self.surv.clone(), surv_count.clone(), self.surv_cap)
        };
        if self.mid > 0 && mode != CheckMode::None && stages >= 3 {
            unsafe {
                mid_kernel::launch_unchecked::<R>(
                    c,
                    CubeCount::Static(self.check_cubes, 1, 1),
                    CubeDim::new_1d(JOIN_WG),
                    ArrayArg::from_raw_parts(self.surv.clone(), 2 * self.surv_cap as usize),
                    ArrayArg::from_raw_parts(surv_count.clone(), 1),
                    ArrayArg::from_raw_parts(top_m_h, 2 * ntops),
                    ArrayArg::from_raw_parts(top_x_h, 2 * ntops),
                    ArrayArg::from_raw_parts(self.list2.clone(), 2 * self.list2_cap as usize),
                    ArrayArg::from_raw_parts(list2_count.clone(), 1),
                    self.surv_cap,
                    self.list2_cap,
                    self.b,
                    self.f0,
                    self.k2,
                );
            }
        }
        prof_mark(c, &mut tp, 5);
        unsafe {
            if mode != CheckMode::None && stages >= 4 {
                check_kernel::launch_unchecked::<R>(
                    c,
                    CubeCount::Static(self.check_cubes, 1, 1),
                    CubeDim::new_1d(JOIN_WG),
                    ArrayArg::from_raw_parts(chk_list, 2 * chk_cap as usize),
                    ArrayArg::from_raw_parts(chk_count, 1),
                    ArrayArg::from_raw_parts(top_p_h, 2 * ntops),
                    ArrayArg::from_raw_parts(self.nice_out.clone(), self.nice_cap as usize * NICEONLY_STRIDE as usize),
                    ArrayArg::from_raw_parts(self.nice_count.clone(), 1),
                    chk_cap,
                    self.nice_cap,
                    self.w_f0,
                    self.b,
                    self.limbs,
                    self.chunk_digits,
                    self.chunk_div,
                    self.wide,
                    0u32,
                    0u32,
                    0u32,
                    mode == CheckMode::Probe,
                );
            }
        }
        prof_mark(c, &mut tp, 4);
        host_mark(&mut th, 7);
        // Submit now (the client's per-dispatch flush: watchdog safety).
        c.flush().map_err(|e| anyhow::anyhow!("flush failed: {e:?}"))?;
        host_mark(&mut th, 8);
        Ok(BatchRec { nslots, ntops, nwork, surv_count, list2_count, stats, top_p: host_top_p, work, tl_len })
    }

    /// The prefilter's output list of a batch launched with `keep_host`, as n.
    ///
    /// # Errors
    /// Device read failure or overflow.
    pub fn read_list2(&self, rec: &BatchRec) -> Result<Vec<u128>> {
        let cnt = self.read_u32(&rec.list2_count)?[0];
        ensure!(cnt <= self.list2_cap, "prefilter list overflow: {cnt} > {}", self.list2_cap);
        if cnt == 0 {
            return Ok(Vec::new());
        }
        let words = self.read_u32(&self.list2)?;
        Ok((0..cnt as usize)
            .map(|i| u128::from(rec.top_p[words[2 * i] as usize]) * u128::from(self.w_f0) + u128::from(words[2 * i + 1]))
            .collect())
    }

    /// Slots per batch after the memory bound.
    #[must_use]
    pub fn max_slots(&self) -> usize {
        self.max_slots
    }

    /// Prefilter depth in force (0 = off).
    #[must_use]
    pub fn mid(&self) -> u32 {
        self.mid
    }

    /// Survivors of a batch launched with `keep_host`, as n (unsorted).
    ///
    /// # Errors
    /// Device read failure or survivor-list overflow.
    pub fn read_survivors(&self, rec: &BatchRec) -> Result<Vec<u128>> {
        let cnt = self.read_u32(&rec.surv_count)?[0];
        ensure!(cnt <= self.surv_cap, "survivor list overflow: {cnt} > {}", self.surv_cap);
        if cnt == 0 {
            return Ok(Vec::new());
        }
        let words = self.read_u32(&self.surv)?;
        Ok((0..cnt as usize)
            .map(|i| u128::from(rec.top_p[words[2 * i] as usize]) * u128::from(self.w_f0) + u128::from(words[2 * i + 1]))
            .collect())
    }

    /// Per-work-item bucket sizes of a batch launched with stats, and the
    /// implied number of matches (sum of bucket size x tops probing it).
    ///
    /// # Errors
    /// Device read failure.
    pub fn read_matches(&self, rec: &BatchRec) -> Result<u64> {
        let Some(st) = &rec.stats else { bail!("batch has no stats") };
        let v = self.read_u32(st)?;
        Ok(v.iter().zip(&rec.tl_len).map(|(&a, &b)| u64::from(a) * u64::from(b)).sum())
    }

    /// # Errors
    /// Device read failure.
    pub fn read_u32(&self, h: &Handle) -> Result<Vec<u32>> {
        let bytes = self.client.read_one(h.clone()).map_err(|e| anyhow::anyhow!("read failed: {e:?}"))?;
        Ok(u32::from_bytes(&bytes).to_vec())
    }

    /// Hits (or probe outputs) accumulated in this device's output buffer.
    ///
    /// # Errors
    /// Device read failure or output overflow.
    pub fn read_hits(&self) -> Result<Vec<u128>> {
        let written = self.read_u32(&self.nice_count)?[0] as usize;
        ensure!(written <= self.nice_cap as usize, "output overflow: {written} > {}", self.nice_cap);
        let words = self.read_u32(&self.nice_out)?;
        let mut v: Vec<u128> = (0..written)
            .map(|i| {
                let o = i * NICEONLY_STRIDE as usize;
                let lo = u128::from(words[o]) | (u128::from(words[o + 1]) << 32);
                let hi = u128::from(words[o + 2]) | (u128::from(words[o + 3]) << 32);
                (hi << 64) | lo
            })
            .collect();
        v.sort_unstable();
        Ok(v)
    }

    /// Zero the hit counter (between verification passes).
    pub fn reset_hits(&mut self) {
        self.nice_count = self.client.create(cubecl::bytes::Bytes::from_elems(vec![0u32; 1]));
    }
}

/// Result of running a set of partitions through the device.
#[derive(Default, Debug, Clone)]
pub struct RunStats {
    pub parts: usize,
    pub nonempty_parts: usize,
    pub batches: usize,
    pub tops: u64,
    pub top_calls: u64,
    pub survivors: u64,
    /// Survivors of the middle-digit prefilter (the full checks run).
    pub mid_survivors: u64,
    pub hits: Vec<u128>,
    /// Sum of per-partition host seconds (top certification + bucketing).
    pub host_cpu_secs: f64,
    /// Wall seconds of the host-only phase (precompute mode).
    pub host_wall: f64,
    /// Wall seconds of the device phase: first launch to results read.
    pub device_wall: f64,
    /// Dispatcher time spent packing/uploading/launching.
    pub dispatch_secs: f64,
    /// Dispatcher time blocked on in-flight fences (device behind).
    pub device_wait: f64,
    /// Dispatcher time blocked on the host workers (host behind).
    pub host_wait: f64,
    pub wall: f64,
}

/// Batching policy.
#[derive(Clone, Copy, Debug)]
pub struct BatchPolicy {
    pub max_slots: usize,
    pub max_tops: usize,
    pub inflight: usize,
}

fn finish<R: Runtime>(dev: &JoinDevice<R>, recs: &[BatchRec], st: &mut RunStats) -> Result<()> {
    // Survivor counts of every batch (also the overflow check), then hits.
    let handles: Vec<Handle> = recs.iter().flat_map(|r| [r.surv_count.clone(), r.list2_count.clone()]).collect();
    if !handles.is_empty() {
        let bytes = cubecl::future::block_on(dev.client.read_async(handles)).map_err(|e| anyhow::anyhow!("read failed: {e:?}"))?;
        for (i, b) in bytes.iter().enumerate() {
            let c = u32::from_bytes(b)[0];
            let cap = if i % 2 == 0 { dev.surv_cap } else { dev.list2_cap };
            ensure!(c <= cap, "survivor list overflow in a batch: {c} > {cap} (lower the batch size)");
            if i % 2 == 0 {
                st.survivors += u64::from(c);
            } else {
                st.mid_survivors += u64::from(c);
            }
        }
    }
    st.hits = dev.read_hits()?;
    Ok(())
}

/// Launch precomputed partitions (device phase only).
///
/// # Errors
/// Device errors.
pub fn run_device<R: Runtime>(dev: &mut JoinDevice<R>, parts: &[PartTops], pol: BatchPolicy) -> Result<RunStats> {
    let mut st = RunStats::default();
    let t0 = Instant::now();
    let mut inflight: std::collections::VecDeque<LaunchFence> = std::collections::VecDeque::new();
    let mut recs = Vec::new();
    let mut batch: Vec<&PartTops> = Vec::new();
    let mut btops = 0usize;
    let mut launch = |batch: &mut Vec<&PartTops>, st: &mut RunStats, dev: &mut JoinDevice<R>| -> Result<()> {
        while inflight.len() >= pol.inflight {
            let tw = Instant::now();
            if let Some(f) = inflight.pop_front() {
                cubecl::future::block_on(f).map_err(|e| anyhow::anyhow!("fence: {e:?}"))?;
            }
            st.device_wait += tw.elapsed().as_secs_f64();
        }
        let td = Instant::now();
        recs.push(dev.launch_batch(batch, CheckMode::Check, false, false)?);
        let mut tf = Instant::now();
        if let Some(f) = launch_fence(&dev.client)? {
            inflight.push_back(f);
        }
        host_mark(&mut tf, 9);
        st.dispatch_secs += td.elapsed().as_secs_f64();
        st.batches += 1;
        batch.clear();
        Ok(())
    };
    for pt in parts {
        st.parts += 1;
        st.top_calls += pt.calls;
        st.host_cpu_secs += pt.secs;
        if pt.p.is_empty() {
            continue;
        }
        st.nonempty_parts += 1;
        st.tops += pt.p.len() as u64;
        batch.push(pt);
        btops += pt.p.len();
        if batch.len() >= pol.max_slots || btops >= pol.max_tops {
            launch(&mut batch, &mut st, dev)?;
            btops = 0;
        }
    }
    if !batch.is_empty() {
        launch(&mut batch, &mut st, dev)?;
    }
    let tw = Instant::now();
    finish(dev, &recs, &mut st)?;
    st.device_wait += tw.elapsed().as_secs_f64();
    st.device_wall = t0.elapsed().as_secs_f64();
    st.wall = st.device_wall;
    Ok(st)
}

/// Host tops for `parts` on `nthreads` threads (host phase only).
#[must_use]
pub fn run_host(fs: &FieldSetup, parts: &[u32], nthreads: usize) -> (Vec<PartTops>, f64) {
    let t0 = Instant::now();
    let next = AtomicUsize::new(0);
    let mut out: Vec<(usize, PartTops)> = std::thread::scope(|sc| {
        let hs: Vec<_> = (0..nthreads)
            .map(|_| {
                sc.spawn(|| {
                    let mut mine = Vec::new();
                    loop {
                        let i = next.fetch_add(1, Ordering::Relaxed);
                        if i >= parts.len() {
                            break;
                        }
                        mine.push((i, fs.part_tops(parts[i])));
                    }
                    mine
                })
            })
            .collect();
        hs.into_iter().flat_map(|h| h.join().unwrap()).collect()
    });
    out.sort_by_key(|x| x.0);
    (out.into_iter().map(|x| x.1).collect(), t0.elapsed().as_secs_f64())
}

/// The continuous pipeline: `nthreads` host workers certify tops while the
/// dispatcher (this thread) batches and launches them.
///
/// # Errors
/// Device errors.
pub fn run_pipelined<R: Runtime>(dev: &mut JoinDevice<R>, fs: &FieldSetup, parts: &[u32], nthreads: usize, pol: BatchPolicy) -> Result<RunStats> {
    let mut st = RunStats::default();
    let t0 = Instant::now();
    let next = AtomicUsize::new(0);
    let (tx, rx) = sync_channel::<PartTops>(4 * pol.max_slots.max(8));
    let res: Result<Vec<BatchRec>> = std::thread::scope(|sc| {
        for _ in 0..nthreads {
            let tx = tx.clone();
            let next = &next;
            sc.spawn(move || {
                loop {
                    let i = next.fetch_add(1, Ordering::Relaxed);
                    if i >= parts.len() {
                        break;
                    }
                    if tx.send(fs.part_tops(parts[i])).is_err() {
                        break;
                    }
                }
            });
        }
        drop(tx);
        let mut inflight: std::collections::VecDeque<LaunchFence> = std::collections::VecDeque::new();
        let mut recs = Vec::new();
        let mut batch: Vec<PartTops> = Vec::new();
        let mut btops = 0usize;
        let mut launch = |batch: &mut Vec<PartTops>, st: &mut RunStats| -> Result<()> {
            while inflight.len() >= pol.inflight {
                let tw = Instant::now();
                if let Some(f) = inflight.pop_front() {
                    cubecl::future::block_on(f).map_err(|e| anyhow::anyhow!("fence: {e:?}"))?;
                }
                st.device_wait += tw.elapsed().as_secs_f64();
            }
            let td = Instant::now();
            let refs: Vec<&PartTops> = batch.iter().collect();
            recs.push(dev.launch_batch(&refs, CheckMode::Check, false, false)?);
            if let Some(f) = launch_fence(&dev.client)? {
                inflight.push_back(f);
            }
            st.dispatch_secs += td.elapsed().as_secs_f64();
            st.batches += 1;
            batch.clear();
            Ok(())
        };
        loop {
            let tw = Instant::now();
            let Ok(pt) = rx.recv() else { break };
            let waited = tw.elapsed();
            if waited > Duration::from_micros(50) {
                st.host_wait += waited.as_secs_f64();
            }
            st.parts += 1;
            st.top_calls += pt.calls;
            st.host_cpu_secs += pt.secs;
            if pt.p.is_empty() {
                continue;
            }
            st.nonempty_parts += 1;
            st.tops += pt.p.len() as u64;
            btops += pt.p.len();
            batch.push(pt);
            if batch.len() >= pol.max_slots || btops >= pol.max_tops {
                launch(&mut batch, &mut st)?;
                btops = 0;
            }
        }
        if !batch.is_empty() {
            launch(&mut batch, &mut st)?;
        }
        Ok(recs)
    });
    let recs = res?;
    let tw = Instant::now();
    finish(dev, &recs, &mut st)?;
    st.device_wait += tw.elapsed().as_secs_f64();
    st.wall = t0.elapsed().as_secs_f64();
    st.device_wall = st.wall;
    Ok(st)
}

/// Every partition in `parts` through the device-tops path: the host only
/// launches (no per-partition host work). Top counts are summed at the end.
///
/// # Errors
/// Device errors.
pub fn run_devtops<R: Runtime>(dev: &mut JoinDevice<R>, parts: &[u32], pol: BatchPolicy) -> Result<RunStats> {
    let mut st = RunStats::default();
    let t0 = Instant::now();
    let mut inflight: std::collections::VecDeque<LaunchFence> = std::collections::VecDeque::new();
    let mut recs = Vec::new();
    let mut counts = Vec::new();
    for ch in parts.chunks(pol.max_slots) {
        while inflight.len() >= pol.inflight {
            let tw = Instant::now();
            if let Some(f) = inflight.pop_front() {
                cubecl::future::block_on(f).map_err(|e| anyhow::anyhow!("fence: {e:?}"))?;
            }
            st.device_wait += tw.elapsed().as_secs_f64();
        }
        let td = Instant::now();
        let d = dev.launch_batch_dev(ch, CheckMode::Check, false)?;
        if let Some(f) = launch_fence(&dev.client)? {
            inflight.push_back(f);
        }
        st.dispatch_secs += td.elapsed().as_secs_f64();
        st.batches += 1;
        st.parts += ch.len();
        counts.push(d.top_count.clone());
        recs.push(d.rec);
    }
    let tw = Instant::now();
    finish(dev, &recs, &mut st)?;
    let bytes = cubecl::future::block_on(dev.client.read_async(counts)).map_err(|e| anyhow::anyhow!("read failed: {e:?}"))?;
    for b in bytes {
        st.tops += u32::from_bytes(&b).iter().map(|&x| u64::from(x)).sum::<u64>();
    }
    st.device_wait += tw.elapsed().as_secs_f64();
    st.wall = t0.elapsed().as_secs_f64();
    st.device_wall = st.wall;
    Ok(st)
}
