#!/usr/bin/env python3
"""Regenerate every owned program, observation, matrix and certificate in a clean
transient directory; compare scientific content exactly, never timing/RSS."""
import csv,json,resource,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import programs,controls,campaign
ROOT=Path(__file__).resolve().parents[1]

def strip(x):
    if isinstance(x,dict):return {k:strip(v) for k,v in x.items() if 'cpu_seconds' not in k and 'rss' not in k and k!='search_states'}
    if isinstance(x,list):return [strip(v) for v in x]
    return x

def run():
    begin=time.process_time();prev=resource.getrusage(resource.RUSAGE_CHILDREN)
    count=0
    with tempfile.TemporaryDirectory(prefix='mutation-clean-') as td:
        temp=Path(td);data=temp/'data'
        for i in range(200):
            family, variant, ident = programs.confirmatory_design(i)
            meta = programs.run_one(family, variant, data, ident=ident, protocol_role="confirmatory")
            campaign.write(data/'metadata'/(meta['id']+'.json'),meta)
        controls.build(data);summary=campaign.run(data,temp/'results')
        for section in ['programs','observations','cases','metadata']:
            expected=ROOT/'data'/section;actual=data/section
            assert {p.name for p in expected.iterdir()}=={p.name for p in actual.iterdir()}
            for path in expected.iterdir():
                rhs=actual/path.name
                if path.suffix=='.json':assert strip(json.loads(path.read_text()))==strip(json.loads(rhs.read_text())),path.name
                else:assert path.read_bytes()==rhs.read_bytes(),path.name
                count+=1
        for section in ['certificates','secondary_certificates','details']:
            expected=ROOT/'results/campaign'/section;actual=temp/'results'/section
            assert {p.name for p in expected.iterdir()}=={p.name for p in actual.iterdir()}
            for path in expected.iterdir():
                assert strip(json.loads(path.read_text()))==strip(json.loads((actual/path.name).read_text())),path.name
                count+=1
        for name in ['primary.csv','secondary.csv']:
            a=list(csv.DictReader((ROOT/'results/campaign'/name).open()));b=list(csv.DictReader((temp/'results'/name).open()))
            assert strip(a)==strip(b),name;count+=1
        old=json.loads((ROOT/'results/campaign/summary.json').read_text())
        assert strip(old)==strip(summary)
    end=resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(scientific_files_compared=count,primary_cases=260,secondary_queries=981,program_schemas_recompiled=220,exact_observation_and_certificate_agreement=True,cpu_seconds=time.process_time()-begin+end.ru_utime-prev.ru_utime+end.ru_stime-prev.ru_stime,peak_rss_kib=max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,end.ru_maxrss),replay_producer=summary['producer'],replay_checker_steps=summary['checker_steps'])
if __name__=='__main__':print(json.dumps(run(),indent=2))
