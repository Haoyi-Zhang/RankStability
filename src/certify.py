#!/usr/bin/env python3
"""Exact top-k-set invariance under two crossing partition quotas.

Producer only. checker.py does not import this module. All scores are exact.
"""
from __future__ import annotations
import argparse
from collections import deque
from fractions import Fraction
import json
from pathlib import Path

COUNTERS = {"networks": 0, "augmentations": 0, "edge_scans": 0, "search_states": 0}

def validate(c: dict) -> None:
    def ints(xs):
        return isinstance(xs, list) and all(type(x) is int for x in xs)
    required = {"id", "fail", "kill", "location", "locations", "tie", "a", "b", "a_bounds", "b_bounds", "size", "force", "forbid", "reference", "empty"}
    if not isinstance(c, dict) or set(c) != required:
        raise ValueError("missing or unknown case fields")
    if not isinstance(c["id"],str) or not 1 <= len(c["id"]) <= 200:
        raise ValueError("invalid case id")
    n = len(c["location"])
    ell = c["locations"]
    if not (type(ell) is int and 1 <= ell <= 100 and n <= 40):
        raise ValueError("dimension outside declared implementation envelope")
    if not ints(c["location"]) or any(x < 0 or x >= ell for x in c["location"]):
        raise ValueError("invalid location")
    if not ints(c["tie"]) or sorted(c["tie"]) != list(range(ell)):
        raise ValueError("tie must be a permutation")
    if not ints(c["fail"]) or not 1 <= len(c["fail"]) <= 200 or any(x not in (0,1) for x in c["fail"]) or not sum(c["fail"]):
        raise ValueError("need at least one failing test")
    if not isinstance(c["kill"], list) or len(c["kill"]) != len(c["fail"]) or any(not ints(row) or len(row) != n or any(x not in (0,1) for x in row) for row in c["kill"]):
        raise ValueError("kill matrix is not binary/rectangular")
    for name in ("a", "b"):
        bounds = c[name+"_bounds"]
        if not isinstance(bounds,list) or not 1 <= len(bounds) <= 40:
            raise ValueError("invalid number of groups")
        if not ints(c[name]) or len(c[name]) != n or any(x < 0 or x >= len(bounds) for x in c[name]):
            raise ValueError("invalid partition labels")
        if any(not ints(q) or len(q) != 2 or not 0 <= q[0] <= q[1] <= n for q in bounds):
            raise ValueError("invalid quota")
    if not ints(c["size"]) or len(c["size"]) != 2 or not 0 <= c["size"][0] <= c["size"][1] <= n:
        raise ValueError("invalid cardinality interval")
    for name in ("force", "forbid"):
        if not ints(c[name]) or len(set(c[name])) != len(c[name]) or any(x < 0 or x >= n for x in c[name]):
            raise ValueError("invalid membership constraint")
    if set(c["force"]) & set(c["forbid"]):
        raise ValueError("contradictory input membership constraints")
    ref = c["reference"]
    if not ints(ref) or not 1 <= len(ref) <= min(10,ell) or len(set(ref)) != len(ref) or any(x < 0 or x >= ell for x in ref):
        raise ValueError("invalid supplied reference set")
    if c["empty"] not in ("bottom", "zero"):
        raise ValueError("unknown empty-location convention")

def scores(c: dict) -> list[Fraction]:
    f_total = sum(c["fail"])
    result = []
    for j in range(len(c["location"])):
        f = sum(row[j] for row, failure in zip(c["kill"],c["fail"]) if failure)
        kills = sum(row[j] for row in c["kill"])
        result.append(Fraction(f*f, f_total*kills) if kills else Fraction(0))
    return result

def top(c: dict, sample: list[int]) -> list[int]:
    floor = Fraction(-1 if c["empty"] == "bottom" else 0)
    q = scores(c)
    values = [floor] * c["locations"]
    for j in sample:
        loc = c["location"][j]
        values[loc] = max(values[loc], q[j])
    priority = {x:i for i,x in enumerate(c["tie"])}
    return sorted(range(c["locations"]), key=lambda x:(-values[x],priority[x]))[:len(c["reference"])]

def admissible(c: dict, sample: list[int]) -> bool:
    n = len(c["location"])
    if any(type(x) is not int or x < 0 or x >= n for x in sample) or len(set(sample)) != len(sample):
        return False
    s = set(sample)
    if not set(c["force"]) <= s or s & set(c["forbid"]):
        return False
    if not c["size"][0] <= len(s) <= c["size"][1]:
        return False
    for name in ("a","b"):
        counts = [0]*len(c[name+"_bounds"])
        for j in s:
            counts[c[name][j]] += 1
        if any(not low <= count <= high for count,(low,high) in zip(counts,c[name+"_bounds"])):
            return False
    return True

