# Fixed-evidence ranking and crossing-quota certificates

These are hand-written mathematical proofs. Finite executable checks accompany them, but neither the general argument nor the checker is mechanically verified.

## 1. Contract

Let M be n mutants, V be ell locations, and loc:M→V assign exactly one location per mutant. Let K be a t-by-n binary matrix and fail a t-bit vector with F=sum(fail)>0. Define f_j=sum_i fail_i K_ij, d_j=sum_i K_ij, and q_j=f_j²/(F d_j) when d_j>0, otherwise q_j=0. All q_j lie in [0,1]. Squaring preserves the order of nonnegative Ochiai scores. Freeze these scores before sampling.

The empty floor e is either −1 (bottom) or 0. For a sample S, v_S(l)=max({e}∪{q_j:j∈S,loc(j)=l}). A fixed permutation pi, with smaller pi(l) preferred, defines key(x,l)=(x,−pi(l)) ordered lexicographically. This is a strict total order across distinct locations. Top_k(S) is a set, not an ordered list. The input supplies a distinct k-element set R; it need not equal Top_k(M).

Each mutant belongs to one A group and one B group. A sample is admissible iff its counts lie in every group interval, L≤|S|≤U, it contains every forced mutant and excludes every forbidden mutant. All bounds are integers between zero and n, with each lower endpoint no larger than its upper endpoint. Inputs with invalid syntax or conflicting forced/forbidden declarations are rejected. Well-formed but globally infeasible policies receive a distinct infeasible result, not a vacuous stability result.

## 2. Exact branch decomposition

**Lemma 1 (pairwise crossing).** Top_k(S)≠R iff some a∈R and b∉R have key(v_S(b),b)>key(v_S(a),a).

Proof. If R is the top set, every member precedes every nonmember. Conversely, if Top_k(S) differs from R, choose b in Top_k(S)\R and a in R\Top_k(S). The strict total order puts b before a. This principle is standard, including necessary top-k sets in partial voting profiles; it is not claimed as a novel general ranking theorem.

For each a∈R,b∉R and each mutant j at b, define a real branch with threshold q_j only when key(e,a)<key(q_j,b). Force j and forbid every mutant h at a with key(q_h,a)≥key(q_j,b). Also include a sentinel branch with threshold e and no forced pivot when pi(b)<pi(a); apply the same blocking rule. A sentinel is a lower-bound witness; it does not assert that b is empty.

**Lemma 2 (threshold completeness).** A sample has a crossing iff it satisfies the base policy and at least one branch's additional membership constraints.

Proof. For soundness, in a real branch the selected pivot ensures v_S(b)≥q_j. Every selected insider mutant has a key strictly below the threshold key, and the explicit floor guard gives the same strict inequality for e. Taking the maximum leaves a strictly below b. The sentinel argument is identical using v_S(b)≥e. For completeness, take a crossing pair. If b has a selected mutant, choose one attaining its maximum; q_j≥e and every insider key, including its floor, is strictly lower. Thus the branch guard holds and none of its blocked mutants occurs in S. If b is empty, it has value e, while a has value at least e. A crossing is then possible only when a also has value e and b wins the fixed tie, so the sentinel exists and S avoids its blockers. This handles e=0 with selected zero-score mutants as well as e=−1.

The floor guard is indispensable. With two zero-score mutants, an earlier insider a, later outsider b, zero floor and S={b}, removing a's mutants does not lower a below zero. A producer without the guard can invent a crossing. The retained regression arose during actual development.

If n_out is the number of mutants outside R, the branch count is at most B=k(n_out+ell−k). Blockers can be constructed in O(Bn) score comparisons. Duplicate thresholds may yield redundant branches but do not invalidate completeness.

## 3. Integral circulation

For one branch and a size upper bound u, construct vertices s,t, one per A group and one per B group. Add s→A_i with the A quota interval; one distinct A_a(j)→B_b(j) arc for every mutant j; B_i→t with its B quota interval; and t→s with [L,min(U,u)]. The mutant arc's lower bound is one iff forced by the base policy or branch; its upper bound is zero iff forbidden by either. Parallel mutant arcs remain distinct.

**Lemma 3.** This network has an integral feasible circulation iff the branch has an admissible sample of size at most u.

