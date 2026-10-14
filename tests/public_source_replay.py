"""Replay actual source-corrected public slices without native project execution.

The immutable upstream source audit is separate. Historical bytes are not edited.
"""
from __future__ import annotations
import argparse
from collections import Counter
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
import external_cases
from generated_oracle_audit import solve_counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if sys.flags.optimize or out.exists() or not out.is_relative_to((ROOT / 'evidence').resolve()):
        raise ValueError('new evidence output and nonoptimized interpreter required')
    out.mkdir(parents=True, exist_ok=False)
    begun = time.monotonic()
    source = ROOT / 'evidence/public-source-correction'
    historical = json.loads((ROOT / 'results/external-matrices.json').read_text())
    old = {r['id']: r for r in historical['records']}
    audit = json.loads((source / 'historical-source-audit.json').read_text())
    good = {r['id'] for r in audit['records'] if r['blob_matches'] and
            r['exact_selected_rows'] == r['local_selected_rows']}
    if good != {'defects4j-chart-24', 'defects4j-closure-28', 'defects4j-lang-54', 'defects4j-math-32'}:
        raise ValueError('static source audit domain changed')
    records, inputs, bindings = [], [], {}
    totals, profiles = Counter(), {}
    for project_index, original in enumerate(sorted(external_cases.SNAPSHOTS.glob('*.json'))):
        path = source / 'input' / original.name if original.stem == 'defects4j-time-10' else original
        meta, operators, fail, kill, names = external_cases._read_snapshot(path)
        for p in (path, path.with_suffix('.csv')):
            bindings[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
        for profile_index, profile in enumerate(external_cases.PROFILES):
            case = external_cases.build_case(meta, operators, fail, kill, profile)
            case_meta = case.pop('external_metadata')
            cert = certify.produce(case)
            status = checker.check(case, cert)
            direct = solve_counts(case)
            if (status, cert.get('size')) != (direct['status'], direct['minimum']):
                raise ValueError('independent direct disagreement')
            interval = baselines.marginal(case)
            random = baselines.random_samples(case, 314159 + project_index * 3 + profile_index)
            prior = old[case['id']]
            record = dict(id=case['id'], project=meta['project'], bug_id=meta['bug_id'],
                          profile=profile, status=status, minimum=cert.get('size'),
                          direct=direct, interval=interval, random=random, certificate=cert,
                          historical_population=dict(status=prior['status'], minimum=prior['minimum'],
                              feasible_samples=prior['feasible_samples'], refuting_samples=prior['refuting_samples']),
                          source_input=path.relative_to(ROOT).as_posix())
            inputs.append(dict(case=case, metadata=case_meta, selected_test_names=names))
            records.append(record)
            counts = Counter(cases=1, masks=direct['subsets'], feasible=direct['feasible_samples'],
                             refuters=direct['refuting_samples'], random_hits=int(random['observed_minimum'] is not None))
            counts[status] += 1
            totals.update(counts); profiles.setdefault(profile, Counter()).update(counts)
    summary = dict(cases=15, projects=5, direct_agreement=15, totals=dict(totals),
                   profiles={k: dict(v) for k, v in profiles.items()},
                   changed_source_slice='Time-10: six absent test names, one changed failure row and a differing operator row in the historical slice.',
                   mutation_semantics='Upstream fixed-version Major kill logs; separate faulty-version trigger labels. Not mutations or output differences of the faulty program.',
                   native_execution=False, upstream_program_execution=False, source_location_maps_available=False,
                   time_ordered_sampling_histories_observed=0)
    def save(name, value):
        with (out / name).open('x', encoding='utf-8') as handle:
            json.dump(value, handle, sort_keys=True, indent=2); handle.write('\n')
    save('cases.json', inputs); save('outcomes.json', records); save('summary.json', summary)
    for name in ('tests/public_source_replay.py', 'src/external_cases.py', 'src/certify.py', 'src/checker.py',
                 'src/baselines.py', 'tests/generated_oracle_audit.py',
                 'results/external-matrices.json', 'evidence/public-source-correction/historical-source-audit.json'):
        bindings[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    save('environment.json', dict(command=[sys.executable, '-B', *sys.argv], python=sys.version,
             platform=platform.platform(), workers=1, wall_seconds=time.monotonic()-begun,
             native_execution=False, upstream_program_execution=False, input_and_source_sha256=bindings))
    print(json.dumps(summary, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
