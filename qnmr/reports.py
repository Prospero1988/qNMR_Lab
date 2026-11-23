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

def _fmt(value,precision=5):return tr('not available') if value is None else f'{value:.{precision}f}'

def export_docx(project,path):
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from .chemistry import depiction
    summary=project_summary(project);groups=substance_summaries(project);doc=Document();section=doc.sections[0]
    section.page_width=Inches(8.5);section.page_height=Inches(11)
    section.top_margin=section.bottom_margin=Inches(.7);section.left_margin=section.right_margin=Inches(.75)
    for name in ('Normal','Title','Subtitle','Heading 1','Heading 2'):
        doc.styles[name].font.name='Calibri';doc.styles[name].font.color.rgb=RGBColor(0,0,0)
        # Corporate/default Word templates can carry borders on Title.
        for border in list(doc.styles[name]._element.iter(qn('w:pBdr'))):border.getparent().remove(border)
        for fonts in doc.styles[name]._element.iter(qn('w:rFonts')):
            for key in ('asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme'):
                fonts.attrib.pop(qn('w:'+key),None)
    doc.styles['Title'].font.underline=False
    doc.styles['Normal'].font.size=Pt(10.5)
    doc.add_heading(tr('Quantitative proton NMR research report'),0)
    doc.add_paragraph(project.name,style='Subtitle')
    doc.add_paragraph(tr('Generated {p0} by qNMR Lab {p1}. Analyst: {p2}.', p0=utc_now(), p1=__version__, p2=project.analyst or tr('not recorded')))
    unassigned=any(s.include and s.analyte_id not in {g['analyte_id'] for g in groups} for s in project.samples)
    if not groups or unassigned or any(g['provisional'] for g in groups):
        doc.add_paragraph(tr('Report status: preliminary. Review the completeness of each substance result.'))
    def table(headers,rows):
        t=doc.add_table(rows=1,cols=len(headers));t.style='Light Shading Accent 1'
        for c,h in zip(t.rows[0].cells,headers):c.text=str(h)
        repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
        for row in rows:
            for c,v in zip(t.add_row().cells,row):c.text='' if v is None else str(v)
        for row in t.rows:
            no_split=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no_split)
            for cell in row.cells:
                borders=OxmlElement('w:tcBorders')
                for side in ('top','left','bottom','right'):
                    el=OxmlElement('w:'+side);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');borders.append(el)
                cell._tc.get_or_add_tcPr().append(borders)
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(4)
                    for run in p.runs:run.font.size=Pt(9)
        return t
    doc.add_heading(tr('Purpose and principle'),1);doc.add_paragraph(message(project.purpose))
    doc.add_paragraph(tr('Assay (% w/w) = (IA / IIS) × (NIS / NA) × (MWA / MWIS) × (mIS / mA) × PIS × 100. PIS is a fraction. Areas are signed integrals of the displayed corrected real spectrum. No endpoint subtraction or independent analytical-peak normalization is applied.'))
    doc.add_heading(tr('Final result and preparation statistics'),1)
    doc.add_paragraph(tr('Signals → acquisition → independent preparation → substance result. Each independent preparation has equal weight; repeated acquisitions do not increase n.'))
    doc.add_paragraph(message(summary['note']))
    for group in groups:
        scoped=project_summary(project,analyte_id=group['analyte_id']);st=scoped['between']
        doc.add_heading(tr('Substance result: {p0}',p0=group['name']),2)
        doc.add_paragraph(tr('Complete (at least 3 preparations)') if group['complete'] else tr('Preliminary — at least three independent preparations with current results are required.'))
        interval=tr('not available') if st['ci'] is None else tr('{p0:.3f} to {p1:.3f}% w/w',p0=st['ci'][0],p1=st['ci'][1])
        doc.add_paragraph(tr('Mean assay {p0}% w/w; sample SD {p1} percentage points; RSD {p2}%; n = {p3} independent preparations. SEM {p4} percentage points. Confidence interval ({p5:.1f}%): {p6}.',p0=_fmt(st['mean'],3),p1=_fmt(st['sd'],3),p2=_fmt(st['rsd_percent'],3),p3=st['n'],p4=_fmt(st['sem'],3),p5=100*st['confidence'],p6=interval))
        if scoped['omitted']:doc.add_paragraph('; '.join(message(row) for row in scoped['omitted']))
        table([tr('Preparation'),tr('Mean assay (% w/w)'),tr('Acquisitions'),tr('Independent')],[(s['name'],_fmt(s['assay_percent'],4),s['acquisitions'],enum_label(s['independent'])) for s in scoped['samples']])
        if scoped['samples']:doc.add_picture(BytesIO(statistics_png(project,analyte_id=group['analyte_id'])),width=Inches(6.7))
    doc.add_page_break()
    doc.add_heading(tr('Sample preparation'),1)
    table([tr('Sample'),tr('Analyte mass'),tr('IS mass'),tr('Solvent'),tr('Prepared')],[(s.name,f'{s.analyte_mass} {s.mass_unit}',f'{s.standard_mass} {s.mass_unit}',s.solvent,s.preparation_date) for s in project.samples])
    for s in project.samples:
        if s.notes:doc.add_paragraph(f'{s.name}: {s.notes}')
    doc.add_heading(tr('Molecular data and reference material'),1)
    for c in project.compounds+[s.compound for s in project.standards]:
        doc.add_heading(c.name,2)
        info=doc.add_paragraph(tr('ID {p0}; formula {p1}; MW {p2} g/mol; weighed chemical form: {p3}.', p0=c.id, p1=c.formula or tr('not recorded'), p2=c.molecular_weight, p3=c.chemical_form or tr('not recorded')))
        provenance=doc.add_paragraph(tr('Provenance: {p0}. Manual MW explanation: {p1}.', p0=c.provenance, p1=c.mw_override_reason or tr('no override')))
        if c.smiles or c.molblock:
            info.paragraph_format.keep_with_next=True;provenance.paragraph_format.keep_with_next=True
        if c.smiles or c.molblock:
            try:doc.add_picture(BytesIO(depiction(c,width=650,height=300,png=True)[0]),width=Inches(4.8))
            except ValueError:doc.add_paragraph(tr('Structure depiction unavailable; inspect molecular data.'))
    for standard in project.standards:
        doc.add_paragraph(tr('Reference {p0}: purity {p1:.6g}% w/w; batch {p2}; material ID {p3}; expiry {p4}; status {p5}. Certificate: {p6}. {p7}', p0=standard.compound.name, p1=standard.purity_fraction * 100, p2=standard.batch or tr('not recorded'), p3=standard.reference_material_id or tr('not recorded'), p4=standard.expiration or tr('not recorded'), p5=standard.validation_status, p6=standard.certificate, p7=standard.notes))
    doc.add_heading(tr('Acquisition, processing and quantitative signals'),1)
    for s in project.samples:
        for m in s.measurements:
            doc.add_heading(f'{s.name} / {m.name}',2)
            doc.add_paragraph(tr('Input: {p0}. Source: {p1}. SHA256: {p2}. Results: {p3}; calculation time {p4}.', p0=message(m.input_kind), p1=m.source_path, p2=m.source_sha256, p3=tr('current') if is_current(project, s, m) else tr('historical/stale'), p4=m.results_at or tr('not calculated')))
            if not m.include:doc.add_paragraph(tr('Measurement excluded: ')+m.exclusion_reason)
            params=m.metadata.get('parameters',{})
            acquisition=[]
            for key,label,scale in [('x_frequency_Hz',tr('Observed frequency (MHz)'),1e-6),
                    ('x_sweep_Hz',tr('Acquired spectral width (Hz)'),1),('offset_ppm',tr('Carrier offset (ppm)'),1)]:
                if key in m.metadata:acquisition.append((label,str(m.metadata[key]*scale)))
            from .jeol import number
            for key,label,base in [('x_acq_duration',tr('Acquisition time (s)'),28),
                    ('relaxation_delay',tr('Relaxation delay (s)'),28),('x_90_width',tr('90-degree pulse (s)'),28)]:
                if key in params:
                    try:acquisition.append((label,str(number(params,key,base))))
                    except (ValueError,TypeError,KeyError):acquisition.append((key+tr(' (raw metadata; verify units)'),json.dumps(params[key])))
            for key,label in [('scans',tr('Number of scans')),('x_points',tr('Acquired points')),('experiment',tr('Pulse program'))]:
                if key in params:acquisition.append((label,str(params[key].get('value'))))
            if acquisition:table([tr('Acquisition parameter'),tr('Recorded value')],acquisition)
            else:doc.add_paragraph(tr('Acquisition metadata were not supplied with these reference integrals.'))
            if m.options:table([tr('Processing parameter'),tr('Value')],[(key,str(enum_label(value))) for key,value in display_record(m.options).items()])
            else:doc.add_paragraph(tr('Processing parameters and baseline model are unavailable for workbook-only reference integrals.'))
            table([tr('Signal / role'),tr('Range (ppm)'),tr('Signed area'),tr('Nuclei'),tr('Use / review')],[(m.roi_label(r)+' / '+r.signal+' / '+tr(r.role),
                tr('{p0:.5f} to {p1:.5f}', p0=r.low, p1=r.high) if m.arrays else tr('not supplied'),_fmt(r.area,2),r.protons,
                (tr('accepted') if r.accepted else tr('excluded: ')+r.exclusion_reason if r.exclusion_reason else tr('excluded'))+'; '+message(r.quality)) for r in m.rois])
            for r in m.rois:
                doc.add_paragraph(tr('{p0}: compound ID {p1}; atoms {p2}; group {p3}; confirmed nuclei {p4}. {p5} Diagnostics: {p6}', p0=r.signal, p1=r.compound_id, p2=r.atoms, p3=r.group, p4=enum_label(r.protons_confirmed), p5=r.comments, p6=json.dumps(display_record(r.diagnostics), ensure_ascii=False)))
            table([tr('Signal'),tr('Reference'),'IA/IIS × NIS/NA',tr('Amount (mmol)'),tr('Mass (mg)'),tr('Assay (%)')],[
                (r['signal'],p['reference_signal'],_fmt(p['proton_normalized_ratio']),_fmt(p['component_mmol'],7),_fmt(p['component_mass_mg']),_fmt(p['assay_percent']))
                for r in m.results.get('signals',[]) for p in r['pairs']])
            if m.results:
                within=m.results['analyte']
                doc.add_paragraph(tr('Within-acquisition analyte variation: {p0} accepted resonances; mean {p1}% w/w; sample SD {p2} percentage points; RSD {p3}%. Resonance values are correlated and do not increase the number of independent preparations.', p0=within['n'], p1=_fmt(within['mean'], 4), p2=_fmt(within['sd'], 4), p3=_fmt(within['rsd_percent'], 4)))
            image=spectrum_png(m)
            if image:doc.add_picture(BytesIO(image),width=Inches(6.7))
    doc.add_heading(tr('Additional components'),1)
    for key,st in summary['components'].items():
        if key in {s.analyte_id for s in project.samples}:continue
        c=project.compound(key);doc.add_paragraph(tr('{p0}: mean {p1}% w/w; SD {p2}; n={p3}. Direct internal-standard quantification; no mass-balance adjustment.', p0=c.name, p1=_fmt(st['mean'], 4), p2=_fmt(st['sd'], 4), p3=st['n']))
    doc.add_heading(tr('Limitations and analyst comments'),1);doc.add_paragraph(tr(LIMITATIONS));doc.add_paragraph(project.comments or tr('No additional analyst comments recorded.'))
    section.footer.paragraphs[0].text=tr('qNMR Lab {p0} — project {p1}', p0=__version__, p1=project.id)
    doc.save(path)

def export_bundle(project,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    export_csv(project,directory/'integrals.csv');export_xlsx(project,directory/'results.xlsx');export_docx(project,directory/'report.docx')
    (directory/'traceability.json').write_text(json.dumps(dict(application_version=__version__,report_language=language(),exported_at=utc_now(),
        summary=project_summary(project),substance_results=substance_summaries(project),project=project_dict(project)),indent=2,ensure_ascii=False,allow_nan=False,default=_json_default),encoding='utf-8')
    for s in project.samples:
        for m in s.measurements:
            if m.arrays:spectrum_png(m,directory/f'spectrum_{s.id}_{m.id}.png')