Proof. From S, put one on selected mutant arcs and zero on others, put each group count on its adjacent quota arc, and put |S| on t→s. Quotas and conservation hold. Conversely, each mutant arc in an integral circulation has value zero or one. Conservation at an A or B vertex equates the relevant quota arc to its selected count. Conservation at s and t equates t→s to the total count. Lower and upper bounds impose exactly the branch, membership and size conditions. An arc whose lower bound exceeds its upper bound is immediately impossible.

For a well-formed bounded arc (x,y,l,h), introduce residual capacity h−l, and let d(v)=sum_in l−sum_out l. Add a super-source SS→v of capacity d(v) for d(v)>0 and v→TT of capacity −d(v) for d(v)<0. Let D=sum_{d(v)>0}d(v). Since total demand is zero, total TT capacity is also D.

A residual flow saturating D reconstructs a circulation by adding lower bounds: residual outgoing minus incoming equals d(v), canceling the lower-bound imbalance. Conversely every circulation yields such a residual flow. Integral augmenting paths preserve integral values. The producer uses breadth-first augmenting paths. As capacities are integers, every augmentation sends at least one unit; here D≤n(a+b+2), so the number of augmentations is polynomial even without appealing to a strongly polynomial flow bound. Each search visits O(E+V) adjacency items.

**Lemma 4 (checkable obstruction).** If no circulation exists, either an original interval is contradictory or there is a transformed cut X with SS∈X, TT∉X and initial crossing capacity cap(X)<D.

Proof. Run integral augmentations until TT is unreachable. Let X be reachable vertices in the residual graph. Every forward arc leaving X is saturated and every arc entering X carries zero net crossing flow in the opposite direction. The current flow value therefore equals the initial capacity of the cut. If D was not saturated, this capacity is below D. Conversely, any SS–TT flow of value D must carry net D across each such cut and cannot exceed its capacity. Thus the displayed inequality alone proves impossibility. The checker needs only the original case and cut vertex set, not the search history or a claimed maximum-flow value.

## 4. Certificate theorem and optimization

There are three results. Infeasible-policy returns a base-network obstruction. Stable returns one admissible base sample and an obstruction for every regenerated branch at upper U. Counterexample returns an admissible sample S whose top set differs from R, and obstructions for every branch at upper |S|−1.

**Theorem 1 (soundness, completeness, minimum cardinality).** The three forms characterize, respectively, base infeasibility, nonvacuous universal invariance, and an unstable policy with a globally minimum-cardinality refuter.

Proof. Lemma 3 and the base obstruction establish infeasibility. The base sample in the stable form rules out vacuity; Lemmas 2–4 exclude every crossing and hence every changed top set. In the counterexample form, the checked sample proves a change, while the complete branch obstruction family rules out any changed top set of smaller size. This is global minimum cardinality, not merely inclusion minimality. Conversely, if the base is infeasible Lemma 4 supplies an obstruction; if stable, every branch is infeasible and a base sample exists; if unstable, choose any minimum refuter, which exists in the finite family, and apply Lemma 4 to all smaller-size branches. No certificate of a particular sample's unique optimality is claimed.

For production, first find a base sample. Search each branch for a sample at upper U or one less than the best size already found. Within a feasible branch, feasibility is monotone in the queried upper bound. Binary search from L to the found cardinality locates its minimum. Finally reconstruct every branch obstruction at the common final bound. At most O((B+1)log(n+1)) flow calls suffice, interpreting log(n+1) as at least one. Both the number of networks and their capacities have polynomial encoding size. The checker uses O(tn+Bn+B(E+V)) elementary rational/edge operations, apart from straightforward permutation lookup; cached priorities remove the latter factor. The delivered checker uses direct permutation lookup, adding at most an ell factor to those comparisons. It performs no max-flow search.

## 5. Why joint quotas matter, but need not help on a workload

Take four mutants with (location,score)=(A,1),(B,1/2),(A,1/3),(B,1/4). Assign A-partition labels (0,1,0,1), B-partition labels (0,1,1,0), require exactly one per group and size two. The only samples are {0,1} and {2,3}. A strictly beats B in both. Yet the exact marginal minimum of A is 1/3 and the marginal maximum of B is 1/2. Their overlap does not prove a crossing because those extrema occur in different feasible samples. Relaxing B admits {1,2}, which does refute A. This is an existence separation, not evidence of frequent practical benefit; the exact marginal baseline matches every stable generated-program result in the actual campaign.

