"""Real Qt actions for live processing, baseline masks and DOSY-style tools."""
from copy import deepcopy
import threading
from unittest.mock import patch
import numpy as np
import pytest
from PySide6 import QtCore,QtGui,QtWidgets as W
from PySide6.QtTest import QTest
from qnmr.gui import MainWindow
from qnmr import i18n
from qnmr.processing import process_fids,signed_integrals,phase_radians
from qnmr.jeol import RawData
from qnmr.phase_window import PhaseWindow
from qnmr.quantification import calculate_project,is_current

def settle(app,window):
    for _ in range(500):
        app.processEvents()
        if not window.busy:return
        QTest.qWait(10)
    raise AssertionError('Live processing did not settle')

def opened(app,project):
    window=MainWindow(project);s=project.samples[0];m=s.measurements[0]
    window.open_measurement(s,m);window.show();window.activateWindow();app.processEvents()
    return window,window.current_workspace(),m

def close(app,window):
    settle(app,window);window.dirty=False;window.close();app.processEvents()

def point(workspace,ppm):
    lo,hi=workspace.view.viewRange()[1]
    return workspace.plot.mapFromScene(workspace.view.mapViewToScene(QtCore.QPointF(ppm,(lo+hi)/2)))

def drag(app,workspace,start_ppm,end_ppm):
    viewport=workspace.plot.viewport();start=point(workspace,start_ppm);end=point(workspace,end_ppm)
    QTest.mouseMove(viewport,start);app.processEvents();QTest.qWait(30)
    QTest.mousePress(viewport,QtCore.Qt.MouseButton.LeftButton,pos=start);app.processEvents()
    for fraction in (.25,.5,.75,1):
        pos=start+(end-start)*fraction
        event=QtGui.QMouseEvent(QtCore.QEvent.Type.MouseMove,QtCore.QPointF(pos),QtCore.QPointF(viewport.mapToGlobal(pos)),
            QtCore.Qt.MouseButton.NoButton,QtCore.Qt.MouseButton.LeftButton,QtCore.Qt.KeyboardModifier.NoModifier)
        W.QApplication.sendEvent(viewport,event);app.processEvents()
    QTest.mouseRelease(viewport,QtCore.Qt.MouseButton.LeftButton,pos=end);app.processEvents()

def key(app,workspace,key):
    workspace.plot.setFocus();app.processEvents();QTest.keyClick(workspace.plot,key);app.processEvents()

@pytest.mark.parametrize('name,value',[('lb_Hz',2.5),('gaussian_FWHM_Hz',3),('phase0_deg',35),('phase1_deg',90),('filter_delay_samples',.5)])
def test_processing_fields_update_display_without_apply(app,project,name,value):
    calculate_project(project);window,w,m=opened(app,project);before=m.arrays['spectrum'].copy()
    w.controls[name].setValue(value);assert window.busy and w.isEnabled()
    settle(app,window)
    assert m.options[name]==value and not np.array_equal(m.arrays['spectrum'],before)
    expected=process_fids(RawData(m.arrays['fid'],m.metadata),m.options)
    np.testing.assert_array_equal(m.arrays['spectrum'],expected.spectrum)
    curve=next(item for item in w.plot.listDataItems() if item.name()==i18n.tr('Corrected real spectrum'))
    np.testing.assert_array_equal(curve.yData,m.arrays['spectrum'][0].real)
    assert not is_current(project,project.samples[0],m)
    close(app,window)

def test_typing_zero_fill_and_latest_request_win(app,project,monkeypatch):
    window,w,m=opened(app,project);entered=threading.Event();release=threading.Event();calls=[]
    def slow(raw,options,bounds):
        calls.append(options['lb_Hz'])
        if len(calls)==1:entered.set();assert release.wait(5)
        return process_fids(raw,options,bounds)
    monkeypatch.setattr('qnmr.gui.process_fids',slow)
    w.controls['lb_Hz'].setValue(1)
    for _ in range(200):
        app.processEvents()
        if entered.is_set():break
        QTest.qWait(10)
    assert entered.is_set()
    w.controls['lb_Hz'].setValue(2);w.controls['lb_Hz'].setValue(3);w.zf.setCurrentText('4')
    release.set();settle(app,window)
    assert calls==[1,3] and m.options['lb_Hz']==3 and m.options['zero_fill_factor']==4
    assert m.arrays['spectrum'].shape[1]==4*m.arrays['fid'].shape[1] and window.busy==0
    assert len(m.process_history)==1
    field=w.controls['lb_Hz'];field.setFocus();field.selectAll();QTest.keyClicks(field,'2.5');settle(app,window)
    assert m.options['lb_Hz']==2.5
    close(app,window)

