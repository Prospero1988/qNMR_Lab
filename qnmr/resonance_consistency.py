"""Descriptive, read-only resonance comparisons using stored quantitative results.

Never pool acquisitions as independent samples or infer identity from S labels/ppm.
An identity is either an exact molecular atom/group assignment or an analyst-
confirmed correspondence bound to the current chemical and ROI assignment.
"""
from collections import defaultdict
import hashlib
import itertools
import json
import math
import numpy as np
from .models import utc_now
from .quantification import project_summary
from .report_data import shift


def assignment_signature(project, sample, roi):
    compound = project.compound(sample.analyte_id)
    payload = dict(compound=compound.id, smiles=compound.smiles, molblock=compound.molblock,
                   role=roi.role, assigned_compound=roi.compound_id, signal=roi.signal,
                   low=roi.low, high=roi.high, nuclei=roi.protons, atoms=roi.atoms, group=roi.group)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


def confirm_correspondence(project, groups, *, analyst=''):
    """Validate and return a new confirmation record; the caller commits it explicitly.

    groups: [{'label': 'H aromatic', 'members': [(measurement_id, roi_id), ...]}].
    No changes to ROIs, integrals, results or calculation fingerprints.
    """
    lookup = {(m.id,r.id):(s,r) for s in project.samples for m in s.measurements for r in m.rois}
    records=[]; used=set(); names=set()
    for group in groups:
        name=group['label'].strip()
        if not name or not group['members']:raise ValueError('Each correspondence requires a name and members.')
        members=[]; measurements=set(); compounds=set(); nuclei=set()
        for mid,rid in group['members']:
            key=(mid,rid)
            if key in used or mid in measurements:raise ValueError('A resonance must have at most one ROI per acquisition; assignments must be unique.')
            sample,roi=lookup[key]
            if roi.role!='analyte' or roi.compound_id!=sample.analyte_id:raise ValueError('Only assigned analyte ROIs can be compared.')
            compounds.add(sample.analyte_id);nuclei.add(roi.protons)
            members.append(dict(measurement_id=mid,roi_id=rid,signature=assignment_signature(project,sample,roi)))
            used.add(key);measurements.add(mid)
        if len(compounds)!=1 or len(nuclei)!=1:raise ValueError('Corresponding resonances must have the same analyte and contributing nuclei count.')
        compound=next(iter(compounds))
        if (compound,name) in names:raise ValueError('Use a unique resonance name within each analyte.')
        names.add((compound,name))
        records.append(dict(label=name,compound_id=compound,members=members,confirmed=True,
                            confirmed_at=utc_now(),analyst=analyst or project.analyst))
    return records


def identities(project):
    lookup={(m.id,r.id):(s,r) for s in project.samples for m in s.measurements for r in m.rois}
    candidates=defaultdict(list); explicit=set()
    for group in project.resonance_correspondence:
        if group.get('confirmed') is not True:continue
        for member in group.get('members',[]):
            key=(member.get('measurement_id'),member.get('roi_id'));explicit.add(key)
            if key not in lookup:continue
            sample,roi=lookup[key]
            if group.get('compound_id')!=sample.analyte_id or roi.compound_id!=sample.analyte_id or roi.role!='analyte':continue
            if member.get('signature')!=assignment_signature(project,sample,roi):continue
            candidates[key].append((('confirmed',sample.analyte_id,group['label']),group['label']))
    for key,(sample,roi) in lookup.items():
        if key in explicit or roi.role!='analyte' or roi.compound_id!=sample.analyte_id or not roi.atoms:continue
        # Atom indices refer to the same compound record; a group can distinguish
        # diastereotopic resonances on the same atom. Ambiguities are rejected below.
        from .chemistry import molecule
        try:
            mol=molecule(project.compound(sample.analyte_id))
            if any(type(i) is not int or i<0 or i>=mol.GetNumAtoms() for i in roi.atoms):continue
        except (ValueError,RuntimeError):continue
        atoms=tuple(sorted(set(roi.atoms)))
        identity=('atoms',sample.analyte_id,atoms,roi.group.strip(),roi.protons)
        name=roi.group.strip() or 'H @ '+','.join(map(str,atoms))
        candidates[key].append((identity,name))
    result={key:values[0] for key,values in candidates.items() if len(values)==1}
    counts=defaultdict(list)
    for key,(identity,_) in result.items():counts[(key[0],identity)].append(key)
    for keys in counts.values():
        if len(keys)>1:
            for key in keys:result.pop(key)
    return result


