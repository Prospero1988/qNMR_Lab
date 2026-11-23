"""Language changes must preserve scientific records and editable GUI state."""
from copy import deepcopy
from pathlib import Path
import json
import os
import subprocess
import sys
from unittest.mock import patch

import numpy as np
import pytest
from docx import Document
from openpyxl import load_workbook
from PySide6 import QtCore, QtWidgets as W

from qnmr import i18n
from qnmr._catalog import PL, LEGACY_EN
from qnmr.dialogs import ROIDialog
from qnmr.gui import MainWindow
from qnmr.quantification import calculate_project, is_current, project_summary
from qnmr.reports import export_bundle, SIGNAL_LABELS
from qnmr.storage import project_dict, load_project

ROOT=Path(__file__).resolve().parents[1]

def test_fresh_process_defaults_to_polish():
    result=subprocess.check_output([sys.executable,'-c','from qnmr.i18n import language;print(language())'],cwd=ROOT,text=True)
    assert result.strip()=='pl'

def test_saved_choice_and_explicit_startup_override(monkeypatch):
    values={}
    class Settings:
        def __init__(self,*args):pass
        def value(self,key,default,type=str):return values.get(key,default)
        def setValue(self,key,value):values[key]=value
        def sync(self):pass
    monkeypatch.setattr(QtCore,'QSettings',Settings)
    monkeypatch.delenv('QNMR_LAB_LANGUAGE',raising=False)
    i18n.load_preference();assert i18n.language()=='pl'
    i18n.set_language('en',persist=True);i18n.load_preference();assert i18n.language()=='en'
    monkeypatch.setenv('QNMR_LAB_LANGUAGE','pl');i18n.load_preference();assert i18n.language()=='pl'

def test_catalog_placeholders_and_diagnostics():
    from string import Formatter
    def fields(text):return sorted((name,spec,conv) for _,name,spec,conv in Formatter().parse(text) if name is not None)
    for source,target in PL.items():assert fields(source)==fields(target),(source,target)
    for source,target in LEGACY_EN.items():assert fields(source)==fields(target),(source,target)
    with i18n.using_language('pl'):
        assert i18n.message('Lower limit (ppm)')=='Dolna granica (ppm)'
        assert i18n.message('My own scientific comment')=='My own scientific comment'
        assert i18n.tr('{p0:.5f} to {p1:.5f}',p0=1,p1=2)=='od 1.00000 do 2.00000'
        assert i18n.message('1.00000 to 2.00000')=='od 1.00000 do 2.00000'
        assert all(label in PL or label in ('ROI ID',) for label in SIGNAL_LABELS.values())

def test_all_explicit_ui_translation_keys_exist():
    import ast
    for path in (ROOT/'qnmr').glob('*.py'):
        if path.stem in ('_catalog','i18n'):continue
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node,ast.Call) and ((isinstance(node.func,ast.Name) and node.func.id=='tr') or (isinstance(node.func,ast.Attribute) and node.func.attr=='tr')) and node.args and isinstance(node.args[0],ast.Constant):
                key=node.args[0].value
                assert key in PL or key in LEGACY_EN,(path.name,node.lineno,key)

@pytest.mark.parametrize('code,ready',[('pl',b'gotowe'),('en',b'environment is ready')])
def test_launcher_language_option_without_reinstallation(code,ready):
    result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
        str(ROOT/'tools/bootstrap.ps1'),'-CheckOnly','-Language',code],cwd=ROOT,capture_output=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
    assert ready in result.stdout

