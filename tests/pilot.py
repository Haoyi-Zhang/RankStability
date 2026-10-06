#!/usr/bin/env python3
"""Bounded exact oracle and negative controls; one worker, no subprocesses."""
import sys,json,random,itertools,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from result_io import emit, output_path, peak_rss_kib
import certify,checker

from oracle import solve as oracle

def cases(seed=715):
    rng=random.Random(seed)
    for i in range(256):
        n=rng.randint(2,8);t=rng.randint(1,5);ell=rng.randint(2,5)
        a=[rng.randrange(2) for _ in range(n)]
        b=[rng.randrange(3) for _ in range(n)]
        ref=rng.sample(range(ell),rng.randint(1,ell))
        c={"id":f"pilot-{i:03d}","fail":[1]+[rng.randrange(2) for _ in range(t-1)],"kill":[[rng.randrange(2) for _ in range(n)] for _ in range(t)],"location":[rng.randrange(ell) for _ in range(n)],"locations":ell,"tie":rng.sample(range(ell),ell),"a":a,"b":b,"a_bounds":[[rng.randrange(2),n] for _ in range(2)],"b_bounds":[[rng.randrange(2),n] for _ in range(3)],"size":[rng.randrange(n),n],"force":[],"forbid":[],"reference":ref,"empty":"bottom" if i%2 else "zero"}
        for side in ["a","b"]:
            for q in c[side+"_bounds"]:
                q[1]=rng.randint(q[0],n)
        if i%4==0:c["force"]=[0]
        if i%5==0:c["forbid"]=[n-1]
        yield c

def run():
    start=time.process_time();counts={};nsubset=0;negative=0
    for c in cases():
        cert=certify.produce(c);status=checker.check(c,cert)
        expected,best,_=oracle(c);nsubset+=1<<len(c["location"])
        assert status==expected,(c,cert,expected)
        if status=="counterexample":assert cert["size"]==best
        counts[status]=counts.get(status,0)+1
        if cert.get("branches"):
            broken=json.loads(json.dumps(cert));broken["branches"].pop()
            try:checker.check(c,broken)
            except ValueError:negative+=1
            else:raise AssertionError("deleted branch accepted")
    return {"cases":256,"seed":715,"oracle_subsets":nsubset,"status_counts":counts,"deleted_branch_rejections":negative,"producer":certify.COUNTERS,"checker_steps":checker.STEPS,"cpu_seconds":time.process_time()-start,"peak_rss_kib":peak_rss_kib(),"workers":1}
if __name__=="__main__":
    emit(output_path(Path(__file__).resolve().parents[1]/"results"/"pilot.json"),run())
