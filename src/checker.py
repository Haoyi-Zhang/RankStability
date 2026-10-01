#!/usr/bin/env python3
"""Independent certificate checker: integer arithmetic, no graph search.

This module deliberately imports no producer, ranking, or flow code.
A valid sample proves existence; a cut proves a branch impossible.
"""
from __future__ import annotations
import argparse
from functools import cmp_to_key
import json
from pathlib import Path

STEPS=0

def insist(p, message):
    if not p:
        raise ValueError(message)

def integer(x):
    return type(x) is int

def prepare(c):
    insist(isinstance(c,dict),"case must be an object")
    insist(set(c)=={"id","fail","kill","location","locations","tie","a","b","a_bounds","b_bounds","size","force","forbid","reference","empty"},"unknown or missing input fields")
    insist(isinstance(c["id"],str) and 1<=len(c["id"])<=200,"case id")
    insist(isinstance(c["location"],list),"location labels must be a list")
    n=len(c["location"]); ell=c["locations"]
    insist(integer(ell) and 1<=ell<=100 and n<=40,"dimensions")
    insist(all(integer(x) and 0<=x<ell for x in c["location"]),"location labels")
    insist(isinstance(c["tie"],list) and all(integer(x) for x in c["tie"]) and sorted(c["tie"])==list(range(ell)),"tie permutation")
    f=c["fail"]; mat=c["kill"]
    insist(isinstance(f,list) and 1<=len(f)<=200 and all(integer(x) and x in [0,1] for x in f) and sum(f)>0,"failing tests")
    insist(isinstance(mat,list) and len(mat)==len(f),"matrix rows")
    insist(all(isinstance(row,list) and len(row)==n and all(integer(x) and x in [0,1] for x in row) for row in mat),"binary matrix")
    for side in ["a","b"]:
        quota=c[side+"_bounds"]; labels=c[side]
        insist(isinstance(quota,list) and 1<=len(quota)<=40,"group count")
        insist(isinstance(labels,list) and len(labels)==n and all(integer(x) and 0<=x<len(quota) for x in labels),"group labels")
        insist(all(isinstance(x,list) and len(x)==2 and all(integer(y) for y in x) and 0<=x[0]<=x[1]<=n for x in quota),"quotas")
    insist(isinstance(c["size"],list) and len(c["size"])==2 and all(integer(x) for x in c["size"]) and 0<=c["size"][0]<=c["size"][1]<=n,"size interval")
    for name in ["force","forbid"]:
        seq=c[name]
        insist(isinstance(seq,list) and len(seq)==len(set(seq)) and all(integer(x) and 0<=x<n for x in seq),"forced or forbidden index")
    insist(not set(c["force"]) & set(c["forbid"]),"input membership conflict")
    ref=c["reference"]
    insist(isinstance(ref,list) and 1<=len(ref)<=min(10,ell) and len(ref)==len(set(ref)) and all(integer(x) and 0<=x<ell for x in ref),"reference set")
    insist(c["empty"] in ["bottom","zero"],"empty convention")
    ratios=[]
    for j in range(n):
        killed=0; killed_f=0
        for t,row in enumerate(mat):
            killed+=row[j]
            killed_f+=row[j]*f[t]
        ratios.append((killed_f*killed_f, sum(f)*killed) if killed else (0,1))
    return ratios

def compare(x,y):
    z=x[0]*y[1]-y[0]*x[1]
    return (z>0)-(z<0)

def sample_ok(c,seq):
    insist(isinstance(seq,list) and len(seq)==len(set(seq)),"sample duplicates")
    insist(all(integer(x) and 0<=x<len(c["location"]) for x in seq),"sample index")
    insist(c["size"][0]<=len(seq)<=c["size"][1],"sample size")
    insist(set(c["force"])<=set(seq) and not set(seq)&set(c["forbid"]),"sample membership")
    for side in ["a","b"]:
        for g,(low,high) in enumerate(c[side+"_bounds"]):
            count=sum(c[side][j]==g for j in seq)
            insist(low<=count<=high,"sample quota")

def ranked(c,seq,ratios):
    vals=[(-1,1) if c["empty"]=="bottom" else (0,1) for _ in range(c["locations"])]
    for j in seq:
        loc=c["location"][j]
        if compare(ratios[j],vals[loc])>0:
            vals[loc]=ratios[j]
    def cmp(a,b):
        order=compare(vals[b],vals[a])
        return order if order else c["tie"].index(a)-c["tie"].index(b)
    return set(sorted(range(c["locations"]),key=cmp_to_key(cmp))[:len(c["reference"])])

