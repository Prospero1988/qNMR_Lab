"""Scientific exports from explicitly calculated, traceable project snapshots."""
from io import BytesIO
from pathlib import Path
import csv
import json
import numpy as np
from .i18n import tr, message, enum_label, display_record, language
from . import __version__
from .models import utc_now
from .quantification import project_summary, is_current, substance_summaries
from .storage import project_dict, _json_default

LIMITATIONS=('Results depend on analyst-confirmed signal assignments, weighed chemical forms, reference-material purity, '
    'adequate relaxation and validated acquisition conditions. Diagnostic heuristics do not prove absence of overlap. '
    'Multiple resonances and repeat acquisitions are not independent preparations. SD, SEM and confidence intervals '
    'describe observed variation and are not a complete measurement uncertainty budget. Components are not forced to sum to 100%.')

SIGNAL_LABELS=dict(sample='Sample',measurement='Measurement',roi_id='ROI ID',signal='Signal',role='Role',
    compound_id='Compound ID',low_ppm='Lower limit (ppm)',high_ppm='Upper limit (ppm)',signed_area='Signed area',
    protons='Nuclei',protons_confirmed='Confirmed nuclei',accepted='Accepted',exclusion_reason='Exclusion reason',
    quality='Quality',atoms='Atoms',group='Group',comments='Comments',sample_included='Sample included',
    measurement_included='Measurement included',result_status='Result status',input_kind='Input kind',
    source_sha256='Source SHA256',reference_signal='Reference signal',reference_id='Reference ID',
    area_standard='Standard area',nuclei_standard='Standard nuclei',mw_analyte='Analyte MW (g/mol)',
    mw_standard='Standard MW (g/mol)',analyte_mass_mg='Analyte mass (mg)',standard_mass_mg='IS mass (mg)',
    purity_standard_fraction='IS purity fraction',proton_normalized_ratio='Proton-normalized ratio',
    standard_mmol='IS amount (mmol)',component_mmol='Component amount (mmol)',
    component_mass_mg='Component mass (mg)',assay_percent='Assay (%)')
SIGNAL_LABELS.update(signal_id='Signal ID',relative_integral='Relative integral',
    relative_reference_roi='Relative reference ROI',relative_reference_value='Relative reference value')

def signal_rows(project):
    rows=[]
    for s in project.samples:
        for m in s.measurements:
            status='current' if is_current(project,s,m) else 'historical / stale'
            for r in m.rois:
                result=next((x for x in m.results.get('signals',[]) if x['roi_id']==r.id),None)
                pairs=result['pairs'] if result else [{}]
                for pair in pairs:
                    rows.append(dict(sample=s.name,measurement=m.name,roi_id=r.id,signal=r.signal,role=r.role,
                        compound_id=r.compound_id,low_ppm=r.low if m.arrays else None,high_ppm=r.high if m.arrays else None,
                        signed_area=r.area,protons=r.protons,protons_confirmed=r.protons_confirmed,
                        accepted=r.accepted,exclusion_reason=r.exclusion_reason,quality=r.quality,
                        atoms=','.join(map(str,r.atoms)),group=r.group,comments=r.comments,
                        sample_included=s.include,measurement_included=m.include,result_status=status,
                        input_kind=m.input_kind,source_sha256=m.source_sha256,
                        **{key:pair.get(key) for key in ('reference_signal','reference_id','area_standard','nuclei_standard',
                            'mw_analyte','mw_standard','analyte_mass_mg','standard_mass_mg','purity_standard_fraction',
                            'proton_normalized_ratio','standard_mmol','component_mmol','component_mass_mg','assay_percent')},
                        signal_id=m.roi_label(r),relative_integral=m.relative_integral(r),
                        relative_reference_roi=m.integration_reference_id,relative_reference_value=m.integration_reference_value if m.integration_reference_id else None))
    return rows

def safe_text(value):
    if isinstance(value,str) and value.startswith(('=','+','-','@')):return "'"+value
    return value

def export_csv(project,path):
    rows=signal_rows(project)
    if not rows:raise ValueError(tr('No integrated resonances to export.'))
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
        for r in rows:w.writerow({k:safe_text(v) for k,v in r.items()})

def export_spectrum_csv(measurement,path):
    if 'spectrum' not in measurement.arrays:raise ValueError(tr('No processed spectrum in this measurement.'))
    x=measurement.arrays['ppm'];spectrum=measurement.arrays['spectrum'][0]
    with Path(path).open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow(['ppm','corrected_real','corrected_imaginary','phased_real_before_baseline','fitted_baseline'])
        writer.writerows(zip(x,spectrum.real,spectrum.imag,measurement.arrays['phased'][0].real,measurement.arrays['baseline'][0]))

