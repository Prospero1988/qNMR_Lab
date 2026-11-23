"""Import and validate the supplied laboratory qNMR workbook layout.

Its spectral entries are ratios to a reference set to one, not recoverable raw
integrals. Imported records are explicitly labeled and cannot masquerade as FIDs.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from openpyxl import load_workbook
from .models import Project, Compound, Sample, Measurement, ROI
from .quantification import calculate_project, project_summary

def inspect_workbook(path):
    formulas=load_workbook(path,data_only=False);values=load_workbook(path,data_only=True)
    return [dict(name=ws.title,rows=ws.max_row,columns=ws.max_column,
        cells=[dict(cell=c.coordinate,value=values[ws.title][c.coordinate].value,
                    formula=c.value if c.data_type=='f' else None)
               for row in ws for c in row if c.value is not None]) for ws in formulas]

def import_reference(path: str | Path, sheet: str) -> Project:
    path=Path(path);workbook=load_workbook(path,data_only=True)
    if sheet not in workbook.sheetnames:raise ValueError('Worksheet not found.')
    ws=workbook[sheet];project=Project(name=f'{path.stem} — {sheet}')
    project.comments='Imported workbook reference values. Integrals are normalized to a one-proton IS integral of 1. Original raw areas and spectral boundaries are unavailable. Review the actual chemical form and certificate before new analyses.'
    project.compounds=[];standard=project.standards[0]
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    analyte=None;water=None
    for row in range(1,ws.max_row+1):
        label=ws[f'A{row}'].value;mi=ws[f'B{row}'].value;ma=ws[f'F{row}'].value
        if not (isinstance(label,str) and isinstance(mi,(float,int)) and isinstance(ma,(float,int))):continue
        mw=ws[f'G{row}'].value;mw_is=ws[f'D{row}'].value;purity=ws[f'C{row}'].value
        if not all(isinstance(v,(int,float)) for v in (mw,mw_is,purity)):raise ValueError(f'Incomplete mass/purity inputs at row {row}.')
        if analyte is None:
            analyte=Compound(name=f'Compound {sheet}',molecular_weight=float(mw),
                chemical_form='As represented by reference workbook; verify weighed form',
                provenance=f'{path.name}, {sheet}!G{row}, SHA256 {sha}',
                mw_override_reason='Manual molecular weight copied from the supplied reference workbook.')
            project.compounds.append(analyte)
            standard.compound.molecular_weight=float(mw_is)
            standard.purity_fraction=float(purity)/100
        if mw!=analyte.molecular_weight or mw_is!=standard.compound.molecular_weight or purity/100!=standard.purity_fraction:
            raise ValueError('This import layout requires a consistent analyte, standard MW and purity within a worksheet.')
        sample=Sample(name=label,analyte_id=analyte.id,standard_id=standard.id,
            analyte_mass=float(ma),standard_mass=float(mi),mass_unit='mg',solvent='DMSO-d6' if sheet=='06-46_v2' else '',
            preparation_date='',notes=f'Independent preparation per reference workbook row {row}; verify against source.')
        m=Measurement(name=f'{sheet} / {label} reference integrals',source_path=str(path.resolve()),source_sha256=sha,
            input_kind='workbook reference: normalized integrals; no raw spectrum',
            metadata=dict(worksheet=sheet,input_row=row,source_sha256=sha))
        ref=ROI(role='standard',compound_id=standard.compound.id,signal='IS reference normalized to 1',
            protons=1,protons_confirmed=True,area=1,quality='Reference values only',
            comments='Reference workbook convention. No original integration range or raw area supplied.')
        m.rois.append(ref)
        for rr in range(row+1,min(row+4,ws.max_row+1)):
            integral=ws[f'I{rr}'].value;factor=ws[f'H{rr}'].value
            if not isinstance(integral,(int,float)):continue
            if not isinstance(factor,(int,float)) or factor<=0:raise ValueError('Missing proton ratio in reference workbook.')
            m.rois.append(ROI(signal=str(ws[f'A{rr}'].value),compound_id=analyte.id,role='analyte',
                protons=1/float(factor),protons_confirmed=True,area=float(integral),reference_ids=[ref.id],
                quality='Reference values only',comments=f'{sheet}!I{rr}; proton ratio H{rr}; integration boundaries unavailable.'))
        wr=row+1;wi=ws[f'P{wr}'].value;wmw=ws[f'Q{wr}'].value
        if isinstance(wi,(int,float)) and isinstance(wmw,(int,float)):
            if water is None:
                water=Compound(name='Water (workbook)',smiles='O',formula='H2O',molecular_weight=float(wmw),
                    chemical_form='Water',provenance=f'{path.name}, Q{wr}',mw_override_reason='Workbook rounded molecular weight.')
                project.compounds.append(water)
            m.rois.append(ROI(signal='Water',role='water',compound_id=water.id,protons=2,protons_confirmed=True,
                area=float(wi),reference_ids=[ref.id],quality='Reference values only',comments=f'{sheet}!P{wr}; water integral relative to 1H reference.'))
        sample.measurements.append(m);project.samples.append(sample)
    if not project.samples:raise ValueError('No sample preparations matching the supplied qNMR layout were found.')
    errors=calculate_project(project)
    if errors:raise ValueError('\n'.join(errors))
    project.record('Imported reference workbook',path=str(path),sheet=sheet,sha256=sha)
    return project

def validation_comparison(path):
    workbook=load_workbook(path,data_only=True);report=[]
    for sheet in workbook.sheetnames:
        project=import_reference(path,sheet);summary=project_summary(project);ws=workbook[sheet]
        comparisons=[];all_signals=[]
        for sample in project.samples:
            m=sample.measurements[0];row=m.metadata['input_row']
            for signal in m.results['signals']:
                roi=next(r for r in m.rois if r.id==signal['roi_id'])
                if signal['role']=='analyte':
                    rr=int(roi.comments.split('!I')[1].split(';')[0]);cell=f'L{rr}'
                    all_signals.append(signal['assay_percent'])
                else:cell=f'T{row+1}'
                expected=float(ws[cell].value)
                comparisons.append(dict(cell=cell,role=signal['role'],expected=expected,
                    actual=signal['assay_percent'],difference=signal['assay_percent']-expected))
        report.append(dict(sheet=sheet,comparisons=comparisons,
            max_absolute_difference=max(abs(c['difference']) for c in comparisons),
            independent_preparation_statistics=summary['between'],
            workbook_pooled_mean=float(ws['N18'].value),workbook_pooled_population_sd=float(ws['N19'].value),
            recomputed_pooled_population_sd=float(np.std(all_signals,ddof=0)),
            mean_difference=summary['between']['mean']-float(ws['N18'].value)))
    return report
