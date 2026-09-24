#!/usr/bin/env python3
"""Owned ambiguity programs and explicitly delimited sampling fixtures."""
from __future__ import annotations
import argparse, copy, json, resource, subprocess, tempfile, time
from pathlib import Path
import certify

def base(ident,loc,columns,fail,ell=None):
    n=len(loc);ell=max(loc)+1 if ell is None and loc else 2 if ell is None else ell
    return dict(id=ident,fail=fail,kill=[list(x) for x in zip(*columns)] if n else [[] for _ in fail],location=loc,locations=ell,tie=list(range(ell)),a=[0]*n,b=[0]*n,a_bounds=[[0,n]],b_bounds=[[0,n]],size=[0,n],force=[],forbid=[],reference=[0],empty='bottom')

def fixtures():
    out=[]
    def add(c,name,expect,minimum=None):
        c['id']=f'fixture-{len(out):02d}'
        certify.validate(c)
        out.append((copy.deepcopy(c),dict(id=c['id'],category='fixture',description=name,expected_status=expect,expected_minimum=minimum)))
    c=base('',[0,1,0,1],[[1,0,0,0],[1,1,0,0],[1,1,1,0],[1,1,1,1]],[1,0,0,0])
    c.update(a=[0,1,0,1],b=[0,1,1,0],a_bounds=[[1,1],[1,1]],b_bounds=[[1,1],[1,1]],size=[2,2])
    add(c,'Crossed matchings: stable despite overlapping marginal intervals','stable')
    c['b_bounds']=[[0,4],[0,4]];add(c,'Removing the second partition admits a reversal','counterexample',2)
    c=base('',[0,1,1,1,1],[[1,0]]+[[1,1]]*4,[1,0]);c.update(a=[1,0,1,2,2],b=[1,0,0,1,2],a_bounds=[[1,3]]*3,b_bounds=[[1,3]]*3,size=[3,5])
    add(c,'Deleting the sole high scorer raises the minimum edge-cover cardinality from three to four','counterexample',4)
    c=base('',[0]*20+[1]*20,[[1,0]]*20+[[1,1]]*20,[1,0]);c['size']=[20,20]
    add(c,'Unique reversal among all forty-choose-twenty samples','counterexample',20)
    c=base('',[0,1],[[1,0],[1,1]],[1,0]);c['force']=[0];add(c,'Mandatory highest-scoring insider','stable')
    c=base('',[0,1],[[0],[0]],[1]);c.update(size=[1,2],empty='zero');add(c,'Zero-score floor cannot be beaten by a later zero-score pivot','stable')
    c=base('',[0,1],[[0],[0]],[1]);c.update(size=[1,2]);add(c,'Bottom floor distinguishes absence from a selected zero-score mutant','counterexample',1)
    c=base('',[0,1],[[1,0],[1,1]],[1,0]);c['forbid']=[1];c['force']=[0];add(c,'Only outsider pivot forbidden','stable')
    c=base('',[0,1],[[1],[1]],[1]);c.update(size=[1,1],a=[0,1],a_bounds=[[1,1],[1,1]]);add(c,'Locally valid quotas globally infeasible','infeasible_policy')
    c=base('',[0,1],[[1],[1]],[1]);c['reference']=[0,1];add(c,'All locations in the reference set: internal order irrelevant','stable')
    c=base('',[0,1],[[1],[1]],[1]);c.update(tie=[1,0],size=[2,2],reference=[1]);add(c,'Fixed reversed tie priority','stable')
    c=base('',[1],[[0]],[1]);c['empty']='zero';add(c,'Zero floor and earlier empty insider','stable')
    c['empty']='bottom';add(c,'Same matrix with bottom floor','counterexample',1)
    c=base('',[],[],[1],ell=2);add(c,'Empty mutant universe with matching reference','stable')
    c['reference']=[1];add(c,'Empty mutant universe with nonmatching reference','counterexample',0)
    c=base('',[0,1,0,1],[[1,0,0,0],[1,1,0,0],[1,1,1,0],[1,1,1,1]],[1,0,0,0],ell=3);c.update(a=[0,1,0,1],b=[0,1,1,0],a_bounds=[[1,1],[1,1]],b_bounds=[[1,1],[1,1]],size=[2,2],reference=[0,1]);add(c,'Top-two set protected while the score levels change','stable')
    c=base('',[0,1],[[1],[1]],[1]);c.update(a=[0,0],a_bounds=[[0,2],[1,1]]);add(c,'Positive quota on an isolated group','infeasible_policy')
    c=base('',[0]*21+[1]*19,[[1]]*40,[1]);c['size']=[20,20];add(c,'Pigeonhole cardinality prevents deleting all tied insiders','stable')
    c=base('',[0,1],[[1,0],[1,1]],[1,0]);c['size']=[2,2];add(c,'Global cardinality forces both mutants','stable')
    c=base('',[0,1],[[1,0],[1,1]],[1,0]);c['size']=[0,1];c['reference']=[1];add(c,'Supplied reference differs from the full-universe ranking','counterexample',0)
    if len(out) != 20:
        raise RuntimeError("fixture inventory must contain exactly 20 cases")
    return out

