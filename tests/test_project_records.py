from copy import deepcopy
from pathlib import Path
import zipfile
from unittest.mock import patch
import numpy as np
import pytest
from PySide6 import QtCore,QtWidgets as W
from PySide6.QtTest import QTest
from qnmr.gui import MainWindow
from qnmr.models import uid
from qnmr.project_edit import delete_record,deletion_details
from qnmr.quantification import calculate_project,is_current,project_summary
from qnmr.dialogs import ROIDialog,SampleDialog
from qnmr.storage import save_project,load_project,project_dict

def close(window):window.dirty=False;window.close()

def test_cancel_and_delete_preparation_close_its_tabs_and_remove_embedded_payload(app,project,tmp_path):
    sample=project.samples[0];repeat=deepcopy(sample.measurements[0]);repeat.id=uid();sample.measurements.append(repeat)
    another=deepcopy(sample);another.id=uid();another.name='Another preparation'
    for m in another.measurements:m.id=uid()
    project.samples.append(another);calculate_project(project)
    source=tmp_path/'original.jdf';source.write_bytes(b'external acquisition, never deleted')
    sample.measurements[0].source_path=str(source)
    window=MainWindow(project)
    for s in project.samples:
        for m in s.measurements:window.open_measurement(s,m)
    window.select_tree_data(('sample',sample.id));before=deepcopy(project_dict(project))
    assert window.selected_data()==('sample',sample.id)
    assert window.delete_tree_button.isEnabled()
    with patch.object(W.QMessageBox,'question',return_value=W.QMessageBox.StandardButton.No):window.delete_tree_button.click()
    assert project_dict(project)==before and window.spectra_tabs.count()==4
    ids=[m.id for m in sample.measurements]
    with patch.object(W.QMessageBox,'question',return_value=W.QMessageBox.StandardButton.Yes):window.delete_tree_button.click()
    assert project.samples==[another] and window.spectra_tabs.count()==2 and window.dirty
    assert not any(key in window.workspaces for key in ids) and source.read_bytes()==b'external acquisition, never deleted'
    assert project_summary(project)['between']['n']==1
    archive=tmp_path/'remaining.qnmr';save_project(project,archive);restored,_=load_project(archive)
    assert len(restored.samples)==1
    with zipfile.ZipFile(archive) as bundle:assert not any(any(key in name for key in ids) for name in bundle.namelist())
    close(window)

def test_deleting_first_acquisition_updates_repeat_processing_source(app,project):
    sample=project.samples[0];first=sample.measurements[0];second=deepcopy(first);second.id=uid();sample.measurements.append(second)
    window=MainWindow(project);window.open_measurement(sample,first);window.open_measurement(sample,second)
    repeat=window.current_workspace();assert repeat.copy_processing_button.isEnabled()
    fid=second.arrays['fid'].copy();window.select_tree_data(('measurement',sample.id,first.id))
    with patch.object(W.QMessageBox,'question',return_value=W.QMessageBox.StandardButton.Yes):window.delete_tree_selected()
    assert sample.measurements==[second] and window.spectra_tabs.count()==1
    assert not repeat.copy_processing_button.isEnabled()
    np.testing.assert_array_equal(second.arrays['fid'],fid);close(window)

def test_standard_deletion_unassigns_only_its_preparations_even_for_same_chemical(project):
    first=project.standards[0];other=deepcopy(first);other.id=uid();project.standards.append(other)
    second=deepcopy(project.samples[0]);second.id=uid();second.standard_id=other.id;second.measurements[0].id=uid();project.samples.append(second)
    assert not calculate_project(project)
    original=project.samples[0];m=original.measurements[0];arrays={k:v.copy() for k,v in m.arrays.items()};areas=[r.area for r in m.rois]
    impact=deletion_details(project,('standard',first.id));assert impact['preparations']==1
    delete_record(project,('standard',first.id))
    assert original.standard_id=='' and second.standard_id==other.id
    assert m.rois[1].role=='unassigned' and not m.rois[1].protons_confirmed
    assert second.measurements[0].rois[1].role=='standard'
    assert is_current(project,second,second.measurements[0]) and not is_current(project,original,m)
    assert [r.area for r in m.rois]==areas
    for key,value in arrays.items():np.testing.assert_array_equal(m.arrays[key],value)
    errors=calculate_project(project);assert len(errors)==1 and 'Select an internal standard' in errors[0]

