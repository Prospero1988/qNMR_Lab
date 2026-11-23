from copy import deepcopy
from io import BytesIO
from pathlib import Path
import hashlib,json,re
from unittest.mock import patch
import numpy as np
import pytest
from docx import Document
from docx.oxml.ns import qn
from PIL import Image
from PySide6 import QtWidgets as W
from qnmr.i18n import using_language,tr
from qnmr.storage import project_dict,load_project
from qnmr.quantification import calculate_project,project_summary
from qnmr.models import Project
from qnmr.chemistry import parse_smiles
from qnmr.report_format import number,readable_date,structured_rows,text,signal_name
from qnmr.report_data import ReportData,measurement_fields,compare_fields
from qnmr.report_text import LABELS
from qnmr.report_figures import structure,spectrum
from qnmr.report_document import ScientificReport
from qnmr.reports import export_docx,export_bundle

ROOT=Path(__file__).resolve().parents[1]

def contents(doc):
    return '\n'.join([p.text for p in doc.paragraphs]+[cell.text for table in doc.tables for row in table.rows for cell in row.cells])

def digest_arrays(project):
    return {(s.id,m.id,key):hashlib.sha256(array.tobytes()).hexdigest() for s in project.samples for m in s.measurements for key,array in m.arrays.items()}

@pytest.mark.parametrize('code,decimal',[('pl',','),('en','.')])
def test_scientific_formatting_examples_and_missing_values(code,decimal):
    with using_language(code):
        assert number(600.1723046037599,4)=='600'+decimal+'1723'
        assert number(7.699999999999999e-6*1e6,2)=='7'+decimal+'70'
        assert number(.00010432097541190899,significant=5)=='1'+decimal+'0432 × 10⁻⁴'
        assert number(5.336381908992573e-15,significant=3)=='5'+decimal+'34 × 10⁻¹⁵'
        assert number(402714.62,significant=3)=='4'+decimal+'03 × 10⁵'
        assert number(30000,significant=3)=='3 × 10⁴'
        assert number(-.00001,2)=='0'+decimal+'00'
        assert signal_name('7.603 ppm')=='7'+decimal+'603 ppm'
        assert signal_name('Analyst signal 7.603')=='Analyst signal 7.603'
        assert number(None)==number(float('nan'))==number(float('inf'))
        rows=structured_rows({'nested':{'flag':False,'values':[]},'missing':None})
        assert all(isinstance(k,str) and isinstance(v,str) for k,v in rows)
        assert not any(v in ('None','False','True','nan','inf','[]','{}') for _,v in rows)
        with pytest.raises(TypeError):text({'not':'prose'})

def test_dates_and_report_translation_placeholders():
    from string import Formatter
    for key,(pl,en) in LABELS.items():
        fields=lambda v:sorted((name,spec,conv) for _,name,spec,conv in Formatter().parse(v) if name is not None)
        assert fields(pl)==fields(en),key
    with using_language('pl'):
        assert readable_date('2026-11-23T13:15:12.987+00:00',time=True)=='23.11.2026 14:15 CET'
        assert readable_date('2026-11-23')=='23.11.2026'
    with using_language('en'):assert readable_date('2026-11-23')=='23 Nov 2026'

@pytest.mark.parametrize('code',['pl','en'])
def test_acquisition_units_and_unrounded_parameter_differences(project,code):
    m=project.samples[0].measurements[0]
    def seconds(value):return dict(value=value,decimal_scaler=0,units=[dict(base_code=28,power=1,prefix_code=0)])
    m.metadata['parameters']={'x_90_width':seconds(7.7e-6),'x_acq_duration':seconds(3.99293664),'relaxation_delay':seconds(60),'scans':{'value':16}}
    other=deepcopy(m);other.options['phase0_deg']+=.00000001
    with using_language(code):
        fields={f.key:f for f in measurement_fields(m,'acquisition')}
        assert fields['pulse'].display==('7,70' if code=='pl' else '7.70')
        assert fields['acq_time'].display==('3,993' if code=='pl' else '3.993')
        common,different=compare_fields([{'measurement':m},{'measurement':other}],'processing')
        # Original values differing below display precision are still classified as different.
        assert any(row[1]==row[2] for row in different)
        assert m.options['phase0_deg']!=other.options['phase0_deg']

@pytest.mark.parametrize('profile',['standard','extended'])
@pytest.mark.parametrize('code',['pl','en'])
def test_docx_is_readable_localized_a4_and_report_generation_is_read_only(project,tmp_path,profile,code):
    m=project.samples[0].measurements[0]
    m.rois[0].diagnostics['nested_review']={'overlap':False,'empty':[],'unknown':None,'small':5.336381908992573e-15}
    m.rois[0].diagnostics['warnings']=['Important signal warning']
    assert not calculate_project(project)
    before=deepcopy(project_dict(project));arrays=digest_arrays(project);stats=deepcopy(project_summary(project))
    path=tmp_path/(code+'_'+profile+'.docx')
    with using_language(code):export_docx(project,path,profile=profile)
    assert project_dict(project)==before and digest_arrays(project)==arrays and project_summary(project)==stats
    doc=Document(path);body=contents(doc)
    assert ('Ilościowa analiza ¹H NMR' if code=='pl' else 'Quantitative ¹H NMR Analysis') in body
    assert 'Untitled qNMR project' not in body
    assert 'Important signal warning' in body
    assert not re.search(r'\{[\s\n]*[\"\x27]|\b(?:nan|inf|True|False)\b|\[\]',body)
    assert '600.1723046037599' not in body
    assert abs(doc.sections[0].page_width/36000-210)<.1
    assert abs(doc.sections[0].page_height/36000-297)<.1
    assert doc.element.body.xpath('.//m:oMath/m:f')
    assert 'PAGE' in doc.sections[0].footer._element.xml and 'NUMPAGES' in doc.sections[0].footer._element.xml
    assert project.compounds[0].name in doc.sections[0].header.paragraphs[0].text
    for table in doc.tables:
        assert table.rows[0]._tr.xpath('./w:trPr/w:tblHeader')
        assert all(row._tr.xpath('./w:trPr/w:cantSplit') for row in table.rows)
        assert sum(c.width for c in table.columns)<=doc.sections[0].page_width-doc.sections[0].left_margin-doc.sections[0].right_margin+36000
    for p in doc.paragraphs:
        if p._p.xpath('.//w:drawing'):
            assert p.paragraph_format.keep_with_next
            following=p._p.getnext()
            assert following is not None and following.xpath('./w:pPr/w:pStyle[@w:val="ReportCaption"]')
    if profile=='extended':
        assert 'nested review' in body.lower()
        assert ('5,34 × 10⁻¹⁵' if code=='pl' else '5.34 × 10⁻¹⁵') in body

