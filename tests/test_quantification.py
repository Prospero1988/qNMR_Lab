from copy import deepcopy
import numpy as np
import pytest
from qnmr.models import uid
from qnmr.quantification import (assay,mass_mg,purity_fraction,descriptive,calculate_project,project_summary,is_current,quantify_measurement)

def test_equation_hand_calculated():
    r=assay(8,2,4,1,300,150,20,10,.9957)
    assert r['proton_normalized_ratio']==1
    assert r['assay_percent']==pytest.approx(99.57)
    assert r['component_mass_mg']==pytest.approx(19.914)

def test_signed_assay_retains_negative():
    r=assay(-8,2,4,1,300,150,20,10,1)
    assert r['assay_percent']==-100 and r['warnings']

@pytest.mark.parametrize('unit,value',[('g',.002),('mg',2),('ug',2000),('µg',2000)])
def test_units(unit,value):assert mass_mg(value,unit)==2

def test_purity_percent_is_explicit():
    assert purity_fraction(99.57,'%')==pytest.approx(.9957)
    assert purity_fraction(.9957,'fraction')==.9957
    with pytest.raises(ValueError):purity_fraction(99.57,'fraction')
    with pytest.raises(ValueError):mass_mg(0,'mg')
    with pytest.raises(ValueError):assay(1,0,1,1,150,150,10,10,1)

def test_entered_nuclei_suffice_but_positive_counts_and_mw_provenance_remain_required(project):
    s=project.samples[0];m=s.measurements[0];m.rois[0].protons_confirmed=False
    assert not calculate_project(project)
    m.rois[0].protons=0
    assert calculate_project(project)
    m.rois[0].protons=1;project.compounds[0].mw_override_reason=''
    assert calculate_project(project)

def test_multiple_references_never_silently_averaged(project):
    s=project.samples[0];m=s.measurements[0];other=deepcopy(m.rois[1]);other.id=uid();other.area*=2;m.rois.append(other)
    assert calculate_project(project)
    m.reference_compatibility_confirmed=True
    result=quantify_measurement(project,s,m)
    assert len(result['signals'][0]['pairs'])==2
    r=result['signals'][0];assert r['assay_percent']==pytest.approx(np.mean([p['assay_percent'] for p in r['pairs']]))
    m.reference_compatibility_confirmed=False;m.rois[0].reference_ids=[other.id]
    assert not calculate_project(project)

def test_stale_history_retained_and_not_in_final_statistics(project):
    assert not calculate_project(project)
    s=project.samples[0];m=s.measurements[0];historical=deepcopy(m.results)
    s.analyte_mass*=2
    assert not is_current(project,s,m)
    assert m.results==historical
    assert project_summary(project)['between']['n']==0
    assert not calculate_project(project)
    assert m.results['analyte']['mean']==pytest.approx(historical['analyte']['mean']/2)

def test_independent_preparations_vs_acquisitions_vs_resonances(project):
    base=project.samples[0]
    for scale in (1.1,.9):
        s=deepcopy(base);s.id=uid();s.name=str(scale);s.analyte_mass*=scale
        s.measurements[0].id=uid();project.samples.append(s)
    extra=deepcopy(base.measurements[0]);extra.id=uid();base.measurements.append(extra)
    assert not calculate_project(project)
    summary=project_summary(project);assert summary['between']['n']==3
    assert summary['samples'][0]['acquisitions']==2
    expected=[s.measurements[0].results['analyte']['mean'] for s in project.samples]
    assert summary['between']['sd']==pytest.approx(np.std(expected,ddof=1))
    assert summary['between']['sem']==pytest.approx(np.std(expected,ddof=1)/np.sqrt(3))
    base.independent=False;calculate_project(project)
    assert project_summary(project)['between']['n']==2

def test_exclusions_are_preserved(project):
    s=project.samples[0];m=s.measurements[0];other=deepcopy(m.rois[0]);other.id=uid();other.area*=100
    other.accepted=False;other.exclusion_reason='Known overlap';m.rois.append(other)
    assert not calculate_project(project)
    assert len(m.results['signals'])==1 and len(m.rois)==3

def test_descriptive_statistics_not_population_sd():
    stats=descriptive([1,2,3])
    assert stats['sd']==1 and stats['sem']==pytest.approx(1/np.sqrt(3))
    assert stats['ci'][0]<1 and stats['ci'][1]>3
    assert descriptive([1])['sd'] is None