def spectrum_png(measurement,path=None):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    if 'spectrum' not in measurement.arrays:return None
    fig=Figure(figsize=(10,3.8),layout='constrained');FigureCanvasAgg(fig);ax=fig.add_subplot()
    x=measurement.arrays['ppm'];y=measurement.arrays['spectrum'][0].real
    ax.plot(x,y,lw=.65,color='#163e62');ax.axhline(0,color='#64748b',lw=.6)
    for r in measurement.rois:
        color='#059669' if r.role=='standard' else '#2563eb'
        ax.axvspan(r.low,r.high,color=color,alpha=.15 if r.accepted else .05)
        value=measurement.relative_integral(r) if measurement.integration_reference_id else r.area
        label=measurement.roi_label(r)+' / '+r.signal+(f' = {value:.2f}' if value is not None else '')
        ax.text((r.low+r.high)/2,.97,label,transform=ax.get_xaxis_transform(),rotation=90,
            va='top',ha='center',fontsize=7,color=color)
    ax.invert_xaxis();ax.set_xlabel(tr('Chemical shift (ppm)'));ax.set_ylabel(tr('Signed real intensity (a.u.)'))
    ax.set_title(measurement.name,fontsize=10)
    buf=BytesIO();fig.savefig(buf,format='png',dpi=180)
    if path:Path(path).write_bytes(buf.getvalue())
    return buf.getvalue()

def statistics_png(project,path=None,*,analyte_id=None):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    summary=project_summary(project,analyte_id=analyte_id);rows=summary['samples']
    fig=Figure(figsize=(8,3),layout='constrained');FigureCanvasAgg(fig);ax=fig.add_subplot()
    for i,row in enumerate(rows):
        ax.plot(i,row['assay_percent'],'o',color='#163e62' if row['independent'] else '#94a3b8')
    if summary['between']['mean'] is not None:ax.axhline(summary['between']['mean'],ls='--',lw=1,color='#059669')
    ax.set_xticks(range(len(rows)),[r['name'] for r in rows],rotation=20)
    ax.set_ylabel(tr('Preparation mean assay (% w/w)'));ax.set_title(tr('Independent preparations; repeat acquisitions averaged within each sample'),fontsize=9)
    buf=BytesIO();fig.savefig(buf,format='png',dpi=160)
    if path:Path(path).write_bytes(buf.getvalue())
    return buf.getvalue()

