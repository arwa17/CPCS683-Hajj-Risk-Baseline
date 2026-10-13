"""Tests for the single-agent M4 baseline, without requiring a real model."""
import json
import threading
import unittest
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request

from hajj_baseline.agent import GeneralistAgent
from hajj_baseline.providers import LLMProvider
from hajj_baseline.schema import ContractError, validate_case, validate_decision
from hajj_baseline.webapp import make_handler

ROOT = Path(__file__).resolve().parents[1]


def sample(name="case_high.json"):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


def decision(case):
    return {
        "case_id":case["case_id"],"status":"DECISION","risk_level":"HIGH",
        "recommended_action":"URGENT_HUMAN_REVIEW",
        "evidence_used":["crowd.queue_minutes","environment.temperature_c"],
        "uncertainty_flags":[],"verify_fields":[],
        "summary":"The observed queue and temperature warrant human review in this simulated case.",
    }


class FakeLLM:
    backend="gemini"
    model="test-only"
    def __init__(self, output):
        self.output=output
        self.calls=0
    def generate(self, system_prompt, user_prompt):
        self.calls+=1
        return json.dumps(self.output), {"input_tokens":100,"output_tokens":50}


class BaselineTests(unittest.TestCase):
    def test_examples(self):
        for p in (ROOT/"examples").glob("case_*.json"):
            self.assertEqual(validate_case(sample(p.name))["case_id"],sample(p.name)["case_id"])

    def test_bad_input_rejected(self):
        c=sample()
        c["domains"]["crowd"]["queue_minutes"]["value"]="many"
        with self.assertRaises(ContractError):
            validate_case(c)

    def test_fake_source_rejected(self):
        c=sample()
        d=decision(c)
        d["evidence_used"]=["nonexistent.camera"]
        with self.assertRaises(ContractError):
            validate_decision(d,c)

    def test_cannot_cite_missing(self):
        c=sample("case_missing.json")
        d=decision(c)
        d["evidence_used"]=["health.emergency_event"]
        with self.assertRaises(ContractError):
            validate_decision(d,c)

    def test_one_generalist_call(self):
        c=sample()
        model=FakeLLM(decision(c))
        r=GeneralistAgent(model).evaluate(c)
        self.assertEqual(model.calls,1)
        self.assertEqual(r.decision["risk_level"],"HIGH")
        self.assertTrue(r.trace["schema_valid"])

    def test_invalid_model_answer_withheld(self):
        c=sample()
        bad=decision(c)
        bad["evidence_used"]=["nonexistent.camera"]
        r=GeneralistAgent(FakeLLM(bad)).evaluate(c)
        self.assertEqual(r.decision["status"],"ABSTAIN")
        self.assertFalse(r.trace["schema_valid"])

    def test_abstain_on_missing_evidence(self):
        c=sample("case_missing.json")
        output={
            "case_id":c["case_id"],"status":"ABSTAIN","risk_level":None,
            "recommended_action":"REQUEST_VERIFICATION","evidence_used":[],
            "uncertainty_flags":["Missing crowd density and emergency event"],
            "verify_fields":["crowd.density_people_per_m2","health.emergency_event"],
            "summary":"The missing readings prevent a decision."
        }
        r=GeneralistAgent(FakeLLM(output)).evaluate(c)
        self.assertTrue(r.trace["schema_valid"])
        self.assertEqual(r.decision["status"],"ABSTAIN")

    def test_reject_placeholder_uncertainty(self):
        c=sample()
        d=decision(c)
        d["uncertainty_flags"]=["short readable issue"]
        with self.assertRaises(ContractError):
            validate_decision(d,c)

    def test_reject_false_missing_claim(self):
        c=sample()
        d={
            "case_id":c["case_id"],"status":"ABSTAIN","risk_level":None,
            "recommended_action":"REQUEST_VERIFICATION","evidence_used":[],
            "uncertainty_flags":["Missing temperature"],
            "verify_fields":["environment.temperature_c"],
            "summary":"Temperature is missing."
        }
        with self.assertRaises(ContractError):
            validate_decision(d,c)

    def test_browser_end_to_end(self):
        c=sample()
        fake=FakeLLM(decision(c))
        server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(fake))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        root=f"http://127.0.0.1:{server.server_port}"
        try:
            with request.urlopen(root+"/") as response:
                self.assertIn("Hajj Risk Baseline",response.read().decode())
            with request.urlopen(root+"/api/cases/case_high.json") as response:
                case=json.load(response)
            body=json.dumps({"case":case}).encode()
            req=request.Request(root+"/api/analyze",data=body,headers={"Content-Type":"application/json"},method="POST")
            with request.urlopen(req) as response:
                result=json.load(response)
            self.assertEqual(result["result"]["decision"]["risk_level"],"HIGH")
            self.assertEqual(fake.calls,1)
        finally:
            server.shutdown();server.server_close()

    def test_gemini_transport(self):
        """Verify Gemini REST request shape, API key header, and JSON reply parsing."""
        case = sample()
        answer = decision(case)
        seen = []

        class Stub(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                seen.append((self.path, self.headers.get("x-goog-api-key"), payload))
                body = json.dumps({
                    "candidates": [{
                        "content": {"parts": [{"text": json.dumps(answer)}]}
                    }],
                    "usageMetadata": {"promptTokenCount": 25, "candidatesTokenCount": 18},
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            provider = LLMProvider(
                api_key="test-token",
                model="gemini-3.1-flash-lite",
                base_url=f"http://127.0.0.1:{server.server_port}",
            )
            result = GeneralistAgent(provider).evaluate(case)
            self.assertEqual(result.decision["risk_level"], "HIGH")
            self.assertTrue(result.trace["schema_valid"])
            self.assertEqual(result.trace["input_tokens"], 25)
            self.assertEqual(seen[0][0], "/models/gemini-3.1-flash-lite:generateContent")
            self.assertEqual(seen[0][1], "test-token")
            self.assertEqual(seen[0][2]["generationConfig"]["responseMimeType"], "application/json")
            self.assertEqual(seen[0][2]["generationConfig"]["temperature"], 0)
            self.assertTrue(seen[0][2]["systemInstruction"]["parts"][0]["text"])
        finally:
            server.shutdown()
            server.server_close()


if __name__=="__main__":
    unittest.main()
