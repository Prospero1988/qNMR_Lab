from pathlib import Path
import csv
import json
import subprocess
import pytest
from docx import Document
from openpyxl import load_workbook
from qnmr.excel_reference import validation_comparison,import_reference,inspect_workbook
from qnmr.quantification import project_summary,calculate_project
from qnmr.reports import export_bundle,export_docx

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/'validation/reference/qNMR.xlsx'

@pytest.mark.skipif(not REFERENCE.is_file(),reason='Optional local laboratory workbook is not distributed')
def test_all_reference_sheets_and_water():
    sheets=inspect_workbook(REFERENCE)
    assert [s['name'] for s in sheets]==['03-61','06-46','06-46_v2','05-32']
    comparisons=validation_comparison(REFERENCE)
    assert all(s['max_absolute_difference']<1e-10 for s in comparisons)
    actual=next(s for s in comparisons if s['sheet']=='06-46_v2')
    assert abs(actual['independent_preparation_statistics']['sd']-1.4337980845689173)<1e-10
    assert actual['workbook_pooled_population_sd']==1.2448077727273212
    assert sum(c['role']=='water' for s in comparisons for c in s['comparisons'])==9

@pytest.mark.skipif(not REFERENCE.is_file(),reason='Optional local laboratory workbook is not distributed')
def test_report_reference_values_agree_with_report_rounding():
    p=import_reference(REFERENCE,'06-46_v2');summary=project_summary(p)
    assert [round(s['assay_percent'],3) for s in summary['samples']]==[80.708,82.901,80.204]
    assert round(summary['between']['mean'],2)==81.27
    assert round(summary['between']['sd'],2)==1.43

def test_exports_numerical_values_and_traceability(project,tmp_path):
    calculate_project(project);export_bundle(project,tmp_path)
    assert all((tmp_path/name).is_file() for name in ('report.docx','results.xlsx','integrals.csv','traceability.json'))
    book=load_workbook(tmp_path/'results.xlsx',data_only=True)
    assert book['Results']['B4'].value==project_summary(project)['between']['mean']
    assert len(book.sheetnames)==5
    rows=list(csv.DictReader((tmp_path/'integrals.csv').open(encoding='utf-8-sig')))
    assert len(rows)==2 and rows[0]['result_status']=='current'
    doc=Document(tmp_path/'report.docx');text='\n'.join(p.text for p in doc.paragraphs)
    assert 'independent preparations' in text and 'complete measurement uncertainty budget' in text
    assert doc.inline_shapes
    trace=json.loads((tmp_path/'traceability.json').read_text(encoding='utf-8'))
    from qnmr import __version__
    assert trace['application_version']==__version__
    assert list(tmp_path.glob('spectrum_*.png'))

def test_launcher_verifies_prepared_environment_without_network():
    r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/bootstrap.ps1'),'-PrepareOnly'],cwd=ROOT,capture_output=True,text=True,timeout=90)
    assert r.returncode==0,r.stdout+r.stderr
    stamp=ROOT/'.venv/qnmr-environment.sha256';before=stamp.stat().st_mtime_ns
    r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/bootstrap.ps1'),'-CheckOnly'],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert r.returncode==0,r.stdout+r.stderr
    assert stamp.stat().st_mtime_ns==before