def ambiguity_source(amount):
    lines=['/* MIT license. Two correction origins; equal reference outputs. */','#include <stdint.h>','#include <inttypes.h>','#include <stdio.h>',f'static int64_t faulty(int64_t x,int m) {{ int64_t a=x+{amount};']
    for j,expr in enumerate(['a+1','a-1','-a','0']):lines.append(f'if(m=={j}) a=({expr});')
    lines.append(f'int64_t b=a+{amount};')
    for j,expr in enumerate(['b+1','b-1','-b','0'],4):lines.append(f'if(m=={j}) b=({expr});')
    lines+=['return b;}',f'static int64_t correction0(int64_t x) {{ int64_t a=x; int64_t b=a+{amount}; return b; }}',f'static int64_t correction1(int64_t x) {{ int64_t a=x+{amount}; int64_t b=a; return b; }}','int main(void) { for(int x=-9;x<=9;x++) {','printf("%d,%" PRId64 ",%" PRId64 ",%" PRId64,x,correction0(x),correction1(x),faulty(x,-1));','for(int m=0;m<8;m++) printf(",%" PRId64,faulty(x,m));',"putchar('\\n'); } return 0; }"]
    return '\n'.join(lines)+'\n'

def build(out):
    out=Path(out)
    for d in ['cases','programs','observations','metadata']:(out/d).mkdir(parents=True,exist_ok=True)
    for i in range(20):
        start=time.process_time();prev=resource.getrusage(resource.RUSAGE_CHILDREN)
        stem=f'ambiguity-pair-{i:02d}';source=out/'programs'/(stem+'.c');source.write_text(ambiguity_source(i+1))
        with tempfile.TemporaryDirectory(prefix='mutation-control-') as td:
            exe=Path(td)/'subject'
            subprocess.run(['cc','-std=c11','-O0','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)],check=True,capture_output=True,timeout=40)
            raw=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=5).stdout
        rows=[[int(v) for v in r.split(',')] for r in raw.splitlines()]
        if len(rows) != 19 or not all(r[1] == r[2] and r[1] != r[3] for r in rows):
            raise RuntimeError("ambiguity control observations violate their construction")
        (out/'observations'/(stem+'.csv')).write_text('x,correction0,correction1,buggy,'+','.join('mutant_'+str(j) for j in range(8))+'\n'+raw)
        end=resource.getrusage(resource.RUSAGE_CHILDREN)
        elapsed=time.process_time()-start+end.ru_utime-prev.ru_utime+end.ru_stime-prev.ru_stime
        for world in [0,1]:
            ident=f'ambiguity-{2*i+world:02d}'
            c=base(ident,[0]*4+[1]*4,[[int(r[4+j]!=r[3]) for r in rows] for j in range(8)],[int(r[1+world]!=r[3]) for r in rows])
            c.update(a=list(range(4))*2,b=[0]*4+[1]*4,a_bounds=[[0,2]]*4,b_bounds=[[1,3],[1,3]],size=[2,6],force=[0])
            c['reference']=certify.top(c,list(range(8)))
            meta=dict(id=ident,category='ambiguity',pair=i,world=world,correction_location=world,source=stem+'.c',observations=stem+'.csv',expected_status='stable',cpu_seconds=elapsed if world==0 else 0,peak_child_rss_kib=end.ru_maxrss)
            (out/'cases'/(ident+'.json')).write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
            (out/'metadata'/(ident+'.json')).write_text(json.dumps(meta,sort_keys=True,indent=2)+'\n')
    for c,meta in fixtures():
        (out/'cases'/(c['id']+'.json')).write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
        (out/'metadata'/(c['id']+'.json')).write_text(json.dumps(meta,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('out',type=Path);build(p.parse_args().out)