def test_language_button_preserves_project_arrays_results_and_pending_controls(app,project,tmp_path,monkeypatch):
    calculate_project(project)
    monkeypatch.setattr('qnmr.gui.set_language',lambda code,**kwargs:i18n.set_language(code))
    with i18n.using_language('pl'):
        window=MainWindow(project);s=project.samples[0];m=s.measurements[0]
        window.open_measurement(s,m);window.path=tmp_path/'projekt.qnmr';window.dirty=True
        window.show();app.processEvents();workspace=window.current_workspace()
        workspace.controls['lb_Hz'].setValue(1.75)
        workspace.controls['phase0_deg'].setValue(12)
        workspace.zf.setCurrentText('4');workspace.mode.setCurrentIndex(2);workspace.table.selectRow(1)
        from PySide6.QtTest import QTest
        for _ in range(500):
            app.processEvents()
            if not window.busy:break
            QTest.qWait(10)
        assert not window.busy
        window.calculate()
        workspace.view.setRange(xRange=(4.1,4.8),yRange=(-10,500),padding=0)
        app.processEvents();ranges=deepcopy(workspace.view.viewRange())
        before=deepcopy(project_dict(project));arrays={k:v.copy() for k,v in m.arrays.items()}
        for expected,button in [('en','ENG → PL'),('pl','PL → ENG')]:
            window.language_button.click();app.processEvents();app.processEvents()
            assert i18n.language()==expected and window.language_button.text()==button
            assert window.project is project and window.dirty and window.path==tmp_path/'projekt.qnmr'
            assert project_dict(project)==before and is_current(project,s,m)
            for key,value in arrays.items():np.testing.assert_array_equal(m.arrays[key],value)
            workspace=window.current_workspace()
            assert workspace.m is m and workspace.controls['lb_Hz'].value()==1.75
            assert workspace.controls['phase0_deg'].value()==12 and workspace.zf.currentText()=='4'
            assert workspace.mode.currentIndex()==2 and workspace.current_roi_index()==1
            np.testing.assert_allclose(workspace.view.viewRange(),ranges,rtol=0,atol=1e-6)
        window.dirty=False;window.close()

@pytest.mark.parametrize('code',['pl','en'])
def test_roles_quality_and_standard_buttons_keep_canonical_data(app,project,code):
    with i18n.using_language(code):
        s=project.samples[0];m=s.measurements[0]
        dialog=ROIDialog(project,s,m,m.rois[0])
        assert dialog.role.currentData()=='analyte'
        assert dialog.role.currentText()==i18n.tr('analyte')
        dialog.quality.setCurrentIndex(1);dialog.accept()
        assert dialog.result.role=='analyte' and dialog.result.quality=='Reviewed — suitable'
        dialog=ROIDialog(project,s,m,dialog.result)
        dialog.quality.setEditText('Moja uwaga / my comment');dialog.accept()
        assert dialog.result.quality=='Moja uwaga / my comment'
        assert QtCore.QCoreApplication.translate('QPlatformTheme','Cancel')==('Anuluj' if code=='pl' else 'Cancel')
        assert dialog.protons.locale().decimalPoint()==(',' if code=='pl' else '.')

@pytest.mark.parametrize('code,title,sheet',[('pl','Raport','Wyniki'),('en','research report','Results')])
def test_localized_reports_preserve_numbers_and_canonical_trace(project,tmp_path,code,title,sheet):
    calculate_project(project);before=deepcopy(project_dict(project));summary=project_summary(project)
    with i18n.using_language(code):export_bundle(project,tmp_path/code)
    book=load_workbook(tmp_path/code/'results.xlsx',data_only=True)
    assert book[sheet]['B4'].value==summary['between']['mean']
    assert all(len(name)<=31 for name in book.sheetnames)
    assert book.worksheets[1]['A1'].value==('Próbka' if code=='pl' else 'Sample')
    doc=Document(tmp_path/code/'report.docx')
    assert title.lower() in '\n'.join(p.text for p in doc.paragraphs).lower()
    trace=json.loads((tmp_path/code/'traceability.json').read_text(encoding='utf-8'))
    assert trace['report_language']==code and trace['project']==before
    assert project_dict(project)==before
    assert (tmp_path/code/'integrals.csv').read_text(encoding='utf-8-sig').startswith('sample,measurement,roi_id,signal,role,')

@pytest.mark.parametrize('code',['pl','en'])
def test_all_manuals_are_available(code):
    with i18n.using_language(code):
        for name in ('USER_MANUAL','SCIENTIFIC_METHODS','DEVELOPER_GUIDE','VALIDATION','EXCEL_COMPARISON'):
            assert i18n.manual_path(name).stat().st_size>2000

def test_old_demo_fingerprints_are_current():
    project,_=load_project(ROOT/'examples/synthetic_three_samples.qnmr')
    assert all(is_current(project,s,m) for s in project.samples for m in s.measurements)

@pytest.mark.parametrize('code',['pl','en'])
def test_export_filter_uses_extension_in_both_languages(app,project,tmp_path,code):
    calculate_project(project)
    with i18n.using_language(code):
        window=MainWindow(project)
        for suffix in ('docx','xlsx','csv'):
            with patch.object(W.QFileDialog,'getSaveFileName',return_value=(str(tmp_path/('result.'+suffix)),i18n.tr({'docx':'Word report (*.docx)','xlsx':'Excel results (*.xlsx)','csv':'Integral table (*.csv)'}[suffix]))),patch('qnmr.gui.export_'+suffix) as export:
                window.export_report();export.assert_called_once()
        window.close()