def classify(deviations):
    if len(deviations)<3:return 'limited'
    if all(abs(d)<1e-10 for d in deviations):return 'centered'
    if all(d < -1e-10 for d in deviations):return 'lower'
    if all(d > 1e-10 for d in deviations):return 'higher'
    return 'mixed'


def resonance_consistency(project):
    mapping=identities(project); summary=project_summary(project)
    eligible={row['id']:row for row in summary['samples'] if row['independent']}
    substances=[]
    for compound in project.compounds:
        grouped=defaultdict(list); unassigned=0; incomplete=0
        for sample in project.samples:
            if sample.analyte_id!=compound.id or sample.id not in eligible:continue
            measurements=[m for m in sample.measurements if m.include]
            signals=defaultdict(list)
            for m in measurements:
                roi_by_id={r.id:r for r in m.rois}
                for signal in m.results.get('signals',[]):
                    roi=roi_by_id.get(signal.get('roi_id'))
                    value=signal.get('assay_percent')
                    if roi is None or not roi.accepted or roi.role!='analyte' or roi.compound_id!=compound.id or signal.get('role')!='analyte' or signal.get('compound_id')!=compound.id:continue
                    match=mapping.get((m.id,roi.id))
                    if match is None:unassigned+=1;continue
                    if not isinstance(value,(int,float)) or not math.isfinite(value):continue
                    identity,name=match
                    signals[identity].append(dict(value=float(value),ppm=shift(roi),name=name,measurement_id=m.id))
            for identity,values in signals.items():
                # Partial repeat coverage can confound a resonance effect with a
                # measurement effect. Omit that sample/resonance, never impute it.
                if len(values)!=len(measurements) or len({v['measurement_id'] for v in values})!=len(measurements):
                    incomplete+=1;continue
                assay=float(np.mean([v['value'] for v in values]))
                ppms=[v['ppm'] for v in values if v['ppm'] is not None]
                grouped[identity].append(dict(sample_id=sample.id,sample=sample.name,assay=assay,
                    sample_mean=eligible[sample.id]['assay_percent'],deviation=assay-eligible[sample.id]['assay_percent'],
                    ppm=float(np.mean(ppms)) if ppms else None,name=values[0]['name'],measurements=len(measurements)))
        rows=[]
        for identity,points in grouped.items():
            deviations=[p['deviation'] for p in points];ppms=[p['ppm'] for p in points if p['ppm'] is not None]
            rows.append(dict(identity=identity,name=points[0]['name'],ppm=float(np.mean(ppms)) if ppms else None,
                mean_assay=float(np.mean([p['assay'] for p in points])),mean_deviation=float(np.mean(deviations)),
                sd_deviation=float(np.std(deviations,ddof=1)) if len(points)>1 else None,n=len(points),
                classification=classify(deviations),points=points))
        rows.sort(key=lambda r: (r['ppm'] is None,-r['ppm'] if r['ppm'] is not None else 0,r['name']))
        pairs=[];plot_available=False
        for a,b in itertools.combinations(rows,2):
            av={p['sample_id']:p for p in a['points']};bv={p['sample_id']:p for p in b['points']}
            common=av.keys() & bv.keys()
            if len(common)>=2:plot_available=True
            differences=[av[key]['assay']-bv[key]['assay'] for key in sorted(common)]
            if len(common)>=3 and (all(d < -1e-10 for d in differences) or all(d > 1e-10 for d in differences)):
                mean=float(np.mean(differences))
                pairs.append(dict(low=a if mean<0 else b,high=b if mean<0 else a,n=len(common),gap=abs(mean)))
        substances.append(dict(compound_id=compound.id,name=compound.name,rows=rows,
            unassigned=unassigned,incomplete=incomplete,plot_available=plot_available,
            persistent_pair=max(pairs,key=lambda p:p['gap']) if pairs else None))
    return substances
