"""Signed assay, explicit reference selection and hierarchical replicate statistics."""
from dataclasses import asdict, fields
import hashlib
import json
import math
import numpy as np
from scipy.stats import t as student_t
from .models import Project, Sample, Measurement, utc_now
from .chemistry import validate_mw

MASS_TO_MG={'g':1000.0,'mg':1.0,'ug':.001,'µg':.001}
CALCULATION_VERSION='1.0.0'  # UI/documentation releases do not invalidate scientific snapshots.

def mass_mg(value: float, unit: str) -> float:
    if unit not in MASS_TO_MG:raise ValueError('Mass units must be g, mg or ug.')
    result=float(value)*MASS_TO_MG[unit]
    if not math.isfinite(result) or result<=0:raise ValueError('Weighed masses must be positive and finite.')
    return result

def purity_fraction(value: float, unit: str) -> float:
    if unit not in ('fraction','%','% w/w'):raise ValueError('Unknown purity units.')
    p=float(value)/(100 if unit.startswith('%') else 1)
    if not math.isfinite(p) or not 0<p<=1:raise ValueError('Purity must be >0 and <=100% (or <=1 as fraction).')
    return p

def assay(area_a, area_is, nuclei_a, nuclei_is, mw_a, mw_is, mass_a_mg, mass_is_mg, purity_is) -> dict:
    values=[area_a,area_is,nuclei_a,nuclei_is,mw_a,mw_is,mass_a_mg,mass_is_mg,purity_is]
    if not np.isfinite(values).all():raise ValueError('Assay inputs must be finite.')
    if area_is==0:raise ValueError('Internal-standard integral is zero.')
    if min(nuclei_a,nuclei_is,mw_a,mw_is,mass_a_mg,mass_is_mg)<=0:raise ValueError('Proton counts, molecular weights and masses must be positive.')
    purity_fraction(purity_is,'fraction')
    ratio=(area_a/area_is)*(nuclei_is/nuclei_a)
    mmol_is=mass_is_mg*purity_is/mw_is
    mmol_a=ratio*mmol_is
    mg_a=mmol_a*mw_a
    fraction=mg_a/mass_a_mg
    return dict(area_analyte=float(area_a),area_standard=float(area_is),nuclei_analyte=float(nuclei_a),
        nuclei_standard=float(nuclei_is),proton_normalized_ratio=float(ratio),
        mw_analyte=mw_a,mw_standard=mw_is,analyte_mass_mg=mass_a_mg,standard_mass_mg=mass_is_mg,
        purity_standard_fraction=purity_is,standard_mmol=float(mmol_is),component_mmol=float(mmol_a),
        component_mass_mg=float(mg_a),assay_fraction=float(fraction),assay_percent=float(100*fraction),
        method='direct internal-standard quantification',
        warnings=['Nonpositive integral: inspect phase, baseline and assignments.'] if area_a<=0 or area_is<0 else [])

def descriptive(values, confidence=.95, *, inferential=True) -> dict:
    x=np.asarray(values,dtype=float)
    if not 0<confidence<1:raise ValueError('Confidence must be between 0 and 1.')
    if not np.isfinite(x).all():raise ValueError('Nonfinite statistical input.')
    n=len(x)
    result=dict(n=n,mean=float(np.mean(x)) if n else None,sd=None,rsd_percent=None,sem=None,ci=None,confidence=confidence)
    if n>1:
        sd=float(np.std(x,ddof=1));sem=sd/np.sqrt(n);mean=result['mean']
        radius=float(student_t.ppf((1+confidence)/2,n-1)*sem)
        result.update(sd=sd,rsd_percent=100*sd/abs(mean) if mean else None,
            sem=float(sem) if inferential else None,ci=[mean-radius,mean+radius] if inferential else None)
    return result

def fingerprint(project: Project, sample: Sample, measurement: Measurement) -> str:
    m=measurement
    standard=project.standard(sample.standard_id)
    payload=dict(compounds=[asdict(c) for c in project.compounds],standard=asdict(standard),
        sample={f.name:getattr(sample,f.name) for f in fields(sample) if f.name!='measurements'},
        options=m.options,source=m.source_sha256,rois=[asdict(r) for r in m.rois],
        reference_compatibility_confirmed=m.reference_compatibility_confirmed,include=m.include,
        spectrum_hash=hashlib.sha256(m.arrays['spectrum'].tobytes()).hexdigest() if 'spectrum' in m.arrays else '',
        input_kind=m.input_kind,calculation_version=CALCULATION_VERSION)
    # Diagnostics and cached areas are part of the recorded measurement snapshot.
    return hashlib.sha256(json.dumps(payload,sort_keys=True,allow_nan=False).encode()).hexdigest()

def is_current(project, sample, measurement) -> bool:
    try:return bool(measurement.results) and measurement.result_fingerprint==fingerprint(project,sample,measurement)
    except (ValueError,StopIteration,TypeError):return False

