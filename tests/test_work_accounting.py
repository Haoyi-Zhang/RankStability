"""Owned finite regressions for phase-local work and same-information semantics."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import secondary_baselines as subject
from generated_oracle_audit import solve_counts
from test_secondary_baselines import fixture, exhaustive


class WorkAccountingTests(unittest.TestCase):
    def test_producer_snapshot_excludes_interval_flow_calls(self):
        case = fixture()
        for key in subject.certify.COUNTERS:
            subject.certify.COUNTERS[key] = 0
        cert = subject.certify.produce(case)
        subject.checker.check(case, cert)
        expected = dict(subject.certify.COUNTERS)
        row = dict(query_index=0, primary_index=0, primary_id=case['id'],
                   change='zero_floor', category='fixture', family='fixture',
                   seed=271828, case=case, status=cert['status'], minimum=cert.get('size'))
        with patch.object(subject, 'validate_plan'):
            actual = subject.run_shard({'rows': [row]}, 'owned', 0, 1)['rows'][0]
        self.assertEqual(actual['producer_counters'], expected)
        self.assertGreater(actual['interval_counters']['networks'], 0)
        subject.validate_counter_accounting(actual)

    def test_components_add_and_do_not_alias(self):
        case = fixture(0)
        cert = subject.certify.produce(case)
        row = dict(query_index=0, primary_index=0, primary_id='empty', change='zero_floor',
                   category='fixture', family='fixture', seed=271828, case=case,
                   status=cert['status'], minimum=cert.get('size'))
        with patch.object(subject, 'validate_plan'):
            actual = subject.run_shard({'rows': [row]}, 'owned', 0, 1)['rows'][0]
        before = copy.deepcopy(actual)
        subject.certify.COUNTERS['networks'] += 99
        self.assertEqual(actual, before)
        subject.validate_counter_accounting(actual)

    def test_accounting_rejects_ambiguous_or_inconsistent_records(self):
        counters = {key: 0 for key in subject.certify.COUNTERS}
        row = dict(counter_scope=subject.COUNTER_SCOPE, producer_counters=counters.copy(),
                   interval_counters=counters.copy(), combined_flow_counters=counters.copy())
        subject.validate_counter_accounting(row)
        for change in ('sum', 'bool', 'missing', 'scope'):
            altered = copy.deepcopy(row)
            if change == 'sum': altered['combined_flow_counters']['networks'] = 1
            if change == 'bool': altered['interval_counters']['networks'] = False
            if change == 'missing': del altered['interval_counters']['networks']
            if change == 'scope': altered['counter_scope'] = 'producer-plus-interval'
            with self.subTest(change=change), self.assertRaises(ValueError):
                subject.validate_counter_accounting(altered)

    def test_record_free_direct_path_does_not_use_producer_or_checker(self):
        case = fixture()
        expected = exhaustive(case)[:2]
        with patch.object(subject.certify, 'produce', side_effect=AssertionError('producer-use')), \
             patch.object(subject.checker, 'check', side_effect=AssertionError('checker-use')):
            actual = solve_counts(case)
        self.assertEqual((actual['status'], actual['minimum']), expected)
        self.assertEqual(actual['subsets'], 16)

    def test_direct_set_claim_distinguishes_empty_reference_and_infeasibility(self):
        case = fixture(0)
        self.assertEqual(solve_counts(case)['status'], 'counterexample')
        case['reference'] = [2]  # earlier tie priority, no selected mutant
        self.assertEqual(solve_counts(case)['status'], 'stable')
        case = fixture(2)
        case['a_bounds'] = [[2, 2], [2, 2]]
        self.assertEqual(solve_counts(case)['status'], 'infeasible_policy')


if __name__ == '__main__':
    unittest.main()
