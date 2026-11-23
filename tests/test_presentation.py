"""Display preferences and formatted diagnostics must preserve scientific data."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
from PySide6 import QtCore,QtWidgets as W
from qnmr import i18n
from qnmr.gui import MainWindow
from qnmr.dialogs import ROIDiagnosticsDialog
from qnmr.spectrum_settings import SpectrumAppearance,SpectrumSettingsDialog
from qnmr.phase_window import PhaseWindow
from qnmr.storage import project_dict
from qnmr.quantification import calculate_project,is_current,project_summary
from qnmr.excel_reference import import_reference

ROOT=Path(__file__).resolve().parents[1]

def test_display_preview_cancel_save_phase_and_reopened_tab_preserve_results(app,project,tmp_path):
    calculate_project(project);window=MainWindow(project);s=project.samples[0];m=s.measurements[0]
    window.open_measurement(s,m);window.show();app.processEvents();workspace=window.current_workspace()
    workspace.view.setRange(xRange=(4.1,4.8),yRange=(-10,500),padding=0);app.processEvents()
    before=deepcopy(project_dict(project));arrays={k:v.copy() for k,v in m.arrays.items()};ranges=deepcopy(workspace.view.viewRange())
    previous=window.appearance
    def preview_cancel(dialog):
        dialog.color='#da3e7c';dialog.width.setValue(2.4);dialog.grid.setChecked(False);dialog.preview()
        assert workspace.spectrum_curve.opts['pen'].color().name()=='#da3e7c'
        assert workspace.spectrum_curve.opts['pen'].widthF()==2.4 and not workspace.plot.getAxis('bottom').grid
        dialog.reject();return W.QDialog.DialogCode.Rejected
    with patch.object(SpectrumSettingsDialog,'exec',preview_cancel):workspace.appearance_button.click()
    assert window.appearance==previous and workspace.spectrum_curve.opts['pen'].color().name()==previous.color
    np.testing.assert_allclose(workspace.view.viewRange(),ranges,rtol=0,atol=1e-9)
    expected=SpectrumAppearance('#ffb000',2.2,False)
    def preview_save(dialog):
        dialog.color=expected.color;dialog.width.setValue(expected.width);dialog.grid.setChecked(expected.grid)
        dialog.preview();dialog.accept();return W.QDialog.DialogCode.Accepted
    window.settings=QtCore.QSettings(str(tmp_path/'appearance.ini'),QtCore.QSettings.Format.IniFormat)
    with patch.object(SpectrumSettingsDialog,'exec',preview_save):workspace.appearance_button.click()
    assert SpectrumAppearance.load(window.settings)==expected
    np.testing.assert_allclose(workspace.view.viewRange(),ranges,rtol=0,atol=1e-9)
    observed=[]
    def phase(dialog):
        assert dialog.appearance==expected and not dialog.plot.getAxis('bottom').grid
        pen=dialog.plot.listDataItems()[0].opts['pen'];assert pen.color().name()==expected.color and pen.widthF()==expected.width
        observed.append(True);dialog.reject();return 0
    with patch.object(PhaseWindow,'exec',phase):workspace.phase_button.click()
    assert observed
    window.close_spectrum_tab(0);window.open_measurement(s,m);workspace=window.current_workspace();workspace.redraw()
    assert workspace.spectrum_curve.opts['pen'].color().name()==expected.color and not workspace.plot.getAxis('bottom').grid
    assert project_dict(project)==before and is_current(project,s,m) and not window.dirty
    for key,value in arrays.items():np.testing.assert_array_equal(m.arrays[key],value)
    window.close()

@pytest.mark.parametrize('code',['pl','en'])
def test_roi_diagnostics_format_values_flags_and_warnings_without_editing(app,project,code):
    with i18n.using_language(code):
        roi=project.samples[0].measurements[0].rois[0]
        roi.diagnostics.update(snr_estimate=28398.32617177032,baseline_mean=-1.99346315087934e-14,
            mixed_sign=False,overlapping_rois=['S2','S3'],boundary_sensitivity_percent=None,
            warnings=['Mixed-sign region: inspect phase and overlap'])
        before=deepcopy(roi.diagnostics);dialog=ROIDiagnosticsDialog(roi,'S1')
        assert not dialog.findChildren(W.QPlainTextEdit)
        assert dialog.metrics['mixed_sign'].text()==i18n.tr('No')
        assert dialog.metrics['overlapping_rois'].text()=='S2, S3'
        assert dialog.metrics['boundary_sensitivity_percent'].text()==i18n.tr('not available')
        number,ok=dialog.locale().toDouble(dialog.metrics['snr_estimate'].text());assert ok and number==pytest.approx(28398.32617177032,rel=2e-5)
        assert 'e-14' in dialog.metrics['baseline_mean'].text()
        assert i18n.message(before['warnings'][0]) in dialog.warnings_label.text()
        assert roi.diagnostics==before
        dialog.close()

@pytest.mark.parametrize('code',['pl','en'])
def test_statistics_show_preparation_values_and_components_in_current_language(app,code):
    with i18n.using_language(code):
        from qnmr.storage import load_project
        project,_=load_project(ROOT/'examples/synthetic_three_samples.qnmr')
        before=deepcopy(project_dict(project));expected=project_summary(project)
        window=MainWindow(project);window.pages.setCurrentIndex(2);window.show();app.processEvents();panel=window.statistics_panel
        assert panel.metrics['n'].text()=='3' and panel.preparations.rowCount()==3
        mean,ok=panel.locale().toDouble(panel.metrics['mean'].text());assert ok and mean==pytest.approx(expected['between']['mean'],rel=1e-6)
        sd,ok=panel.locale().toDouble(panel.metrics['sd'].text());assert ok and sd==pytest.approx(expected['between']['sd'],rel=5e-6)
        low,high=[panel.locale().toDouble(value.strip())[0] for value in panel.metrics['ci'].text().split('—')]
        np.testing.assert_allclose([low,high],expected['between']['ci'],rtol=1e-6)
        assert '95' in panel.ci_caption.text() and not panel.small_sample_note.isVisible()
        assert panel.preparations.item(0,3).text()==i18n.tr('Yes')
        assert panel.components.rowCount()==len(expected['components']) and panel.components.item(0,0).text()==project.compounds[0].name
        assert not panel.findChildren(W.QPlainTextEdit) and window.stats_plot.isVisible()
        assert project_dict(project)==before
        window.close()

def test_statistics_distinguish_no_results_single_preparation_and_stale_results(app,project):
    window=MainWindow(project);window.pages.setCurrentIndex(2);window.show();app.processEvents();panel=window.statistics_panel
    assert panel.metrics['n'].text()=='0' and not window.stats_plot.isVisible()
    assert 'No current calculated results' in panel.status.text() and 'missing or stale' in panel.omissions.text()
    calculate_project(project);window.refresh_results()
    assert panel.metrics['n'].text()=='1' and panel.metrics['sd'].text()==i18n.tr('not available')
    assert window.stats_plot.isVisible() and panel.small_sample_note.isVisible()
    measurement=project.samples[0].measurements[0];snapshot=deepcopy(measurement.results)
    measurement.options['lb_Hz']+=1;window.refresh_results()
    assert panel.metrics['n'].text()=='0' and not window.stats_plot.isVisible() and measurement.results==snapshot
    window.close()
