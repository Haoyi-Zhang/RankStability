"""Regression on the actual immutable-source correction; no upstream execution."""
import csv
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
import external_cases
import certify
import checker
from generated_oracle_audit import solve_counts


class PublicSourceCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / 'evidence/public-source-correction/input/defects4j-time-10.json'

    def test_bound_source_corrected_names_operator_labels_and_failed_kills(self):
        meta, operators, fail, kill, names = external_cases._read_snapshot(self.path)
        self.assertEqual(operators, ['ROR'] * 6 + ['COR'] * 6)
        self.assertEqual(fail, [0] * 8 + [1, 1])
        self.assertEqual(kill[-2:], [[0] * 12, [0] * 12])
        self.assertEqual(names[:8], meta['selected_passing_tests'])
        self.assertEqual(names[-2:], meta['selected_failing_tests'])
        self.assertEqual(meta['blob'], '2413a65b4f7b0490baa4f794ca9f88b41445114c')

    def test_historical_slice_is_distinct_and_stays_available(self):
        old = json.loads((ROOT / 'external/snapshots/defects4j-time-10.json').read_text())
        corrected = json.loads(self.path.read_text())
        self.assertEqual(len(set(old['selected_passing_tests']) - set(corrected['selected_passing_tests'])), 6)
        self.assertNotEqual(old['operators'], corrected['operators'])
        self.assertTrue((ROOT / 'results/external-matrices.json').is_file())

    def test_three_corrected_profiles_match_record_free_direct_status_and_minimum(self):
        meta, operators, fail, kill, _ = external_cases._read_snapshot(self.path)
        for profile, minimum in [('balanced', 5), ('exact', 6), ('relaxed', 4)]:
            case = external_cases.build_case(meta, operators, fail, kill, profile)
            case.pop('external_metadata')
            cert = certify.produce(case)
            self.assertEqual(checker.check(case, cert), 'counterexample')
            direct = solve_counts(case)
            self.assertEqual((direct['status'], direct['minimum']), ('counterexample', minimum))
            self.assertEqual(cert['size'], minimum)

    def test_complete_replay_keeps_negative_baselines_and_actual_population(self):
        report = json.loads((ROOT / 'evidence/public-source-correction/replay/summary.json').read_text())
        self.assertEqual(report['totals'], dict(cases=15, counterexample=15, feasible=26855,
                                               masks=61440, random_hits=15, refuters=23781))
        self.assertFalse(report['native_execution'])
        records = json.loads((ROOT / 'evidence/public-source-correction/replay/outcomes.json').read_text())
        self.assertEqual(sum(row['interval']['result'] == 'stable' for row in records), 0)
        self.assertTrue(all(row['random']['observed_minimum'] is not None for row in records))


if __name__ == '__main__':
    unittest.main()