def test_invalid_live_edit_keeps_previous_dataset_and_recovers(app,project):
    window,w,m=opened(app,project);before=m.arrays['spectrum'].copy();old=deepcopy(m.options)
    w.controls['filter_delay_samples'].setValue(251);settle(app,window)
    # The control caps the value at 250, which is still a supported value.
    assert m.options['filter_delay_samples']==250
    before=m.arrays['spectrum'].copy();old=deepcopy(m.options)
    w.submit_processing(baseline=True);settle(app,window)
    assert m.options==old and 'could not be applied' in w.status.text()
    np.testing.assert_array_equal(m.arrays['spectrum'],before)
    w.submit_processing(baseline=False);settle(app,window);assert not window.busy
    close(app,window)

def test_interactive_baseline_drag_resize_remove_and_subtract(app,project):
    window,w,m=opened(app,project);w.baseline_button.click();app.processEvents()
    assert w.view.mode=='baseline' and w.processing_panel.isVisible() and w.baseline_help.isVisible()
    drag(app,w,3.6,3.85);settle(app,window)
    assert len(m.options['baseline_regions'])==1 and w.baseline_items[0].movable
    drag(app,w,5.1,5.35);settle(app,window)
    assert len(m.options['baseline_regions'])==2 and np.any(m.arrays['baseline'])
    first=m.options['baseline_regions'][0][0]
    drag(app,w,first,first+.08);settle(app,window)
    assert m.options['baseline_regions'][0][0]>first+.01
    w.degree.setCurrentText('2');settle(app,window);assert m.options['baseline_degree']==2
    w.apply_baseline_button.click();settle(app,window)
    assert m.options['baseline_enabled']
    np.testing.assert_allclose(m.arrays['spectrum'],m.arrays['phased']-m.arrays['baseline'])
    w.baseline_items[0].remove_requested.emit();settle(app,window)
    assert len(m.options['baseline_regions'])==1
    w.clear_baseline();settle(app,window)
    assert not m.options['baseline_regions'] and not m.options['baseline_enabled']
    close(app,window)

def test_dosy_shortcuts_modify_split_remove_and_keep_areas(app,project):
    window,w,m=opened(app,project)
    for k,mode in [(QtCore.Qt.Key.Key_P,'pan'),(QtCore.Qt.Key.Key_Z,'zoom'),(QtCore.Qt.Key.Key_I,'roi'),(QtCore.Qt.Key.Key_M,'modify')]:
        key(app,w,k);assert w.view.mode==mode
    old_low=m.rois[0].low;drag(app,w,old_low,old_low-.05)
    assert m.rois[0].low<old_low-.005
    original=m.rois[0];area=original.area;cut=(original.low+original.high)/2
    key(app,w,QtCore.Qt.Key.Key_D);assert w.view.mode=='split'
    drag(app,w,original.low,cut)
    assert len(m.rois)==3 and len({r.id for r in m.rois})==3
    assert not m.rois[0].protons_confirmed and not m.rois[1].protons_confirmed
    assert m.rois[0].area+m.rois[1].area==pytest.approx(area,rel=1e-12,abs=1e-12)
    w.table.selectRow(1);removed=m.rois[1].id;key(app,w,QtCore.Qt.Key.Key_R)
    assert len(m.rois)==2 and all(r.id!=removed for r in m.rois)
    w.view.setXRange(4.6,4.8,padding=0);key(app,w,QtCore.Qt.Key.Key_F)
    assert np.ptp(w.view.viewRange()[0])>1
    close(app,window)

@pytest.mark.parametrize('code',['pl','en'])
def test_phase_opened_via_main_button_has_main_window_language(app,project,monkeypatch,code):
    monkeypatch.setattr('qnmr.gui.set_language',lambda code,**kw:i18n.set_language(code))
    with i18n.using_language('pl'):
        window,w,m=opened(app,project)
        if code=='en':window.language_button.click();app.processEvents();w=window.current_workspace()
        observed=[]
        def inspect(dialog):
            assert dialog.language_code==code
            assert dialog.apply_button.text()==i18n.translate('Apply phase to this acquisition',code)
            assert dialog.zoom_button.text()==i18n.translate('Zoom range [Z]',code)
            # Subsequent callbacks must keep the owning window's language.
            with i18n.using_language('pl' if code=='en' else 'en'):
                dialog.controls['phase0_deg'].setValue(10)
                assert ('full SW' in dialog.phase_label.text())==(code=='en')
            observed.append(True);dialog.reject();return 0
        with patch.object(PhaseWindow,'exec',inspect):w.phase_button.click()
        assert observed
        close(app,window)

