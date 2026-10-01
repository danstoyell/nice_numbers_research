//! overlap_join_gpu modes (one JSON line out each):
//!   verify B S E T K P            all partitions of [S,E): GPU survivors, matches, hits and the
//!                                 device-reconstructed n == CPU prototype (+ brute force if small)
//!   verify-parts B S E T K P NPART SEED
//!                                 the same on NPART random partitions of a (production) field
//!   field B S E T K P NPART SEED NTHREADS SLOTS
//!                                 timing: host-only phase and device-only phase on NPART random
//!                                 partitions, then the pipelined run on the same partitions
//!   field-full B S E T K P NTHREADS SLOTS
//!                                 pipelined run over every partition of the field
//!   client-range B S E            the client's own CubeCL niceonly pipeline on [S,E)
//!   client-sample B S E PIECE NPIECE SEED
//!                                 the client's pipeline on NPIECE random PIECE-sized pieces
use anyhow::{Result, ensure};
use nice_common::FieldSize;
use nice_common::cubecl_backend::{CubeclContext, begin_niceonly_cubecl, finish_niceonly_cubecl};
use nice_common::gpu_niceonly::{NiceonlyStarted, fields_in_flight, msd_floor_in_use};
use overlap_join_gpu::join_gpu::{BatchPolicy, CheckMode, FieldSetup, JoinDevice, PartTops, RunStats, run_device, run_devtops, run_host, run_pipelined};
use overlap_join_gpu::proto::{self, JoinParams};
use serde_json::json;
use std::time::Instant;

type Wgpu = cubecl::wgpu::WgpuRuntime;

fn arg<T: std::str::FromStr>(a: &[String], i: usize) -> T
where
    T::Err: std::fmt::Debug,
{
    a[i].parse().unwrap()
}