def verify_impossible(c,blocked,forced,upper,proof):
    global STEPS
    insist(isinstance(proof,dict),"proof format")
    # Ordered edge list is reconstructed from the public instance only.
    first=len(c["a_bounds"]); second=len(c["b_bounds"])
    vertices=2+first+second
    edges=[]
    for i,q in enumerate(c["a_bounds"]):
        edges.append([0,i+2,*q])
    for j in range(len(c["location"])):
        edges.append([2+c["a"][j],2+first+c["b"][j],int(j in forced or j in c["force"]),int(j not in blocked and j not in c["forbid"])])
    for i,q in enumerate(c["b_bounds"]):
        edges.append([i+2+first,1,*q])
    edges.append([1,0,c["size"][0],min(c["size"][1],upper)])
    STEPS+=len(edges)
    if proof.get("kind")=="interval":
        insist(set(proof)=={"kind","edge"},"unknown or missing interval-proof fields")
        i=proof.get("edge")
        insist(integer(i) and 0<=i<len(edges),"interval index")
        insist(edges[i][2]>edges[i][3],"interval is not contradictory")
        return
    insist(proof.get("kind")=="cut","unknown infeasibility proof")
    insist(set(proof)=={"kind","vertices"},"unknown or missing cut-proof fields")
    insist(all(lo<=hi for _,_,lo,hi in edges),"cut on malformed interval")
    cut=proof.get("vertices")
    insist(isinstance(cut,list) and len(cut)==len(set(cut)) and all(integer(x) and 0<=x<vertices+2 for x in cut),"cut labels")
    cut=set(cut); ss=vertices; tt=vertices+1
    insist(ss in cut and tt not in cut,"cut terminals")
    balance=[0]*vertices; capacity=0
    for u,v,lo,hi in edges:
        balance[u]-=lo;balance[v]+=lo
        if u in cut and v not in cut:
            capacity+=hi-lo
    demand=0
    for v,b in enumerate(balance):
        if b>0:
            demand+=b
            if v not in cut:
                capacity+=b
        elif b<0 and v in cut:
            capacity-=b
    STEPS+=len(edges)+len(balance)
    insist(capacity<demand,"cut does not prove infeasibility")

def check(c,cert):
    global STEPS
    ratios=prepare(c)
    insist(isinstance(cert,dict) and cert.get("case_id")==c["id"],"certificate case id")
    status=cert.get("status")
    if status=="infeasible_policy":
        insist(set(cert)=={"case_id","status","proof"},"unknown or missing infeasible-certificate fields")
        verify_impossible(c,[],[],c["size"][1],cert["proof"])
        return status
    insist(status in ["stable","counterexample"],"unknown certificate status")
    if status=="stable":
        insist(set(cert)=={"case_id","status","base_sample","branches"},"unknown or missing stable-certificate fields")
        sample_ok(c,cert["base_sample"])
        upper=c["size"][1]
    else:
        insist(set(cert)=={"case_id","status","sample","size","branches"},"unknown or missing counterexample-certificate fields")
        seq=cert["sample"]
        sample_ok(c,seq)
        insist(integer(cert.get("size")) and cert["size"]==len(seq),"claimed sample size")
        insist(ranked(c,seq,ratios)!=set(c["reference"]),"sample does not refute top-k set")
        upper=len(seq)-1
    records=cert.get("branches")
    insist(isinstance(records,list),"branch array")
    expected=[];floor=(-1,1) if c["empty"]=="bottom" else (0,1)
    for a in sorted(c["reference"]):
        for b in range(c["locations"]):
            if b in c["reference"]:
                continue
            candidates=[]
            if c["tie"].index(b)<c["tie"].index(a):
                candidates.append(-1)
            candidates.extend(j for j in range(len(ratios)) if c["location"][j]==b)
            for m in candidates:
                th=floor if m==-1 else ratios[m]
                base_cmp=compare(floor,th)
                if base_cmp>0 or base_cmp==0 and c["tie"].index(a)<c["tie"].index(b):
                    continue
                blocks=[]
                for j,loc in enumerate(c["location"]):
                    STEPS+=1
                    if loc!=a:continue
                    cmp=compare(ratios[j],th)
                    if cmp>0 or cmp==0 and c["tie"].index(a)<c["tie"].index(b):
                        blocks.append(j)
                expected.append(([a,b,m],blocks,[] if m==-1 else [m]))
    insist(len(records)==len(expected),"missing or extra branch proof")
    for record,(ident,blocks,forced) in zip(records,expected):
        insist(isinstance(record,dict) and set(record)=={"branch","proof"},"branch fields")
        branch=record.get("branch")
        insist(isinstance(branch,list) and len(branch)==3 and all(integer(x) for x in branch),"branch labels")
        insist(branch==ident,"branch identity or order")
        verify_impossible(c,blocks,forced,upper,record["proof"])
    return status

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case",type=Path)
    parser.add_argument("certificate",type=Path)
    args=parser.parse_args()
    try:
        c=json.loads(args.case.read_text());cert=json.loads(args.certificate.read_text())
        status=check(c,cert)
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        parser.exit(2,"REJECT: "+str(exc)+"\n")
    print("ACCEPT:",status,"checker_steps=",STEPS)
if __name__=="__main__":
    main()
