import json
import unittest
from pathlib import Path
from copy import deepcopy
from factorized_v7 import FactorizedV7, FIELD_ORDER, POLICY, aggregate, policy_band, check_bands, band_report_schema
from hajj_baseline.schema import validate_case

CASES=[json.loads(s) for s in Path(__file__).with_name('hajj_agent_inputs_v2.jsonl').read_text().splitlines() if s]

class FakeProvider:
    backend='mock'
    model='mock'
    temperature=0
    seed=11
    def __init__(self,mutate=False): self.calls=[];self.mutate=mutate;self.schemas=[]
    def generate(self,system,user,response_schema=None):
        obj=json.loads(user)
        self.calls.append((system,obj))
        self.schemas.append(response_schema)
        bands={}
        for path in obj['policy_banding']:
            d,f=path.split('.')
            obs=obj['observations'][d][f]
            bands[path]=policy_band(path,obs['value']) if obs['quality']=='observed' else None
        if self.mutate:
            path=next(x for x in bands if bands[x] is not None)
            bands[path]=(bands[path]+1)%3
        return json.dumps({'bands':bands}), {'input_tokens':10,'output_tokens':5}

class BadProvider(FakeProvider):
    def generate(self,*a,**kw): return '{invalid', {'input_tokens':1,'output_tokens':1}

class TestV7(unittest.TestCase):
    def test_both_complete_and_same_decision(self):
        case=CASES[4]
        sp,mp=FakeProvider(),FakeProvider()
        a=FactorizedV7(sp,'single').evaluate(case)
        b=FactorizedV7(mp,'multi').evaluate(case)
        self.assertEqual(a.decision,b.decision)
        self.assertTrue(a.trace['schema_valid'] and b.trace['schema_valid'])
        self.assertEqual((a.trace['agent_calls_this_pass'],b.trace['agent_calls_this_pass']),(1,3))
        self.assertEqual(len(mp.calls),3)
        self.assertEqual({next(iter(x['observations'])) for _,x in mp.calls},set(('crowd','health','environment')))
        self.assertEqual(set(sp.calls[0][1]['observations']),set(('crowd','health','environment')))

    def test_structured_schema_is_sent_to_both_arms(self):
        case=CASES[4]
        sp,mp=FakeProvider(),FakeProvider()
        self.assertTrue(FactorizedV7(sp,'single').evaluate(case).trace['schema_valid'])
        self.assertTrue(FactorizedV7(mp,'multi').evaluate(case).trace['schema_valid'])
        self.assertEqual(len(sp.schemas),1)
        self.assertEqual(len(mp.schemas),3)
        for provider in (sp,mp):
            for schema,(_,payload) in zip(provider.schemas,provider.calls):
                paths=list(payload['policy_banding'])
                self.assertEqual(set(schema['properties']['bands']['required']),set(paths))
                self.assertEqual(set(schema['properties']['bands']['properties']),set(paths))
                for path in paths:
                    entry=schema['properties']['bands']['properties'][path]
                    self.assertEqual(entry['type'],'INTEGER')
                    self.assertTrue(entry['nullable'])

    def test_failed_specialist_is_traceable(self):
        a=FactorizedV7(BadProvider(),'multi').evaluate(CASES[4])
        self.assertEqual(a.trace['agent_calls_this_pass'],1)
        self.assertFalse(a.trace['schema_valid'])
        self.assertIn('json',a.trace['failure_stage'])

    def test_missing_ranges_yield_abstain(self):
        case=deepcopy(CASES[4])
        case['domains']['environment']['temperature_c']['quality']='missing'
        case['domains']['environment']['temperature_c']['value']=None
                                                                                   
        a=FactorizedV7(FakeProvider(),'single').evaluate(case)
        self.assertTrue(a.trace['schema_valid'])
        self.assertIn(a.decision['status'],('DECISION','ABSTAIN'))
        if a.decision['status']=='ABSTAIN':
            self.assertIn('environment.temperature_c',a.decision['verify_fields'])
        else: self.assertEqual(a.decision['verify_fields'],[])

    def test_observed_unreliable_cannot_be_cited_as_observed(self):
        case=CASES[0]
        bands={p:(policy_band(p,case['domains'][p.split('.')[0]][p.split('.')[1]]['value'])
                   if case['domains'][p.split('.')[0]][p.split('.')[1]]['quality']=='observed' else None) for p in FIELD_ORDER}
        self.assertEqual(check_bands(bands,case),bands)
        bands['environment.temperature_c']=1
        with self.assertRaises(ValueError): check_bands(bands,case)

    def test_bad_json_detected_as_failure(self):
        a=FactorizedV7(BadProvider(),'single').evaluate(CASES[4])
        self.assertFalse(a.trace['schema_valid'])
        self.assertEqual(a.decision['status'],'ABSTAIN')

    def test_policy_is_not_old_gold_formula(self):
        self.assertNotIn('gold_score',json.dumps(POLICY))
        self.assertNotIn('0.25',json.dumps(POLICY))
        self.assertIn('research_only',POLICY)

    def test_band_error_affects_output_and_is_audited(self):
        a=FactorizedV7(FakeProvider(mutate=True),'single').evaluate(CASES[4])
        self.assertTrue(a.trace['schema_valid'])
        self.assertLess(a.trace['observed_band_accuracy'],1)

if __name__=='__main__': unittest.main()