fn splitmix(s: &mut u64) -> u64 {
    *s = s.wrapping_add(0x9E37_79B9_7F4A_7C15);
    let mut z = *s;
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

/// User + system CPU seconds of this process so far (all threads).
fn cpu_secs() -> f64 {
    let mut ru: libc::rusage = unsafe { std::mem::zeroed() };
    unsafe { libc::getrusage(libc::RUSAGE_SELF, &raw mut ru) };
    let t = |tv: libc::timeval| tv.tv_sec as f64 + f64::from(tv.tv_usec) * 1e-6;
    t(ru.ru_utime) + t(ru.ru_stime)
}

fn strs(v: &[u128]) -> Vec<String> {
    v.iter().map(ToString::to_string).collect()
}

fn wgpu_client() -> Result<(cubecl::prelude::ComputeClient<Wgpu>, String)> {
    let ctx = CubeclContext::new_default()?;
    let name = ctx.device_name();
    #[allow(irrefutable_let_patterns)]
    let CubeclContext::Wgpu { client, .. } = ctx else { unreachable!() };
    Ok((client, name))
}

/// Brute force of the same certificate, per n (join_proto's `verify`).
fn brute(base: &proto::Base, s: u128, e: u128, jp: JoinParams) -> (u64, Vec<u128>) {
    let bb = u128::from(base.b);
    let f0 = base.l - jp.t;
    let w_t = bb.pow(f0);
    let bk = bb.pow(jp.k);
    let roots: Vec<u128> = base.roots.iter().map(|&r| u128::from(r)).collect();
    let (mut matches, mut surv) = (0u64, Vec::new());
    for n in s..e {
        if !roots.contains(&(n % (bb - 1))) {
            continue;
        }
        let r = n % bk;
        let (mut x2, mut x3) = ((r * r) % bk, ((r * r) % bk * r) % bk);
        let mut bm = 0u64;
        let mut ok = true;
        for _ in 0..jp.k {
            for d in [x2 % bb, x3 % bb] {
                let bit = 1u64 << d;
                if bm & bit != 0 {
                    ok = false;
                }
                bm |= bit;
            }
            x2 /= bb;
            x3 /= bb;
        }
        if !ok {
            continue;
        }
        let p = n / w_t;
        let lo = (p * w_t).max(s);
        let hi = (p * w_t + w_t - 1).min(e - 1);
        let Some(tm) = base.cert(lo, hi, jp.k) else { continue };
        matches += 1;
        if tm & bm == 0 {
            surv.push(n);
        }
    }
    (matches, surv)
}

/// Exact, independent nice test (u128 schoolbook into base-b digit vectors).
fn exact_is_nice(n: u128, b: u32) -> bool {
    fn mul(a: &[u32], m: u128, b: u32) -> Vec<u32> {
        // a: base-b digits LSD first; returns a*m in base b
        let mut out = Vec::new();
        let mut carry: u128 = 0;
        for &d in a {
            let t = u128::from(d) * m + carry;
            out.push((t % u128::from(b)) as u32);
            carry = t / u128::from(b);
        }
        while carry > 0 {
            out.push((carry % u128::from(b)) as u32);
            carry /= u128::from(b);
        }
        out
    }
    let mut nd = Vec::new();
    let mut x = n;
    while x > 0 {
        nd.push((x % u128::from(b)) as u32);
        x /= u128::from(b);
    }
    let sq = mul(&nd, n, b);
    let cu = mul(&sq, n, b);
    let mut seen = vec![false; b as usize];
    for &d in sq.iter().chain(cu.iter()) {
        if seen[d as usize] {
            return false;
        }
        seen[d as usize] = true;
    }
    seen.iter().all(|&x| x)
}

/// The middle-digit prefilter by definition: n^2 and n^3's digits at
/// positions 0..k2-1 (computed mod b^k2 in u128) distinct, and disjoint from
/// n's top certificate when every certified position is >= k2.
fn mid_mirror(fs: &FieldSetup, n: u128) -> bool {
    let b = u128::from(fs.b);
    let bk = b.pow(fs.k2);
    let r = n % bk;
    let sq = r * r % bk;
    let cu = sq * r % bk;
    let p = n / fs.w;
    let a = (p * fs.w).max(fs.s);
    let ee = (p * fs.w + fs.w - 1).min(fs.e - 1);
    let mut seen = 0u64;
    // The host's seed rule: unclipped blocks use the field-wide floor bound.
    let floor = if a == p * fs.w && ee == p * fs.w + fs.w - 1 { fs.full_floor } else { fs.base.cert_floor(a, ee, fs.jp.k) };
    if floor >= fs.k2 {
        seen = fs.base.cert(a, ee, fs.jp.k).expect("a survivor's top is certified");
    }
    let (mut x2, mut x3) = (sq, cu);
    for _ in 0..fs.k2 {
        for d in [x2 % b, x3 % b] {
            let bit = 1u64 << d;
            if seen & bit != 0 {
                return false;
            }
            seen |= bit;
        }
        x2 /= b;
        x3 /= b;
    }
    true
}

/// GPU survivors, matches, device-rebuilt n and hits for `parts`, against
/// the CPU prototype on the same partitions.
fn verify(client: &cubecl::prelude::ComputeClient<Wgpu>, b: u32, s: u128, e: u128, jp: JoinParams, parts: Option<Vec<u32>>, do_brute: bool) -> Result<serde_json::Value> {
    let fs = FieldSetup::new(b, s, e, jp)?;
    let plist = parts.clone().unwrap_or_else(|| fs.all_parts());
    // CPU reference.
    let t0 = Instant::now();
    let base = proto::Base::new(b, s, e - 1);
    let mut cpu_surv = Vec::new();
    let p128: Option<Vec<u128>> = parts.as_ref().map(|v| v.iter().map(|&x| u128::from(x)).collect());
    let c = proto::join_range(&base, s, e, jp, p128.as_deref(), Some(&mut cpu_surv));
    cpu_surv.sort_unstable();
    let mut cpu_hits = c.hits.clone();
    cpu_hits.sort_unstable();
    let cpu_sec = t0.elapsed().as_secs_f64();
    // GPU.
    let t1 = Instant::now();
    let (pts, _) = run_host(&fs, &plist, 8);
    let nonempty: Vec<&PartTops> = pts.iter().filter(|p| !p.p.is_empty()).collect();
    let max_slots = (4_000_000 / fs.bp_r.len()).clamp(1, 64);
    let est: u32 = u32::try_from((c.survivors + 1024).next_power_of_two()).unwrap_or(1 << 26).clamp(1 << 12, 1 << 26);
    let mut dev = JoinDevice::<Wgpu>::new(client, &fs, max_slots, est, est)?;
    let max_slots = dev.max_slots();
    if dev.devtops.is_some() {
        let mut r = verify_devtops(&mut dev, &fs, &plist, &pts, &cpu_surv, c.matches, &cpu_hits, t1)?;
        if do_brute {
            let (bm, bs) = brute(&base, s, e, jp);
            let bok = bs == cpu_surv && bm == c.matches - c.out_of_range;
            r["brute_matches"] = json!(bm);
            r["brute_survivors"] = json!(bs.len());
            r["brute_equal"] = json!(bok);
            r["exact"] = json!(r["exact"].as_bool().unwrap_or(false) && bok);
        }
        return Ok(r);
    }
    let mut gpu_surv = Vec::new();
    let mut gpu_list2 = Vec::new();
    let mut gpu_matches = 0u64;
    let mut batches = 0;
    for ch in nonempty.chunks(max_slots) {
        let rec = dev.launch_batch(ch, CheckMode::Probe, true, true)?;
        gpu_surv.extend(dev.read_survivors(&rec)?);
        if dev.mid() > 0 {
            gpu_list2.extend(dev.read_list2(&rec)?);
        }
        gpu_matches += dev.read_matches(&rec)?;
        batches += 1;
    }
    gpu_surv.sort_unstable();
    gpu_list2.sort_unstable();
    // Host mirror of the middle-digit prefilter on the CPU survivors, by
    // exact integer arithmetic (u128), not by the kernel's digit arrays.
    let mirror: Vec<u128> = if dev.mid() > 0 {
        cpu_surv.iter().copied().filter(|&n| mid_mirror(&fs, n)).collect()
    } else {
        cpu_surv.clone()
    };
    if dev.mid() == 0 {
        gpu_list2 = gpu_surv.clone();
    }
    let probe_n = dev.read_hits()?; // every n the check kernel rebuilt
    dev.reset_hits();
    for ch in nonempty.chunks(max_slots) {
        let _ = dev.launch_batch(ch, CheckMode::Check, false, false)?;
    }
    let gpu_hits = dev.read_hits()?;
    let gpu_sec = t1.elapsed().as_secs_f64();
    let hits_exact = gpu_hits.iter().all(|&n| exact_is_nice(n, b) && nice_common::client_process::get_is_nice(n, b));
    let mut out = json!({
        "base": b, "start": s.to_string(), "end": e.to_string(), "t": jp.t, "k": jp.k, "p": jp.p,
        "parts": plist.len(), "batches": batches, "wide": dev.wide,
        "cpu_survivors": cpu_surv.len(), "gpu_survivors": gpu_surv.len(),
        "cpu_matches": c.matches, "gpu_matches": gpu_matches, "cpu_out_of_range": c.out_of_range,
        "survivors_equal": cpu_surv == gpu_surv, "matches_equal": c.matches == gpu_matches,
        "mid": dev.mid(), "prefilter_survivors": gpu_list2.len(), "prefilter_equal_mirror": gpu_list2 == mirror,
        "device_rebuilt_n_equal": probe_n == mirror,
        "cpu_hits": strs(&cpu_hits), "gpu_hits": strs(&gpu_hits), "hits_equal": cpu_hits == gpu_hits,
        "hits_exact_verified": hits_exact, "cpu_sec": cpu_sec, "gpu_sec": gpu_sec,
    });
    let mut exact = cpu_surv == gpu_surv && c.matches == gpu_matches && gpu_list2 == mirror && probe_n == mirror && cpu_hits == gpu_hits && hits_exact;
    if do_brute {
        let (bm, bs) = brute(&base, s, e, jp);
        out["brute_matches"] = json!(bm);
        out["brute_survivors"] = json!(bs.len());
        let bok = bs == gpu_surv && bm == c.matches - c.out_of_range;
        out["brute_equal"] = json!(bok);
        exact &= bok;
    }
    out["exact"] = json!(exact);
    Ok(out)
}

/// Device-tops verification: the device's certified tops per partition must
/// equal the host's, then survivors, matches, prefilter list, rebuilt n and
/// hits as in [`verify`].
#[allow(clippy::too_many_arguments)]
fn verify_devtops(dev: &mut JoinDevice<Wgpu>, fs: &FieldSetup, plist: &[u32], pts: &[PartTops], cpu_surv: &[u128], cpu_matches: u64, cpu_hits: &[u128], t1: Instant) -> Result<serde_json::Value> {
    let ms = dev.max_slots();
    let (mut tops_equal, mut ntops) = (true, 0usize);
    let (mut gpu_surv, mut gpu_list2, mut gpu_matches) = (Vec::new(), Vec::new(), 0u64);
    for (ci, ch) in plist.chunks(ms).enumerate() {
        let d = dev.launch_batch_dev(ch, CheckMode::Probe, true)?;
        let dt = dev.read_dev_tops(&d)?;
        for (j, slot_tops) in dt.iter().enumerate() {
            let pt = &pts[ci * ms + j];
            let mut host: Vec<(u64, u64, u32, u32, u32, u32)> =
                (0..pt.p.len()).map(|i| (pt.p[i], pt.m[i], pt.rlo[i], pt.rhi[i], pt.x[2 * i], pt.x[2 * i + 1])).collect();
            host.sort_unstable();
            ntops += host.len();
            tops_equal &= &host == slot_tops;
        }
        gpu_surv.extend(dev.read_dev_survivors(&d, false)?);
        if dev.mid() > 0 {
            gpu_list2.extend(dev.read_dev_survivors(&d, true)?);
        }
        gpu_matches += dev.read_dev_matches(&d)?;
    }
    gpu_surv.sort_unstable();
    gpu_list2.sort_unstable();
    let mirror: Vec<u128> = if dev.mid() > 0 { cpu_surv.iter().copied().filter(|&n| mid_mirror(fs, n)).collect() } else { cpu_surv.to_vec() };
    if dev.mid() == 0 {
        gpu_list2 = gpu_surv.clone();
    }
    let probe_n = dev.read_hits()?;
    dev.reset_hits();
    for ch in plist.chunks(ms) {
        let _ = dev.launch_batch_dev(ch, CheckMode::Check, false)?;
    }
    let gpu_hits = dev.read_hits()?;
    let hits_exact = gpu_hits.iter().all(|&n| exact_is_nice(n, fs.b) && nice_common::client_process::get_is_nice(n, fs.b));
    let exact = tops_equal && gpu_surv == cpu_surv && gpu_matches == cpu_matches && gpu_list2 == mirror && probe_n == mirror
        && gpu_hits == cpu_hits && hits_exact;
    Ok(json!({
        "base": fs.b, "start": fs.s.to_string(), "end": fs.e.to_string(), "t": fs.jp.t, "k": fs.jp.k, "p": fs.jp.p,
        "parts": plist.len(), "devtops": true, "tops": ntops, "tops_equal": tops_equal, "wide": dev.wide,
        "cpu_survivors": cpu_surv.len(), "gpu_survivors": gpu_surv.len(), "cpu_matches": cpu_matches, "gpu_matches": gpu_matches,
        "survivors_equal": gpu_surv == cpu_surv, "matches_equal": gpu_matches == cpu_matches,
        "mid": dev.mid(), "prefilter_survivors": gpu_list2.len(), "prefilter_equal_mirror": gpu_list2 == mirror,
        "device_rebuilt_n_equal": probe_n == mirror, "cpu_hits": strs(cpu_hits), "gpu_hits": strs(&gpu_hits),
        "hits_equal": gpu_hits == cpu_hits, "hits_exact_verified": hits_exact, "gpu_sec": t1.elapsed().as_secs_f64(), "exact": exact,
    }))
}

fn stats_json(st: &RunStats) -> serde_json::Value {
    json!({"parts": st.parts, "nonempty_parts": st.nonempty_parts, "batches": st.batches, "tops": st.tops,
        "top_calls": st.top_calls, "survivors": st.survivors, "mid_survivors": st.mid_survivors, "hits": strs(&st.hits),
        "host_cpu_secs": st.host_cpu_secs, "host_wall": st.host_wall, "device_wall": st.device_wall,
        "dispatch_secs": st.dispatch_secs, "device_wait": st.device_wait, "host_wait": st.host_wait, "wall": st.wall})
}

/// The client's own CubeCL niceonly pipeline on `pieces`, pushed back to back
/// as consecutive fields (the continuous pipeline, `fields_in_flight` open).
fn client_pipeline(ctx: &CubeclContext, base: u32, pieces: &[FieldSize]) -> Result<serde_json::Value> {
    let lookahead = fields_in_flight().saturating_sub(1);
    let t = Instant::now();
    let c0 = cpu_secs();
    let mut finish_times: Vec<f64> = Vec::new();
    let mut queued = 0usize;
    let mut hits = Vec::new();
    let (mut msd, mut ranges, mut valid, mut cpu_wait, mut dev_wait) = (0.0, 0usize, 0u64, 0.0, 0.0);
    let mut floors = Vec::new();
    let mut take = |ctx: &CubeclContext, hits: &mut Vec<u128>| -> Result<()> {
        let (res, st) = finish_niceonly_cubecl(ctx)?;
        hits.extend(res.nice_numbers.iter().map(|n| n.number));
        msd += st.msd_secs;
        ranges += st.num_ranges;
        valid += st.valid_numbers;
        cpu_wait += st.cpu_wait_secs;
        dev_wait += st.device_wait_secs;
        floors.push(st.floor);
        finish_times.push(t.elapsed().as_secs_f64());
        Ok(())
    };
    for f in pieces {
        match begin_niceonly_cubecl(ctx, f, base)? {
            NiceonlyStarted::Queued => queued += 1,
            NiceonlyStarted::Immediate(r) => hits.extend(r.nice_numbers.iter().map(|n| n.number)),
        }
        while queued > lookahead {
            take(ctx, &mut hits)?;
            queued -= 1;
        }
    }
    while queued > 0 {
        take(ctx, &mut hits)?;
        queued -= 1;
    }
    let wall = t.elapsed().as_secs_f64();
    let cpu = cpu_secs() - c0;
    let n: u128 = pieces.iter().map(FieldSize::size).sum();
    Ok(json!({
        "wall": wall, "cpu_secs": cpu, "finish_times": finish_times, "numbers": n.to_string(), "rate": n as f64 / wall,
        "msd_secs_sum": msd, "ranges": ranges, "valid_numbers": valid,
        "cpu_wait": cpu_wait, "device_wait": dev_wait,
        "floor_end": msd_floor_in_use().to_string(),
        "floor_min": floors.iter().min().map(ToString::to_string),
        "floor_max": floors.iter().max().map(ToString::to_string),
        "hits": strs(&hits),
    }))
}

fn main() -> Result<()> {
    env_logger::init();
    let a: Vec<String> = std::env::args().collect();
    match a[1].as_str() {
        "verify" | "verify-parts" => {
            let (b, s, e): (u32, u128, u128) = (arg(&a, 2), arg(&a, 3), arg(&a, 4));
            let jp = JoinParams { t: arg(&a, 5), k: arg(&a, 6), p: arg(&a, 7) };
            let (client, name) = wgpu_client()?;
            let (parts, brute) = if a[1] == "verify" {
                (None, e - s <= 3_000_000)
            } else {
                let (np, mut seed): (usize, u64) = (arg(&a, 8), arg(&a, 9));
                let nv = u64::from(b).pow(jp.p);
                let mut v: Vec<u32> = (0..np).map(|_| (splitmix(&mut seed) % nv) as u32).collect();
                v.sort_unstable();
                v.dedup();
                (Some(v), false)
            };
            let mut r = verify(&client, b, s, e, jp, parts.clone(), brute)?;
            r["mode"] = json!(a[1]);
            r["device"] = json!(name);
            if let Some(p) = parts {
                r["part_values"] = json!(p);
            }
            println!("{r}");
        }
        "field" | "field-full" => {
            let (b, s, e): (u32, u128, u128) = (arg(&a, 2), arg(&a, 3), arg(&a, 4));
            let jp = JoinParams { t: arg(&a, 5), k: arg(&a, 6), p: arg(&a, 7) };
            let full = a[1] == "field-full";
            let (nthreads, slots): (usize, usize) = if full { (arg(&a, 8), arg(&a, 9)) } else { (arg(&a, 10), arg(&a, 11)) };
            let (client, name) = wgpu_client()?;
            let t0 = Instant::now();
            let fs = FieldSetup::new(b, s, e, jp)?;
            let setup_sec = t0.elapsed().as_secs_f64();
            let nv = fs.nparts as u64;
            let parts: Vec<u32> = if full {
                fs.all_parts()
            } else {
                let (np, mut seed): (usize, u64) = (arg(&a, 8), arg(&a, 9));
                (0..np).map(|_| (splitmix(&mut seed) % nv) as u32).collect()
            };
            let mut dev = JoinDevice::<Wgpu>::new(&client, &fs, slots, 1 << 25, 1 << 10)?;
            let pol = BatchPolicy { max_slots: dev.max_slots(), max_tops: usize::MAX, inflight: 4 };
            // Warm-up: kernel JIT on first launch, untimed.
            let tw = Instant::now();
            let devtops = dev.devtops.is_some();
            if devtops {
                let _ = run_devtops(&mut dev, &parts[..1], pol)?;
            } else {
                let (warm, _) = run_host(&fs, &parts[..1], 1);
                let _ = run_device(&mut dev, &warm, pol)?;
            }
            let warm_sec = tw.elapsed().as_secs_f64();
            let mut out = json!({"mode": a[1], "device": name, "base": b, "start": s.to_string(), "end": e.to_string(),
                "t": jp.t, "k": jp.k, "p": jp.p, "L": fs.l, "nparts_field": nv, "npart": parts.len(),
                "nthreads": nthreads, "slots": dev.max_slots(), "wide": dev.wide, "kernel": dev.kernel, "mid": dev.mid(),
                "ept": std::env::var("JOIN_EPT").ok(), "nbp": fs.bp_r.len(),
                "tlay": fs.tlay.len(), "sec_tlay": fs.sec_tlay, "sec_bpre": fs.sec_bpre, "setup_sec": setup_sec, "warm_sec": warm_sec});
            let scale = nv as f64 / parts.len() as f64;
            out["devtops"] = json!(devtops);
            if devtops {
                let c1 = cpu_secs();
                let pst = run_devtops(&mut dev, &parts, pol)?;
                let cpu = cpu_secs() - c1;
                out["pipelined_cpu"] = json!(cpu);
                out["est_field_pipelined_cpu"] = json!(fs.sec_tlay + fs.sec_bpre + scale * cpu);
                out["est_field_pipelined_sec"] = json!(setup_sec + scale * pst.wall);
                out["est_field_device_sec"] = json!(scale * pst.wall);
                out["est_field_host_cpu_sec"] = json!(fs.sec_tlay + fs.sec_bpre + scale * cpu);
                out["est_field_survivors"] = json!(scale * pst.survivors as f64);
                out["pipelined"] = stats_json(&pst);
                ensure!(pst.hits.iter().all(|&n| exact_is_nice(n, b)), "a reported hit fails the exact check");
                println!("{out}");
                return Ok(());
            }
            if !full {
                let c0 = cpu_secs();
                let (pts, host_wall) = run_host(&fs, &parts, nthreads);
                out["host_phase_cpu"] = json!(cpu_secs() - c0);
                let mut dst = run_device(&mut dev, &pts, pol)?;
                dst.host_wall = host_wall;
                drop(pts);
                out["host_phase_wall"] = json!(host_wall);
                out["device_phase"] = stats_json(&dst);
                out["est_field_host_cpu_sec"] = json!(fs.sec_tlay + fs.sec_bpre + scale * dst.host_cpu_secs);
                out["est_field_device_sec"] = json!(scale * dst.device_wall);
                out["est_field_survivors"] = json!(scale * dst.survivors as f64);
            }
            let c1 = cpu_secs();
            let pst = run_pipelined(&mut dev, &fs, &parts, nthreads, pol)?;
            out["pipelined_cpu"] = json!(cpu_secs() - c1);
            out["est_field_pipelined_cpu"] = json!(fs.sec_tlay + fs.sec_bpre + scale * (cpu_secs() - c1));
            out["est_field_pipelined_sec"] = json!(setup_sec + scale * pst.wall);
            out["pipelined"] = stats_json(&pst);
            ensure!(pst.hits.iter().all(|&n| exact_is_nice(n, b)), "a reported hit fails the exact check");
            out["profile_us"] = json!(overlap_join_gpu::join_gpu::PROFILE_US.iter().map(|x| x.load(std::sync::atomic::Ordering::Relaxed)).collect::<Vec<_>>());
            println!("{out}");
        }
        "client-range" => {
            let (b, s, e): (u32, u128, u128) = (arg(&a, 2), arg(&a, 3), arg(&a, 4));
            let ctx = CubeclContext::new_default()?;
            let r = client_pipeline(&ctx, b, &[FieldSize::new(s, e)])?;
            println!("{}", json!({"mode": "client-range", "device": ctx.device_name(), "base": b,
                "start": s.to_string(), "end": e.to_string(), "res": r}));
        }
        // client-strat B S E STRATA PIECE SEED: one random aligned PIECE-sized
        // piece in each of STRATA equal strata of [S, E) (stratified sample),
        // after two untimed warm-up pieces that let the floor controller settle.
        "client-strat" => {
            let (b, s, e): (u32, u128, u128) = (arg(&a, 2), arg(&a, 3), arg(&a, 4));
            let (strata, piece, mut seed): (u128, u128, u64) = (arg(&a, 5), arg(&a, 6), arg(&a, 7));
            let ctx = CubeclContext::new_default()?;
            let width = (e - s) / strata;
            let per = width / piece;
            let pieces: Vec<FieldSize> = (0..strata)
                .map(|i| {
                    let c = u128::from(splitmix(&mut seed)) % per;
                    let st = s + i * width + c * piece;
                    FieldSize::new(st, st + piece)
                })
                .collect();
            let warm_pieces = [FieldSize::new(s, s + piece), FieldSize::new(s + width, s + width + piece)];
            let warm = client_pipeline(&ctx, b, &warm_pieces)?;
            let r = client_pipeline(&ctx, b, &pieces)?;
            let sampled = (strata * piece) as f64;
            println!("{}", json!({"mode": "client-strat", "device": ctx.device_name(), "base": b,
                "start": s.to_string(), "end": e.to_string(), "strata": strata.to_string(), "piece": piece.to_string(),
                "warm_wall": warm["wall"], "res": r,
                "est_field_sec": r["wall"].as_f64().unwrap() / sampled * (e - s) as f64,
                "est_field_cpu": r["cpu_secs"].as_f64().unwrap() / sampled * (e - s) as f64,
                "fields_in_flight": fields_in_flight(), "workers": std::thread::available_parallelism().map_or(0, std::num::NonZero::get)}));
        }
        // cpu-client B S E CHUNK NSAMP SEED NTHREADS: the client's own CPU path
        // (process_range_niceonly, stride k = 3, MSD floor 8000) on NSAMP random
        // aligned CHUNK pieces, NTHREADS at once (the client binary's rayon
        // parallelism over chunks); wall and CPU seconds scaled to the field.
        "cpu-client" => {
            let (b, s, e): (u32, u128, u128) = (arg(&a, 2), arg(&a, 3), arg(&a, 4));
            let (chunk, nsamp, mut seed, nth): (u128, usize, u64, usize) = (arg(&a, 5), arg(&a, 6), arg(&a, 7), arg(&a, 8));
            let table = nice_common::stride_filter::StrideTable::new(b, 3);
            let nch = (e - s) / chunk;
            let pieces: Vec<FieldSize> = (0..nsamp)
                .map(|_| {
                    let c = u128::from(splitmix(&mut seed)) % nch;
                    FieldSize::new(s + c * chunk, s + (c + 1) * chunk)
                })
                .collect();
            let next = std::sync::atomic::AtomicUsize::new(0);
            let c0 = cpu_secs();
            let t0 = Instant::now();
            let hits: Vec<u128> = std::thread::scope(|sc| {
                let hs: Vec<_> = (0..nth)
                    .map(|_| {
                        sc.spawn(|| {
                            let mut h = Vec::new();
                            loop {
                                let i = next.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                                if i >= pieces.len() {
                                    break;
                                }
                                let r = nice_common::client_process::process_range_niceonly(&pieces[i], b, &table);
                                h.extend(r.nice_numbers.iter().map(|n| n.number));
                            }
                            h
                        })
                    })
                    .collect();
                hs.into_iter().flat_map(|h| h.join().unwrap()).collect()
            });
            let wall = t0.elapsed().as_secs_f64();
            let cpu = cpu_secs() - c0;
            let scale = (e - s) as f64 / (nsamp as f64 * chunk as f64);
            println!("{}", json!({"mode": "cpu-client", "base": b, "start": s.to_string(), "end": e.to_string(), "chunk": chunk.to_string(),
                "nsamp": nsamp, "nthreads": nth, "wall": wall, "cpu": cpu, "est_field_sec": wall * scale, "est_field_cpu": cpu * scale, "hits": strs(&hits)}));
        }
        // cpu-join B S E T K P NPART SEED NTHREADS: the CPU prototype join
        // (proto.rs = join-proto) on NPART random partitions, NTHREADS at once
        // (one partition per thread at a time); the per-field top layer once.
        "cpu-join" => {
            let (b, s, e): (u32, u128, u128) = (arg(&a, 2), arg(&a, 3), arg(&a, 4));
            let jp = JoinParams { t: arg(&a, 5), k: arg(&a, 6), p: arg(&a, 7) };
            let (np, mut seed, nth): (usize, u64, usize) = (arg(&a, 8), arg(&a, 9), arg(&a, 10));
            let base = proto::Base::new(b, s, e - 1);
            let nv = u128::from(b).pow(jp.p);
            let parts: Vec<u128> = (0..np).map(|_| u128::from(splitmix(&mut seed)) % nv).collect();
            // Setup cost (top layer, bpre) once per field: a zero-partition run.
            let t0 = Instant::now();
            let c0 = cpu_secs();
            let _ = proto::join_range(&base, s, e, jp, Some(&[]), None);
            let setup_wall = t0.elapsed().as_secs_f64();
            let next = std::sync::atomic::AtomicUsize::new(0);
            let c1 = cpu_secs();
            let t1 = Instant::now();
            let (hits, surv): (Vec<u128>, u64) = std::thread::scope(|sc| {
                let hs: Vec<_> = (0..nth)
                    .map(|_| {
                        sc.spawn(|| {
                            let mut h = Vec::new();
                            let mut sv = 0u64;
                            loop {
                                let i = next.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                                if i >= parts.len() {
                                    break;
                                }
                                let c = proto::join_range(&base, s, e, jp, Some(&parts[i..=i]), None);
                                h.extend(c.hits);
                                sv += c.survivors;
                            }
                            (h, sv)
                        })
                    })
                    .collect();
                hs.into_iter().map(|h| h.join().unwrap()).fold((Vec::new(), 0), |(mut a, n), (h, sv)| { a.extend(h); (a, n + sv) })
            });
            let wall = t1.elapsed().as_secs_f64();
            let cpu = cpu_secs() - c1;
            // Each partition run above also rebuilds the top layer; subtract it.
            let scale = nv as f64 / np as f64;
            let setup_cpu = c1 - c0;
            let part_wall = (wall - setup_wall * np as f64 / nth as f64).max(0.0);
            let part_cpu = (cpu - setup_cpu * np as f64).max(0.0);
            println!("{}", json!({"mode": "cpu-join", "base": b, "start": s.to_string(), "end": e.to_string(), "t": jp.t, "k": jp.k, "p": jp.p,
                "npart": np, "nthreads": nth, "setup_wall": setup_wall, "wall": wall, "cpu": cpu,
                "est_field_sec": setup_wall + scale * part_wall, "est_field_cpu": setup_cpu + scale * part_cpu,
                "est_field_survivors": scale * surv as f64, "hits": strs(&hits)}));
        }
        "client-sample" => {
            let (b, s, e): (u32, u128, u128) = (arg(&a, 2), arg(&a, 3), arg(&a, 4));
            let (piece, np, mut seed): (u128, usize, u64) = (arg(&a, 5), arg(&a, 6), arg(&a, 7));
            let ctx = CubeclContext::new_default()?;
            let nch = (e - s) / piece;
            let pieces: Vec<FieldSize> = (0..np)
                .map(|_| {
                    let c = u128::from(splitmix(&mut seed)) % nch;
                    FieldSize::new(s + c * piece, s + (c + 1) * piece)
                })
                .collect();
            let warm = client_pipeline(&ctx, b, &pieces[..1])?;
            let r = client_pipeline(&ctx, b, &pieces)?;
            println!("{}", json!({"mode": "client-sample", "device": ctx.device_name(), "base": b,
                "start": s.to_string(), "end": e.to_string(), "piece": piece.to_string(), "npiece": np,
                "warm_wall": warm["wall"], "res": r,
                "est_field_sec": r["wall"].as_f64().unwrap() / (np as f64 * piece as f64) * (e - s) as f64}));
        }
        m => anyhow::bail!("unknown mode {m}"),
    }
    Ok(())
}
