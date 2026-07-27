#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'pipeline/case_workflow/00b_refresh_combined_g2p.py'
spec = importlib.util.spec_from_file_location('g2p_builder', TARGET)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as temp:
    directory = Path(temp)
    (directory / 'patient_01_a.hpo.txt').write_text('HP:0000001\n')
    (directory / 'patient_10_b.hpo.txt').write_text('HP:0000010\n')
    (directory / 'patient_12_c.hpo.txt').write_text('HP:0000012\n')
    assert module.hpo_terms_for_sample(directory, 'PATIENT_01') == ['HP:0000001']
    assert module.hpo_terms_for_sample(directory, 'PATIENT_10') == ['HP:0000010']
    assert module.hpo_terms_for_sample(directory, 'PATIENT_12') == ['HP:0000012']

print('PASS: Exact HPO patient-number matching regression test completed.')
