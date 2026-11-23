from copy import deepcopy
from unittest.mock import patch
import numpy as np
import pytest
from PySide6 import QtWidgets as W
from docx import Document
from openpyxl import load_workbook
from qnmr import i18n
from qnmr.gui import MainWindow
from qnmr.models import uid
from qnmr.quantification import calculate_project,project_summary,substance_summaries
from qnmr.reports import export_xlsx,export_docx

def test_substance_result_weights_independent_preparations_equally(substance_study):
    project=substance_study;assert not calculate_project(project)
    a,b=project.compounds;stats=project_summary(project,analyte_id=a.id)
    np.testing.assert_allclose([s['assay_percent'] for s in stats['samples']],[90,100,110],rtol=1e-12)
    assert [s['acquisitions'] for s in stats['samples']]==[2,1,3]
    assert stats['between']['n']==3 and stats['between']['mean']==pytest.approx(100) and stats['between']['sd']==pytest.approx(10)
    assert stats['between']['sem']==pytest.approx(10/np.sqrt(3))
    assert stats['between']['mean']!=pytest.approx(np.mean([80,100,100,110,110,110]))
    rows=substance_summaries(project);assert len(rows)==2 and all(r['complete'] for r in rows)
    assert rows[0]['statistics']['n']==3 and rows[0]['acquisitions']==6
    assert rows[1]['statistics']['mean']==pytest.approx(50) and rows[1]['statistics']['sd']==pytest.approx(10)
    assert project_summary(project)['between']['mean'] is None

def test_repeats_and_missing_results_do_not_satisfy_three_preparation_requirement(substance_study):
    project=substance_study;a=project.compounds[0]
    project.samples[2].include=False;project.samples[2].exclusion_reason='Test exclusion'
    extra=deepcopy(project.samples[0].measurements[0]);extra.id=uid();project.samples[0].measurements.append(extra)
    assert not calculate_project(project)
    row=next(r for r in substance_summaries(project) if r['analyte_id']==a.id)
    assert row['statistics']['n']==2 and not row['complete'] and row['provisional']
    project.samples[0].measurements[0].result_fingerprint='stale'
    row=next(r for r in substance_summaries(project) if r['analyte_id']==a.id)
    assert row['statistics']['n']==1 and row['provisional']

@pytest.mark.parametrize('code',['pl','en'])
def test_ui_exposes_separate_substance_results_and_preserves_selection_on_language_switch(app,substance_study,code,monkeypatch):
    project=substance_study;calculate_project(project);a,b=project.compounds
    monkeypatch.setattr('qnmr.gui.set_language',lambda code,**kw:i18n.set_language(code))
    with i18n.using_language(code):
        window=MainWindow(project);window.show();app.processEvents();panel=window.statistics_panel
        assert window.substances_table.rowCount()==2 and window.substances_table.item(0,1).text()=='3'
        assert window.substances_table.item(0,2).text()=='100' and window.substances_table.item(1,2).text()=='50'
        window.open_substance_statistics_row(1);app.processEvents()
        assert panel.analyte_selector.currentData()==b.id and panel.metrics['n'].text()=='3'
        assert panel.locale().toDouble(panel.metrics['mean'].text())[0]==50 and panel.preparations.rowCount()==3
        for row in range(panel.preparations.rowCount()):assert panel.preparations.item(row,0).text().startswith('Substance B')
        curve=window.stats_plot.listDataItems()[0];np.testing.assert_allclose(curve.yData,[40,50,60],rtol=1e-12)
        window.language_button.click();app.processEvents();panel=window.statistics_panel
        assert panel.analyte_selector.currentData()==b.id and panel.locale().toDouble(panel.metrics['mean'].text())[0]==50
        window.dirty=False;window.close()

def test_reports_include_each_substance_with_its_own_n_mean_and_sd(substance_study,tmp_path):
    project=substance_study;calculate_project(project)
    export_xlsx(project,tmp_path/'substances.xlsx');book=load_workbook(tmp_path/'substances.xlsx',data_only=True)
    rows=list(book['Results'].values)
    header=next(i for i,row in enumerate(rows) if row[0]=='Substance' and row[1]=='Independent preparations')
    assert rows[header+1][:2]==('Substance A',3) and rows[header+2][:2]==('Substance B',3)
    np.testing.assert_allclose(rows[header+1][2:4],[100,10],rtol=1e-12)
    np.testing.assert_allclose(rows[header+2][2:4],[50,10],rtol=1e-12)
    export_docx(project,tmp_path/'substances.docx');doc=Document(tmp_path/'substances.docx')
    text='\n'.join(p.text for p in doc.paragraphs)
    assert 'Substance A' in text and 'Substance B' in text
    assert '100.000 % w/w' in text and '50.000 % w/w' in text
    means=[table for table in doc.tables if table.rows[0].cells[0].text=='Mean assay (% w/w)']
    assert len(means)==2 and [table.rows[1].cells[3].text for table in means]==['3','3']