def branches(c: dict):
    q = scores(c)
    priority = {x:i for i,x in enumerate(c["tie"])}
    floor = Fraction(-1 if c["empty"] == "bottom" else 0)
    ref = set(c["reference"])
    for inside in sorted(ref):
        for outside in range(c["locations"]):
            if outside in ref:
                continue
            pivots = [-1] if priority[outside] < priority[inside] else []
            pivots += [j for j,l in enumerate(c["location"]) if l == outside]
            for pivot in pivots:
                threshold = floor if pivot == -1 else q[pivot]
                if (floor,-priority[inside]) >= (threshold,-priority[outside]):
                    continue
                blocked = [j for j,l in enumerate(c["location"]) if l == inside and (q[j],-priority[inside]) >= (threshold,-priority[outside])]
                yield [inside,outside,pivot], blocked, ([] if pivot == -1 else [pivot])

def network(c: dict, blocked: list[int], forced: list[int], upper: int):
    na,nb = len(c["a_bounds"]),len(c["b_bounds"])
    nv = 2 + na + nb
    edge = []
    for i,(lo,hi) in enumerate(c["a_bounds"]):
        edge.append((0,2+i,lo,hi))
    start = len(edge)
    no = set(blocked) | set(c["forbid"])
    yes = set(forced) | set(c["force"])
    for j,(a,b) in enumerate(zip(c["a"],c["b"])):
        edge.append((2+a,2+na+b,int(j in yes),int(j not in no)))
    for i,(lo,hi) in enumerate(c["b_bounds"]):
        edge.append((2+na+i,1,lo,hi))
    edge.append((1,0,c["size"][0],min(c["size"][1],upper)))
    return nv,edge,start

def circulation(c: dict, blocked: list[int], forced: list[int], upper: int):
    COUNTERS["networks"] += 1
    nv, original, start = network(c,blocked,forced,upper)
    for i,(u,v,lo,hi) in enumerate(original):
        if lo > hi:
            return None, {"kind":"interval", "edge":i}
    ss,tt = nv,nv+1
    g = [[] for _ in range(nv+2)]
    def add(u,v,cap):
        idx = len(g[u])
        g[u].append([v,len(g[v]),cap])
        g[v].append([u,idx,0])
        return u,idx,cap
    demand = [0]*nv
    handles=[]
    for u,v,lo,hi in original:
        handles.append(add(u,v,hi-lo))
        demand[v] += lo
        demand[u] -= lo
    target=0
    for v,d in enumerate(demand):
        if d>0:
            add(ss,v,d)
            target += d
        elif d<0:
            add(v,tt,-d)
    sent=0
    while True:
        parent=[None]*(nv+2)
        parent[ss]=(-1,-1)
        queue=deque([ss])
        while queue and parent[tt] is None:
            u=queue.popleft()
            COUNTERS["search_states"] += 1
            for eidx,(v,rev,cap) in enumerate(g[u]):
                COUNTERS["edge_scans"] += 1
                if cap>0 and parent[v] is None:
                    parent[v]=(u,eidx)
                    queue.append(v)
        if parent[tt] is None:
            reached=[i for i,p in enumerate(parent) if p is not None]
            break
        amount=10**9
        v=tt
        while v!=ss:
            u,idx=parent[v]; amount=min(amount,g[u][idx][2]);v=u
        v=tt
        while v!=ss:
            u,idx=parent[v];rev=g[u][idx][1]
            g[u][idx][2]-=amount;g[v][rev][2]+=amount;v=u
        sent+=amount
        COUNTERS["augmentations"] += 1
    if sent!=target:
        return None,{"kind":"cut", "vertices":reached}
    selected=[]
    for j in range(len(c["location"])):
        i=start+j
        u,idx,cap=handles[i]
        value=original[i][2]+cap-g[u][idx][2]
        if value:
            if value != 1:
                raise RuntimeError("non-binary mutant flow in integral circulation")
            selected.append(j)
    return selected,None

def produce(c: dict) -> dict:
    validate(c)
    base, proof = circulation(c,[],[],c["size"][1])
    if base is None:
        return {"case_id":c["id"],"status":"infeasible_policy","proof":proof}
    bs=list(branches(c))
    best=None
    for _,blocked,forced in bs:
        upper=c["size"][1] if best is None else len(best)-1
        sample,_=circulation(c,blocked,forced,upper)
        if sample is None:
            continue
        low=c["size"][0]
        high=len(sample)
        while low<high:
            mid=(low+high)//2
            attempt,_=circulation(c,blocked,forced,mid)
            if attempt is None:
                low=mid+1
            else:
                sample=attempt
                high=len(attempt)
        best=sample
    upper=c["size"][1] if best is None else len(best)-1
    records=[]
    for ident,blocked,forced in bs:
        sample,proof=circulation(c,blocked,forced,upper)
        if sample is not None:
            raise AssertionError("unproved lower bound")
        records.append({"branch":ident,"proof":proof})
    cert={"case_id":c["id"],"status":"stable" if best is None else "counterexample","branches":records}
    if best is None:
        cert["base_sample"]=base
    else:
        cert["sample"]=best
        cert["size"]=len(best)
    return cert

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    p.add_argument("certificate",type=Path)
    args=p.parse_args()
    try:
        c=json.loads(args.case.read_text())
        cert=produce(c)
        args.certificate.write_text(json.dumps(cert,sort_keys=True,indent=2)+"\n")
    except (OSError,ValueError,KeyError,TypeError) as e:
        p.exit(2,str(e)+"\n")
if __name__=="__main__":
    main()
