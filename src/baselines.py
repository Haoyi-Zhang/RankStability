"""Transparent same-input baselines, not external package reimplementations."""
import random,time
from fractions import Fraction
import certify

def marginal(c):
    begin=time.process_time();n=len(c['location'])
    feasible,_=certify.circulation(c,[],[],c['size'][1])
    if feasible is None:return {'result':'infeasible_policy','cpu_seconds':time.process_time()-begin}
    score=certify.scores(c);floor=Fraction(-1 if c['empty']=='bottom' else 0)
    bounds=[]
    for loc in range(c['locations']):
        members=[j for j,x in enumerate(c['location']) if x==loc]
        lower=None
        for threshold in sorted(set([floor]+[score[j] for j in members])):
            blocks=[j for j in members if score[j]>threshold]
            possible,_=certify.circulation(c,blocks,[],c['size'][1])
            if possible is not None:lower=threshold;break
        if lower is None:
            raise RuntimeError("feasible policy produced no attainable lower score")
        upper=floor
        for j in sorted(members,key=lambda j:score[j],reverse=True):
            possible,_=certify.circulation(c,[],[j],c['size'][1])
            if possible is not None:upper=score[j];break
        bounds.append((lower,upper))
    rank={l:i for i,l in enumerate(c['tie'])}
    stable=all((bounds[a][0],-rank[a])>(bounds[b][1],-rank[b]) for a in c['reference'] for b in range(c['locations']) if b not in c['reference'])
    return {'result':'stable' if stable else 'unknown','bounds':[[str(x),str(y)] for x,y in bounds],'cpu_seconds':time.process_time()-begin}

def random_samples(c,seed):
    begin=time.process_time();rng=random.Random(seed);n=len(c['location']);accepted=0;attempts=0;minimum=None
    while accepted<64 and attempts<4096:
        attempts+=1
        size=rng.randint(*c['size']);seq=sorted(rng.sample(range(n),size))
        if not certify.admissible(c,seq):continue
        accepted+=1
        if set(certify.top(c,seq))!=set(c['reference']):
            minimum=len(seq) if minimum is None else min(minimum,len(seq))
    return {'result':'observed_counterexample' if minimum is not None else 'unknown','accepted':accepted,'attempts':attempts,'observed_minimum':minimum,'cpu_seconds':time.process_time()-begin}
