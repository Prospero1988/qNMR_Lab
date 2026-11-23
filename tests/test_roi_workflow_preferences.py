from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import pytest
from PySide6 import QtWidgets as W
from openpyxl import load_workbook
from qnmr import i18n
from qnmr.dialogs import ROIDialog
from qnmr.gui import MainWindow
from qnmr.quantification import calculate_project
from qnmr.reports import export_xlsx
from qnmr.storage import save_project,load_project,reports_directory


def test_signal_exclusion_reason_is_optional_and_preserved_on_reopen(app,project,tmp_path):
    sample=project.samples[0];measurement=sample.measurements[0]
    for reason in ('','Known overlap'):
        dialog=ROIDialog(project,sample,measurement,measurement.rois[0])
        dialog.accepted.setChecked(False);dialog.reason.setText(reason);dialog.protons.setValue(2)
        with patch('qnmr.dialogs.error') as error:
            dialog.accept();assert not error.called
        assert dialog.result.protons_confirmed and dialog.result.protons==2
        assert not dialog.result.accepted and dialog.result.exclusion_reason==reason
        measurement.rois[0]=dialog.result
        path=tmp_path/'optional.qnmr';save_project(project,path);loaded,_=load_project(path)
        roi=loaded.samples[0].measurements[0].rois[0]
        assert not roi.accepted and roi.exclusion_reason==reason


@pytest.mark.parametrize('code,expected',[('pl','12,35'),('en','12.35')])
def test_integral_display_rounding_keeps_full_precision_calculation_inputs(app,project,code,expected):
    sample=project.samples[0];measurement=sample.measurements[0];roi=measurement.rois[0]
    roi.area=12.34567
    assert not calculate_project(project);before=deepcopy(measurement.results)
    with i18n.using_language(code):
        window=MainWindow(project);window.open_measurement(sample,measurement);workspace=window.current_workspace()
        assert workspace.integral_labels[roi.id].toPlainText()==expected
        assert workspace.table.item(0,4).text()==expected
        assert workspace.table.item(0,5).text()=='—'
        measurement.integration_reference_id=roi.id;measurement.integration_reference_value=1
        workspace.refresh_table()
        assert workspace.integral_labels[roi.id].toPlainText()==('1,00' if code=='pl' else '1.00')
        assert workspace.table.item(0,5).text()==('1,00' if code=='pl' else '1.00')
        assert roi.area==12.34567 and measurement.results==before
        window.dirty=False;window.close()


def test_export_defaults_to_reports_and_xlsx_rounds_display_only(app,project,tmp_path):
    assert not calculate_project(project);window=MainWindow(project);folder=tmp_path/'reports'
    with patch('qnmr.gui.reports_directory',return_value=folder),patch.object(W.QFileDialog,'getSaveFileName',return_value=('','')) as dialog:
        window.export_report();assert Path(dialog.call_args.args[2])==folder/(project.id+'.docx')
    assert reports_directory()==Path(__file__).resolve().parents[1]/'reports' and reports_directory().is_dir()
    path=tmp_path/'results.xlsx';export_xlsx(project,path);book=load_workbook(path)
    sheet=book['Signals and calculations'];headers=[c.value for c in sheet[1]]
    cell=sheet.cell(2,headers.index('Signed area')+1)
    assert cell.number_format=='0.00' and cell.value==pytest.approx(project.samples[0].measurements[0].rois[0].area,rel=1e-14)
    window.dirty=False;window.close()
