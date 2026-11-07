"""Live model benchmarking runner. Requires GEMINI_API_KEY; never fabricates model responses.

Baseline variants and V5 variants use the same case IDs and generation seeds.
Real API charges apply. Use --limit 1 for smoke tests and --resume for interrupted runs.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from hajj_baseline.providers import LLMProvider, ProviderError
from hajj_baseline.schema import validate_case
from m5_agent import M5Agent

CONDITIONS = ('single_factorized_v7','multi_factorized_v7')

def load_cases(path):
    cases = [validate_case(json.loads(line)) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(cases) != len({x['case_id'] for x in cases}): raise ValueError('Duplicate case ids')
    return cases


def make_agent(name, provider):
    if name not in CONDITIONS:
        raise ValueError(f'Unsupported condition in M5 submission: {name}')
    return M5Agent(provider, mode='single' if name == 'single_factorized_v7' else 'multi')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--cases',default='m5_data/test_locked_cases.jsonl')
    p.add_argument('--out',default='live_results.jsonl')
    p.add_argument('--seeds',nargs='+',type=int,default=[11,42,77])
    p.add_argument('--conditions',nargs='+',choices=CONDITIONS,default=list(CONDITIONS))
    p.add_argument('--model',default='gemini-3.5-flash-lite')
    p.add_argument('--temperature',type=float,default=1.0)
    p.add_argument('--limit',type=int,default=None)
    p.add_argument('--resume',action='store_true')
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--case-delay',type=float,default=10.0,help='Idle delay between complete cases; excluded from per-pass latency')
    a=p.parse_args()
    if not 0 <= a.temperature <= 2: p.error('temperature must be between 0 and 2')
    if a.case_delay < 0: p.error('--case-delay must be nonnegative')
    cases=load_cases(a.cases)[:a.limit]
    combinations=len(cases)*len(a.seeds)*len(a.conditions)
                                                                                          
    material = {'model': a.model, 'temperature': a.temperature,
                'seeds': a.seeds, 'conditions': a.conditions,
                'cases_sha256': hashlib.sha256(Path(a.cases).read_bytes()).hexdigest(),
                'limit': a.limit,
                'code_sha256': {filename: hashlib.sha256(Path(filename).read_bytes()).hexdigest()
                    for filename in ('run_experiment.py','m5_agent.py','m5_policy.json',
                                     'hajj_baseline/schema.py','hajj_baseline/providers.py')}}
    fingerprint = hashlib.sha256(json.dumps(material,sort_keys=True).encode()).hexdigest()
    if a.dry_run:
        print(json.dumps({'runs':combinations,'cases':len(cases),'seeds':a.seeds,'conditions':a.conditions, 'experiment_sha256':fingerprint,
                          'WARNING':'Actual API call count is higher, due to specialists, review, retry.'},indent=2))
        return
    if not os.getenv('GEMINI_API_KEY'): p.error('Missing GEMINI_API_KEY (set it in your own terminal).')
    dest=Path(a.out)
    meta_path=dest.with_name(dest.name+'.meta.json')
    if dest.exists() and not a.resume: p.error('Results file exists. Use --resume or another --out path to avoid duplication.')
    if a.resume and dest.exists():
        if not meta_path.exists(): p.error('Cannot resume: experiment metadata missing.')
        old=json.loads(meta_path.read_text(encoding='utf-8'))
        if old.get('experiment_sha256') != fingerprint:
            p.error('Cannot resume: model, code, cases, seeds, or conditions changed. Use a new output path.')
    else:
        if meta_path.exists(): p.error('Stale experiment metadata exists: choose another output path.')
        meta_path.write_text(json.dumps({'experiment_sha256':fingerprint,**material},indent=2),encoding='utf-8')
    completed=set()
    if dest.exists():
        for line in dest.read_text(encoding='utf-8').splitlines():
            if line.strip():
                d=json.loads(line)
                completed.add((d['condition'],str(d['seed']),d['case_id']))
    with dest.open('a', encoding='utf-8') as out:
        for seed in a.seeds:
            provider = LLMProvider(model=a.model,seed=seed,temperature=a.temperature)
            for case in cases:
                for condition in a.conditions:
                    key=(condition,str(seed),case['case_id'])
                    if key in completed: continue
                    try:
                        run=make_agent(condition, provider).evaluate(case)
                    except (ProviderError, TimeoutError, OSError) as exc:
                        print(f'API failure on {key}: {type(exc).__name__}: {exc}',file=sys.stderr)
                        print('No row saved. Resume after fixing the error.',file=sys.stderr)
                        raise SystemExit(2)
                    record={'condition':condition,'seed':str(seed),'case_id':case['case_id'],
                            'decision':run.decision,'trace':run.trace}
                    out.write(json.dumps(record,ensure_ascii=False)+'\n');out.flush()
                    completed.add(key)
                    print(f"{condition} seed={seed} {case['case_id']} status={run.decision['status']}"
                          f" risk={run.decision['risk_level']} calls={run.trace['agent_calls_this_pass']}",flush=True)
                    if condition.endswith('_v7') and run.trace.get('schema_valid') is False:
                        print(f"  M5 validation failure: stage={run.trace.get('failure_stage')}"
                              f" error={run.trace.get('schema_error')}",file=sys.stderr,flush=True)
                if a.case_delay:
                    time.sleep(a.case_delay)
    print(f'Completed {len(completed)} rows in {dest} (not yet scored).')

if __name__=='__main__':main()
