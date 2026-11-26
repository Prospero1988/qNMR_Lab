from copy import deepcopy
import hashlib
from unittest.mock import patch
import numpy as np
import pytest
from docx import Document
from PySide6 import QtWidgets as W
from qnmr.models import uid
from qnmr.quantification import calculate_project, project_summary, is_current
from qnmr.storage import project_dict, save_project, load_project
from qnmr.resonance_consistency import confirm_correspondence, resonance_consistency
from qnmr.resonance_dialog import ResonanceCorrespondenceDialog
from qnmr.reports import export_docx
from qnmr import report_figures as figures


@pytest.fixture
def study(substance_study):
    p=substance_study;p.samples=p.samples[:3];p.compounds=p.compounds[:1]
    for index,sample in enumerate(p.samples):
        for m in sample.measurements:
            low=m.rois[0];low.signal='7.898 ppm';low.low=7.85;low.high=7.94
            high=deepcopy(low);high.id=uid();high.signal='2.912 ppm';high.low=2.86;high.high=2.97
            high.area+=(index+1)*.1
            m.rois.append(high);m.assign_roi_labels()
            # Local IDs intentionally disagree across measurements.
            m.roi_labels[low.id]='S'+str(index+11);m.roi_labels[high.id]='S'+str(30-index)
    assert not calculate_project(p)
    return p


def confirm(p):
    groups=[]
    for name in ('7.898 ppm','2.912 ppm'):
        groups.append(dict(label=name,members=[(m.id,r.id) for s in p.samples for m in s.measurements for r in m.rois if r.signal==name]))
    p.resonance_correspondence=confirm_correspondence(p,[g for g in groups if g['members']],analyst='Test analyst')


def diagnostic(p):return resonance_consistency(p)[0]


def test_names_shifts_and_local_ids_alone_never_establish_correspondence(study):
    result=diagnostic(study)
    assert not result['rows'] and not result['plot_available'] and result['persistent_pair'] is None
    assert result['unassigned']==12


def test_equal_independent_weights_centered_deviations_and_sample_sd(study):
    confirm(study);before=deepcopy(project_dict(study));summary=deepcopy(project_summary(study))
    result=diagnostic(study);low,high=result['rows']
    assert low['ppm']==pytest.approx(7.898) and high['ppm']==pytest.approx(2.912)
    assert low['n']==high['n']==3 and [p['measurements'] for p in low['points']]==[2,1,3]
    np.testing.assert_allclose([p['assay'] for p in low['points']],[90,100,110])
    np.testing.assert_allclose([p['deviation'] for p in low['points']],[-5,-10,-15])
    assert low['mean_assay']==pytest.approx(100) and low['mean_deviation']==pytest.approx(-10)
    assert low['sd_deviation']==pytest.approx(5) and low['classification']=='lower'
    assert high['classification']=='higher' and result['persistent_pair']['gap']==pytest.approx(20)
    assert project_dict(study)==before and project_summary(study)==summary


@pytest.mark.parametrize('count',[0,1,2])
def test_insufficient_samples_do_not_claim_persistence_or_significance(study,count):
    study.samples=study.samples[:count];confirm(study)
    result=diagnostic(study)
    assert result['persistent_pair'] is None
    assert result['plot_available']==(count==2)
    for row in result['rows']:
        assert row['classification']=='limited'
        if count==1:assert row['sd_deviation'] is None


def test_missing_and_excluded_signals_require_complete_repeat_coverage(study):
    confirm(study)
    m=study.samples[0].measurements[0];m.rois[-1].accepted=False
    assert not calculate_project(study)
    result=diagnostic(study)
    assert result['incomplete']==1
    high=next(r for r in result['rows'] if r['name']=='2.912 ppm')
    assert high['n']==2 and result['persistent_pair'] is None
    assert not any(p['sample_id']==study.samples[0].id for p in high['points'])


def test_excluded_and_nonindependent_preparations_do_not_count(study):
    confirm(study);study.samples[0].include=False;study.samples[1].independent=False
    assert not calculate_project(study)
    assert all(r['n']==1 for r in diagnostic(study)['rows'])
    assert not diagnostic(study)['plot_available']


def test_stale_acquisition_omits_entire_preparation_as_in_official_summary(study):
    confirm(study);study.samples[0].measurements[0].options['phase0_deg']=12
    assert all(r['n']==2 for r in diagnostic(study)['rows'])


def test_excluded_acquisition_never_adds_a_replicate(study):
    confirm(study);study.samples[0].measurements[0].include=False
    result=diagnostic(study)
    assert all(r['n']==3 for r in result['rows'])
    low=next(r for r in result['rows'] if r['name']=='7.898 ppm')
    assert low['points'][0]['measurements']==1 and low['points'][0]['assay']==pytest.approx(100)


def test_missing_assignment_in_one_repeat_does_not_impute_or_pool(study):
    confirm(study)
    study.resonance_correspondence[0]['members'].pop(0)
    result=diagnostic(study)
    assert result['incomplete']==1 and result['unassigned']==1
    assert next(r for r in result['rows'] if r['name']=='7.898 ppm')['n']==2


def test_atom_correspondence_never_pools_different_analytes(substance_study):
    from qnmr.chemistry import parse_smiles
    for index,c in enumerate(substance_study.compounds):
        new=parse_smiles('CCO');new.id=c.id;substance_study.compounds[index]=new
    for s in substance_study.samples:
        for m in s.measurements:m.rois[0].atoms=[0]
    assert not calculate_project(substance_study)
    results=resonance_consistency(substance_study)
    assert len(results)==2 and all(d['rows'][0]['n']==3 for d in results)


