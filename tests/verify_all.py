#!/usr/bin/env python3
"""Check certificates, reconstruct matrices from raw C observations, reconcile CSV."""
import argparse,copy,csv,json,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import checker
from result_io import emit

def run(data,out):
    checker.STEPS=0
    data=Path(data);out=Path(out);counts=Counter();checks=0;matrix_checks=0
    table={r['id']:r for r in csv.DictReader((out/'primary.csv').open())}
    second={ (r['id'],r['change']):r for r in csv.DictReader((out/'secondary.csv').open()) }
    for path in sorted((data/'cases').glob('*.json')):
        c=json.loads(path.read_text());cert=json.loads((out/'certificates'/path.name).read_text());observed=checker.check(c,cert)
        r=table[c['id']];assert observed==r['status'] and str(cert.get('size',''))==r['minimum']
        counts[(r['category'],observed)]+=1;checks+=1
        meta=json.loads((data/'metadata'/path.name).read_text())
        if r['category'] in ['program','ambiguity']:
            raw=data/'observations'/(meta.get('observations',c['id']+'.csv'))
            observations=list(csv.DictReader(raw.open()))
            key='reference' if r['category']=='program' else 'correction'+str(meta['world'])
            fail=[int(row[key]!=row['buggy']) for row in observations]
            kill=[[int(row['mutant_'+str(j)]!=row['buggy']) for j in range(len(c['location']))] for row in observations]
            assert fail==c['fail'] and kill==c['kill'];matrix_checks+=1
            if r['category']=='ambiguity':assert all(row['correction0']==row['correction1'] for row in observations)
        # Independent ranking helper from checker, not producer, builds sensitivity references.
        for name in ['relax_b','zero_floor','k2','k3']:
            if (c['id'],name) not in second:continue
            d=copy.deepcopy(c);n=len(c['location'])
            if name=='relax_b':d['b_bounds']=[[0,n] for _ in d['b_bounds']]
            else:
                if name=='zero_floor':
                    d['empty']='zero'
                else:
                    d['reference']=list(range(int(name[1:])))
                    ratios=checker.prepare(d);d['reference']=sorted(checker.ranked(d,list(range(n)),ratios))
            d['id']+='-'+name
            proof=json.loads((out/'secondary_certificates'/(d['id']+'.json')).read_text())
            s=checker.check(d,proof);row=second[(c['id'],name)]
            assert s==row['status'] and str(proof.get('size',''))==row['minimum'];checks+=1
    summary=json.loads((out/'summary.json').read_text())
    assert summary['primary_cases']==len(table)==260
    assert summary['secondary_queries']==len(second)==981
    assert {a+':'+b:v for (a,b),v in sorted(counts.items())}==summary['status_counts']
    return dict(accepted_certificates=checks,matrices_reconstructed=matrix_checks,primary_cases=len(table),secondary_queries=len(second),checker_steps=checker.STEPS)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);p.add_argument('results',type=Path);a=p.parse_args()
    emit(Path(a.results).parents[0]/'verification.json',run(a.data,a.results))