def test_reference_links_and_chemical_drawing_preserve_salts_and_stereochemistry(project,tmp_path):
    compound=parse_smiles('C[C@H](O)C(=O)[O-].[Na+]','Synthetic salt')
    before=deepcopy(compound);image=structure(compound)
    assert compound==before and '.[' in compound.smiles
    with Image.open(BytesIO(image)) as rendered:assert rendered.width>100 and rendered.height>100
    project.compounds.append(compound);project.samples[0].analyte_id=compound.id
    project.standards[0].certificate='https://example.org/certificate?id=123'
    path=tmp_path/'linked.docx';export_docx(project,path);doc=Document(path)
    assert any(rel.target_ref=='https://example.org/certificate?id=123' for rel in doc.part.rels.values() if rel.is_external)
    assert len(doc.inline_shapes)>=2

def test_excluded_and_historical_signals_are_not_reinterpreted(project,tmp_path):
    assert not calculate_project(project)
    sample=project.samples[0];m=sample.measurements[0];m.rois[0].accepted=False;m.rois[0].exclusion_reason=''
    before=deepcopy(project_dict(project));path=tmp_path/'stale.docx';export_docx(project,path)
    body=contents(Document(path))
    assert 'Historical' in body and 'Excluded and unassigned signals' in body
    assert project_summary(project)['between']['n']==0 and project_dict(project)==before

@pytest.mark.parametrize('profile',['standard','extended'])
def test_empty_and_missing_sections_have_human_readable_placeholders(tmp_path,profile):
    project=Project();project.compounds=[];project.standards=[]
    path=tmp_path/(profile+'.docx');export_docx(project,path,profile=profile)
    body=contents(Document(path))
    assert 'No current calculated results' in body and 'Untitled' not in body
    assert not re.search(r'\b(?:None|nan|inf|True|False)\b',body)

def test_signal_matrix_keeps_per_acquisition_ids_and_discloses_display_precision(project):
    sample=project.samples[0];m=sample.measurements[0];other=deepcopy(m);other.id='repeat'
    other.roi_labels={roi.id:'S'+str(i+20) for i,roi in enumerate(other.rois)}
    other.rois[0].low+=.000001;sample.measurements.append(other)
    rows,notes=ReportData(project).selection_matrix()
    target=next(row for row in rows if row[1]==project.compounds[0].name)
    assert target[4]=='S1' and target[5]=='S20' and m.rois[0].low!=other.rois[0].low

def test_bundle_profile_is_recorded_and_keeps_machine_precision(project,tmp_path):
    assert not calculate_project(project);before=deepcopy(project_dict(project))
    export_bundle(project,tmp_path,profile='extended')
    trace=json.loads((tmp_path/'traceability.json').read_text(encoding='utf-8'))
    assert trace['report_profile']=='extended' and trace['report_format_version']=='2'
    assert trace['project']==before

def test_extended_profile_is_available_in_export_dialog(app,project,tmp_path):
    from qnmr.gui import MainWindow
    assert not calculate_project(project);window=MainWindow(project)
    with patch.object(W.QFileDialog,'getSaveFileName',return_value=(str(tmp_path/'report.docx'),tr('Extended technical Word report (*.docx)'))),patch('qnmr.gui.export_docx') as export:
        window.export_report();assert export.call_args.kwargs=={'profile':'extended'}
    window.dirty=False;window.close()

def test_invalid_profile_is_rejected_before_writing(project,tmp_path):
    with pytest.raises(ValueError):export_docx(project,tmp_path/'no.docx',profile='unknown')
    assert not (tmp_path/'no.docx').exists()

def test_a_single_analyte_signal_is_not_described_as_a_discrepancy(project,tmp_path):
    calculate_project(project);path=tmp_path/'single.docx';export_docx(project,path)
    body=contents(Document(path))
    assert 'Lowest result:' not in body and 'cause of the difference' not in body

def test_nonindependent_observations_are_identified_and_not_counted_as_new_n(project,tmp_path):
    second=deepcopy(project.samples[0]);second.id='correlated';second.name='Correlated repeat';second.independent=False
    second.measurements[0].id='correlated-acquisition';project.samples.append(second)
    assert not calculate_project(project)
    path=tmp_path/'correlated.docx';export_docx(project,path);doc=Document(path)
    table=next(t for t in doc.tables if [c.text for c in t.rows[0].cells]==['Preparation','Assay (% w/w)','Acquisition','Independent'])
    assert table.rows[2].cells[-1].text=='No' and project_summary(project)['between']['n']==1
