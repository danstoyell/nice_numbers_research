#!/usr/bin/env python3
"""Construct non-solution witnesses against fixed-depth edge-filter proofs.

Every witness has the correct length, digit-sum congruence, and mutually
distinct first/last k digits of both powers. It is NOT claimed to be nice.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from verify import digits, verify


def convolve(a,b):
    c=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            c[i+j]+=x*y
    return c


def powers(a):
    square=convolve(a,a)
    return square,convolve(square,a)


def coefficients(k):
    prefix,suffix=[3],[2]
    used={9,27,4,8}
    for series in [prefix,suffix]:
        while len(series)<k:
            j=len(series)
            for a in range(1,2*len(used)+3):
                sq,cu=powers(series+[a])
                new={sq[j],cu[j]}
                if len(new)==2 and not used & new:
                    series.append(a)
                    used |= new
                    break
            else:
                raise AssertionError('finite forbidden-value bound failed')
    assert len(used)==4*k
    return prefix,suffix


def construct(k):
    prefix,suffix=coefficients(k)
    square,cube=powers(prefix)
    suffix_square,suffix_cube=powers(suffix)
    c=max(square+cube+suffix_square[:k]+suffix_cube[:k])
    threshold=max(2*(c+75)+1,10*k+12,max(prefix)+2,65)
    b=threshold+(2-threshold)%10
    q=(b-2)//5
    assert b%10==2 and q>=2*k+2
    n0=sum(a*b**(q-i) for i,a in enumerate(prefix))
    residue=sum(a*b**i for i,a in enumerate(suffix))
    modulus=b**k*(b-1)
    combined=residue+b**k*((-residue)%(b-1))
    n=combined+((n0-combined+modulus-1)//modulus)*modulus
    assert n0<=n<=n0+b**(q-k)
    ds,dc=digits(n*n,b),digits(n*n*n,b)
    edges=ds[:k]+dc[:k]+ds[-k:]+dc[-k:]
    assert len(edges)==len(set(edges))==4*k
    assert ds[:k]==square[:k] and dc[:k]==cube[:k]
    assert len(ds)+len(dc)==b
    assert n%(b-1)==0
    if hasattr(sys,'set_int_max_str_digits'):
        sys.set_int_max_str_digits(0)
    ns=str(n)
    return {
        'k':k,'base':b,'n':ns,'n_sha256':hashlib.sha256(ns.encode()).hexdigest(),
        'n_decimal_digits':len(ns),'prefix_root_coefficients':prefix,
        'suffix_root_coefficients':suffix,'square_prefix':ds[:k],
        'cube_prefix':dc[:k],'square_suffix':ds[-k:],'cube_suffix':dc[-k:],
        'digit_count':len(ds)+len(dc),'distinct_digits':len(set(ds+dc)),
        'mutually_distinct_edge_digits':len(set(edges)),
        'digit_sum_congruence':True,
        'nice':len(set(ds+dc))==b,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--depths',type=int,nargs='+',default=[1,2,4,8,12])
    ap.add_argument('--output',default='results/edge-constraints.json')
    args=ap.parse_args()
    output=[]
    for k in args.depths:
        row=construct(k)
        output.append(row)
        Path(args.output).write_text(json.dumps(output,indent=2)+'\n')
        print(json.dumps({x:row[x] for x in ['k','base','n_decimal_digits','mutually_distinct_edge_digits','distinct_digits','nice']}),flush=True)


if __name__=='__main__':
    main()
