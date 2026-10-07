"""Self-contained finite ranking/certificate regression; no saved evidence."""
from __future__ import annotations

import copy
from fractions import Fraction
from functools import cmp_to_key
import itertools
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import checker
import certify
import oracle


def independent_scores(case):
    columns = list(zip(*case["kill"]))
    failures = [index for index, value in enumerate(case["fail"]) if value == 1]
    return [Fraction(sum(column[index] for index in failures) ** 2,
                     len(failures) * sum(column)) if sum(column) else Fraction(0)
            for column in columns]


def literal_ranking(case, sample):
    scores = independent_scores(case)
    floor = Fraction(-1 if case["empty"] == "bottom" else 0)
    values = {loc: max([floor] + [scores[j] for j in sample if case["location"][j] == loc])
              for loc in range(case["locations"])}
    # Distinct tie ranks guarantee a total order; no checker/producer helper.
    ranked = sorted(case["tie"], key=lambda loc: -values[loc])
    return set(ranked[:len(case["reference"])])


def scan_ranking_reference(case, sample, ratios):
    """Named index-scan comparison reference, not a historical checker copy."""
    values = [(-1, 1) if case["empty"] == "bottom" else (0, 1)] * case["locations"]
    for j in sample:
        old = values[case["location"][j]]
        value = ratios[j]
        if value[0] * old[1] > old[0] * value[1]:
            values[case["location"][j]] = value

    def order(left, right):
        difference = values[right][0] * values[left][1] - values[left][0] * values[right][1]
        return (difference > 0) - (difference < 0) or case["tie"].index(left) - case["tie"].index(right)

    return set(sorted(range(case["locations"]), key=cmp_to_key(order))[:len(case["reference"])])


def literal_admissible(case, sample):
    chosen = set(sample)
    if not case["size"][0] <= len(chosen) <= case["size"][1]:
        return False
    if not set(case["force"]) <= chosen or chosen.intersection(case["forbid"]):
        return False
    return all(low <= sum(labels[j] == group for j in chosen) <= high
               for side in ("a", "b")
               for labels in (case[side],)
               for group, (low, high) in enumerate(case[side + "_bounds"]))


def literal_outcome(case):
    admissible = []
    for bits in itertools.product((0, 1), repeat=len(case["location"])):
        sample = [j for j, bit in enumerate(bits) if bit]
        if literal_admissible(case, sample):
            admissible.append(sample)
    refuters = [sample for sample in admissible if literal_ranking(case, sample) != set(case["reference"])]
    return ("infeasible_policy" if not admissible else "counterexample" if refuters else "stable",
            min(map(len, refuters)) if refuters else None)


def branch_reference(case):
    scores = independent_scores(case)
    floor = Fraction(-1 if case["empty"] == "bottom" else 0)
    priorities = {loc: case["tie"].index(loc) for loc in range(case["locations"])}
    result = []
    for inside in sorted(case["reference"]):
        for outside in range(case["locations"]):
            if outside in case["reference"]:
                continue
            pivots = ([-1] if priorities[outside] < priorities[inside] else [])
            pivots += [j for j, loc in enumerate(case["location"]) if loc == outside]
            for pivot in pivots:
                threshold = floor if pivot == -1 else scores[pivot]
                bound = (threshold, -priorities[outside])
                if (floor, -priorities[inside]) >= bound:
                    continue
                blocked = [j for j, loc in enumerate(case["location"])
                           if loc == inside and (scores[j], -priorities[inside]) >= bound]
                result.append(([inside, outside, pivot], blocked, [] if pivot == -1 else [pivot]))
    return result


def checked_trace(case, certificate):
    original = checker.verify_impossible
    calls = []

    def capture(subject, blocked, forced, upper, proof):
        calls.append((list(blocked), list(forced), upper, copy.deepcopy(proof)))
        return original(subject, blocked, forced, upper, proof)

    checker.STEPS = 0
    with patch.object(checker, "verify_impossible", side_effect=capture):
        try:
            value = ("accepted", checker.check(case, certificate))
        except (ValueError, KeyError, TypeError, IndexError) as error:
            value = ("rejected", type(error).__name__, str(error))
    return value, checker.STEPS, calls