def test_compound_deletion_keeps_spectra_and_clears_invalid_assignments(project):
    sample=project.samples[0];m=sample.measurements[0];compound=project.compounds[0];calculate_project(project)
    historical=deepcopy(m.results);spectrum=m.arrays['spectrum'].copy()
    delete_record(project,('compound',compound.id))
    assert not project.compounds and sample.analyte_id==''
    assert m.rois[0].role=='unassigned' and m.rois[0].compound_id=='' and not m.rois[0].protons_confirmed
    np.testing.assert_array_equal(m.arrays['spectrum'],spectrum);assert m.results==historical
    assert 'Select an analyte compound' in calculate_project(project)[0]

def test_missing_standard_can_be_reviewed_in_roi_editor_without_exception(app,project):
    sample=project.samples[0];m=sample.measurements[0];delete_record(project,('standard',project.standards[0].id))
    dialog=ROIDialog(project,sample,m,m.rois[1]);dialog.role.setCurrentIndex(dialog.role.findData('standard'))
    assert not dialog.compound.currentData()
    with patch('qnmr.dialogs.error') as error:
        dialog.accept();assert error.called and dialog.result.role=='unassigned'
    dialog.close()

def test_delete_all_project_record_types_via_tree(app,project):
    window=MainWindow(project);sample=project.samples[0];window.open_measurement(sample,sample.measurements[0])
    keys=[('compound',project.compounds[0].id),('standard',project.standards[0].id),('sample',sample.id)]
    with patch.object(W.QMessageBox,'question',return_value=W.QMessageBox.StandardButton.Yes):
        for key in keys:window.select_tree_data(key);window.delete_tree_selected()
    assert not project.compounds and not project.standards and not project.samples and not window.workspaces
    close(window)

def test_delete_shortcut_and_busy_guard_are_scoped_to_tree(app,project):
    window=MainWindow(project);window.show();window.activateWindow();app.processEvents()
    sample=project.samples[0];window.open_measurement(sample,sample.measurements[0]);window.select_tree_data(('sample',sample.id))
    window.busy=1
    with patch('qnmr.gui.error') as error,patch.object(W.QMessageBox,'question') as confirm:
        window.delete_tree_selected();assert error.called and not confirm.called and project.samples
    window.busy=0;window.tree.setFocus();app.processEvents()
    with patch.object(W.QMessageBox,'question',return_value=W.QMessageBox.StandardButton.Yes):
        QTest.keyClick(window.tree,QtCore.Qt.Key.Key_Delete)
    assert not project.samples;close(window)

def test_new_preparation_uses_selected_substance_and_is_grouped_beneath_it(app,project):
    compound=deepcopy(project.compounds[0]);compound.id=uid();compound.name='Substance B';project.compounds.append(compound)
    window=MainWindow(project);window.select_tree_data(('compound',compound.id))
    def enter(dialog):
        assert dialog.analyte.currentData()==compound.id
        dialog.ma.setValue(10);dialog.mi.setValue(1);dialog.accept();return 1
    with patch.object(SampleDialog,'exec',enter):sample=window.add_sample()
    assert sample.analyte_id==compound.id and sample.independent
    item=window.tree.currentItem();assert tuple(item.data(0,QtCore.Qt.ItemDataRole.UserRole))==('sample',sample.id)
    assert tuple(item.parent().data(0,QtCore.Qt.ItemDataRole.UserRole))==('compound',compound.id)
    close(window)
