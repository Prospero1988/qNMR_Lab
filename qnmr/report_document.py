"""Reusable A4 scientific DOCX composition, independent of analytical algorithms."""
from datetime import datetime
from io import BytesIO
import re
from zoneinfo import ZoneInfo
from docx import Document
from docx.shared import Mm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from . import __version__
from .quantification import project_summary,CALCULATION_VERSION
from .i18n import message,display_record,language
from .report_data import ReportData,shift,sample_code
from .report_format import text,number,scalar,interval,missing,readable_date,yesno,signal_name
from .report_text import label
from . import report_figures as figures

NAVY='243F57';PALE='F2F5F8';GRAY='D9D9D9'

def element(name,**attributes):
    node=OxmlElement(name)
    for key,val in attributes.items():node.set(qn('w:'+key),str(val))
    return node

def breakable(value):
    value=text(value)
    return '\u200b'.join(value[i:i+32] for i in range(0,len(value),32))

class ScientificReport:
    def __init__(self,project,profile='standard'):
        if profile not in ('standard','extended'):raise ValueError('Report profile must be standard or extended')
        self.data=ReportData(project);self.project=project;self.profile=profile
        self.doc=Document();self.figures=0;self.generated=datetime.now(ZoneInfo('Europe/Warsaw'))
        self.configure()

    def configure(self):
        section=self.doc.sections[0]
        section.page_width=Mm(210);section.page_height=Mm(297)
        section.top_margin=section.bottom_margin=Mm(18)
        section.left_margin=section.right_margin=Mm(19)
        section.header_distance=section.footer_distance=Mm(8)
        section.different_first_page_header_footer=False
        self.doc.settings.odd_and_even_pages_header_footer=False
        from docx.enum.style import WD_STYLE_TYPE
        specifications={
            'Normal':(9.5,False,4),'Title':(23,False,7),'Subtitle':(11,False,5),
            'Heading 1':(12,True,5),'Heading 2':(10.5,True,4),'Heading 3':(10,True,3),
            'Report Small':(8,False,3),'Report Caption':(8,False,5),
            'Report Result':(20,True,4),'Report Table':(8.2,False,0),'Report Figure':(8,False,0),
        }
        for name,(size,bold,after) in specifications.items():
            style=self.doc.styles[name] if name in self.doc.styles else self.doc.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
            style.font.name='Calibri';style.font.size=Pt(size);style.font.bold=bold;style.font.color.rgb=RGBColor(0,0,0)
            style.font.underline=False
            for border in list(style.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
            for fonts in style.element.iter(qn('w:rFonts')):
                for key in ('asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme'):fonts.attrib.pop(qn('w:'+key),None)
            pf=style.paragraph_format;pf.space_after=Pt(after);pf.line_spacing=1.08;pf.widow_control=True
            if name.startswith('Heading'):pf.space_before=Pt(9);pf.keep_with_next=True
        header=section.header.paragraphs[0];header.style=self.doc.styles['Report Small']
        header.text='qNMR Lab  |  '+self.data.analyte_names[:85]
        footer=section.footer.paragraphs[0];footer.style=self.doc.styles['Report Small']
        footer.paragraph_format.tab_stops.add_tab_stop(Mm(172),WD_TAB_ALIGNMENT.RIGHT)
        footer.add_run('qNMR Lab '+__version__+'\t'+label('page')+' ')
        for field,following in [('PAGE',' '+label('of')+' '),('NUMPAGES','')]:
            footer._p.append(element('w:fldSimple',instr=field));footer.add_run(following)
        self.doc.core_properties.title=label('title')+' — '+self.data.analyte_names
        self.doc.core_properties.subject=self.data.project_name
        self.doc.core_properties.author=self.project.analyst or ''
        self.doc.core_properties.comments='Generated from stored project results; no reprocessing or recalculation.'
        self.doc.settings.element.append(element('w:updateFields',val='true'))

    def p(self,content,style=None):return self.doc.add_paragraph(text(content),style=style)
    def heading(self,content,level=1):return self.doc.add_heading(text(content),level)

    def table(self,headers,rows,widths,*,numeric=(),small=False,keep=False):
        assert abs(sum(widths)-172)<.1
        table=self.doc.add_table(rows=1,cols=len(headers));table.autofit=False
        table.alignment=WD_TABLE_ALIGNMENT.CENTER
        for col,width in zip(table.columns,widths):col.width=Mm(width)
        table.rows[0]._tr.get_or_add_trPr().append(element('w:tblHeader'))
        content_rows=[headers]+list(rows)
        for index,row in enumerate(content_rows):
            cells=table.rows[0].cells if index==0 else table.add_row().cells
            table.rows[index]._tr.get_or_add_trPr().append(element('w:cantSplit'))
            for column,(cell,content,width) in enumerate(zip(cells,row,widths)):
                cell.width=Mm(width);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                props=cell._tc.get_or_add_tcPr();borders=element('w:tcBorders')
                for side in ('top','left','bottom','right'):borders.append(element('w:'+side,val='single',sz='4',color=GRAY))
                props.append(borders)
                margins=element('w:tcMar')
                for side,value in [('top',60),('bottom',60),('left',75),('right',75)]:margins.append(element('w:'+side,w=value,type='dxa'))
                props.append(margins)
                props.append(element('w:shd',fill=NAVY if index==0 else PALE if index%2 else 'FFFFFF'))
                p=cell.paragraphs[0];p.style=self.doc.styles['Report Table']
                p.text=text(content)
                if column in numeric:p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
                if index==0:
                    p.paragraph_format.keep_with_next=True
                    for run in p.runs:run.font.bold=True;run.font.color.rgb=RGBColor(255,255,255)
                elif small:
                    for run in p.runs:run.font.size=Pt(7.6)
                if keep:p.paragraph_format.keep_with_next=index<len(content_rows)-1
        spacer=self.p('',style='Report Small');spacer.paragraph_format.line_spacing=Pt(1)
        spacer.paragraph_format.space_after=Pt(3)
        return table

    def caption(self,caption):
        self.figures+=1
        return self.p(label('figure',n=self.figures,caption=caption),'Report Caption')

    def figure(self,picture,caption):
        if not picture:return
        p=self.doc.add_paragraph(style='Report Figure');p.paragraph_format.keep_with_next=True
        p.add_run().add_picture(BytesIO(picture),width=Mm(172))
        self.caption(caption)

    def hyperlink(self,paragraph,target):
        # Keep the original URL target intact, even when the display wraps.
        link=OxmlElement('w:hyperlink');link.set(qn('r:id'),paragraph.part.relate_to(target,RELATIONSHIP_TYPE.HYPERLINK,is_external=True))
        run=OxmlElement('w:r');props=OxmlElement('w:rPr');props.append(element('w:color',val=NAVY));props.append(element('w:u',val='single'));run.append(props)
        content=OxmlElement('w:t');content.text=breakable(target);run.append(content);link.append(run);paragraph._p.append(link)

    def identification(self):
        self.heading(label('title'),0)
        self.p(self.data.analyte_names,'Subtitle')
        slug=re.sub(r'[^\w-]+','-',self.data.analyte_names).strip('-')[:42] or 'QNMR'
        document_id='QNMR-'+self.generated.strftime('%Y%m%d-%H%M')+'-'+slug
        self.p(label('document')+': '+document_id,'Report Small')
        self.p(label('project')+': '+self.data.project_name+'  |  '+label('generated')+': '+readable_date(self.generated),'Report Small')
        if self.project.analyst:self.p(label('analyst')+': '+self.project.analyst,'Report Small')
        self.p('qNMR Lab '+__version__+'  |  '+label('extended' if self.profile=='extended' else 'standard_profile'),'Report Small')

    def summary(self):
        self.heading(label('summary'))
        if not self.data.groups:self.p(label('no_results'))
        for group in self.data.groups:
            st=group['statistics']
            if len(self.data.groups)>1:self.heading(group['name'],2)
            if st['mean'] is not None:self.p(number(st['mean'],3)+' '+label('fraction_unit'),'Report Result')
            else:self.p(label('no_results'))
            self.table([label('sd'),label('rsd'),label('n'),label('ci',confidence=number(st['confidence']*100,0))],
                [[number(st['sd'],3),number(st['rsd_percent'],3),number(st['n'],0),interval(st['ci'],3)+' '+label('fraction_unit') if st['ci'] else missing()]],
                [31,29,37,75],numeric=(0,1,2,3))
            used={s.standard_id for s in self.project.samples if s.analyte_id==group['analyte_id']}
            names=[s.compound.name for s in self.project.standards if s.id in used]
            self.p(label('standard')+': '+('; '.join(names) or missing()))
            if group['provisional']:self.p(label('preliminary'))
        self.p(label('aggregation'),'Report Small')

    def chemistry(self):
        self.heading(label('chemistry'))
        chemicals=[(c,label('analyte'),None) for c in self.project.compounds if any(s.analyte_id==c.id for s in self.project.samples)]
        chemicals += [(s.compound,label('standard'),s) for s in self.project.standards if any(sample.standard_id==s.id for sample in self.project.samples)]
        if not chemicals:self.p(label('empty'));return
        for start in range(0,len(chemicals),2):
            pair=chemicals[start:start+2]
            headers=['']+[role+' — '+c.name for c,role,_ in pair]
            width=66 if len(pair)==2 else 132;widths=[40]+[width]*len(pair)
            rows=[]
            for key,extract in [
                ('formula',lambda c,s:c.formula or missing()),('mw',lambda c,s:number(c.molecular_weight,4) if c.molecular_weight>0 else missing()),
                ('form',lambda c,s:c.chemical_form or missing()),
                ('purity',lambda c,s:number(s.purity_fraction*100,2) if s and s.purity_fraction>0 else missing() if s else '—'),
                ('batch',lambda c,s:s.batch or missing() if s else '—'),
                ('material_id',lambda c,s:s.reference_material_id or missing() if s else '—'),
                ('expiry',lambda c,s:readable_date(s.expiration) if s else '—'),
                ('status',lambda c,s:message(s.validation_status) if s else '—')]:
                rows.append([label(key)]+[extract(c,s) for c,_,s in pair])
            self.caption(label('structures')).paragraph_format.keep_with_next=True
            table=self.table(headers,[['']*(len(pair)+1)]+rows,widths)
            table.cell(1,0).paragraphs[0].text='2D'
            for i,(compound,role,standard) in enumerate(pair,1):
                try:picture=figures.structure(compound)
                except (ValueError,RuntimeError):picture=None
                cell=table.cell(1,i)
                if picture:
                    from PIL import Image
                    image=Image.open(BytesIO(picture));factor=min((width-6)/image.width,62/image.height)
                    p=cell.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run().add_picture(BytesIO(picture),width=Mm(image.width*factor),height=Mm(image.height*factor))
                else:cell.paragraphs[0].text=label('no_structure')
                if standard:
                    p=self.p(label('certificate')+' — '+compound.name+': ','Report Small')
                    if re.match(r'^https?://',standard.certificate):self.hyperlink(p,standard.certificate)
                    else:p.add_run(standard.certificate or missing())
                    if standard.notes:self.p(standard.notes,'Report Small')

    def methodology(self):
        from .report_data import compare_fields
        self.heading(label('experimental')).paragraph_format.page_break_before=True
        for kind in ('acquisition','processing'):
            self.heading(label(kind),2)
            common,different=compare_fields(self.data.records,kind)
            common=[row for row in common if row[1]!=missing()]
            if common:self.table([label('parameter'),label('value')],common,[76,96],numeric=(1,))
            if different:
                self.p(label('differences'),'Report Small')
                # Limit comparison width; additional acquisition groups get their own table.
                for start in range(0,len(self.data.records),4):
                    records=self.data.records[start:start+4];count=len(records)
                    rows=[[row[0]]+row[start+1:start+1+count] for row in different]
                    self.table([label('parameter')]+[r['code'] for r in records],rows,[64]+[108/count]*count,numeric=tuple(range(1,count+1)))
            if not common and not different:self.p(label('empty'))
        self.p(label('method_note'),'Report Small')

    def preparation(self):
        self.heading(label('preparation'))
        if not self.project.samples:self.p(label('empty'));return
        self.table([label('sample'),label('mass_a'),label('mass_is'),label('solvent'),label('date')],
            [[s.name,self.data.mass(s),self.data.mass(s,True),s.solvent or missing(),readable_date(s.preparation_date)] for s in self.project.samples],
            [42,29,29,40,32],numeric=(1,2))
        for s in self.project.samples:
            if s.notes:self.p(s.name+': '+s.notes,'Report Small')

    def principle(self):
        self.heading(label('principle'))
        if self.project.purpose and self.project.purpose!='Quantitative proton NMR using an internal standard':self.p(message(self.project.purpose))
        # Office Math uses true fractions and subscripts, not a serialized equation.
        def run(content):
            node=OxmlElement('m:r');t=OxmlElement('m:t');t.text=content;node.append(t);return node
        def sub(base,index):
            node=OxmlElement('m:sSub');e=OxmlElement('m:e');e.append(run(base));s=OxmlElement('m:sub');s.append(run(index));node.extend([e,s]);return node
        def fraction(base,top,bottom):
            node=OxmlElement('m:f');num=OxmlElement('m:num');num.append(sub(base,top));den=OxmlElement('m:den');den.append(sub(base,bottom));node.extend([num,den]);return node
        p=self.doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        math=OxmlElement('m:oMath');math.extend([sub('w','A'),run(' (%) = '),fraction('I','A','IS'),run(' × '),fraction('N','IS','A'),run(' × '),fraction('M','A','IS'),run(' × '),fraction('m','IS','A'),run(' × '),sub('P','IS'),run(' × 100')]);p._p.append(math)
        self.p(label('definitions'),'Report Small');self.p(label('equation_note'))

    def selection(self):
        self.heading(label('signals'))
        for accepted,key in [(True,'included_signals'),(False,'other_signals')]:
            rows,notes=self.data.selection_matrix(accepted)
            if not rows:continue
            self.heading(label(key),2)
            for start in range(0,len(self.data.records),4):
                records=self.data.records[start:start+4];n=len(records)
                self.table([label('ppm'),label('compound'),label('protons'),label('range')]+[r['code'] for r in records]+[label('use')],
                    [row[:4]+row[4+start:4+start+n]+row[-1:] for row in rows],[16,37,12,33]+[48/n]*n+[26],numeric=(0,2),small=True)
            for note in notes:self.p(note,'Report Small')
        if not self.data.records:self.p(label('empty'))
        self.p(label('selection_note'),'Report Small')

    def individual(self):
        self.heading(label('individual'))
        if not self.project.samples:self.p(label('empty'));return
        for sample in self.project.samples:
            self.heading(sample.name,2)
            result=self.data.sample_result(sample)
            records=[r for r in self.data.records if r['sample'] is sample]
            acquisition='  |  '+label('measurement')+' '+records[0]['code'] if len(records)==1 else ''
            if result:p=self.p(label('sample_result',value=number(result['assay_percent'],3),unit=label('fraction_unit'))+acquisition)
            else:p=self.p(label('no_results'))
            p.paragraph_format.keep_with_next=bool(sample.measurements)
            if not sample.include:self.p(label('excluded_sample')+(': '+sample.exclusion_reason if sample.exclusion_reason else ''))
            if not sample.independent:self.p(label('not_independent'))
            if result and result['acquisitions']>1:
                stats=result['acquisition_statistics'];self.p(label('repeat_stats',count=stats['n'],sd=number(stats['sd'],3),rsd=number(stats['rsd_percent'],3)),'Report Small')
            for rec in records:
                block_start=len(self.doc.element.body)-1
                m=rec['measurement']
                if len(records)>1:self.heading(rec['code']+' — '+m.name,3)
                eligible=self.data.eligible(rec)
                if not eligible:self.p(label('stale_notice'))
                rows=[]
                for sig in m.results.get('signals',[]):
                    roi=next((r for r in m.rois if r.id==sig['roi_id']),None)
                    sid=m.roi_label(roi) if roi else sig.get('signal','')
                    for pair in sig.get('pairs',[]):
                        ref=next((r for r in m.rois if r.id==pair.get('reference_id')),None)
                        reference=m.roi_label(ref) if ref else pair.get('reference_signal','')
                        rows.append([sid+' / '+signal_name(sig['signal']),signal_name(reference),number(pair.get('nuclei_analyte'),significant=6),
                            number(pair.get('proton_normalized_ratio'),5),number(pair.get('assay_percent'),3),label('current' if eligible else 'historical')])
                if rows:self.table([label('signal'),label('reference_short'),label('protons'),label('ratio'),label('assay'),label('status')],rows,[43,18,21,32,34,24],numeric=(2,3,4))
                else:self.p(label('no_results'))
                within=m.results.get('analyte')
                if within and within.get('n',0)>1:self.p(label('within',count=within['n'],sd=number(within['sd'],3),rsd=number(within['rsd_percent'],3)),'Report Small')
                if any(len(sig.get('pairs',[]))>1 for sig in m.results.get('signals',[])):self.p(label('multiple_refs'),'Report Small')
                if m.notes:self.p(m.notes,'Report Small')
                if not m.include and m.exclusion_reason:self.p(label('excluded')+': '+m.exclusion_reason,'Report Small')
                picture=figures.spectrum(m)
                if picture:self.figure(picture,rec['code']+'. '+label('spectrum'))
                else:self.p(label('no_spectrum'),'Report Small')
                # Keep a compact acquisition table with its observations and figure.
                for node in list(self.doc.element.body)[block_start:-1]:
                    for paragraph in ([node] if node.tag==qn('w:p') else node.iter(qn('w:p'))):
                        paragraph.get_or_add_pPr().get_or_add_keepNext().val=True
                self.doc.paragraphs[-1].paragraph_format.keep_with_next=False

    def statistics(self):
        self.heading(label('statistics'))
        if not self.data.groups:self.p(label('no_results'));return
        for group in self.data.groups:
            summary=project_summary(self.project,analyte_id=group['analyte_id']);stats=summary['between']
            if len(self.data.groups)>1:self.heading(group['name'],2)
            rows=[[row['name'],number(row['assay_percent'],3),number(row['acquisitions'],0),yesno(row['independent'])] for row in summary['samples']]
            if rows:self.table([label('sample'),label('assay'),label('measurement'),label('independent')],rows,[64,43,32,33],numeric=(1,2))
            self.table([label('mean'),label('sd'),label('rsd'),label('n'),label('sem')],
                [[number(stats['mean'],3),number(stats['sd'],3),number(stats['rsd_percent'],3),number(stats['n'],0),number(stats['sem'],3)]],
                [43,33,29,35,32],numeric=(0,1,2,3,4))
            self.p(label('ci',confidence=number(stats['confidence']*100,0))+': '+interval(stats['ci'],3)+' '+label('fraction_unit'),'Report Small')
            self.figure(figures.statistics(summary),group['name']+'. '+label('statistics_caption'))
            for note in summary['omitted']+summary['excluded']:self.p(message(note),'Report Small')
            self.p(label('complete') if group['complete'] else label('preliminary'),'Report Small')
            components=[(self.data.compound_name(key),st) for key,st in summary['components'].items() if key!=group['analyte_id']]
            if components:
                self.heading(label('components'),2)
                self.table([label('compound'),label('mean'),label('sd'),label('rsd'),label('n')],
                    [[name,number(st['mean'],3),number(st['sd'],3),number(st['rsd_percent'],3),number(st['n'],0)] for name,st in components],
                    [50,38,30,26,28],numeric=(1,2,3,4))

    def discussion(self):
        self.heading(label('discussion'));lowest=[]
        for rec in self.data.records:
            if not self.data.eligible(rec):continue
            signals=[s for s in rec['measurement'].results.get('signals',[]) if s['role']=='analyte']
            if len(signals)<2:continue
            low=min(signals,key=lambda s:s['assay_percent']);high=max(signals,key=lambda s:s['assay_percent'])
            if number(low['assay_percent'],3)==number(high['assay_percent'],3):continue
            self.p(label('span',measurement=rec['code'],low=number(low['assay_percent'],3),high=number(high['assay_percent'],3),unit=label('fraction_unit'),signal=signal_name(low['signal'])))
            lowest.append((rec['sample'].analyte_id,low['signal']))
        for group in self.data.groups:
            names=[name for key,name in lowest if key==group['analyte_id']]
            if len(names)>1 and len(set(names))==1:self.p(label('consistent_low',signal=signal_name(names[0]),count=len(names)))
        excluded=sum(not roi.accepted for rec in self.data.records for roi in rec['measurement'].rois)
        unassigned=sum(roi.role=='unassigned' for rec in self.data.records for roi in rec['measurement'].rois)
        if excluded:self.p(label('excluded_count',count=excluded),'Report Small')
        if unassigned:self.p(label('unassigned_count',count=unassigned),'Report Small')
        warnings=self.data.warnings()
        if warnings:
            self.heading(label('qc'),2)
            for origin,warning in warnings:self.p(origin+': '+warning,'Report Small')
        else:self.p(label('no_qc'),'Report Small')
        if self.project.comments:self.p(self.project.comments)

    def limitations(self):
        self.heading(label('limitations'));self.p(label('limits_text'));self.p(label('no_inference'))

    def appendices(self):
        self.doc.add_page_break();self.heading(label('appendices'))
        self.heading(label('trace'),2)
        self.table([label('parameter'),label('value')],[[label('project'),self.project.id],
            [label('software'),'qNMR Lab '+__version__],[label('calculation_version'),CALCULATION_VERSION],
            [label('layout_version'),'2']], [45,127])
        for rec in self.data.records:
            m=rec['measurement'];s=rec['sample'];self.heading(rec['code']+' — '+sample_code(s),3)
            rows=[[label('sample'),s.name],[label('original_name'),m.name],[label('internal_id'),m.id],
                [label('source'),breakable(m.source_path) or missing()],[label('sha'),m.source_sha256 or missing()],
                [label('input'),message(m.input_kind)],[label('calculated'),readable_date(m.results_at,time=True)],
                [label('status'),label('current' if rec['current'] else 'historical')]]
            self.table([label('parameter'),label('value')],rows,[35,137],small=True,keep=True)
        self.heading(label('chemical_trace'),2)
        for compound in self.project.compounds+[s.compound for s in self.project.standards]:
            self.heading(compound.name,3)
            self.table([label('parameter'),label('value')],[[label('internal_id'),compound.id],
                [label('provenance'),compound.provenance or missing()],[label('override'),compound.mw_override_reason or missing()],
                [label('smiles'),breakable(compound.smiles) or missing()],
                [label('source'),breakable(compound.source_path) or missing()],
                [label('sha'),compound.source_sha256 or missing()]], [45,127],small=True,keep=True)
        if self.profile=='extended':self.technical_appendix()
        else:self.p(label('extended_note'),'Report Small')

    def technical_appendix(self):
        from .report_format import structured_rows,field_label
        self.heading(label('technical'),2)
        def rendered(v,key=''):
            if isinstance(v,(dict,list,tuple)):
                return '; '.join((key+': ' if key else '')+item for key,item in structured_rows(display_record(v)))
            from numbers import Real
            precision=3 if key=='snr_estimate' or isinstance(v,Real) and v and abs(v)<1e-10 else 4 if key in ('noise_rms_estimate','boundary_sensitivity_percent') else 5 if key=='boundary_step_ppm' else 6
            return scalar(v,significant=precision)
        for rec in self.data.records:
            m=rec['measurement'];self.heading(rec['code']+' — '+m.name,3)
            if m.options:self.table([label('processing'),label('value')],structured_rows(display_record(m.options),significant=12)+[(label('ref_compat'),yesno(m.reference_compatibility_confirmed))],[73,99],small=True)
            if m.diagnostics:self.table([label('diagnostics'),label('value')],structured_rows(display_record(m.diagnostics)),[73,99],small=True)
            roi_rows=[[m.roi_label(r),number(r.low,6),number(r.high,6),number(r.area,significant=12),number(r.protons,significant=8),label('accepted' if r.accepted else 'excluded')] for r in m.rois]
            if roi_rows:self.table([label('signal'),'ppm min','ppm max',label('area'),label('protons'),label('use')],roi_rows,[19,31,31,40,21,30],numeric=(1,2,3,4),small=True)
            notes={}
            for roi in m.rois:
                fields=[(label('atoms'),', '.join(number(i,0) for i in roi.atoms)),(label('group'),roi.group),(label('comments'),roi.comments),(label('excluded'),roi.exclusion_reason),(label('quality'),message(roi.quality))]
                references=[signal_name(next((r.signal for r in m.rois if r.id==key),key)) for key in roi.reference_ids]
                if references:fields.append((label('reference_ids'),'; '.join(references)))
                for key,v in fields:
                    if v:notes.setdefault((key,v),[]).append(m.roi_label(roi))
            if notes:self.table([label('signal'),label('parameter'),label('value')],[[', '.join(ids),key,v] for (key,v),ids in notes.items()],[30,41,101],small=True)
            keys=list(dict.fromkeys(key for r in m.rois for key in r.diagnostics));common=[];different=[]
            for key in keys:
                values=[r.diagnostics.get(key) for r in m.rois]
                display_name=field_label(next(iter(display_record({key:None}))))
                if all(v==values[0] for v in values):common.append([display_name,rendered(values[0],key)])
                else:different.append((display_name,values,key))
            if common:self.table([label('diagnostics'),label('value')],common,[76,96],small=True)
            for start in range(0,len(different),3):
                columns=different[start:start+3];count=len(columns)
                rows=[[m.roi_label(r)]+[rendered(values[i],key) for _,values,key in columns] for i,r in enumerate(m.rois)]
                self.table([label('signal')]+[name for name,_,_ in columns],rows,[20]+[152/count]*count,small=True)
            pairs=[]
            for sig in m.results.get('signals',[]):
                for pair in sig.get('pairs',[]):
                    pairs.append([signal_name(sig['signal']),signal_name(pair['reference_signal']),number(pair.get('proton_normalized_ratio'),significant=10),number(pair.get('component_mmol'),significant=10),number(pair.get('component_mass_mg'),significant=10),number(pair.get('assay_percent'),significant=10)])
            if pairs:self.table([label('signal'),label('reference_short'),label('ratio'),label('amount'),label('mass'),label('assay')],pairs,[27,27,31,29,29,29],numeric=(2,3,4,5),small=True)
            events=[]
            for i,event in enumerate(m.process_history,1):
                action=event.get('action','')
                action=label({'Initial processing':'initial_processing','Interactive reference':'interactive_reference'}[action]) if action in ('Initial processing','Interactive reference') else message(action)
                stamp=readable_date(event.get('time'),time=True)+(' / '+action if action else '')
                before=event.get('before',{});after=event.get('options',{})
                changes={key:v for key,v in after.items() if key not in before or before[key]!=v}
                changes.update({key:v for key,v in event.items() if key not in ('before','options','time','action') and v is not None})
                if changes:
                    for key,v in structured_rows(display_record(changes),significant=12):events.append([stamp,key,v]);stamp=''
                else:events.append([stamp,'',''])
            if events:self.table([label('event'),label('parameter'),label('value')],events,[50,48,74],small=True)
            zoom=figures.spectrum(m,zoom=True)
            if zoom:self.figure(zoom,rec['code']+'. '+label('zoom'))

    def save(self,path):
        for section in (self.identification,self.summary,self.chemistry,self.methodology,self.preparation,self.principle,
                self.selection,self.individual,self.statistics,self.discussion,self.limitations,self.appendices):section()
        self.doc.save(path)

def generate_report(project,path,*,profile='standard'):
    ScientificReport(project,profile).save(path)
