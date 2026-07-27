#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "pipeline/run_real_patient_case.sh"
text = TARGET.read_text(encoding="utf-8")

assert 'INTAKE_EVIDENCE_DIR="$CASE_INPUT_DIR/intake"' in text
assert (
    'PRESERVED_INTAKE_REPORT="$INTAKE_EVIDENCE_DIR/'
    '${CASE_ID}.external_vcf_intake.tsv"'
) in text
assert 'mkdir -p "$PREPARED_DIR" "$INTAKE_EVIDENCE_DIR"' in text

print("PASS: Intake evidence is preserved outside prepared/.")
