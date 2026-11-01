"""Segmented, paired diagnostic report for the frozen supplemental challenge set.

Usage from the V7.1 project root:
  python3 hajj_challenge_v1/challenge_report.py --results challenge_v71.jsonl
Reports policy-aligned action and latent-label selective accuracy separately.
No external dependencies and no model calls.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import statistics

LEVELS={'LOW':0,'MEDIUM':1,'HIGH':2}

def read_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf8').splitlines() if x.strip()]

def mean(items):
    return round(statistics.mean(items),3) if items else None

def score(rows, gold):
    found={(str(x.get('seed')),x['case_id'],x['condition']):x for x in rows}
    if len(found)!=len(rows):raise ValueError('Duplicate seed / case / condition rows')
    groups=defaultdict(list)
    for x in rows:
        if x['case_id'] not in gold:raise ValueError('Unknown case: '+x['case_id'])
        groups[x['condition']].append(x)
    result={}
    for cond, subset in sorted(groups.items()):
        grp=defaultdict(list)
        for r in subset:grp[gold[r['case_id']]['case_group']].append(r)
        def metrics(chunk):
            tot=len(chunk); valid=[];accepted=[];status_ok=[];oracle_ok=[]
            expected_abstentions=0;correct_abstentions=0;wrong_abstentions=0
            under=over=0;wrong_decisions=0
            for r in chunk:
                g=gold[r['case_id']];d=r.get('decision') or {};trace=r.get('trace') or {}
                if trace.get('schema_valid') is not True: continue
                valid.append(r)
                is_accepted=d.get('status')=='DECISION' and d.get('risk_level') in LEVELS
                if is_accepted:
                    accepted.append(r)
                    if d['risk_level']!=g['gold_label']:
                        wrong_decisions+=1
                        if LEVELS[d['risk_level']]<LEVELS[g['gold_label']]:under+=1
                        else:over+=1
                if d.get('status')==g['oracle_expected_status']:
                    status_ok.append(r)
                    if d['status']=='ABSTAIN':
                        if set(d.get('verify_fields') or [])==set(g['oracle_expected_verify_fields']):oracle_ok.append(r)
                    elif d.get('risk_level')==g['oracle_expected_risk_level']:oracle_ok.append(r)
                if g['oracle_expected_status']=='ABSTAIN':
                    expected_abstentions+=1
                    if d.get('status')=='ABSTAIN':correct_abstentions+=1
                elif d.get('status')=='ABSTAIN':wrong_abstentions+=1
            return {
                'rows':tot,'schema_valid':len(valid),'schema_validity':round(len(valid)/tot,4),
                'coverage':round(len(accepted)/tot,4),
                'accepted_decisions':len(accepted),
                'selective_accuracy':round((len(accepted)-wrong_decisions)/len(accepted),4) if accepted else None,
                'all_case_accuracy':round((len(accepted)-wrong_decisions)/tot,4),
                'correct_policy_status':len(status_ok),
                'policy_status_agreement':round(len(status_ok)/tot,4),
                'policy_action_and_verification_agreement':round(len(oracle_ok)/tot,4),
                'expected_policy_abstentions_among_valid':expected_abstentions,
                'appropriate_abstentions':correct_abstentions,
                'unnecessary_abstentions':wrong_abstentions,
                'over_escalations_against_latent_truth':over,
                'under_escalations_against_latent_truth':under,
                'mean_calls':mean([(r.get('trace') or {}).get('agent_calls_this_pass',0) for r in chunk]),
                'mean_latency_ms':mean([(r.get('trace') or {}).get('latency_ms_this_pass',0) for r in chunk]),
                'mean_input_tokens':mean([(r.get('trace') or {}).get('input_tokens',0) for r in chunk]),
                'mean_output_tokens':mean([(r.get('trace') or {}).get('output_tokens',0) for r in chunk]),
            }
        result[cond]={'overall':metrics(subset),'by_group':{g:metrics(x) for g,x in sorted(grp.items())}}
    by_key={(r['case_id'],str(r['seed']),r['condition']):r for r in rows}
    conditions=sorted(groups)
    paired={}
    if len(conditions)==2:
        a,b=conditions
        shared=set((case,seed) for case,seed,cond in by_key if cond==a)&set((case,seed) for case,seed,cond in by_key if cond==b)
        same=0;different=0;b_better=a_better=0
        for case,seed in shared:
            u,v=by_key[(case,seed,a)],by_key[(case,seed,b)]
            du,dv=u.get('decision') or {},v.get('decision') or {}
            lu=(du.get('status'),du.get('risk_level')) if (u.get('trace') or {}).get('schema_valid') is True else ('INVALID',None)
            lv=(dv.get('status'),dv.get('risk_level')) if (v.get('trace') or {}).get('schema_valid') is True else ('INVALID',None)
            same+=lu==lv;different+=lu!=lv
            truth=gold[case]['gold_label']
            correct_u=lu==('DECISION',truth)
            correct_v=lv==('DECISION',truth)
            b_better+=correct_v and not correct_u
            a_better+=correct_u and not correct_v
        paired={'baseline':a,'candidate':b,'matched_case_seed_pairs':len(shared),
                'same_status_and_level':same,'different_status_or_level':different,
                'candidate_only_correct_vs_latent_truth':b_better,
                'baseline_only_correct_vs_latent_truth':a_better,
                'note':'This is a diagnostic challenge set, not an independent deployment safety evaluation.'}
    return {'conditions':result,'paired':paired,'interpretation_notes':[
        'Latent gold_label is the clean synthetic input scored by the published classroom policy.',
        'Oracle policy status is based only on visible reliable fields; an appropriate abstention is not a classification failure.',
        'Trust metadata is not acted upon by V7 beyond quality flags; this does not test actual cross-agent communication.',
        'A balanced synthetic challenge set does not imply Hajj field validity.',
    ]}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--results',required=True)
    parser.add_argument('--gold',default=str(Path(__file__).with_name('challenge_gold_private.jsonl')))
    parser.add_argument('--out',default=None)
    args=parser.parse_args()
    golds=read_jsonl(args.gold); gold={g['case_id']:g for g in golds}
    rows=read_jsonl(args.results)
    report=score(rows,gold)
    content=json.dumps(report,indent=2,ensure_ascii=False)
    print(content)
    if args.out:Path(args.out).write_text(content+'\n',encoding='utf8')

if __name__=='__main__':main()
