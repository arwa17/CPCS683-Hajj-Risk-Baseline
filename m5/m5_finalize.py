"""Strict M5 harness: frozen golden set, three-seed validation, reproducible CSV and Markdown.

Requires only Python standard library; never invokes Gemini or changes any labels.
"""
import argparse, csv, json, hashlib, statistics
from pathlib import Path
from collections import defaultdict
from scoring import analyze, paired_comparison, read_jsonl, load_gold, save_csv

CASES=Path('m5_data/test_locked_cases.jsonl')
GOLD=Path('m5_data/test_locked_gold.jsonl')
MANIFEST=Path('m5_data/manifest.json')
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


def trajectory_complete(trace, condition):
    if trace.get('schema_valid') is not True:
        return False
    expected = {'single'} if condition=='single_factorized_v7' else {'crowd','health','environment'}
    reports = trace.get('report_bands') or {}
    if set(reports) != expected:
        return False
    attempts = trace.get('report_attempts')
    calls = trace.get('agent_calls_this_pass')
    if isinstance(attempts, dict) and attempts:
        if set(attempts) != expected:
            return False
        if any(not isinstance(a,list) or len(a) not in (1,2) for a in attempts.values()):
            return False
        return calls == sum(len(a) for a in attempts.values())
    return calls == len(expected)


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
            'complete_trajectory_rate':round(sum(trajectory_complete(t,condition) for t in traces)/len(batch),6)})
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='results/m5_scores')
    p.add_argument('--allow-incomplete',action='store_true',help='Preview only. Do not submit as three-seed evidence.')
    p.add_argument('--results',nargs='+',default=['results/m5_runs.jsonl'])
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
    baseline=next(r for r in agg if r['condition']=='single_factorized_v7')
    baseline_rows=sum(r['cases'] for r in per if r['condition']=='single_factorized_v7')
    baseline_comp=[r for r in comp if r['condition']=='single_factorized_v7']
    def pct(metric):
        value=baseline[metric+'_mean']
        sd=baseline[metric+'_sd']
        return 'N/A' if value is None or sd is None else f'{value*100:.2f}% ± {sd*100:.2f} pp'
    def numeric(metric):
        value=baseline[metric+'_mean']
        sd=baseline[metric+'_sd']
        return 'N/A' if value is None or sd is None else f'{value:.4f} ± {sd:.4f}'
    component=[r['mean_observed_band_accuracy'] for r in baseline_comp if r['mean_observed_band_accuracy'] is not None]
    trajectory=[r['complete_trajectory_rate'] for r in baseline_comp]
    component_rate='N/A' if not component else f'{statistics.mean(component)*100:.2f}%'
    trajectory_rate='N/A' if not trajectory else f'{statistics.mean(trajectory)*100:.2f}%'
    label='COMPLETE' if not missing else 'INCOMPLETE (PREVIEW ONLY)'
    lines=[
        '# M5 Evaluation Results',
        '',
        f'**Golden set:** {status["gold_cases"]} synthetic cases | **Baseline:** Single-Agent | **Seeds:** {", ".join(SEEDS)}',
        f'**Model:** {identity["model"]} | **Temperature:** {identity["temperature"]} | **Runs:** {baseline_rows}/{len(SEEDS)*status["gold_cases"]} | **Status:** {label}',
        '',
        '| Baseline metric (mean ± SD across seeds) | Result |',
        '|---|---:|',
        f'| Coverage | {pct("coverage")} |',
        f'| Selective accuracy (accepted decisions only) | {pct("selective_accuracy")} |',
        f'| Schema/policy validity | {pct("schema_validity")} |',
        f'| Calls per case (trajectory metric) | {numeric("mean_calls")} |',
        '',
        f'**Component/trajectory:** Observed-field band accuracy {component_rate} on valid reports; complete trajectories {trajectory_rate}.',
        '',
        '**Scoring:** python3 m5_finalize.py (offline and reproducible).',
        '**Limitation:** Synthetic policy-based labels; no real-world safety validation.',
    ]
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(status,indent=2))

if __name__=='__main__': main()
