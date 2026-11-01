"""Reproducible, gold-blind-at-inference evaluation for the Hajj-AI course study.
No external dependencies. All denominators and failure categories are explicit.
"""
import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ORDER = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
RATE_COLUMNS = ('schema_validity', 'coverage', 'selective_accuracy', 'all_case_accuracy', 'review_valid_rate', 'beneficial_flip_rate', 'harmful_flip_rate', 'specialist_validity')
METRICS = RATE_COLUMNS + ('mean_latency_ms', 'mean_calls', 'mean_input_tokens', 'mean_output_tokens')


def read_jsonl(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def load_gold(path):
    gold = {}
    for row in read_jsonl(path):
        key, label = row['case_id'], row['gold_label']
        if key in gold or label not in ORDER:
            raise ValueError('Duplicate case or unrecognized gold label: ' + key)
        gold[key] = label
    return gold


def run_level(decision, schema_valid):
    if not schema_valid or decision.get('status') != 'DECISION':
        return None
    level = decision.get('risk_level')
    return level if level in ORDER else None


def score_seed(rows, gold):
    if not rows:
        raise ValueError('No rows to score')
    n = len(rows)
    seen = set()
    counts = defaultdict(int)
    latencies, calls, inputs, outputs = [], [], [], []
    for row in rows:
        case_id = row['case_id']
        if case_id in seen:
            raise ValueError('Duplicate evaluated case ' + case_id)
        seen.add(case_id)
        if case_id not in gold:
            raise ValueError('Missing gold for ' + case_id)
        true = gold[case_id]
        trace = row.get('trace') or {}
        decision = row.get('decision') or {}
        schema_valid = trace.get('schema_valid') is True
        if schema_valid:
            counts['schema_valid'] += 1
        else:
            counts['fallback_or_failure'] += 1
        pred = run_level(decision, schema_valid)
        if pred is not None:
            counts['decisions'] += 1
            if pred == true:
                counts['correct'] += 1
            elif ORDER[pred] < ORDER[true]:
                counts['under_escalation'] += 1
            else:
                counts['over_escalation'] += 1
        elif schema_valid and decision.get('status') == 'ABSTAIN':
            counts['model_abstains'] += 1
        if trace.get('specialist_reports_valid') is True:
            counts['all_specialist_reports_valid'] += 1
        if trace.get('coordinator_retry_attempted') is True:
            counts['coordinator_retries'] += 1
        if trace.get('review_attempted') is True:
            counts['reviews_attempted'] += 1
            if trace.get('review_valid') is True:
                counts['reviews_valid'] += 1
            before = trace.get('pre_review_decision') or {}
            orig = run_level(before, schema_valid)
            if orig is not None and pred is not None and orig != pred:
                if orig != true and pred == true:
                    counts['beneficial_flips'] += 1
                elif orig == true and pred != true:
                    counts['harmful_flips'] += 1
                else:
                    counts['other_flips'] += 1
            if orig is not None and pred is None:
                counts['decision_to_abstain'] += 1
        for name, target in (('latency_ms_this_pass', latencies), ('agent_calls_this_pass', calls),
                             ('input_tokens', inputs), ('output_tokens', outputs)):
            x = trace.get(name)
            if isinstance(x, (int, float)) and math.isfinite(x):
                target.append(x)
    def rate(num, denom):
        return round(num / denom, 6) if denom else None
    return {
        'cases': n, 'schema_validity': rate(counts['schema_valid'], n),
        'coverage': rate(counts['decisions'], n),
        'selective_accuracy': rate(counts['correct'], counts['decisions']),
        'all_case_accuracy': rate(counts['correct'], n),
        'review_valid_rate': rate(counts['reviews_valid'], counts['reviews_attempted']),
        'beneficial_flip_rate': rate(counts['beneficial_flips'], counts['reviews_attempted']),
        'harmful_flip_rate': rate(counts['harmful_flips'], counts['reviews_attempted']),
        'specialist_validity': rate(counts['all_specialist_reports_valid'], n) if any('specialist_reports_valid' in (r.get('trace') or {}) for r in rows) else None,
        'mean_latency_ms': round(statistics.mean(latencies), 2) if latencies else None,
        'mean_calls': round(statistics.mean(calls), 3) if calls else None,
        'mean_input_tokens': round(statistics.mean(inputs), 2) if inputs else None,
        'mean_output_tokens': round(statistics.mean(outputs), 2) if outputs else None,
        **{x: counts[x] for x in ('schema_valid','fallback_or_failure','decisions','correct',
            'under_escalation','over_escalation','model_abstains','reviews_attempted',
            'reviews_valid','beneficial_flips','harmful_flips','other_flips','decision_to_abstain',
            'all_specialist_reports_valid','coordinator_retries')},
    }


def analyze(rows, gold):
    groups = defaultdict(list)
    for row in rows:
        groups[(str(row['condition']), str(row['seed']))].append(row)
    per_seed = []
    for (cond, seed), batch in sorted(groups.items()):
        per_seed.append({'condition': cond, 'seed': seed, **score_seed(batch, gold)})
    by_condition = defaultdict(list)
    for r in per_seed: by_condition[r['condition']].append(r)
    aggregate = []
    for cond, seeds in sorted(by_condition.items()):
        result = {'condition': cond, 'seeds': len(seeds)}
        for key in METRICS:
            vals = [r[key] for r in seeds if r[key] is not None]
            result[key + '_mean'] = round(statistics.mean(vals), 6) if vals else None
            result[key + '_sd'] = round(statistics.stdev(vals), 6) if len(vals) >= 2 else None
        result['total_cases_across_seeds'] = sum(x['cases'] for x in seeds)
        aggregate.append(result)
    return per_seed, aggregate


def paired_comparison(rows, gold, reference, candidate):
    by_key = {(str(r['seed']), r['case_id'], r['condition']): r for r in rows}
    pairs = set((s, i) for (s, i, c) in by_key if c == reference) & set((s, i) for (s, i, c) in by_key if c == candidate)
    totals = defaultdict(int)
    for seed, case_id in pairs:
        a, b = by_key[(seed, case_id, reference)], by_key[(seed, case_id, candidate)]
        true = gold[case_id]
        a_level = run_level(a.get('decision') or {}, (a.get('trace') or {}).get('schema_valid') is True)
        b_level = run_level(b.get('decision') or {}, (b.get('trace') or {}).get('schema_valid') is True)
        x, y = a_level == true, b_level == true
        if a_level is not None and b_level is not None:
            totals['both_accepted'] += 1
            if x and y: totals['both_accepted_both_correct'] += 1
            elif x: totals['both_accepted_reference_only'] += 1
            elif y: totals['both_accepted_candidate_only'] += 1
            else: totals['both_accepted_both_wrong'] += 1
        totals['both_correct' if x and y else 'reference_only' if x else 'candidate_only' if y else 'both_not_correct'] += 1
    return {'reference': reference, 'candidate': candidate, 'paired_seed_case_runs': len(pairs), **totals,
            'note': 'Paired observations of the same cases across seeds are NOT independent cases.'}


def save_csv(path, records):
    if not records: return
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, list(records[0].keys()))
        w.writeheader(); w.writerows(records)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--results', required=True)
    p.add_argument('--gold', required=True)
    p.add_argument('--out', default='scored')
    p.add_argument('--reference', default='single_factorized_v7')
    p.add_argument('--candidate', default='multi_factorized_v7')
    a=p.parse_args()
    rows=list(read_jsonl(a.results)); gold=load_gold(a.gold)
    per, agg=analyze(rows,gold)
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    save_csv(out/'per_seed.csv',per);save_csv(out/'mean_sd.csv',agg)
    pair=paired_comparison(rows,gold,a.reference,a.candidate)
    (out/'paired_comparison.json').write_text(json.dumps(pair,indent=2),encoding='utf-8')
    print(json.dumps({'aggregate':agg, 'paired':pair},indent=2,ensure_ascii=False))

if __name__=='__main__': main()
