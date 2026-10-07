"""Portable literal finite reference; no historical code or private-path imports."""
import copy
from fractions import Fraction
import itertools
import random
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import secondary_baselines as subject

def values(case, selected):
    floor = Fraction(-1 if case["empty"] == "bottom" else 0)
    result = [floor] * case["locations"]
    for j in selected:
        killed = sum(row[j] for row in case["kill"])
        numerator = sum(row[j] for row, failed in zip(case["kill"], case["fail"]) if failed)
        score = Fraction(numerator * numerator, sum(case["fail"]) * killed) if killed else Fraction(0)
        result[case["location"][j]] = max(result[case["location"][j]], score)
    return result

def top(case, selected):
    scores = values(case, selected)
    return sorted(range(case["locations"]), key=lambda loc: (-scores[loc], case["tie"].index(loc)))[:len(case["reference"])]

def admits(case, selected):
    if not case["size"][0] <= len(selected) <= case["size"][1]:
        return False
    if not set(case["force"]) <= set(selected) or set(case["forbid"]) & set(selected):
        return False
    return all(low <= sum(case[side][j] == group for j in selected) <= high
               for side in ("a", "b") for group, (low, high) in enumerate(case[side + "_bounds"]))

def exhaustive(case):
    samples = [list(s) for size in range(len(case["location"]) + 1)
               for s in itertools.combinations(range(len(case["location"])), size) if admits(case, s)]
    refuters = [s for s in samples if set(top(case, s)) != set(case["reference"])]
    status = "infeasible_policy" if not samples else "counterexample" if refuters else "stable"
    minimum = min(map(len, refuters)) if refuters else None
    bounds = [[str(min(values(case, s)[l] for s in samples)), str(max(values(case, s)[l] for s in samples))]
              for l in range(case["locations"])] if samples else None
    return status, minimum, bounds

def sampled(case, seed):
    rng = random.Random(seed)
    accepted = attempts = 0
    minimum = None
    while accepted < 64 and attempts < 4096:
        attempts += 1
        size = rng.randint(*case["size"])
        selected = sorted(rng.sample(range(len(case["location"])), size))
        if not admits(case, selected):
            continue
        accepted += 1
        if set(top(case, selected)) != set(case["reference"]):
            minimum = len(selected) if minimum is None else min(minimum, len(selected))
    return dict(result="observed_counterexample" if minimum is not None else "unknown",
                accepted=accepted, attempts=attempts, observed_minimum=minimum)

def fixture(n=4):
    return dict(id="literal", fail=[1, 0], kill=[[int(j % 2 == 0) for j in range(n)], [int(j % 3 == 0) for j in range(n)]],
                location=[j % 3 for j in range(n)], locations=3, tie=[2, 0, 1],
                a=[j % 2 for j in range(n)], b=[(j // 2) % 2 for j in range(n)],
                a_bounds=[[0, n], [0, n]], b_bounds=[[0, n], [0, n]],
                size=[0, n], force=[], forbid=[], reference=[0], empty="bottom")

class SecondaryBaselineTests(unittest.TestCase):
    def test_literal_all_domains(self):
        visits = 0
        for n, floor, reference, policy in itertools.product(range(5), ("bottom", "zero"), ([0], [2], [0, 2]), range(3)):
            c = fixture(n); c["empty"] = floor; c["reference"] = reference.copy()
            if policy == 1:
                c["size"] = [n, n]
            elif policy == 2 and n:
                c["force"] = [0]; c["forbid"] = [n - 1] if n > 1 else []
            for change in subject.CHANGES:
                altered = subject.transform(c, change)
                status, minimum, bounds = exhaustive(altered)
                certificate = subject.certify.produce(altered)
                self.assertEqual(subject.checker.check(altered, certificate), status)
                self.assertEqual(certificate.get("size"), minimum)
                interval = subject.baselines.marginal(altered)
                if status == "infeasible_policy":
                    self.assertEqual(interval["result"], status)
                else:
                    self.assertEqual(interval["bounds"], bounds)
                    if interval["result"] == "stable":
                        self.assertEqual(status, "stable")
                actual = subject.baselines.random_samples(altered, 271828)
                self.assertEqual({k: actual[k] for k in sampled(altered, 271828)}, sampled(altered, 271828))
                visits += 1
        self.assertEqual(visits, 360)

    def test_reference_rules_and_copy_isolation(self):
        c = fixture(); before = copy.deepcopy(c)
        for change in subject.CHANGES:
            result = subject.transform(c, change)
            self.assertEqual(c, before)
            if change in ("k2", "k3"):
                temp = copy.deepcopy(c); temp["reference"] = list(range(int(change[1:])))
                self.assertEqual(result["reference"], top(temp, list(range(4))))
            else:
                self.assertEqual(result["reference"], c["reference"])
            result["kill"][0][0] = 99
            self.assertEqual(c, before)

    def test_empty_zero_floor_supplied_reference(self):
        c = fixture(0); c["reference"] = [1]
        result = subject.transform(c, "zero_floor")
        self.assertEqual(result["reference"], [1])
        self.assertEqual(exhaustive(result)[:2], ("counterexample", 0))

    def test_infeasible_random_budget(self):
        c = fixture(); c["a_bounds"] = [[4, 4], [4, 4]]
        actual = subject.baselines.random_samples(c, 271828)
        self.assertEqual(actual["accepted"], 0)
        self.assertEqual(actual["attempts"], 4096)
        self.assertIsNone(actual["observed_minimum"])
        self.assertEqual(actual["result"], "unknown")
        self.assertEqual(subject.baselines.marginal(c)["result"], "infeasible_policy")

    def test_unavailable_or_unknown_change(self):
        c = fixture(); c["locations"] = 2; c["location"] = [0, 1, 0, 1]; c["tie"] = [1, 0]
        with self.assertRaises(ValueError): subject.transform(c, "k3")
        with self.assertRaises(ValueError): subject.transform(c, "favorable")

    def test_bounds_and_protected_outputs(self):
        for start, stop in ((-1, 2), (1, 1), (0, 982)):
            with self.assertRaises(ValueError): subject.run_shard({}, "unused", start, stop)
        with self.assertRaises(ValueError): subject.save_new(subject.ROOT / "results/never-created.json", {})

    def test_protocol_and_cohort_tampering_rejected(self):
        with self.assertRaises(ValueError): subject.validate_plan({"protocol": {}})
        with self.assertRaises(ValueError):
            subject.validate_plan({"protocol": subject.PROTOCOL, "rows": [], "primary_order": []})

if __name__ == "__main__":
    unittest.main()