def test_chemical_structure_edit_invalidates_confirmed_identity(study):
    confirm(study);study.compounds[0].smiles='CCO'
    assert not calculate_project(study)
    assert not diagnostic(study)['rows']


def test_consistency_plot_uses_one_point_per_preparation_and_skips_small_n(study):
    assert figures.resonance_consistency(diagnostic(study)) is None
    confirm(study);captured=[]
    with patch.object(figures,'png',side_effect=lambda fig:captured.append(fig) or b'png'):
        assert figures.resonance_consistency(diagnostic(study))==b'png'
    for ax in captured[0].axes:
        assert len(ax.lines[0].get_ydata())==3
    study.samples=study.samples[:1]
    assert figures.resonance_consistency(diagnostic(study)) is None


def test_assignment_edit_requires_reconfirmation_and_does_not_fall_back_to_ppm(study):
    confirm(study);m=study.samples[0].measurements[0];m.rois[0].low+=.01
    assert not calculate_project(study)
    result=diagnostic(study)
    low=next(r for r in result['rows'] if r['name']=='7.898 ppm')
    assert low['n']==2 and result['unassigned']==1 and result['incomplete']==1


def test_duplicate_correspondence_is_rejected_without_project_changes(study):
    before=deepcopy(project_dict(study));m=study.samples[0].measurements[0]
    with pytest.raises(ValueError):
        confirm_correspondence(study,[dict(label='ambiguous',members=[(m.id,m.rois[0].id),(m.id,m.rois[-1].id)])])
    assert project_dict(study)==before


def test_atom_assignments_compare_without_local_ids_and_refuse_ambiguity(study):
    from qnmr.chemistry import parse_smiles
    compound=parse_smiles('CCO');compound.id=study.compounds[0].id;study.compounds=[compound]
    for s in study.samples:
        for m in s.measurements:m.rois[0].atoms=[0];m.rois[-1].atoms=[1]
    assert not calculate_project(study)
    assert len(diagnostic(study)['rows'])==2
    for m in study.samples[0].measurements:m.rois[-1].atoms=[0]
    assert not calculate_project(study)
    assert all(r['n']==2 for r in diagnostic(study)['rows'])


def test_confirmation_survives_portable_save_without_invalidating_results(study,tmp_path):
    confirm(study);path=tmp_path/'confirmed.qnmr';save_project(study,path);restored,_=load_project(path)
    assert restored.resonance_correspondence==study.resonance_correspondence
    assert all(is_current(restored,s,m) for s in restored.samples for m in s.measurements)
    assert diagnostic(restored)==diagnostic(study)


def test_dialog_confirmation_is_explicit_cancellable_and_read_only_until_accepted(app,study):
    before=deepcopy(project_dict(study));dialog=ResonanceCorrespondenceDialog(study)
    assert all(not dialog.table.item(i,5).text() for i in range(dialog.table.rowCount()))
    dialog.suggest();dialog.accept()
    assert len(dialog.result)==2 and project_dict(study)==before
    from qnmr.gui import MainWindow
    window=MainWindow(study)
    def accept(dialog):dialog.suggest();dialog.accept();return 1
    with patch.object(ResonanceCorrespondenceDialog,'exec',accept):window.edit_resonance_correspondence()
    assert len(study.resonance_correspondence)==2
    assert all(is_current(study,s,m) for s in study.samples for m in s.measurements)
    window.dirty=False;window.close()


def test_reports_include_diagnostics_and_omit_plot_when_not_comparable(study,tmp_path):
    path=tmp_path/'missing.docx';export_docx(study,path)
    document=Document(path);text='\n'.join(p.text for p in document.paragraphs)
    assert 'No comparable current resonance assignments' in text
    confirm(study);before=deepcopy(project_dict(study));path=tmp_path/'confirmed.docx';export_docx(study,path)
    document=Document(path);text='\n'.join(p.text for p in document.paragraphs)
    assert '7.898 ppm resonance gives a lower assay than 2.912 ppm' in text
    assert 'partly attenuated' in text and 'without significance tests' in text
    assert any(t.rows[0].cells[-1].text=='Consistency description' for t in document.tables)
    assert 'sample' in ''.join(document.element.body.xpath('.//m:t/text()'))
    assert document.element.body.xpath('.//m:f/m:num/m:f')
    assert project_dict(study)==before


def test_spectral_zoom_preserves_arrays_and_boundaries_and_decreasing_ppm(project):
    m=project.samples[0].measurements[0]
    second=deepcopy(m.rois[0]);second.id=uid();second.low=4.5;second.high=4.6;second.signal='Assigned resonance';m.rois.append(second)
    before={k:hashlib.sha256(a.tobytes()).hexdigest() for k,a in m.arrays.items()}
    assert len(figures.quantitative_regions(m,clusters_only=True))==1
    captured=[]
    with patch.object(figures,'png',side_effect=lambda fig:captured.append(fig) or b'png'):
        assert figures.spectrum(m,zoom=True,clusters_only=True)==b'png'
    ax=captured[0].axes[0]
    assert ax.get_xlim()[0]>ax.get_xlim()[1]
    assert len(ax.patches)==2 and len(ax.texts)==2
    assert before=={k:hashlib.sha256(a.tobytes()).hexdigest() for k,a in m.arrays.items()}


def test_mixed_directions_are_described_without_inference():
    from qnmr.resonance_consistency import classify
    assert classify([-1,1,0])=='mixed' and classify([0,0,0])=='centered'
