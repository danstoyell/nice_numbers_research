//! Cross-check of client_count.c against the real client library (unmodified
//! nice_common, commit fe1b0b8): runs the client's own MSD masked recursion,
//! stride table and seeded nice check, counting what process_range_niceonly
//! does, over a list of chunks.
//! Usage: d5_crosscheck BASE FLOOR CHUNK START END   (process [START,END) in CHUNK pieces)
use nice_common::FieldSize;
use nice_common::client_process::get_is_nice_with_known_lsd;
use nice_common::msd_prefix_filter::{MaskedRecursion, get_valid_ranges_recursive_masked, MSD_RECURSIVE_MAX_DEPTH};
use nice_common::stride_filter::StrideTable;

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let base: u32 = a[1].parse().unwrap();
    let floor: u128 = a[2].parse().unwrap();
    let chunk: u128 = a[3].parse().unwrap();
    let start: u128 = a[4].parse().unwrap();
    let end: u128 = a[5].parse().unwrap();
    let k = 3u32;
    let t = StrideTable::new(base, k);
    let params = MaskedRecursion { base, fixed_lsd_k: k as usize, max_depth: MSD_RECURSIVE_MAX_DEPTH, min_range_size: floor, subdivision_factor: 2 };
    let (mut leaves, mut leaf_n, mut visits, mut rej, mut full, mut hits) = (0u64, 0u128, 0u64, 0u64, 0u64, Vec::new());
    let mut cert_sum = 0f64;
    let mut s = start;
    while s < end {
        let e = (s + chunk).min(end);
        let mut out = Vec::new();
        get_valid_ranges_recursive_masked(FieldSize::new(s, e), &params, 0, 0, &mut out);
        for (r, high) in out {
            leaves += 1; leaf_n += r.size();
            let (mut n, mut idx) = t.first_valid_at_or_after(r.start());
            let v0 = visits;
            while n < r.end() {
                visits += 1;
                if t.low_digit_masks[idx] & high != 0 { rej += 1; }
                else {
                    full += 1;
                    if get_is_nice_with_known_lsd(n, base, k, t.low_digit_masks[idx]) { hits.push(n); }
                }
                n += u128::from(t.gap_table[idx]);
                idx += 1; if idx == t.gap_table.len() { idx = 0; }
            }
            cert_sum += (visits - v0) as f64 * f64::from(high.count_ones());
        }
        s = e;
    }
    println!("{{\"base\":{base},\"floor\":{floor},\"chunk\":{chunk},\"start\":{start},\"end\":{end},\"stride_residues\":{},\"leaves\":{leaves},\"leaf_n\":{leaf_n},\"visits\":{visits},\"mask_rejects\":{rej},\"full_checks\":{full},\"cert_per_visit\":{:.4},\"hits\":{:?}}}",
        t.valid_residues.len(), if visits > 0 { cert_sum / visits as f64 } else { 0.0 }, hits);
}
