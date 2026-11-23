from pathlib import Path
from copy import deepcopy
import pytest
from qnmr.storage import load_project,save_project
from qnmr.quantification import project_summary,is_current,calculate_project
from qnmr.reports import export_bundle,export_spectrum_csv

ROOT=Path(__file__).resolve().parents[1]

def test_three_synthetic_jdf_preparations_reproduce_after_reopen(tmp_path):
    project,warnings=load_project(ROOT/'examples/synthetic_three_samples.qnmr')
    assert not warnings
    assert len(project.samples)==3
    for sample in project.samples:
        m=sample.measurements[0]
        assert m.input_kind=='raw JDF' and is_current(project,sample,m)
        assert len(m.rois)==3 and m.options['baseline_enabled']
        assert all(r.protons_confirmed for r in m.rois)
    before=project_summary(project)['between']
    assert before['n']==3 and abs(before['mean']-95)<.03
    path=tmp_path/'again.qnmr';save_project(project,path);restored,_=load_project(path)
    assert not calculate_project(restored)
    assert project_summary(restored)['between']==before
    export_bundle(restored,tmp_path/'report')
    export_spectrum_csv(restored.samples[0].measurements[0],tmp_path/'spectrum.csv')
    assert (tmp_path/'spectrum.csv').read_text(encoding='utf-8-sig').startswith('ppm,corrected_real')

def test_correlated_resonances_do_not_get_inferential_intervals(project):
    assert not calculate_project(project)
    within=project.samples[0].measurements[0].results['analyte']
    assert within['sem'] is None and within['ci'] is None

def test_different_analytes_are_never_pooled(project):
    second=deepcopy(project.compounds[0]);second.id='another-compound';project.compounds.append(second)
    s=deepcopy(project.samples[0]);s.id='another-preparation';s.analyte_id=second.id
    s.measurements[0].rois[0].compound_id=second.id;project.samples.append(s)
    assert not calculate_project(project)
    summary=project_summary(project)
    assert summary['between']['n']==0
    assert len(summary['between_by_analyte'])==2 and summary['provisional']
