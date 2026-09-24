"""Exhaustive third implementation. No producer/checker imports."""
from functools import cmp_to_key

def solve(c):
    n=len(c['location']); f=sum(c['fail']); q=[]
    for j in range(n):
        x=sum(c['kill'][i][j] for i in range(len(c['fail'])) if c['fail'][i])
        y=sum(row[j] for row in c['kill'])
        q.append((x*x,f*y) if y else (0,1))
    def cmp(u,v):
        z=u[0]*v[1]-v[0]*u[1]
        return (z>0)-(z<0)
    count=0; best=None; witness=None
    for mask in range(1<<n):
        selected=[j for j in range(n) if mask & (1<<j)]
        if not c['size'][0]<=len(selected)<=c['size'][1]:continue
        if any(not mask&(1<<j) for j in c['force']) or any(mask&(1<<j) for j in c['forbid']):continue
        good=True
        for side in ['a','b']:
            for group,(lo,hi) in enumerate(c[side+'_bounds']):
                num=sum(c[side][j]==group for j in selected)
                if not lo<=num<=hi:good=False;break
            if not good:break
        if not good:continue
        count+=1
        values=[(-1,1) if c['empty']=='bottom' else (0,1) for l in range(c['locations'])]
        for j in selected:
            loc=c['location'][j]
            if cmp(q[j],values[loc])>0:values[loc]=q[j]
        def order(a,b):
            difference=cmp(values[b],values[a])
            return difference or c['tie'].index(a)-c['tie'].index(b)
        ranked=sorted(range(c['locations']),key=cmp_to_key(order))[:len(c['reference'])]
        if set(ranked)!=set(c['reference']) and (best is None or len(selected)<best):best=len(selected);witness=selected
    return ('infeasible_policy' if not count else 'stable' if best is None else 'counterexample'),best,witness