def export_xlsx(project,path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table, TableStyleInfo
    summary=project_summary(project);groups=substance_summaries(project);wb=Workbook();ws=wb.active;ws.title=tr('Results')
    unassigned=any(s.include and s.analyte_id not in {g['analyte_id'] for g in groups} for s in project.samples)
    ws.append(['qNMR Lab '+__version__,project.name]);ws.append([tr('Status'),tr('Preliminary / incomplete') if not groups or unassigned or any(g['provisional'] for g in groups) else tr('Complete (at least 3 preparations)')])
    if len(groups)<=1:
        ws.append([tr('Independent preparations'),summary['between']['n']]);ws.append([tr('Mean assay (% w/w)'),summary['between']['mean']])
        for key,label in [('sd',tr('Sample SD (percentage points)')),('rsd_percent','RSD (%)'),('sem',tr('SEM (percentage points)'))]:ws.append([label,summary['between'][key]])
        ws.append([tr('Confidence interval'),json.dumps(summary['between']['ci'])])
    else:
        ws.append([tr('Substances'),len(groups)]);ws.append([tr('Separate substance results; no pooled mean')])
    ws.append([tr('Statistics'),message(summary['note'])])
    ws.append([tr('Omitted samples'),'; '.join(message(x) for x in summary['omitted'])]);ws.append([])
    ws.append([tr('Combined results by substance')])
    ws.append([tr('Substance'),tr('Independent preparations'),tr('Mean (% w/w)'),tr('SD (pp)'),'RSD (%)',tr('SEM (pp)'),tr('CI lower (% w/w)'),tr('CI upper (% w/w)'),tr('Status')])
    for group in groups:
        st=group['statistics'];ci=st['ci'] or [None,None]
        ws.append([group['name'],st['n'],st['mean'],st['sd'],st['rsd_percent'],st['sem'],*ci,
            tr('Complete (at least 3 preparations)') if group['complete'] else tr('Preliminary / incomplete')])
    ws.append([]);ws.append([tr('Substance'),tr('Preparation'),tr('Assay (% w/w)'),tr('Acquisitions'),tr('Independent')])
    for s in summary['samples']:
        name=next((c.name for c in project.compounds if c.id==s['analyte_id']),s['analyte_id'])
        ws.append([name,s['name'],s['assay_percent'],s['acquisitions'],enum_label(s['independent'])])
    rows=signal_rows(project);signal=wb.create_sheet(tr('Signals and calculations'))
    if rows:
        signal.append([tr(SIGNAL_LABELS[key]) for key in rows[0]])
        for row in rows:
            signal.append([safe_text(enum_label(v) if key in ('role','protons_confirmed','accepted','sample_included','measurement_included','result_status')
                                     else message(v) if key in ('quality','input_kind') else v) for key,v in row.items()])
        table=Table(displayName='QuantitativeSignals',ref=f'A1:{get_column_letter(len(rows[0]))}{len(rows)+1}')
        table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=True);signal.add_table(table)
    prep=wb.create_sheet(tr('Sample preparation'));prep.append([tr('Sample'),tr('Analyte ID'),tr('IS ID'),tr('Analyte mass'),tr('IS mass'),tr('Unit'),tr('Solvent'),tr('Date'),tr('Notes')])
    for s in project.samples:prep.append([s.name,s.analyte_id,s.standard_id,s.analyte_mass,s.standard_mass,s.mass_unit,s.solvent,s.preparation_date,s.notes])
    chem=wb.create_sheet(tr('Compounds and standards'));chem.append([tr('Type'),'ID',tr('Name'),'SMILES',tr('Formula'),tr('MW (g/mol)'),tr('Chemical form'),tr('Provenance'),tr('MW override reason'),tr('Purity fraction'),tr('Certificate'),tr('Batch'),tr('Reference ID'),tr('Expiration'),tr('Status')])
    for c in project.compounds:chem.append([tr('Compound'),c.id,c.name,c.smiles,c.formula,c.molecular_weight,c.chemical_form,c.provenance,c.mw_override_reason])
    for s in project.standards:
        c=s.compound;chem.append([tr('Standard'),s.id,c.name,c.smiles,c.formula,c.molecular_weight,c.chemical_form,c.provenance,c.mw_override_reason,s.purity_fraction,s.certificate,s.batch,s.reference_material_id,s.expiration,s.validation_status])
    trace=wb.create_sheet(tr('Processing and traceability'));trace.append([tr('Sample'),tr('Measurement'),tr('Source'),'SHA256',tr('Processing JSON'),tr('Input kind'),tr('Result time'),tr('Result status')])
    for s in project.samples:
        for m in s.measurements:trace.append([s.name,m.name,m.source_path,m.source_sha256,json.dumps(display_record(m.options),ensure_ascii=False),message(m.input_kind),m.results_at,tr('current') if is_current(project,s,m) else tr('historical/stale')])
    for sheet in wb:
        sheet.freeze_panes='B2';sheet.auto_filter.ref=sheet.dimensions
        for cell in sheet[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='163E62')
        for col in sheet.columns:
            letter=col[0].column_letter
            sheet.column_dimensions[letter].width=min(65,max(16,max(len(str(c.value or '')) for c in col[:40])+2))
            for c in col:
                c.alignment=Alignment(vertical='top',wrap_text=True)
                if isinstance(c.value,float):c.number_format='0.00' if sheet is signal and rows and list(rows[0])[c.column-1] in ('signed_area','relative_integral') else '0.000000'
                elif isinstance(c.value,str):c.value=safe_text(c.value)
        for row in sheet.iter_rows(min_row=2):
            if any(isinstance(c.value,str) and len(c.value)>70 for c in row):sheet.row_dimensions[row[0].row].height=60
    wb.save(path)

def export_docx(project,path,*,profile='standard'):
    from .report_document import generate_report
    generate_report(project,path,profile=profile)


def export_bundle(project,directory,*,profile='standard'):
    from .resonance_consistency import resonance_consistency
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    export_csv(project,directory/'integrals.csv');export_xlsx(project,directory/'results.xlsx');export_docx(project,directory/'report.docx',profile=profile)
    (directory/'traceability.json').write_text(json.dumps(dict(application_version=__version__,report_language=language(),report_profile=profile,report_format_version='3',exported_at=utc_now(),
        summary=project_summary(project),substance_results=substance_summaries(project),resonance_consistency=resonance_consistency(project),project=project_dict(project)),indent=2,ensure_ascii=False,allow_nan=False,default=_json_default),encoding='utf-8')
    for s in project.samples:
        for m in s.measurements:
            if m.arrays:spectrum_png(m,directory/f'spectrum_{s.id}_{m.id}.png')
