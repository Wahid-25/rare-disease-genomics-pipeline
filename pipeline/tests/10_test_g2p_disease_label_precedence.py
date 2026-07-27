#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / "pipeline/case_workflow"
sys.path.insert(0, str(WORKFLOW))

TARGET = WORKFLOW / "07_score_disease_candidates.py"
spec = importlib.util.spec_from_file_location("scoring", TARGET)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.choose_candidate_disease(
    "MEFV-related familial mediterranean fever",
    "Acute febrile neutrophilic dermatosis",
) == "MEFV-related familial mediterranean fever"

assert module.choose_candidate_disease(
    "",
    "ClinVar fallback condition",
) == "ClinVar fallback condition"

print("PASS: G2P disease label takes precedence over ClinVar conditions.")