def finite_cases():
    rng = random.Random(20261008)
    for index in range(32):
        n = index % 9
        ell = (2, 6, 100)[index % 3]
        tie = rng.sample(range(ell), ell)
        case = {
            "id": "local-priority", "fail": [1, 0, 1],
            "kill": [[0 if index % 4 == 0 else 1 if index % 4 == 1
                      else (index + j + row) % 2 for j in range(n)] for row in range(3)],
            "location": [rng.randrange(ell) for _ in range(n)], "locations": ell, "tie": tie,
            "a": [j % 2 for j in range(n)], "b": [(j // 2) % 2 for j in range(n)],
            "a_bounds": [[0, n], [0, n]], "b_bounds": [[0, n], [0, n]], "size": [0, n],
            "force": [], "forbid": [], "reference": rng.sample(range(ell), min(3, ell)),
            "empty": "bottom",
        }
        mode = index % 5
        if mode == 1:
            chosen = [j for j in range(n) if rng.randrange(2)]
            case["size"] = [len(chosen)] * 2
            for side in ("a", "b"):
                case[side + "_bounds"] = [[sum(case[side][j] == group for j in chosen)] * 2
                                          for group in range(2)]
        elif mode == 2 and n > 1:
            case.update(force=[0], forbid=[n - 1], size=[1, n])
        elif mode == 3 and n:
            case["a_bounds"].append([1, 1])  # locally valid, empty positive-quota group
        elif mode == 4:
            case["reference"] = list(range(min(ell, 10)))
        for floor in ("bottom", "zero"):
            variant = copy.deepcopy(case)
            variant["empty"] = floor
            yield variant


def authored_cases():
    crossed = {
        "id": "crossed", "fail": [1, 0, 0, 0],
        "kill": [[1, 1, 1, 1], [0, 1, 1, 1], [0, 0, 1, 1], [0, 0, 0, 1]],
        "location": [0, 1, 0, 1], "locations": 2, "tie": [0, 1],
        "a": [0, 1, 0, 1], "b": [0, 1, 1, 0], "a_bounds": [[1, 1], [1, 1]],
        "b_bounds": [[1, 1], [1, 1]], "size": [2, 2], "force": [], "forbid": [],
        "reference": [0], "empty": "bottom",
    }
    yield crossed
    relaxed = copy.deepcopy(crossed)
    relaxed["id"] = "relaxed-crossing"
    relaxed["b_bounds"] = [[0, 4], [0, 4]]
    yield relaxed
    for reference in ([0], [1]):
        empty = copy.deepcopy(crossed)
        empty.update(id="empty-universe", fail=[1], kill=[[]], location=[], a=[], b=[],
                     a_bounds=[[0, 0]], b_bounds=[[0, 0]], size=[0, 0], reference=reference)
        yield empty
    tied = copy.deepcopy(crossed)
    tied.update(id="floor-tie", fail=[1], kill=[[0, 0]], location=[0, 1], a=[0, 0], b=[0, 0],
                a_bounds=[[0, 2]], b_bounds=[[0, 2]], size=[1, 2], empty="zero")
    yield tied
    all_locations = copy.deepcopy(tied)
    all_locations.update(id="all-locations", reference=[0, 1], tie=[1, 0])
    yield all_locations


def corruption_variants(certificate):
    for field, replacement in (("case_id", "wrong"), ("status", "unknown")):
        changed = copy.deepcopy(certificate)
        changed[field] = replacement
        yield changed
    changed = copy.deepcopy(certificate)
    changed["extra"] = 0
    yield changed
    if certificate.get("branches"):
        changed = copy.deepcopy(certificate)
        changed["branches"].pop()
        yield changed
        changed = copy.deepcopy(certificate)
        changed["branches"][0]["branch"][2] = True
        yield changed
        if len(certificate["branches"]) > 1:
            changed = copy.deepcopy(certificate)
            changed["branches"][0], changed["branches"][1] = changed["branches"][1], changed["branches"][0]
            yield changed
    changed = copy.deepcopy(certificate)
    proof = changed.get("proof", (changed.get("branches") or [{"proof": None}])[0]["proof"])
    if proof is not None:
        proof["kind"] = "not-a-proof"
        yield changed
    if certificate["status"] == "counterexample":
        changed = copy.deepcopy(certificate)
        changed["size"] = 1.0 * certificate["size"]
        yield changed


class TiePriorityTests(unittest.TestCase):
    def test_all_bounded_subsets_rankings_minima_and_independent_branches(self):
        for case in itertools.chain(authored_cases(), finite_cases()):
            unchanged = copy.deepcopy(case)
            ratios = checker.prepare(case)
            for bits in itertools.product((0, 1), repeat=len(case["location"])):
                sample = [j for j, bit in enumerate(bits) if bit]
                expected = literal_ranking(case, sample)
                self.assertEqual(checker.ranked(case, sample, ratios), expected)
                self.assertEqual(scan_ranking_reference(case, sample, ratios), expected)
            expected, minimum = literal_outcome(case)
            self.assertEqual(oracle.solve(case)[:2], (expected, minimum))
            certificate = certify.produce(case)
            trace = checked_trace(case, certificate)
            self.assertEqual(trace[0], ("accepted", expected))
            self.assertEqual(certificate.get("size"), minimum)
            branches = branch_reference(case)
            if expected == "infeasible_policy":
                self.assertEqual(trace[2], [([], [], case["size"][1], certificate["proof"])])
            else:
                upper = case["size"][1] if expected == "stable" else certificate["size"] - 1
                self.assertEqual([record["branch"] for record in certificate["branches"]],
                                 [identity for identity, _, _ in branches])
                self.assertEqual(trace[2], [(blocked, forced, upper, record["proof"])
                                           for (_, blocked, forced), record
                                           in zip(branches, certificate["branches"], strict=True)])
            self.assertEqual(case, unchanged)

    def test_scan_reference_complete_trace_steps_and_corruptions(self):
        for case in itertools.chain(authored_cases(), finite_cases()):
            certificate = certify.produce(case)
            for candidate in itertools.chain([certificate], corruption_variants(certificate)):
                actual = checked_trace(case, candidate)
                with patch.object(checker, "ranked", side_effect=scan_ranking_reference):
                    reference = checked_trace(case, candidate)
                self.assertEqual(actual, reference)
                if candidate != certificate:
                    self.assertEqual(actual[0][0], "rejected")

    def test_lazy_public_lookup_and_validated_branch_priority_reuse(self):
        class CountingTie(list):
            def __init__(self, values):
                super().__init__(values)
                self.lookups = []

            def index(self, value):
                self.lookups.append(value)
                return super().index(value)

        case = next(authored_cases())
        case.update(locations=100, tie=list(reversed(range(100))), reference=[99])
        case["tie"] = CountingTie(case["tie"])
        ratios = checker.prepare(case)
        self.assertEqual(checker.ranked(case, [], ratios), {99})
        self.assertEqual(len(case["tie"].lookups), len(set(case["tie"].lookups)))
        self.assertLessEqual(len(case["tie"].lookups), 100)
        stable = copy.deepcopy(case)
        stable["reference"] = [0, 1]  # fix every mutant; only floor locations trail
        stable.update(force=list(range(4)), size=[4, 4],
                      a_bounds=[[0, 4], [0, 4]], b_bounds=[[0, 4], [0, 4]])
        certificate = certify.produce(stable)
        self.assertEqual(certificate["status"], "stable")
        stable["tie"].lookups.clear()
        self.assertEqual(checker.check(stable, certificate), "stable")
        self.assertEqual(stable["tie"].lookups, [])
        singleton = {"locations": 1, "empty": "bottom", "reference": [0]}
        self.assertEqual(checker.ranked(singleton, [], []), {0})  # no tie lookup needed

    def test_same_id_mutation_between_calls_does_not_reuse_priorities(self):
        case = list(authored_cases())[4]
        ratios = checker.prepare(case)
        first = checker.ranked(case, [], ratios)
        case["tie"].reverse()
        second = checker.ranked(case, [], ratios)
        self.assertEqual(first, {0})
        self.assertEqual(second, {1})
        self.assertEqual(second, scan_ranking_reference(case, [], ratios))
        certificate = certify.produce(case)
        first_trace = checked_trace(case, certificate)
        case["tie"].reverse()
        changed = checked_trace(case, certificate)
        self.assertNotEqual(first_trace[0], changed[0])

    def test_invalid_precedence_exact_types_and_caps_are_preserved(self):
        base = next(authored_cases())
        certificate = certify.produce(base)
        for field, value in (("tie", [0, 0]), ("tie", [False, 1]), ("locations", 101),
                             ("locations", True), ("fail", [0] * 4), ("reference", [0, 0]),
                             ("size", [0, 5])):
            case = copy.deepcopy(base)
            case[field] = value
            trace = checked_trace(case, {"case_id": "also-wrong"})
            self.assertEqual(trace[0][0], "rejected")
            self.assertEqual(trace[1:], (0, []))
            self.assertNotEqual(trace[0][-1], "certificate case id")
        for invalid in corruption_variants(certificate):
            self.assertEqual(checked_trace(base, invalid)[0][0], "rejected")
        at_limit = copy.deepcopy(base)
        at_limit["fail"] = [1] + [0] * 199
        at_limit["kill"] = [[0] * 4 for _ in range(200)]
        checker.prepare(at_limit)
        at_limit["fail"].append(0)
        at_limit["kill"].append([0] * 4)
        self.assertEqual(checked_trace(at_limit, certificate)[0][-1], "failing tests")

    def test_floor_sentinel_nonvacuity_and_arbitrary_reference(self):
        cases = list(authored_cases())
        self.assertEqual(literal_outcome(cases[0]), ("stable", None))
        self.assertEqual(literal_outcome(cases[1]), ("counterexample", 2))
        self.assertEqual(literal_outcome(cases[3]), ("counterexample", 0))
        self.assertEqual(branch_reference(cases[5]), [])
        c = copy.deepcopy(cases[4])
        self.assertEqual(literal_outcome(c)[0], "stable")
        c["empty"] = "bottom"
        self.assertEqual(literal_outcome(c), ("counterexample", 1))
        c["a_bounds"] = [[1, 1], [1, 1]]
        c["a"] = [0, 1]
        c["size"] = [1, 1]
        self.assertEqual(literal_outcome(c), ("infeasible_policy", None))
        self.assertEqual(certify.produce(c)["status"], "infeasible_policy")


if __name__ == "__main__":
    unittest.main()
