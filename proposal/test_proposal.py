"""Smoke and reproducibility checks for the M2-aligned code; no API needed."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from prepare import WEIGHTS, prepare, risk_tier
from study import (RulesOnlySmokeProvider, CONDITIONS, SEEDS, load_suite,
                   simulate_case, summarize)

class ProposalChecks(unittest.TestCase):
    def test_proxy_thresholds(self):
        self.assertEqual(risk_tier(1.7999), "LOW")
        self.assertEqual(risk_tier(1.8), "MEDIUM")
        self.assertEqual(risk_tier(2.4), "MEDIUM")
        self.assertEqual(risk_tier(2.40001), "HIGH")
        self.assertAlmostEqual(sum(WEIGHTS.values()), 1.0)

    def test_locked_cases_and_controlled_grid(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            csv_path = base / "fixture_only.csv"
            data = []
            for i in range(600):
                tier = i % 3
                data.append({
                    "Crowd_Density": ["Low","Medium","High"][tier],
                    "Temperature": [24,35,45][tier],
                    "Fatigue_Level": ["Low","Medium","High"][tier],
                    "Stress_Level": ["Low","Medium","High"][tier],
                    "Queue_Time_minutes": [3,30,60][tier],
                    "Emergency_Event": ["No","No","Yes"][tier],
                    "Distance_Between_People_m": [3.0,1.2,0.5][tier],
                })
            with csv_path.open("w",newline="",encoding="utf-8") as f:
                writer = csv.DictWriter(f,fieldnames=list(WEIGHTS))
                writer.writeheader()
                writer.writerows(data)
            manifest = prepare(csv_path,base/"out")
            cases, from_disk = load_suite(base/"out")
            self.assertEqual(manifest["source_rows"],600)
            self.assertEqual(manifest["holdout_rows"],120)
            self.assertEqual(len(cases),30)
            self.assertEqual(sum(x["difficulty"]=="clean" for x in cases),18)
            self.assertEqual(sum(x["difficulty"]!="clean" for x in cases),12)
            self.assertEqual({x["gold"] for x in cases},{"LOW","MEDIUM","HIGH"})
            rows = []
            for seed in SEEDS:
                provider = RulesOnlySmokeProvider(from_disk["encoding"])
                for case in cases:
                    for condition in CONDITIONS:
                        row = simulate_case(case,from_disk,provider,condition)
                        row["seed"] = seed
                        rows.append(row)
            self.assertEqual(len(rows),180)
            self.assertTrue(all(r["verification_count"]<=1 for r in rows))
            metrics = summarize(rows,cases)
            self.assertEqual(len(metrics),6)
            self.assertTrue(all(m["cases"]==30 for m in metrics))
            self.assertTrue(all(m["corruption_detection_m2"] is None for m in metrics))
            # Source integrity is enforced: modified cases must be rejected.
            locked = base/"out"/"locked_cases.jsonl"
            locked.write_text(locked.read_text()+"\n",encoding="utf-8")
            with self.assertRaises(ValueError):
                load_suite(base/"out")

if __name__ == "__main__":
    unittest.main()
