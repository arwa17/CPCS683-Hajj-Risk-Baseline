"""Strict M5 harness: frozen golden set, three-seed validation, reproducible CSV and Markdown.

Requires only Python standard library; never invokes Gemini or changes any labels.
"""
import argparse, csv, json, hashlib, statistics
from pathlib import Path
from collections import defaultdict
from scoring import analyze, paired_comparison, read_jsonl, load_gold, save_csv

CASES=Path('v7_synthetic_data/test_locked_cases.jsonl')
GOLD=Path('v7_synthetic_data/test_locked_gold.jsonl')
MANIFEST=Path('v7_synthetic_data/manifest.json')
CONDITIONS=('single_factorized_v7','multi_factorized_v7')
SEEDS=('11','42','77')

def verify_hashes():
    meta=json.loads(MANIFEST.read_text())['test']
    for path,key in ((CASES,'cases_sha256'),(GOLD,'gold_sha256')):
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=meta[key]: raise RuntimeError(f'Frozen input changed: {path}')

def combine_and_check(paths, allow_incomplete):
    expected={x['case_id'] for x in read_jsonl(CASES)}
    gold=load_gold(GOLD)
    assert expected==set(gold), 'Cases and gold labels do not match'
    found={}
    for path in paths:
        if not Path(path).exists():
            if allow_incomplete: continue
            raise FileNotFoundError(path)
        for r in read_jsonl(path):
            key=(r['condition'],str(r['seed']),r['case_id'])
            if r['condition'] not in CONDITIONS or str(r['seed']) not in SEEDS or r['case_id'] not in expected:
                raise ValueError(f'Unexpected evaluation row {key}')
            if key in found: raise ValueError(f'Duplicate evaluation row {key}')
            found[key]=r
    missing=[(cond,seed,cid) for cond in CONDITIONS for seed in SEEDS for cid in sorted(expected)
             if (cond,seed,cid) not in found]
    if missing and not allow_incomplete:
        raise ValueError(f'Incomplete three-seed M5 results: {len(missing)} missing rows. First: {missing[:4]}')
    return [found[k] for k in sorted(found)],missing

def run_identity(rows):
    identities = set()
    for row in rows:
        trace = row.get('trace') or {}
        identity = (trace.get('model'), trace.get('prompt_version'), trace.get('temperature'))
        if any(value is None for value in identity):
            raise ValueError('Missing model, prompt version, or temperature in evaluation trace')
        identities.add(identity)
    if len(identities) != 1:
        raise ValueError('Mixed experiment versions or model settings: separate runs before scoring')
    model, prompt_version, temperature = next(iter(identities))
    return {'model':model, 'prompt_version':prompt_version, 'temperature':temperature}


def extra_metrics(rows):
    groups=defaultdict(list)
    for r in rows: groups[r['condition'],str(r['seed'])].append(r)
    result=[]
    for (condition,seed), batch in sorted(groups.items()):
        traces=[r.get('trace') or {} for r in batch]
        x=[t['observed_band_accuracy'] for t in traces if isinstance(t.get('observed_band_accuracy'),(float,int))]
        result.append({'condition':condition,'seed':seed,'cases':len(batch),
            'mean_observed_band_accuracy':round(statistics.mean(x),6) if x else None,
            'band_accuracy_trace_coverage':round(len(x)/len(batch),6),
            'complete_trajectory_rate':round(sum(t.get('schema_valid') is True and t.get('agent_calls_this_pass')==(1 if condition=='single_factorized_v7' else 3) for t in traces)/len(batch),6)})
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='results/m5_35_score')
    p.add_argument('--allow-incomplete',action='store_true',help='Preview only. Do not submit as three-seed evidence.')
    p.add_argument('--results',nargs='+',default=['results/v71_35_all_seeds.jsonl'])
    a=p.parse_args()
    verify_hashes()
    rows,missing=combine_and_check(a.results,a.allow_incomplete)
    if not rows: raise ValueError('No evaluation results')
    identity=run_identity(rows)
    per,agg=analyze(rows,load_gold(GOLD))
    comp=extra_metrics(rows)
    paired=paired_comparison(rows,load_gold(GOLD),*CONDITIONS)
    out=Path(a.out);out.mkdir(exist_ok=True,parents=True)
    save_csv(out/'per_seed.csv',per)
    save_csv(out/'mean_sd.csv',agg)
    save_csv(out/'component_trajectory_per_seed.csv',comp)
    (out/'paired.json').write_text(json.dumps(paired,indent=2),encoding='utf-8')
    status={**identity, 'gold_cases':len(set(r['case_id'] for r in read_jsonl(CASES))),
        'completed_rows':len(rows),'expected_rows':len(SEEDS)*len(CONDITIONS)*36,
        'missing_rows':len(missing),'seeds_completed':sorted(set(r['seed'] for r in per if r['cases']==36)),
        'complete':not missing,
        'WARNING':'PREVIEW ONLY; NOT FINAL THREE-SEED RESULTS' if missing else 'All three seeds complete'}
    (out/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    lines=['# M5 results', '', f"Model: **{identity['model']}**; prompt version: **{identity['prompt_version']}**; temperature: **{identity['temperature']}**.", '',f"Status: **{'COMPLETE' if not missing else 'INCOMPLETE / PREVIEW ONLY'}**",f"Golden cases: **36**; evaluated rows: **{len(rows)}/216**; missing: **{len(missing)}**.",'',
    'Synthetic course-label accuracy is not real-world crowd safety validation. Multi-agent and single-agent must use the same cases and seeds.','',
    '| Condition | Seeds | Coverage (mean ± SD) | Selective accuracy (mean ± SD) | Schema validity (mean ± SD) | Calls/case (mean ± SD) | Latency ms (mean ± SD) |',
    '|---|---:|---:|---:|---:|---:|---:|']
    def val(x):return 'N/A' if x is None else f'{x:.4f}'
    for r in agg:
        def cell(name):return val(r.get(name+'_mean'))+' ± '+val(r.get(name+'_sd'))
        lines.append(f"| {r['condition']} | {r['seeds']} | {cell('coverage')} | {cell('selective_accuracy')} | {cell('schema_validity')} | {cell('mean_calls')} | {cell('mean_latency_ms')} |")
    lines+=['','Component level: `component_trajectory_per_seed.csv` includes observed-field band accuracy and complete-trajectory rate.',
      'Trajectory metric: calls per case, complete three-specialist reporting with valid schema.','',
      'SD across a single seed is **undefined**, not 0. Repeated seeds share the same 36 cases.','',
      'The aggregation policy is explicit and synthetic, so high scores measure policy compliance rather than medical/operational validity.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(status,indent=2))

if __name__=='__main__': main()
