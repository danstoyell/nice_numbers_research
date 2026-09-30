#!/usr/bin/env python3
"""Sanity check of Lemma 1 (Fourier decay of digit-weight functions):
for theta in T^(b-1) (theta_0 = 0), F_1(t) = (1/b) sum_d e(theta_d - d t / b),
    max_t |F_1(t) F_1(b t)| <= 1 - 8 D(theta)^2 / (9 b^2),
D(theta) = min_j max_d || theta_d - j d/(b-1) ||.  Random theta and theta near spikes.
Numpy not required; ~1 minute on 1 core."""
import cmath, math, random, json
def e(x): return cmath.exp(2j*math.pi*x)
def dist(x): return abs(x-round(x))
def D(th,b):
    return min(max(dist(th[d]-j*d/(b-1)) for d in range(1,b)) for j in range(b-1))
def maxprod(th,b,G=4000):
    best=0.0
    for i in range(G):
        t=b*i/G   # F_1(t) has period b in t; F_1(bt) period 1
        F1=sum(e(th[d]-d*t/b) for d in range(b))/b
        F2=sum(e(th[d]-d*t) for d in range(b))/b
        best=max(best,abs(F1*F2))
    return best
random.seed(1)
worst={}
for b in (2,3,6,8,9,10):
    w=float('inf')
    for trial in range(300):
        if trial%2==0:
            th=[0.0]+[random.random() for _ in range(b-1)]
        else:
            j=random.randrange(b-1); eps=10**random.uniform(-3,-0.5)
            th=[0.0]+[(j*d/(b-1)+eps*random.uniform(-1,1))%1 for d in range(1,b)]
        Dt=D(th,b)
        if Dt==0: continue
        slack=(1-maxprod(th,b)) / (8*Dt*Dt/(9*b*b))   # >= 1 iff lemma holds
        w=min(w,slack)
    worst[b]=w
    print(b, "min of (1-max|F1F1|)/(8D^2/(9b^2)) =", round(w,3))
json.dump(worst, open("results/check_decay.json","w"))