def quantify_measurement(project: Project, sample: Sample, measurement: Measurement) -> dict:
    try:standard=project.standard(sample.standard_id)
    except StopIteration:raise ValueError('Select an internal standard for this preparation.') from None
    try:analyte=project.compound(sample.analyte_id)
    except StopIteration:raise ValueError('Select an analyte compound for this preparation.') from None
    validate_mw(analyte);validate_mw(standard.compound)
    ma=mass_mg(sample.analyte_mass,sample.mass_unit);mi=mass_mg(sample.standard_mass,sample.mass_unit)
    refs=[r for r in measurement.rois if r.role=='standard' and r.accepted]
    targets=[r for r in measurement.rois if r.accepted and r.role in ('analyte','water','solvent','impurity','other')]
    if not refs:raise ValueError(f'{measurement.name}: select an accepted internal-standard ROI.')
    if not any(r.role=='analyte' for r in targets):raise ValueError('Select at least one accepted analyte signal.')
    for r in refs+targets:
        if r.area is None:raise ValueError(f'{r.signal}: no integrated area.')
        if r.role=='standard' and r.compound_id != standard.compound.id:
            raise ValueError('A reference ROI belongs to a different standard. Review assignments after changing standards.')
        if r.role=='analyte' and r.compound_id!=analyte.id:
            raise ValueError('An analyte ROI belongs to a different compound.')
    signals=[]
    for r in targets:
        compound=project.compound(r.compound_id);validate_mw(compound)
        selected=[ref for ref in refs if not r.reference_ids or ref.id in r.reference_ids]
        if r.reference_ids and len(selected)!=len(set(r.reference_ids)):
            raise ValueError('An assigned reference signal is missing or excluded.')
        if len(selected)>1 and not measurement.reference_compatibility_confirmed:
            raise ValueError('Multiple reference signals: explicitly confirm compatibility, or select a reference per ROI.')
        pairs=[]
        for ref in selected:
            pairs.append(dict(reference_id=ref.id,reference_signal=ref.signal,**assay(r.area,ref.area,r.protons,
                ref.protons,compound.molecular_weight,standard.compound.molecular_weight,ma,mi,standard.purity_fraction)))
        if not pairs:raise ValueError(f'{r.signal}: no eligible internal-standard signal.')
        signals.append(dict(roi_id=r.id,signal=r.signal,role=r.role,compound_id=compound.id,
            compound_name=compound.name,pairs=pairs,assay_percent=float(np.mean([p['assay_percent'] for p in pairs])),
            reference_aggregation='mean of explicitly compatible references' if len(pairs)>1 else 'single reference'))
    components={}
    for key in dict.fromkeys(s['compound_id'] for s in signals):
        group=[s for s in signals if s['compound_id']==key]
        components[key]=dict(name=group[0]['compound_name'],role=group[0]['role'],
            statistics=descriptive([s['assay_percent'] for s in group],inferential=False))
    return dict(signals=signals,components=components,analyte=components[analyte.id]['statistics'],
        standard_id=standard.id,standard_status=standard.validation_status,
        input_kind=measurement.input_kind,calculation_version=CALCULATION_VERSION,calculated_at=utc_now())

def calculate_project(project: Project) -> list[str]:
    """Explicit action: commit fresh measurement results, retain failed historical results."""
    errors=[]
    for sample in project.samples:
        if not sample.include:continue
        for m in sample.measurements:
            if not m.include:continue
            try:
                result=quantify_measurement(project,sample,m)
                m.results=result;m.results_at=utc_now();m.result_fingerprint=fingerprint(project,sample,m)
            except (ValueError,StopIteration) as e:errors.append(f'{sample.name} / {m.name}: {e}')
    project.record('Explicit calculation',errors=errors)
    return errors

def project_summary(project: Project, *, analyte_id=None) -> dict:
    samples=[];components={};omitted=[];excluded=[];analyte_groups={}
    for sample in project.samples:
        if analyte_id is not None and sample.analyte_id!=analyte_id:continue
        current=[m for m in sample.measurements if m.include and is_current(project,sample,m)]
        eligible=[m for m in sample.measurements if m.include]
        if not sample.include:excluded.append(f'{sample.name}: excluded ({sample.exclusion_reason})');continue
        if not eligible or len(current)!=len(eligible):
            omitted.append(f'{sample.name}: missing or stale measurement results');continue
        values=[m.results['analyte']['mean'] for m in current]
        entry=dict(id=sample.id,name=sample.name,analyte_id=sample.analyte_id,independent=sample.independent,acquisitions=len(current),
            acquisition_statistics=descriptive(values,inferential=False),assay_percent=float(np.mean(values)))
        samples.append(entry)
        # Only independently prepared samples count toward between-sample statistics.
        if sample.independent:
            analyte_groups.setdefault(sample.analyte_id,[]).append(entry['assay_percent'])
            for key in dict.fromkeys(k for m in current for k in m.results['components']):
                group=[m.results['components'][key]['statistics']['mean'] for m in current if key in m.results['components']]
                components.setdefault(key,[]).append(float(np.mean(group)))
    independent=next(iter(analyte_groups.values())) if len(analyte_groups)==1 else []
    if len(analyte_groups)>1:omitted.append('Multiple analytes: pooled statistics are disabled. Review the separate substance results.')
    return dict(samples=samples,between=descriptive(independent,project.statistics_settings['confidence']),
        between_by_analyte={key:descriptive(values,project.statistics_settings['confidence']) for key,values in analyte_groups.items()},
        components={key:descriptive(values,project.statistics_settings['confidence']) for key,values in components.items()},
        omitted=omitted,excluded=excluded,provisional=bool(omitted),
        note='SD and SEM describe observed variation; they are not a complete measurement uncertainty budget.')

def substance_summaries(project: Project) -> list[dict]:
    """One result per analyte; repeated acquisitions never increase n."""
    rows=[]
    for key in dict.fromkeys(s.analyte_id for s in project.samples if s.analyte_id):
        try:compound=project.compound(key)
        except StopIteration:continue
        summary=project_summary(project,analyte_id=key);stats=summary['between']
        planned=sum(s.include and s.independent and s.analyte_id==key for s in project.samples)
        rows.append(dict(analyte_id=key,name=compound.name,statistics=stats,planned_preparations=planned,
            acquisitions=sum(row['acquisitions'] for row in summary['samples'] if row['independent']),
            complete=stats['n']>=3 and not summary['provisional'],provisional=summary['provisional'] or stats['n']<3))
    return rows
