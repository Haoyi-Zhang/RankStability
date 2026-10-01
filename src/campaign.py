#!/usr/bin/env python3
"""Frozen 260-case campaign. Run sequentially; secondary queries separately."""
from __future__ import annotations
import argparse,copy,csv,json,resource,signal,time
from collections import Counter
from pathlib import Path
import certify,checker,baselines,oracle

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def write(path,x):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')

def corruptions(c,cert):
    changed=[]
    x=copy.deepcopy(cert);x['case_id']='not-this-case';changed.append(('wrong_case',x))
    if cert.get('branches'):
        x=copy.deepcopy(cert);x['branches'].pop();changed.append(('missing_branch',x))
        x=copy.deepcopy(cert);x['branches'][0]['branch']=[-7,-7,-7];changed.append(('wrong_branch',x))
    seq=cert.get('sample',cert.get('base_sample'))
    if seq:
        x=copy.deepcopy(cert);key='sample' if 'sample' in cert else 'base_sample';x[key].append(x[key][0]);changed.append(('duplicate_sample',x))
    if cert['status']=='counterexample':
        x=copy.deepcopy(cert);x['size']+=1;changed.append(('wrong_minimum',x))
    proof=cert.get('proof')
    if proof is None and cert.get('branches'):proof=cert['branches'][0]['proof']
    if proof is not None:
        x=copy.deepcopy(cert);p=x['proof'] if 'proof' in x else x['branches'][0]['proof']
        p.clear();p.update(kind='cut',vertices=[]);changed.append(('invalid_cut',x))
    counts=Counter()
    for kind,x in changed:
        try:checker.check(c,x)
        except (ValueError,KeyError,TypeError,IndexError):counts[kind]+=1
        else:raise AssertionError(('invalid_certificate_accepted',c['id'],kind))
    return counts

def run(data,out):
    for key in certify.COUNTERS:
        certify.COUNTERS[key]=0
    checker.STEPS=0
    data=Path(data);out=Path(out);start=time.process_time();rows=[];secondary=[];corrupt=Counter();status=Counter();generation_cpu=0
    casepaths=sorted((data/'cases').glob('*.json'))
    require(len(casepaths) == 260, "primary campaign must contain exactly 260 cases")
    def alarm(signum,frame):raise TimeoutError('per-case 45-second wall budget')
    signal.signal(signal.SIGALRM,alarm)
    raw_matrix_entries=0;max_n=0;max_t=0;max_l=0
    for index,path in enumerate(casepaths):
        signal.alarm(45)
        c=json.loads(path.read_text());meta=json.loads((data/'metadata'/path.name).read_text());category=meta.get('category','program');n=len(c['location'])
        raw_matrix_entries+=n*len(c['fail']);max_n=max(max_n,n);max_t=max(max_t,len(c['fail']));max_l=max(max_l,c['locations']);generation_cpu+=meta.get('cpu_seconds',0)
        t=time.process_time();cert=certify.produce(c);producer_cpu=time.process_time()-t
        t=time.process_time();observed=checker.check(c,cert);checker_cpu=time.process_time()-t
        if 'expected_status' in meta:
            require(observed == meta['expected_status'], f"status mismatch for {c['id']}")
        if meta.get('expected_minimum') is not None:
            require(cert.get('size') == meta['expected_minimum'], f"minimum mismatch for {c['id']}")
        if category=='fixture' and n<=8:
            expected,minimum,_=oracle.solve(c)
            require(observed == expected, f"oracle status mismatch for {c['id']}")
            if observed == 'counterexample':
                require(cert['size'] == minimum, f"oracle minimum mismatch for {c['id']}")
        write(out/'certificates'/path.name,cert)
        intervals=baselines.marginal(c);random=baselines.random_samples(c,271828+index)
        if intervals['result'] == 'stable':
            require(observed == 'stable', f"interval baseline unsound for {c['id']}")
        if random['result'] == 'observed_counterexample':
            require(observed == 'counterexample' and random['observed_minimum'] >= cert['size'], f"random baseline mismatch for {c['id']}")
        if observed == 'stable':
            require(set(certify.top(c, cert['base_sample'])) == set(c['reference']), f"stable base witness mismatch for {c['id']}")
        record=dict(id=c['id'],category=category,family=meta.get('family',category),status=observed,mutants=n,tests=len(c['fail']),locations=c['locations'],k=len(c['reference']),minimum=cert.get('size'),producer_cpu_seconds=producer_cpu,checker_cpu_seconds=checker_cpu,certificate_bytes=len(json.dumps(cert,sort_keys=True,separators=(',',':')).encode()),branches=len(cert.get('branches',[])),interval_result=intervals['result'],interval_cpu_seconds=intervals['cpu_seconds'],random_result=random['result'],random_accepted=random['accepted'],random_attempts=random['attempts'],random_minimum=random['observed_minimum'],random_cpu_seconds=random['cpu_seconds'])
        write(out/'details'/path.name,dict(interval=intervals,random=random))
        corrupt.update(corruptions(c,cert));rows.append(record);status[(category,observed)]+=1
        for name in ['relax_b','zero_floor','k2','k3']:
            if name.startswith('k') and c['locations']<int(name[1:]):continue
            d=copy.deepcopy(c)
            if name=='relax_b':d['b_bounds']=[[0,n] for _ in d['b_bounds']]
            elif name=='zero_floor':d['empty']='zero'
            else:d['reference']=list(range(int(name[1:])));d['reference']=certify.top(d,list(range(n)))
            d['id']+='-'+name;answer=certify.produce(d);checker.check(d,answer)
            if name == 'relax_b' and observed == 'counterexample':
                require(answer['status'] == 'counterexample' and answer['size'] <= cert['size'], f"relaxation monotonicity mismatch for {c['id']}")
            secondary.append(dict(id=c['id'],change=name,status=answer['status'],minimum=answer.get('size')))
            write(out/'secondary_certificates'/(d['id']+'.json'),answer)
        signal.alarm(0)
        if certify.COUNTERS['search_states']>2000000 or checker.STEPS>10000000:raise RuntimeError('instrumented campaign budget exceeded')
    require(raw_matrix_entries <= 4_000_000, "primary matrix-entry guard exceeded")
    with (out/'primary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with (out/'secondary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(secondary[0]));writer.writeheader();writer.writerows(secondary)
    summary=dict(primary_cases=len(rows),secondary_queries=len(secondary),matrix_entries=raw_matrix_entries,dimensions=dict(max_mutants=max_n,max_tests=max_t,max_locations=max_l),status_counts={a+':'+b:v for (a,b),v in sorted(status.items())},interval_stable=sum(r['interval_result']=='stable' for r in rows),random_counterexamples=sum(r['random_result']=='observed_counterexample' for r in rows),random_short_budget=sum(r['random_accepted']<64 for r in rows),corruption_rejections=dict(corrupt),producer=certify.COUNTERS,checker_steps=checker.STEPS,cpu_seconds=time.process_time()-start,generation_cpu_seconds=generation_cpu,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,workers=1)
    write(out/'summary.json',summary)
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);p.add_argument('out',type=Path);args=p.parse_args();print(json.dumps(run(args.data,args.out),indent=2))