Minimum size need not equal L. With three groups on each side, quota [1,3] and size [3,5], use a high A mutant at edge (1,1) and four lower B mutants at (0,0),(1,0),(2,1),(2,2). A three-edge admissible matching contains the A mutant. A refuter must delete it; then every remaining edge is forced by a degree-one endpoint, giving minimum four. This is an explicit edge-cover construction, not a new general edge-cover theorem.

## 6. A sharp boundary at a third quota partition

The circulation reduction uses exactly two independent partition labels: each mutant is one ordinary edge between its A group and B group. With a third label, mutants become 3-uniform hyperedges.

**Theorem 2.** Feasibility with three partition systems is NP-complete, even when every group has exact quota one, the global size is fixed, and there are no forced or forbidden mutants.

Proof. A selected set is a polynomial witness. Reduce perfect three-dimensional matching. Let X, Y and Z be disjoint sets of size q and T a set of triples. Create one mutant for each t=(x,y,z) in T and assign its three quota labels x, y and z. Give every group quota [1,1] and require exactly q selected mutants. A feasible sample covers every element of each coordinate exactly once and is therefore a perfect three-dimensional matching; every perfect matching is feasible. The construction is polynomial. Unless P=NP, the two-partition producer cannot extend to all such instances by merely adding a layer. Unless NP=coNP, not every infeasible three-partition instance has a polynomially bounded, polynomial-time-checkable certificate. This is a feasibility boundary, not a proof that ranking instability itself first becomes hard at three partitions.

The semantic regression exhausts all 256 sub-hypergraphs of the 2x2x2 universe and checks 64 seeded 3x3x3 instances by independently enumerating perfect matchings and exact-quota selections. This is a finite check of the reduction map, not a proof of NP-completeness. The shipped JSON schema rejects a third partition.

## 7. Hardness of unrestricted membership formulas

Consider the unbounded-size mathematical model and allow arbitrary CNF formulas over membership variables instead of two-partition quotas. From a CNF C(x_1,...,x_m), create z at location A with kill column (1,0), w at B with column (1,1), and x_i mutants at B with column (0,0); fail=(1,0). Scores are 1,1/2,0. Impose w and clauses z∨C_i for every clause of C. Set R={A} and either permitted floor.

**Theorem 3.** Instability for this policy language is NP-complete, and stability is coNP-complete, even when the policy is promised feasible and location-mutant incidence is a forest of stars.

Proof. A selected sample is a polynomial witness: evaluate the formula and ranking. The policy is always feasible by selecting z,w. If z is selected then A wins. Otherwise mandatory w makes B win, and the policy reduces exactly to C on the selected x_i. Thus a refuting sample exists iff C is satisfiable. This is a polynomial reduction from CNF-SAT, giving NP-hardness and, by complementation under the nonempty-policy promise, coNP-hardness. Each mutant is adjacent to exactly one location, so the location-only incidence graph is a disjoint union of stars, with treewidth at most one. The graph omits CNF constraint incidence; it cannot justify tractability for that larger language unless P=NP. The implemented 40-mutant limit is not an asymptotic hardness domain. The implementation rejects CNF input fields.

## 8. Observable ambiguity of correction provenance

For each positive integer c define faulty code a=x+c; b=a+c; return b. One designated correction replaces the first assignment with a=x; another replaces the second with b=a. Both reference programs return x+c for every x, whereas the faulty program returns x+2c. Applying the same mutants to the same faulty code yields identical mutant outputs, kill matrices and test pass/fail labels in both worlds. The designated single-edit correction origins differ.

**Proposition 4.** These observations, even with a stable top set under a declared policy, do not identify the designated correction origin.

Proof. An observation-only function receives identical inputs in both worlds and must return the same origin, so it cannot be right in both. For randomized decisions and a uniform mixture of the two worlds, success is at most one half. For stability, force the increment mutant at the first location; it changes output on every failing test and has score one. With that location earlier in the fixed tie order it remains top-ranked in all admissible samples. Thus the counterexample persists under nonvacuous stable ranking. This proposition concerns recorded correction provenance, not human behavior or a uniquely defined metaphysical fault cause.