def test_interactive_reference_moves_axis_rois_masks_and_pivot_together(app,project):
    window,w,m=opened(app,project)
    o=w.processing_options();o.update(phase1_deg=80,baseline_regions=[[3.6,3.8],[5.1,5.3]],baseline_enabled=True)
    w.submit_processing(options=o);settle(app,window)
    arrays={k:v.copy() for k,v in m.arrays.items()};old=deepcopy(m.options)
    rois=deepcopy(m.rois);areas=[r.area for r in m.rois]
    assert 'ppm_shift' not in w.controls
    w.process_toggle.setChecked(True);w.toggle_processing();app.processEvents()
    w.reference_target.setValue(0);w.reference_button.click();app.processEvents()
    click=point(w,4.7);clicked=w.view.mapSceneToView(w.plot.mapToScene(click)).x()
    QTest.mouseClick(w.plot.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=click);app.processEvents()
    delta=m.options['ppm_shift']-old['ppm_shift']
    assert abs(clicked+delta)<1e-6 and w.view.mode=='zoom'
    np.testing.assert_allclose(m.arrays['ppm'],arrays['ppm']+delta)
    for key_ in ('fid','spectrum','phased','baseline'):np.testing.assert_array_equal(m.arrays[key_],arrays[key_])
    for before,after in zip(rois,m.rois):
        assert after.low==pytest.approx(before.low+delta) and after.high==pytest.approx(before.high+delta)
    np.testing.assert_allclose([r.area for r in m.rois],areas,rtol=1e-12,atol=1e-12)
    np.testing.assert_allclose(m.options['baseline_regions'],np.array(old['baseline_regions'])+delta)
    np.testing.assert_allclose(phase_radians(m.arrays['ppm'],m.metadata,m.options),phase_radians(arrays['ppm'],m.metadata,old),atol=1e-12)
    expected=process_fids(RawData(m.arrays['fid'],m.metadata),m.options,[(r.low,r.high) for r in m.rois])
    np.testing.assert_allclose(m.arrays['spectrum'],expected.spectrum,rtol=1e-10,atol=1e-10)
    close(app,window)

def test_ids_and_relative_calibration_survive_split_delete_and_reopen(app,project,tmp_path):
    from qnmr.storage import save_project,load_project
    window,w,m=opened(app,project)
    assert [m.roi_label(r) for r in m.rois]==['S1','S2']
    w.table.selectRow(1);w.integral_target.setValue(1);w.integral_calibration_button.click()
    ref_id=m.rois[1].id
    parent=m.rois[0];w.split_roi(parent.id,(parent.low+parent.high)/2)
    assert [m.roi_label(r) for r in m.rois]==['S3','S4','S2']
    w.table.selectRow(0);w.delete_selected()
    assert [m.roi_label(r) for r in m.rois]==['S4','S2']
    save_project(project,tmp_path/'relative.qnmr');restored,_=load_project(tmp_path/'relative.qnmr')
    saved=restored.samples[0].measurements[0]
    assert saved.integration_reference_id==ref_id and saved.integration_reference_value==1
    assert [saved.roi_label(r) for r in saved.rois]==['S4','S2'] and saved.next_roi_number==5
    close(app,window)

def test_relative_integrals_update_without_changing_raw_areas_or_assays(app,project,tmp_path):
    from qnmr.reports import signal_rows,export_csv
    calculate_project(project);window,w,m=opened(app,project)
    before=deepcopy(m.results);areas=[r.area for r in m.rois]
    w.table.selectRow(0);w.integral_target.setValue(1);w.integral_calibration_button.click()
    assert m.relative_integral(m.rois[0])==pytest.approx(1)
    assert m.relative_integral(m.rois[1])==pytest.approx(areas[1]/areas[0])
    assert [r.area for r in m.rois]==areas and m.results==before and is_current(project,project.samples[0],m)
    assert signal_rows(project)[0]['signal_id']=='S1' and signal_rows(project)[0]['relative_integral']==pytest.approx(1)
    export_csv(project,tmp_path/'relative.csv')
    assert 'relative_integral' in (tmp_path/'relative.csv').read_text(encoding='utf-8-sig')
    w.controls['lb_Hz'].setValue(4);settle(app,window)
    assert m.relative_integral(m.rois[0])==pytest.approx(1)
    assert m.relative_integral(m.rois[1])==pytest.approx(m.rois[1].area/m.rois[0].area)
    w.table.selectRow(0);w.delete_selected()
    assert m.relative_integral(m.rois[0]) is None and 'missing' in w.integral_calibration_label.text()
    w.reset_integral_button.click();assert not m.integration_reference_id
    close(app,window)

