#!/usr/bin/env python3
"""Search globally pandigital outputs formed by affine digit permutations.

For each base, arrange all digits as (a*j+c) mod b with gcd(a,b)=1, then
split into square and cube blocks of the necessary lengths. The complete
permutation property is automatic; only A^3=B^2 remains to test. A 64-bit
modular filter is necessary only, and survivors receive exact verification.
"""
import argparse
import json
import math
import time
from pathlib import Path
from verify import candidate_intervals,verify


def value(ds,b):
    result=0
    for d in ds: result=result*b+d
    return result


def check_rotations():
    mask=(1<<64)-1
    count=0
    for b in range(4,25):
        s=b//2;c=b-s
        for a in range(1,b):
            if math.gcd(a,b)!=1: continue
            word=[a*i%b for i in range(b)]
            A=value(word[:s],b)&mask;B=value(word[s:],b)&mask
            sp=pow(b,s-1,1<<64);cp=pow(b,c-1,1<<64)
            for r in range(b):
                rotated=word[r:]+word[:r]
                assert A==value(rotated[:s],b)&mask
                assert B==value(rotated[s:],b)&mask
                first,nextfirst=word[r],word[(r+s)%b]
                A=((A-first*sp)*b+nextfirst)&mask
                B=((B-nextfirst*cp)*b+first)&mask
                count+=1
    return count


def search(max_base):
    mask=(1<<64)-1
    rows=[];solutions=[]
    for b in range(2,max_base+1):
        intervals=candidate_intervals(b)
        if not intervals or b%4==3: continue
        assert len(intervals)==1
        s,c=intervals[0]['square_digits'],intervals[0]['cube_digits']
        sp=pow(b,s-1,1<<64);cp=pow(b,c-1,1<<64)
        tested,passed=0,0
        for a in range(1,b):
            if math.gcd(a,b)!=1: continue
            word=[a*i%b for i in range(b)]
            A=value(word[:s],b)&mask;B=value(word[s:],b)&mask
            for r in range(b):
                first,nextfirst=word[r],word[(r+s)%b]
                if first and nextfirst:
                    tested+=1
                    if ((A*A*A-B*B)&mask)==0:
                        passed+=1
                        rotated=word[r:]+word[:r]
                        x,y=value(rotated[:s],b),value(rotated[s:],b)
                        n=math.isqrt(x)
                        if n*n==x and n*n*n==y:
                            result=verify(n,b)
                            assert result['nice']
                            solutions.append(result|{'step':a,'offset':first})
                A=((A-first*sp)*b+nextfirst)&mask
                B=((B-nextfirst*cp)*b+first)&mask
        rows.append({'base':b,'square_length':s,'cube_length':c,
                     'leading_legal_permutations':tested,
                     'passed_mod_2_64':passed})
    return rows,solutions


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--max-base',type=int,default=300)
    ap.add_argument('--output',default='results/structured-outputs.json')
    args=ap.parse_args()
    started=time.monotonic()
    checks=check_rotations()
    rows,solutions=search(args.max_base)
    result={'family':'full output word (a*j+c) mod b, gcd(a,b)=1; square block first',
            'max_base':args.max_base,'rotation_validation_cases':checks,
            'permutations_tested':sum(x['leading_legal_permutations'] for x in rows),
            'modular_survivors':sum(x['passed_mod_2_64'] for x in rows),
            'seconds':time.monotonic()-started,'bases':rows,'solutions':solutions,
            'scope':'Exhaustive only within this affine-permutation output family in the listed bases'}
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='bases'}))


if __name__=='__main__':
    main()
