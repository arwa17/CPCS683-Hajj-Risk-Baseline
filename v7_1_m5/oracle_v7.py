"""Deterministic upper-reference for executing the authored V7 policy; NO Gemini calls.
This is a benchmark, not a deployable risk system or a MAS competitor.
"""
import argparse
import json
from pathlib import Path
from factorized_v7 import FIELD_ORDER, aggregate, policy_band
from hajj_baseline.schema import validate_case


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cases',default='v7_synthetic_data/dev_cases.jsonl')
    ap.add_argument('--out',default='v7_oracle.jsonl')
    args=ap.parse_args()
    output=[]
    for line in Path(args.cases).read_text(encoding='utf8').splitlines():
        if not line.strip():continue
        case=validate_case(json.loads(line))
        bands={}
        for path in FIELD_ORDER:
            d,f=path.split('.')
            x=case['domains'][d][f]
            bands[path]=policy_band(path,x['value']) if x['quality']=='observed' else None
        decision,diagnostic=aggregate(bands,case)
        output.append({'condition':'deterministic_oracle_v7','seed':'0','case_id':case['case_id'],
                       'decision':decision,
                       'trace':{'schema_valid':True,'agent_calls_this_pass':0,
                       'input_tokens':0,'output_tokens':0,'policy_diagnostic':diagnostic}})
    Path(args.out).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in output),encoding='utf8')
    print(f'Wrote {len(output)} policy-only deterministic results to {args.out}')

if __name__=='__main__':main()
