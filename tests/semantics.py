#!/usr/bin/env python3
"""Finite CNF-boundary validation and schema/floor regression checks."""
import copy,itertools,json,random,sys,time,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import certify,checker,oracle

def run():
    start=time.process_time();clauses=list(itertools.product([-1,0,1],repeat=2));formulas=0
    for include in range(1<<len(clauses)):
        selected=[clause for j,clause in enumerate(clauses) if include>>j&1]
        def satisfied(assignment):
            return all(any(sign and assignment[j]==(sign==1) for j,sign in enumerate(clause)) for clause in selected)
        sat=any(satisfied(assignment) for assignment in itertools.product([False,True],repeat=2))
        c={'id':'cnf-boundary','fail':[1,0],'kill':[[1,1,0,0],[0,1,0,0]],'location':[0,1,1,1],'locations':2,'tie':[0,1],'a':[0]*4,'b':[0]*4,'a_bounds':[[0,4]],'b_bounds':[[0,4]],'size':[0,4],'force':[1],'forbid':[],'reference':[0],'empty':'bottom'}
        changes=[]
        for z,x,y in itertools.product([False,True],repeat=3):
            # A generic CNF policy extension, deliberately outside the solver schema.
            if not (z or satisfied([x,y])):continue
            sample=[1]+([0] if z else [])+([2] if x else [])+([3] if y else [])
            changes.append(set(certify.top(c,sample))!={0})
        assert changes and any(changes)==sat
        formulas+=1
    # Direct boundary for the retained two-partition policy: with three
    # independent exact-quota partitions, feasibility already encodes perfect
    # three-dimensional matching.  Exhaust every q=2 hypergraph and sample a
    # deterministic set of q=3 hypergraphs.  This validates the reduction map,
    # not the asymptotic NP-completeness proof.
    three_partition_instances=0
    three_partition_selections=0
    def check_3dm(q, triples):
        nonlocal three_partition_instances, three_partition_selections
        triples=list(triples)
        matching=False
        for choice in itertools.combinations(range(len(triples)),q):
            three_partition_selections+=1
            picked=[triples[i] for i in choice]
            if all(len({t[d] for t in picked})==q for d in range(3)):
                matching=True
                break
        # Generic exact-quota interpretation: one selected mutant per group in
        # each of three partitions, with global size exactly q.
        quota=False
        for mask in range(1<<len(triples)):
            if mask.bit_count()!=q:
                continue
            picked=[triples[i] for i in range(len(triples)) if mask>>i&1]
            three_partition_selections+=1
            if all(all(sum(t[d]==g for t in picked)==1 for g in range(q)) for d in range(3)):
                quota=True
                break
        assert matching==quota
        three_partition_instances+=1
    universe2=list(itertools.product(range(2),repeat=3))
    for include in range(1<<len(universe2)):
        check_3dm(2,[t for i,t in enumerate(universe2) if include>>i&1])
    rng=random.Random(20260915)
    universe3=list(itertools.product(range(3),repeat=3))
    for _ in range(64):
        check_3dm(3,[t for t in universe3 if rng.random()<0.30])

    regression=json.loads((Path(__file__).parent/'zero-floor-tie.json').read_text())
    cert=certify.produce(regression)
    assert checker.check(regression,cert)==oracle.solve(regression)[0]=='stable'
    invalid=[]
    c=copy.deepcopy(regression);c['cnf']=[[1]];invalid.append(c)
    c=copy.deepcopy(regression);c['score']='MUSE';invalid.append(c)
    c=copy.deepcopy(regression);c['fail']=[0 for _ in c['fail']];invalid.append(c)
    c=copy.deepcopy(regression);c['kill'][0][0]=0.5;invalid.append(c)
    c=copy.deepcopy(regression);c['tie']=[0]*c['locations'];invalid.append(c)
    c=copy.deepcopy(regression);c['location'][0]=[0,1];invalid.append(c)
    rejects=0
    for c in invalid:
        for function in [certify.produce,lambda x:checker.check(x,cert)]:
            try:function(c)
            except (ValueError,TypeError,KeyError,IndexError):rejects+=1
            else:raise AssertionError('unsupported input accepted')
    return {'cnf_formulas':formulas,'sat_assignments_enumerated':formulas*4,'extended_samples_enumerated':formulas*8,'three_partition_instances':three_partition_instances,'three_partition_selections_enumerated':three_partition_selections,'schema_rejections':rejects,'floor_regression':'stable','cpu_seconds':time.process_time()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
if __name__=='__main__':print(json.dumps(run(),indent=2))
