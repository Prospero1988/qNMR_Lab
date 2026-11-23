from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PySide6 import QtCore, QtWidgets as W, QtGui
from PySide6.QtTest import QTest
from qnmr.models import ROI
from qnmr.gui import MainWindow
from qnmr.dialogs import CompoundDialog,ROIDialog,StructureDialog,SampleDialog
from qnmr.phase_window import PhaseWindow
from qnmr.analysis import dataset_from_measurement
from qnmr.chemistry import parse_smiles
from qnmr.quantification import is_current

def finish_processing(app,window,timeout=5000):
    elapsed=0
    while window.busy and elapsed<timeout:
        app.processEvents();QTest.qWait(10);elapsed+=10
    assert not window.busy

def test_compound_editor_parses_and_commits(app):
    dialog=CompoundDialog();dialog.name.setText('Ethanol');dialog.smiles.setText('CCO');dialog.parse()
    assert dialog.formula.text()=='C2H6O';assert dialog.mw.value()>46
    dialog.accept();assert dialog.result.name=='Ethanol'

def test_structure_atom_selection_and_zoom(app):
    dialog=StructureDialog(parse_smiles('CCO'));dialog.show();app.processEvents()
    before=dialog.view.transform().m11();dialog.select(1)
    assert 1 in dialog.atoms
    dialog.view.scale(1.2,1.2);assert dialog.view.transform().m11()>before
    dialog.select(1);assert 1 not in dialog.atoms;dialog.close()

def test_roi_editor_saves_nuclei_without_separate_confirmation(app,project):
    sample=project.samples[0];m=sample.measurements[0]
    dialog=ROIDialog(project,sample,m,m.rois[0]);dialog.protons.setValue(2)
    assert not hasattr(dialog,'confirmed')
    dialog.group.setText('CH2');dialog.accept()
    assert dialog.result.protons==2 and dialog.result.protons_confirmed and dialog.result.group=='CH2'

def test_phase_pivot_cached_preview_and_cancel(app,project):
    m=project.samples[0].measurements[0];before=m.arrays['spectrum'].copy()
    d=dataset_from_measurement(m);dialog=PhaseWindow(d)
    dialog.controls['phase1_deg'].setValue(60);preview=dialog.preview.copy()
    dialog.controls['pivot_ppm'].setValue(4.8)
    np.testing.assert_allclose(dialog.preview,preview,atol=1e-8)
    dialog.reject();np.testing.assert_array_equal(m.arrays['spectrum'],before)

def test_workspace_integration_processing_results_and_reopen(app,project,tmp_path):
    window=MainWindow(project);sample=project.samples[0];m=sample.measurements[0]
    window.open_measurement(sample,m);window.show();app.processEvents();workspace=window.current_workspace()
    assert workspace.table.rowCount()==2
    window.calculate();assert is_current(project,sample,m)
    assert window.samples_table.rowCount()==1
    workspace.mode.setCurrentIndex(2);assert all(r.movable for r in workspace.regions.values())
    workspace.mode.setCurrentIndex(0);assert not any(r.movable for r in workspace.regions.values())
    workspace.controls['lb_Hz'].setValue(1);workspace.submit_processing(baseline=False);finish_processing(app,window)
    assert m.options['lb_Hz']==1 and not is_current(project,sample,m)
    window.calculate();window.path=tmp_path/'reopen.qnmr';assert window.save()
    from qnmr.storage import load_project
    restored,_=load_project(window.path);window.replace_project(restored,window.path)
    assert window.current_workspace().table.rowCount()==2
    assert window.samples_table.rowCount()==1
    window.dirty=False;window.close()

def test_roi_creation_dialog_and_drag_edit_share_integrals(app,project):
    window=MainWindow(project);sample=project.samples[0];m=sample.measurements[0];window.open_measurement(sample,m)
    workspace=window.current_workspace()
    def accepted(dialog):
        dialog.signal.setText('Additional resonance');dialog.accept();return 1
    with patch.object(ROIDialog,'exec',accepted):workspace.create_roi(4.68,4.72)
    assert len(m.rois)==3 and m.rois[-1].area is not None
    original=m.rois[-1].area;region=workspace.regions[m.rois[-1].id];region.setRegion((4.69,4.71))
    workspace.boundary_changed(m.rois[-1],region)
    assert m.rois[-1].area<original
    workspace.table.selectRow(2);workspace.delete_selected();assert len(m.rois)==2
    window.dirty=False;window.close()

def test_jdf_import_action_and_repeat_sample_handling(app,tmp_path):
    source=Path(__file__).resolve().parents[1]/'examples/synthetic_P01.jdf';window=MainWindow()
    def accepted(dialog):
        dialog.ma.setValue(10);dialog.mi.setValue(1);dialog.accept();return 1
    with patch.object(W.QFileDialog,'getOpenFileNames',return_value=([str(source)],'')),patch.object(SampleDialog,'exec',accepted):window.import_files()
    assert len(window.project.samples)==1 and window.spectra_tabs.count()==1
    with patch.object(W.QFileDialog,'getOpenFileNames',return_value=([str(source)],'')):window.import_files(repeat=True)
    assert len(window.project.samples)==1 and len(window.project.samples[0].measurements)==2
    window.dirty=False;window.close()

def test_synthetic_example_ui_three_independent_samples(app):
    window=MainWindow();window.open_reference_example();app.processEvents()
    assert len(window.project.samples)==3
    assert window.samples_table.rowCount()==3
    from qnmr.quantification import project_summary
    stats=project_summary(window.project)['between']
    assert stats['n']==3 and abs(stats['mean']-95)<.03
    assert window.substances_table.rowCount()==1
    window.dirty=False;window.close()

def test_pasted_roi_preserves_entered_count_and_legacy_flag(app,project):
    window=MainWindow(project);s=project.samples[0];m=s.measurements[0];window.open_measurement(s,m)
    workspace=window.current_workspace();workspace.paste_rois(text='New\t4.66\t4.74\tanalyte\t2')
    assert len(m.rois)==3 and not m.rois[-1].protons_confirmed
    assert m.rois[-1].area is not None
    window.dirty=False;window.close()
