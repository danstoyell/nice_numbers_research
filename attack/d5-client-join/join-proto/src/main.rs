//! join_proto modes (single thread; one JSON line out):
//!   verify B S E T K P        exactness: join survivors and matches == brute force on [S,E)
//!   full   B S E T K P        whole range, all partitions: hits and counters
//!   field  B S E T K P NPART SEED
//!                             range [S,E) (e.g. a 1e14 production field), top layer once,
//!                             NPART random partitions of b^P; extrapolated per-field cost
//!   client B S E CHUNK NSAMP SEED
//!                             the client's own process_range_niceonly (nice_common, k = 3
//!                             stride table) on NSAMP random aligned CHUNK-sized pieces of [S,E)
use join_proto::{Base, Counters, JoinParams, join_range};
use nice_common::FieldSize;
use nice_common::client_process::process_range_niceonly;
use nice_common::stride_filter::StrideTable;
use std::time::Instant;

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

fn ctr_json(c: &Counters) -> String {
    format!(
        "\"top_calls\":{},\"tlay_calls\":{},\"bpre_calls\":{},\"tlay\":{},\"tops\":{},\"bottom_calls\":{},\"bottoms\":{},\"lookups\":{},\"matches\":{},\"out_of_range\":{},\"survivors\":{},\"partitions\":{},\"sec_tlay\":{:.4},\"sec_bottom\":{:.4},\"sec_top_ext\":{:.4},\"sec_join\":{:.4},\"hits\":{:?}",
        c.top_calls, c.tlay_calls, c.bpre_calls, c.tlay, c.tops, c.bottom_calls, c.bottoms, c.lookups, c.matches, c.out_of_range, c.survivors, c.partitions,
        c.sec_tlay, c.sec_bottom, c.sec_top_ext, c.sec_join, c.hits
    )
}

fn digits(mut x: u128, b: u128, n: usize) -> Vec<u128> {
    let mut v = Vec::with_capacity(n);
    for _ in 0..n {
        v.push(x % b);
        x /= b;
    }
    v
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let mode = a[1].as_str();
    let b: u32 = arg(&a, 2);
    let s: u128 = arg(&a, 3);
    let e: u128 = arg(&a, 4);
    match mode {
        "verify" | "full" | "field" => {
            let jp = JoinParams { t: arg(&a, 5), k: arg(&a, 6), p: arg(&a, 7) };
            let base = Base::new(b, s, e - 1);
            if mode == "field" {
                let npart: usize = arg(&a, 8);
                let mut seed: u64 = arg(&a, 9);
                let nv = (b as u128).pow(jp.p);
                let parts: Vec<u128> = (0..npart).map(|_| (splitmix(&mut seed) as u128) % nv).collect();
                let t0 = Instant::now();
                let c = join_range(&base, s, e, jp, Some(&parts), None);
                let wall = t0.elapsed().as_secs_f64();
                let scale = nv as f64 / npart as f64;
                let per_field_sec = c.sec_tlay + scale * (c.sec_bottom + c.sec_top_ext + c.sec_join);
                let est_top = c.tlay_calls as f64 + scale * (c.top_calls - c.tlay_calls) as f64;
                let est_bot = c.bpre_calls as f64 + scale * (c.bottom_calls - c.bpre_calls) as f64;
                println!(
                    "{{\"mode\":\"field\",\"base\":{b},\"L\":{},\"t\":{},\"k\":{},\"p\":{},\"start\":{s},\"end\":{e},\"npart\":{npart},\"scale\":{scale},\"wall\":{wall:.3},\"est_field_sec\":{per_field_sec:.3},\"est_top_calls\":{:.4e},\"est_bottom_calls\":{:.4e},\"est_lookups\":{:.4e},\"est_matches\":{:.4e},\"est_survivors\":{:.4e},{}}}",
                    base.l, jp.t, jp.k, jp.p,
                    est_top, est_bot, scale * c.lookups as f64, scale * c.matches as f64,
                    scale * c.survivors as f64, ctr_json(&c)
                );
                return;
            }
            let mut rec = Vec::new();
            let t0 = Instant::now();
            let c = join_range(&base, s, e, jp, None, Some(&mut rec));
            let wall = t0.elapsed().as_secs_f64();
            if mode == "full" {
                println!("{{\"mode\":\"full\",\"base\":{b},\"start\":{s},\"end\":{e},\"t\":{},\"k\":{},\"p\":{},\"wall\":{wall:.3},{}}}",
                         jp.t, jp.k, jp.p, ctr_json(&c));
                return;
            }
            // brute force
            let bb = b as u128;
            let l = base.l as usize;
            let f0 = l - jp.t as usize;
            let w_t = bb.pow(f0 as u32);
            let k = jp.k as usize;
            let (mut bf_matches, mut bf_surv) = (0u64, Vec::new());
            let roots: Vec<u128> = base.roots.iter().map(|&r| r as u128).collect();
            for n in s..e {
                if !roots.contains(&(n % (bb - 1))) {
                    continue;
                }
                // bottom
                let bk = bb.pow(k as u32);
                let r = n % bk;
                let d2 = digits((r * r) % bk, bb, k);
                let d3 = digits(((r * r) % bk * r) % bk, bb, k);
                let mut bm = 0u64;
                let mut ok = true;
                for &d in d2.iter().chain(d3.iter()) {
                    let bit = 1u64 << d;
                    if bm & bit != 0 {
                        ok = false;
                        break;
                    }
                    bm |= bit;
                }
                if !ok {
                    continue;
                }
                let p = n / w_t;
                let lo = (p * w_t).max(s);
                let hi = (p * w_t + w_t - 1).min(e - 1);
                let Some(tm) = base.cert(lo, hi, jp.k) else { continue };
                bf_matches += 1;
                if tm & bm == 0 {
                    bf_surv.push(n);
                }
            }
            rec.sort_unstable();
            let ok = rec == bf_surv && c.matches - c.out_of_range == bf_matches;
            println!("{{\"mode\":\"verify\",\"base\":{b},\"start\":{s},\"end\":{e},\"t\":{},\"k\":{},\"p\":{},\"exact\":{ok},\"join_survivors\":{},\"brute_survivors\":{},\"join_matches\":{},\"brute_matches\":{},\"wall\":{wall:.3},{}}}",
                     jp.t, jp.k, jp.p, rec.len(), bf_surv.len(), c.matches, bf_matches, ctr_json(&c));
        }
        "client" => {
            let chunk: u128 = arg(&a, 5);
            let nsamp: usize = arg(&a, 6);
            let mut seed: u64 = arg(&a, 7);
            let table = StrideTable::new(b, 3);
            let nch = (e - s) / chunk;
            let mut secs = 0.0;
            let mut hits = 0usize;
            for _ in 0..nsamp {
                let ci = (splitmix(&mut seed) as u128) % nch;
                let cs = s + ci * chunk;
                let r = FieldSize::new(cs, cs + chunk);
                let t0 = Instant::now();
                let res = process_range_niceonly(&r, b, &table);
                secs += t0.elapsed().as_secs_f64();
                hits += res.nice_numbers.len();
            }
            let per_n = secs / (nsamp as f64 * chunk as f64);
            println!("{{\"mode\":\"client\",\"base\":{b},\"start\":{s},\"end\":{e},\"chunk\":{chunk},\"nsamp\":{nsamp},\"sec\":{secs:.3},\"sec_per_n\":{per_n:.4e},\"est_field_sec\":{:.3},\"hits\":{hits}}}",
                     per_n * (e - s) as f64);
        }
        _ => panic!("unknown mode"),
    }
}
