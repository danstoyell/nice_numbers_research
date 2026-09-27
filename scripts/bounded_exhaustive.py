#!/usr/bin/env python3
"""Reproduce a small finite complete search, not the public search frontier."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from verify import candidate_intervals,verify


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--max-base',type=int,default=30)
    ap.add_argument('--output',default='results/bounded-exhaustive.json')
    args=ap.parse_args()
    if not 2<=args.max_base<=30:
        ap.error('supported maximum base is 2..30')
    root=Path(__file__).resolve().parents[1]
    src=root/'scripts/bounded_exhaustive.cpp'
    binary=Path('/private/tmp/nicenumbers-bounded-exhaustive')
    build=['clang++','-O3','-std=c++17',str(src),'-o',str(binary)]
    subprocess.run(build,check=True)
    report={'scope':'Exhaustive for all integer bases 2 through max_base, using necessary-condition pruning',
            'max_base':args.max_base,'kernel_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
            'compiler':subprocess.check_output(['clang++','--version'],text=True).splitlines()[0],
            'build_command':build,'bases':[]}
    for base in range(2,args.max_base+1):
        intervals=candidate_intervals(base)
        if not intervals:
            rows=[{'base':base,'excluded':'empty exact digit-length interval'}]
        else:
            rows=[]
            for interval in intervals:
                command=[str(binary),str(base),str(interval['lo']),str(interval['hi'])]
                row=json.loads(subprocess.check_output(command,text=True))
                for n in row['solutions']:
                    assert verify(n,base)['nice']
                rows.append(row)
        report['bases'].extend(rows)
        Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(rows),flush=True)


if __name__=='__main__':
    main()