@pytest.mark.parametrize('code',['pl','en'])
def test_signal_ids_and_integral_values_match_plot_and_table(app,project,code):
    with i18n.using_language(code):
        window,w,m=opened(app,project)
        for index,r in enumerate(m.rois):
            label=m.roi_label(r)
            assert w.table.item(index,0).text()==label and w.signal_labels[r.id].toPlainText()==label
            assert w.integral_display(r)==w.integral_labels[r.id].toPlainText()
        first=m.rois[0];w.table.selectRow(0);w.integral_target.setValue(1.5);w.integral_calibration_button.click()
        assert ('1,5' if code=='pl' else '1.5') in w.integral_labels[first.id].toPlainText()
        w.view.setYRange(-20,50,padding=0);app.processEvents()
        assert w.signal_labels[first.id].pos().y()==pytest.approx(50-.04*70)
        close(app,window)

def test_reference_waits_for_latest_live_edit_and_typing_does_not_delete_roi(app,project):
    window,w,m=opened(app,project);w.controls['lb_Hz'].setValue(3)
    w.calibrate_reference(4.7,0);settle(app,window)
    assert m.options['lb_Hz']==3 and m.options['ppm_shift']==pytest.approx(-4.7)
    w.integral_target.setFocus();QTest.keyClick(w.integral_target,QtCore.Qt.Key.Key_R);app.processEvents()
    assert len(m.rois)==2
    close(app,window)

@pytest.mark.parametrize('code',['pl','en'])
def test_copy_roi_definitions_matches_paste_format(app,project,code):
    with i18n.using_language(code):
        window,w,m=opened(app,project);original=deepcopy(m.rois)
        w.copy_roi_button.click();text=W.QApplication.clipboard().text()
        assert all(len(line.split('\t'))==6 for line in text.splitlines())
        assert text.splitlines()[0].split('\t')[3]=='analyte'
        w.paste_rois(text=text)
        assert len(m.rois)==2*len(original)
        for source,target in zip(original,m.rois[len(original):]):
            assert (source.signal,source.low,source.high,source.role,source.protons,source.compound_id)==(target.signal,target.low,target.high,target.role,target.protons,target.compound_id)
            assert source.id!=target.id and not target.protons_confirmed
        w.table.selectRow(1);w.copy_rois(selected=True)
        assert len(W.QApplication.clipboard().text().splitlines())==1
        close(app,window)

def test_copy_processing_uses_first_acquisition_but_target_fid(app,project):
    from qnmr.models import uid
    from qnmr.analysis import store_dataset,template_rois
    window,w,first=opened(app,project);sample=project.samples[0]
    second=deepcopy(first);second.id=uid();second.name='Repeat acquisition';second.roi_labels={};second.next_roi_number=1
    own_fid=first.arrays['fid']*.8
    store_dataset(second,process_fids(RawData(own_fid,second.metadata),second.options))
    second.rois=template_rois(first,second);sample.measurements.append(second)
    original_bounds=[(r.low,r.high) for r in second.rois]
    o=w.processing_options();o.update(lb_Hz=2.5,phase0_deg=20,phase1_deg=80,zero_fill_factor=2,
        baseline_regions=[[3.6,3.8],[5.1,5.3]],baseline_enabled=True)
    w.submit_processing(options=o);settle(app,window);w.calibrate_reference(4.7,0)
    expected=deepcopy(first.options);source_spectrum=first.arrays['spectrum'].copy()
    window.open_measurement(sample,second);target=window.current_workspace();assert target.copy_processing_button.isEnabled()
    target.copy_processing_button.click();settle(app,window)
    assert second.options==expected and second.process_history[-1]['source_measurement_id']==first.id
    np.testing.assert_array_equal(second.arrays['fid'],own_fid)
    np.testing.assert_array_equal(first.arrays['spectrum'],source_spectrum)
    for old,roi in zip(original_bounds,second.rois):
        np.testing.assert_allclose([roi.low,roi.high],np.array(old)+expected['ppm_shift'])
    independent=process_fids(RawData(own_fid,second.metadata),expected,[(r.low,r.high) for r in second.rois])
    np.testing.assert_array_equal(second.arrays['spectrum'],independent.spectrum)
    assert target.controls['lb_Hz'].value()==2.5 and target.zf.currentText()=='2'
    close(app,window)
