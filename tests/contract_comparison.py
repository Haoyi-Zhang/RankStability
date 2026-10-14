"""Same-information direct enumeration and phase-local work on frozen cases.

No new matrices, native compiler, upstream program, network or score tuning.
The independent direct path uses no certificate/producer/checker semantics.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
import baselines
import certify
import checker
from generated_oracle_audit import solve_counts
from secondary_baselines import COUNTER_SCOPE, validate_counter_accounting


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    require(not sys.flags.optimize, 'optimized-execution')
    require(out.is_relative_to((ROOT / 'evidence').resolve()) and not out.exists(), 'new-evidence-path-required')
    out.mkdir(parents=True, exist_ok=False)
    begin = time.monotonic()
    bindings = {}
    def load(path):
        bindings[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text(encoding='utf-8'))
    old_primary = {r['id']: r for r in csv.DictReader((ROOT / 'results/campaign/primary.csv').open(encoding='utf-8'))}
    primary_csv = ROOT / 'results/campaign/primary.csv'
    bindings[primary_csv.relative_to(ROOT).as_posix()] = hashlib.sha256(primary_csv.read_bytes()).hexdigest()
    old_external = {r['id']: r for r in load(ROOT / 'results/external-matrices.json')['records']}
    pairs = [(path, ROOT / 'data/metadata' / path.name, 'owned')
             for path in sorted((ROOT / 'data/cases').glob('*.json'))]
    pairs += [(path, path.with_suffix('.meta.json'), 'public')
              for path in sorted((ROOT / 'external/cases').glob('*.json')) if not path.name.endswith('.meta.json')]
    require(len(pairs) == 275, 'frozen-domain-count')
    inputs, rows, skipped = [], [], []
    totals, strata = Counter(), {}
    producer_sum = Counter(); interval_sum = Counter()
    for index, (path, metadata, origin) in enumerate(pairs):
        require(time.monotonic() - begin < 180, '180-second-total-budget')
        case, meta = load(path), load(metadata)
        inputs.append(dict(case=case, metadata=meta, case_path=path.relative_to(ROOT).as_posix(), origin=origin))
        if len(case['location']) > 15:
            skipped.append(dict(id=case['id'], mutants=len(case['location']), reason='predeclared direct-enumeration cap 15'))
            continue
        category = meta['category']
        group = 'public' if origin == 'public' else category
        for key in certify.COUNTERS: certify.COUNTERS[key] = 0
        checker.STEPS = 0
        started = time.perf_counter()
        certificate = certify.produce(case)
        producer_seconds = time.perf_counter() - started
        status = checker.check(case, certificate)
        producer_counters = dict(certify.COUNTERS)
        checker_steps = checker.STEPS
        started = time.perf_counter()
        direct = solve_counts(case)
        direct_seconds = time.perf_counter() - started
        require((status, certificate.get('size')) == (direct['status'], direct['minimum']), 'direct-contract-disagreement')
        historical = old_external[case['id']] if origin == 'public' else old_primary[case['id']]
        old_minimum = historical['minimum']
        old_minimum = None if old_minimum in ('', None) else int(old_minimum)
        require((status, certificate.get('size')) == (historical['status'], old_minimum), 'historical-outcome-drift')
        intervals = baselines.marginal(case)
        combined = dict(certify.COUNTERS)
        interval_counters = {key: combined[key] - producer_counters[key] for key in combined}
        sample_index = index if origin == 'owned' else index - 260
        seed = (271828 if origin == 'owned' else 314159) + sample_index
        sampled = baselines.random_samples(case, seed)
        require(intervals['result'] != 'stable' or status == 'stable', 'unsound-interval')
        require(sampled['observed_minimum'] is None or status == 'counterexample', 'unsound-random')
        row = dict(id=case['id'], origin=origin, category=category, status=status,
                   minimum=certificate.get('size'), direct=direct, certificate=certificate,
                   counter_scope=COUNTER_SCOPE, producer_counters=producer_counters,
                   interval_counters=interval_counters, combined_flow_counters=combined,
                   checker_steps=checker_steps, intervals=intervals, random=sampled, seed=seed,
                   producer_wall_seconds=producer_seconds, direct_wall_seconds=direct_seconds)
        validate_counter_accounting(row)
        rows.append(row)
        measures = Counter(queries=1, direct_masks=direct['subsets'])
        measures[status] += 1
        measures['interval_stable'] += int(intervals['result'] == 'stable')
        measures['random_refuters'] += int(sampled['observed_minimum'] is not None)
        measures['random_minimum_larger'] += int(sampled['observed_minimum'] is not None and sampled['observed_minimum'] > direct['minimum'])
        totals.update(measures); strata.setdefault(group, Counter()).update(measures)
        producer_sum.update(producer_counters); interval_sum.update(interval_counters)
    require(len(skipped) == 2 and {r['id'] for r in skipped} == {'fixture-03', 'fixture-17'}, 'excluded-domain-drift')
    def save(name, value):
        with (out / name).open('x', encoding='utf-8') as handle:
            json.dump(value, handle, indent=2, sort_keys=True); handle.write('\n')
    save('inputs.json', inputs)
    save('outcomes.json', rows)
    summary = dict(queries=len(rows), excluded=skipped, agreement=len(rows), disagreements=0,
                   totals=dict(totals), groups={k: dict(v) for k, v in strata.items()},
                   producer_flow_counters=dict(producer_sum), interval_flow_counters=dict(interval_sum),
                   time_ordered_sampling_histories_observed=0, generated_program_templates=10,
                   ambiguity_source_pairs=20, public_project_version_snapshots=5,
                   direct_scope='Same full finite inputs and status/global-minimum obligation; no portable cut certificate is produced by direct enumeration.',
                   work_scope='Flow counters, partial checker steps and direct-mask visits are different units, not a speedup ratio or complete primitive-work accounting.',
                   native_execution=False, upstream_program_execution=False)
    save('summary.json', summary)
    source_files = ['src/certify.py', 'src/checker.py', 'src/baselines.py',
                    'tests/generated_oracle_audit.py', 'tests/secondary_baselines.py',
                    'tests/contract_comparison.py']
    for name in source_files:
        bindings[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    save('environment.json', dict(command=[sys.executable, '-B', *sys.argv], python=sys.version,
                                 platform=platform.platform(), workers=1, wall_seconds=time.monotonic()-begin,
                                 native_execution=False, upstream_program_execution=False,
                                 memory_limit_enforced=False, input_and_source_sha256=bindings))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
