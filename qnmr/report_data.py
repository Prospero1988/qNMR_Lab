"""Read-only extraction of stored report data, without processing or calculation."""
from dataclasses import dataclass
import re
from .quantification import project_summary,substance_summaries,is_current,MASS_TO_MG
from .jeol import number as parameter_number
from .report_format import number,value,interval,missing,scalar,text,structured_rows
from .report_text import label
from .i18n import message

@dataclass(frozen=True)
class Field:
    key:str
    original:object
    display:str

def measurement_fields(m,kind):
    fields=[]
    def add(key,raw,decimals=None,unit='',*,display=None):
        fields.append(Field(key,raw,display if display is not None else value(raw,unit,decimals)))
    if kind=='acquisition':
        for key,source,scale,digits in [('frequency','x_frequency_Hz',1e-6,4),('sweep','x_sweep_Hz',1,1),('offset','offset_ppm',1,4)]:
            raw=m.metadata.get(source)
            add(key,raw*scale if raw is not None else None,digits)
        params=m.metadata.get('parameters',{})
        for key,source,scale,digits in [('acq_time','x_acq_duration',1,3),('delay','relaxation_delay',1,1),('pulse','x_90_width',1e6,2)]:
            try:raw=parameter_number(params,source,28)*scale
            except (KeyError,ValueError,TypeError):raw=None
            add(key,raw,digits)
        for key,source in [('scans','scans'),('points','x_points'),('sequence','experiment')]:
            raw=params.get(source,{}).get('value')
            add(key,raw,display=scalar(raw))
    else:
        for key,source,digits in [('lb','lb_Hz',2),('gaussian','gaussian_FWHM_Hz',2),('zf','zero_fill_factor',0),
                ('phase0','phase0_deg',3),('phase1','phase1_deg',3),('pivot','pivot_ppm',5),('shift','ppm_shift',6)]:
            add(key,m.options.get(source),digits)
        state=m.options.get('baseline_enabled');degree=m.options.get('baseline_degree')
        add('baseline',(state,degree),display=missing() if state is None else label('legendre',degree=number(degree,0)) if state else label('off'))
        regions=m.options.get('baseline_regions')
        display='; '.join(interval(pair,2) for pair in regions) if regions else missing()
        add('regions',regions,display=display)
    return fields

def compare_fields(records,kind):
    if not records:return [],[]
    columns=[measurement_fields(r['measurement'],kind) for r in records]
    common=[];different=[]
    for index,first in enumerate(columns[0]):
        row=[column[index] for column in columns]
        if all(item.original==first.original for item in row[1:]):common.append((label(first.key),first.display))
        else:different.append([label(first.key)]+[item.display for item in row])
    return common,different

def shift(roi):
    match=re.search(r'([-+]?\d+(?:[.,]\d+)?)\s*ppm',roi.signal)
    if match:return float(match.group(1).replace(',','.'))
    return (roi.low+roi.high)/2 if roi.low!=roi.high else None

def useful_comment(roi):
    # Repeated clipboard instructions are provenance, not an analytical observation.
    comment=text(roi.comments)
    if comment.startswith(('Pasted definitions.','Wklejone definicje.')):comment=''
    quality=message(roi.quality) if roi.quality not in ('','Not reviewed','Reviewed — suitable','Reference values only','Simulator assignment') else ''
    return '; '.join(x for x in (roi.exclusion_reason if not roi.accepted else '',comment,quality) if x)

def sample_code(sample):
    name=sample if isinstance(sample,str) else sample.name
    suffix=re.search(r'(?:_|\s)(P\d+)$',name,re.I)
    return suffix.group(1) if suffix else name

class ReportData:
    def __init__(self,project):
        self.project=project;self.summary=project_summary(project);self.groups=substance_summaries(project)
        self.records=[]
        for sample in project.samples:
            for measurement in sample.measurements:
                self.records.append(dict(sample=sample,measurement=measurement,
                    code=f'M{len(self.records)+1:02d}',current=is_current(project,sample,measurement)))
        names=[row['name'] for row in self.groups]
        self.analyte_names='; '.join(names) or '; '.join(c.name for c in project.compounds if c.name) or label('unassigned')
        self.project_name=project.name.strip() if project.name and project.name not in ('Untitled qNMR project','Nowy projekt qNMR') else self.analyte_names
    def compound_name(self,key):
        for c in self.project.compounds+[s.compound for s in self.project.standards]:
            if c.id==key:return c.name
        return label('unassigned')
    def eligible(self,record):
        return record['current'] and record['sample'].include and record['measurement'].include
    def sample_result(self,sample):
        return next((r for r in self.summary['samples'] if r['id']==sample.id),None)
    def selection_matrix(self,accepted=True):
        grouped={}
        for rec in self.records:
            m=rec['measurement']
            for roi in m.rois:
                included=roi.accepted and roi.role!='unassigned'
                if included!=accepted:continue
                status=label('accepted' if included else 'unassigned' if roi.role=='unassigned' else 'excluded')
                if included and m.input_kind!='raw JDF':status=label('reference_only')
                if not rec['sample'].include or not m.include:status+=' / '+label('excluded')
                # This is a presentation matrix; grouping at its stated precision
                # does not rewrite the full stored bounds in the project/JSON.
                delta=shift(roi)
                key=(round(delta,3) if delta is not None else None,roi.compound_id,roi.protons,round(roi.low,4),round(roi.high,4),roi.role,status,useful_comment(roi),bool(m.arrays))
                if key not in grouped:grouped[key]={}
                grouped[key][rec['code']]=m.roi_label(roi)
        rows=[];notes=[]
        for key,codes in grouped.items():
            delta,compound,protons,lo,hi,role,status,comment,has_arrays=key
            rows.append([number(delta,3),self.compound_name(compound),number(protons,significant=6),interval([lo,hi],4) if has_arrays else missing()]+[codes.get(rec['code'],'—') for rec in self.records]+[status])
            if comment:notes.append('; '.join(code+': '+sid for code,sid in codes.items())+' — '+comment)
        return rows,list(dict.fromkeys(notes))
    def mass(self,sample,standard=False):
        raw=sample.standard_mass if standard else sample.analyte_mass
        scale=MASS_TO_MG.get(sample.mass_unit)
        return number(raw*scale,3) if scale is not None else missing()
    def warnings(self):
        rows=[]
        def visit(value,prefix):
            if isinstance(value,dict):
                for key,item in value.items():
                    if key=='warnings' and item:
                        for warning in ([item] if isinstance(item,(str,dict)) else item):
                            for key,rendered in structured_rows(warning):rows.append((prefix,(key+': ' if key else '')+rendered))
                    elif isinstance(item,(dict,list,tuple)):visit(item,prefix)
            elif isinstance(value,(list,tuple)):
                for item in value:visit(item,prefix)
        for rec in self.records:
            m=rec['measurement'];visit(m.diagnostics,rec['code'])
            for roi in m.rois:visit(roi.diagnostics,rec['code']+' / '+m.roi_label(roi))
            for sig in m.results.get('signals',[]):
                for pair in sig.get('pairs',[]):visit(pair,rec['code']+' / '+sig.get('signal',''))
        return list(dict.fromkeys(rows))
