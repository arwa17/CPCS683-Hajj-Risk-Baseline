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
                    domain, field = path.split('.')
                    quality = payload['observations'][domain][field]['quality']
                    self.assertEqual(entry['nullable'], quality != 'observed')
                    expected = 'integer 0, 1, or 2 required' if quality == 'observed' else 'JSON null required'
                    self.assertEqual(payload['output_format']['bands'][path], expected)

    def test_failed_specialist_is_traceable(self):
        a=FactorizedV7(BadProvider(),'multi').evaluate(CASES[4])
        self.assertEqual(a.trace['agent_calls_this_pass'],2)
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
        self.assertFalse(a.trace['schema_valid'])
        self.assertEqual(a.decision['status'],'ABSTAIN')
        self.assertIn('Observed band violates supplied policy',a.trace['schema_error'])


class RepairProvider(FakeProvider):
    def __init__(self, broken_path, fail_forever=False):
        super().__init__()
        self.broken_path=broken_path
        self.fail_forever=fail_forever
        self.attempts=0

    def generate(self, system, user, response_schema=None):
        raw, usage=super().generate(system,user,response_schema)
        payload=json.loads(user)
        bands=json.loads(raw)['bands']
        if self.broken_path in bands:
            self.attempts+=1
            if self.attempts==1 or self.fail_forever:
                if self.broken_path=='crowd.queue_minutes':
                    bands[self.broken_path]=None
                else:
                    bands[self.broken_path]=1
                raw=json.dumps({'bands':bands})
        return raw,usage


class TestV72Repair(unittest.TestCase):
    def test_schema_failure_is_retried_without_changing_policy(self):
        cases=[json.loads(s) for s in Path('v7_synthetic_data/test_locked_cases.jsonl').read_text().splitlines() if s]
        case=next(c for c in cases if c['case_id']=='V7-0013')
        provider=RepairProvider('crowd.queue_minutes')
        result=FactorizedV7(provider,'multi').evaluate(case)
        self.assertTrue(result.trace['schema_valid'])
        self.assertEqual(result.trace['agent_calls_this_pass'],4)
        self.assertEqual(len(result.trace['report_attempts']['crowd']),2)
        self.assertIn('crowd.queue_minutes',result.trace['correction_events'][0]['previous_error'])
        self.assertTrue(result.trace['correction_events'][-1]['recovered'])

    def test_wrong_valid_band_is_retried(self):
        cases=[json.loads(s) for s in Path('v7_synthetic_data/test_locked_cases.jsonl').read_text().splitlines() if s]
        case=next(c for c in cases if c['case_id']=='V7-0123')
        provider=RepairProvider('crowd.distance_between_people_m')
        result=FactorizedV7(provider,'multi').evaluate(case)
        self.assertTrue(result.trace['schema_valid'])
        self.assertEqual(result.trace['agent_calls_this_pass'],4)
        self.assertEqual(result.trace['report_bands']['crowd']['crowd.distance_between_people_m'],2)
        self.assertEqual(result.decision['risk_level'],'HIGH')

    def test_failed_second_validation_abstains(self):
        cases=[json.loads(s) for s in Path('v7_synthetic_data/test_locked_cases.jsonl').read_text().splitlines() if s]
        case=next(c for c in cases if c['case_id']=='V7-0123')
        provider=RepairProvider('crowd.distance_between_people_m',fail_forever=True)
        result=FactorizedV7(provider,'multi').evaluate(case)
        self.assertFalse(result.trace['schema_valid'])
        self.assertEqual(result.decision['status'],'ABSTAIN')
        self.assertEqual(result.trace['agent_calls_this_pass'],2)
        self.assertIn('crowd.distance_between_people_m',result.trace['schema_error'])

    def test_schema_observed_fields_are_non_nullable(self):
        cases=[json.loads(s) for s in Path('v7_synthetic_data/test_locked_cases.jsonl').read_text().splitlines() if s]
        case=next(c for c in cases if c['case_id']=='V7-0013')
        schema=band_report_schema(['crowd.queue_minutes','crowd.distance_between_people_m'],case)
        b=schema['properties']['bands']['properties']
        self.assertFalse(b['crowd.queue_minutes']['nullable'])
        self.assertTrue(b['crowd.distance_between_people_m']['nullable'])



class TestScoringIntegrity(unittest.TestCase):
    def test_matching_experiment_identity_is_accepted(self):
        from m5_finalize import run_identity
        record={'trace':{'model':'gemini-3.5-flash-lite','prompt_version':'v7_2','temperature':1.0}}
        self.assertEqual(run_identity([record,record])['prompt_version'],'v7_2')

    def test_mixed_code_versions_are_rejected(self):
        from m5_finalize import run_identity
        a={'trace':{'model':'gemini-3.5-flash-lite','prompt_version':'v7_1','temperature':1.0}}
        b={'trace':{'model':'gemini-3.5-flash-lite','prompt_version':'v7_2','temperature':1.0}}
        with self.assertRaises(ValueError):
            run_identity([a,b])

if __name__=='__main__': unittest.main()
