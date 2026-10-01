#!/usr/bin/env python3
"""All 2x3 binary matrices, location maps, tie orders, floors and references
under three specified policies. This is finite validation, not a general proof."""
import sys,json,itertools,time,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from result_io import emit
import certify,checker,oracle

def run():
    start=time.process_time();total=0;counts={}
    for bits in itertools.product([0,1],repeat=6):
      for loc in itertools.product([0,1],repeat=3):
       for tie in [[0,1],[1,0]]:
        for empty in ['bottom','zero']:
         for ref in [0,1]:
          for policy in range(3):
            c={'id':'exhaustive','fail':[1,0],'kill':[list(bits[:3]),list(bits[3:])], 'location':list(loc),'locations':2,'tie':tie,'a':[0,0,1],'b':[0,1,0], 'a_bounds':[[0,3],[0,3]],'b_bounds':[[0,3],[0,3]],'size':[0,3],'force':[],'forbid':[],'reference':[ref],'empty':empty}
            if policy==1:c.update(a_bounds=[[1,1],[1,1]],b_bounds=[[1,2],[0,1]],size=[2,2])
            if policy==2:c.update(force=[0],forbid=[2],b_bounds=[[1,1],[1,1]],size=[1,2])
            cert=certify.produce(c);observed=checker.check(c,cert);expected,minimum,_=oracle.solve(c)
            assert observed==expected,(c,cert,expected)
            if observed=='counterexample':assert cert['size']==minimum
            total+=1;counts[observed]=counts.get(observed,0)+1
    return {'cases':total,'oracle_subsets':total*8,'status_counts':counts,'producer':certify.COUNTERS,'checker_steps':checker.STEPS,'cpu_seconds':time.process_time()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'workers':1}
if __name__=='__main__':emit(Path(__file__).resolve().parents[1]/'results'/'exhaustive.json',run())
