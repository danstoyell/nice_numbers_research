#!/usr/bin/env python3
"""Validate the two ingredients of the base 57-64 comparison on the testbed.

1. Join model (model_gain.join_cost with S = N) against the measured join
   with the digit-sum filter (join_ds_testbed.json), component by component,
   on the nice testbed bases, at the measured (t, k).
2. Client sampling estimator (sample_client.py, stratified random chunks)
   against the exact full-interval client run (client_testbed.json) on
   nice bases 34, 38 and 40 (same chunk 1e6 and floor 8000 as the testbed).
Output: validation.json and printed ratios (measured / model or estimate / exact).
"""
import json
import math
from pathlib import Path

import model_gain as mg

HERE = Path(__file__).resolve().parent


def main():
    out = {"join_model": [], "client_sampling": []}
    jd = json.loads((HERE / "join_ds_testbed.json").read_text()) if (HERE / "join_ds_testbed.json").exists() else {}
    mcs = json.loads((HERE / "join_mc.json").read_text()) if (HERE / "join_mc.json").exists() else {}
    print("Join rates vs measured join + digit-sum, ratio measured/model (lookups = |T| x classes here)")
    for name, r in sorted(jd.items(), key=lambda kv: kv[1]["base"]):
        if r["mult"] != 1:
            continue
        info = mg.base_info(r["base"])
        srcs = {"analytic": mg.AnalyticRates(info)}
        if str(r["base"]) in mcs:
            srcs["mc"] = mg.MCRates(info, mcs[str(r["base"])])
        for run in r["runs"]:
            meas = {"top_calls": run["top_calls"], "bottom_calls": run["bottom_calls"], "lookups": run["lookups"],
                    "matches": run["matches"], "survivors": run["survivors"]}
            for sname, R in srcs.items():
                m = mg.join_cost(info, R, info["N"], run["t"], run["k"])
                if m is None:
                    continue
                m = dict(m, lookups=m["T"] * info["roots"])
                comp = ("top_calls", "bottom_calls", "lookups", "matches", "survivors")
                m["total"] = sum(m[k] for k in comp)
                meas["total"] = sum(meas[k] for k in comp)
                ratio = {k: meas[k] / m[k] if m[k] else None for k in meas}
                out["join_model"].append({"case": name, "rates": sname, "t": run["t"], "k": run["k"], "measured": meas,
                                          "model": {k: m[k] for k in meas}, "ratio": ratio})
                print(f"  {name} (t,k)=({run['t']},{run['k']}) {sname:>8}: " + " ".join(
                    f"{k}={v:.2f}" for k, v in ratio.items() if v is not None))
    cl = json.loads((HERE / "client_testbed.json").read_text())
    sm = json.loads((HERE / "client_sample.json").read_text()) if (HERE / "client_sample.json").exists() else {}
    print("Client sampling estimate vs exact run, ratio estimate/exact")
    for b in (34, 38, 40):
        s, e = sm.get(f"{b}:cpu1e6"), cl.get(f"nice-{b}@8000")
        if not s or not e:
            continue
        N = e["N"]
        est = {k: s["per_n"][k] * N for k in ("analyses", "visits", "full_checks")}
        est["ops"] = s["total_ops"]
        ratio = {k: est[k] / e[k] for k in est}
        out["client_sampling"].append({"base": b, "nsamples": s["nsamples"], "rel_se": s["rel_se_ops"],
                                       "estimate": est, "exact": {k: e[k] for k in est}, "ratio": ratio})
        print(f"  b={b} (n={s['nsamples']}, se {100 * s['rel_se_ops']:.1f}%): " + " ".join(f"{k}={v:.3f}" for k, v in ratio.items()))
    (HERE / "validation.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
