"""Desktop workspace: spectra remain primary; preparation and molecular data are explicit."""
from __future__ import annotations
from copy import copy, deepcopy
from pathlib import Path
import sys
import traceback
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets as W
import pyqtgraph as pg
from .i18n import tr, language, set_language, load_preference, configure_qt, message, enum_label, manual_path
from . import __version__
from .models import Project, Compound, Standard, Sample, Measurement, ROI, uid
from .analysis import (import_jdf, dataset_from_measurement, store_dataset, update_integrals,
    template_rois, alignment_proposal)
from .processing import process_fids, signed_integrals, validate_baseline_roi_overlap
from .jeol import RawData
from .quantification import calculate_project, project_summary, is_current, substance_summaries
from .project_edit import deletion_details, delete_record
from .storage import save_project, load_project, save_standard_library, load_standard_library, relink_measurement, projects_directory, reports_directory
from .chemistry import depiction
from .spectrum_view import SpectrumBox
from .phase_window import PhaseWindow
from .spectrum_settings import SpectrumAppearance, SpectrumSettingsDialog
from .statistics_view import StatisticsPanel
from .dialogs import (CompoundDialog, StandardDialog, SampleDialog, ROIDialog, StructureDialog,
    CopyTable, ROIDiagnosticsDialog, spin, error)
from .reports import export_bundle, export_csv, export_xlsx, export_docx, spectrum_png, export_spectrum_csv
from .excel_reference import import_reference

THEME='''
QWidget { background: #121b29; color: #dce5f2; font-family: Segoe UI; font-size: 10pt; }
QMainWindow, QDialog { background: #101722; }
QToolBar { spacing: 6px; padding: 7px; border-bottom: 1px solid #304057; }
QPushButton, QToolButton { background: #24364c; border: 1px solid #3c526d; border-radius: 4px; padding: 6px 11px; }
QPushButton:hover, QToolButton:hover { background: #304c69; }
QPushButton:checked, QToolButton:checked { background: #175568; border-color: #67e8f9; }
QPushButton:disabled { color: #708096; }
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QPlainTextEdit, QTextEdit { background: #0c1420; border: 1px solid #344862; border-radius: 3px; padding: 4px; selection-background-color: #155e75; }
QTreeWidget, QTableWidget, QListWidget { background: #111b2a; alternate-background-color: #162338; border: 1px solid #293d55; }
QHeaderView::section { background: #22354b; color: #dce5f2; padding: 6px; border: 0; border-right: 1px solid #344862; }
QTabBar::tab { background: #1c2c40; padding: 9px 16px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { background: #223c50; border-bottom: 2px solid #67e8f9; }
QGroupBox { border: 1px solid #344862; border-radius: 5px; margin-top: 13px; padding-top: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #8bd5e3; }
QMenu { background: #1c2c40; border: 1px solid #496078; }
QMenu::item:selected { background: #175568; }
QSplitter::handle { background: #27384e; }
QToolTip { color: #e2e8f0; background: #24364c; border: 1px solid #57728e; }
QScrollBar { background: #152235; }
QToolButton { padding: 4px; icon-size: 24px; }
QComboBox { padding-right: 30px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 26px; border-left: 1px solid #344862; }
QComboBox::down-arrow { image: url("@icons@/down.svg"); width: 14px; height: 14px; }
QAbstractSpinBox { min-height: 28px; padding: 3px 29px 3px 6px; }
QDoubleSpinBox::up-button, QSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 24px; height: 17px; background: #24364c; border-left: 1px solid #3c526d; border-bottom: 1px solid #3c526d; border-top-right-radius: 3px; }
QDoubleSpinBox::down-button, QSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 24px; height: 17px; background: #24364c; border-left: 1px solid #3c526d; border-bottom-right-radius: 3px; }
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover, QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #304c69; }
QDoubleSpinBox::up-arrow, QSpinBox::up-arrow { image: url("@icons@/up.svg"); width: 12px; height: 12px; }
QDoubleSpinBox::down-arrow, QSpinBox::down-arrow { image: url("@icons@/down.svg"); width: 12px; height: 12px; }
QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; border: 1px solid #708096; background: #0c1420; }
QCheckBox::indicator { border-radius: 3px; }
QRadioButton::indicator { border-radius: 8px; }
QCheckBox::indicator:checked { image: url("@icons@/check.svg"); background: #175568; border-color: #67e8f9; }
QRadioButton::indicator:checked { image: url("@icons@/radio.svg"); background: #175568; border-color: #67e8f9; }
QTabBar::close-button { image: url("@icons@/close.svg"); width: 14px; height: 14px; padding: 3px; border-radius: 3px; }
QTabBar::close-button:hover { background: #7b3345; }
QTabBar QToolButton { min-width: 22px; padding: 4px; }
QTabBar QToolButton::left-arrow { image: url("@icons@/left.svg"); width: 14px; height: 14px; }
QTabBar QToolButton::right-arrow { image: url("@icons@/right.svg"); width: 14px; height: 14px; }
QHeaderView::up-arrow { image: url("@icons@/up.svg"); width: 12px; height: 12px; }
QHeaderView::down-arrow { image: url("@icons@/down.svg"); width: 12px; height: 12px; }
QTreeView::branch:closed:has-children { image: url("@icons@/right.svg"); }
QTreeView::branch:open:has-children { image: url("@icons@/down.svg"); }
QScrollBar:vertical { width: 14px; margin: 14px 0; }
QScrollBar:horizontal { height: 14px; margin: 0 14px; }
QScrollBar::handle { background: #415a75; border-radius: 3px; }
QScrollBar::handle:vertical { min-height: 24px; }
QScrollBar::handle:horizontal { min-width: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { background: #24364c; subcontrol-origin: margin; }
QScrollBar::sub-line:vertical { height: 14px; subcontrol-position: top; }
QScrollBar::add-line:vertical { height: 14px; subcontrol-position: bottom; }
QScrollBar::sub-line:horizontal { width: 14px; subcontrol-position: left; }
QScrollBar::add-line:horizontal { width: 14px; subcontrol-position: right; }
QScrollBar::up-arrow { image: url("@icons@/up.svg"); width: 10px; height: 10px; }
QScrollBar::down-arrow { image: url("@icons@/down.svg"); width: 10px; height: 10px; }
QScrollBar::left-arrow { image: url("@icons@/left.svg"); width: 10px; height: 10px; }
QScrollBar::right-arrow { image: url("@icons@/right.svg"); width: 10px; height: 10px; }
QScrollBar::add-page, QScrollBar::sub-page { background: #152235; }
'''.replace('@icons@',(Path(__file__).resolve().parent/'icons').as_posix())

def button(text,callback,layout,tooltip=''):
    b=W.QPushButton(text);b.clicked.connect(callback)
    if tooltip:b.setToolTip(tooltip)
    layout.addWidget(b);return b

class WorkerSignals(QtCore.QObject):
    done=QtCore.Signal(object,object)

class ProcessWorker(QtCore.QRunnable):
    def __init__(self,raw,options,bounds):
        super().__init__();self.raw=raw;self.options=deepcopy(options);self.bounds=bounds;self.signals=WorkerSignals()
    def run(self):
        try:self.signals.done.emit(process_fids(self.raw,self.options,self.bounds),None)
        except Exception as exc:self.signals.done.emit(None,str(exc))

class BaselineRegion(pg.LinearRegionItem):
    remove_requested=QtCore.Signal()
    def mouseClickEvent(self,event):
        if self.movable and event.button()==QtCore.Qt.MouseButton.RightButton:
            event.accept();menu=W.QMenu()
            menu.addAction(tr('Remove this baseline region'),self.remove_requested.emit)
            menu.exec(event.screenPos().toPoint())
        else:super().mouseClickEvent(event)

class SpectrumWorkspace(W.QWidget):
    changed=QtCore.Signal()
    def __init__(self,main,sample,measurement):
        super().__init__();self.main=main;self.sample=sample;self.m=measurement;self.regions={};self.processing=False
        self.baseline_items=[];self._requested_options=deepcopy(measurement.options)
        self.signal_labels={};self.integral_labels={}
        self._request_id=0;self._pending_request=None;self._processing_busy=False;self._open_phase_when_ready=False;self._reference_request=None
        self._shift_rois_with_processing=False;self._processing_origin=''
        self.live_timer=QtCore.QTimer(self);self.live_timer.setSingleShot(True);self.live_timer.setInterval(75)
        self.live_timer.timeout.connect(self._start_processing)
        outer=W.QVBoxLayout(self);outer.setContentsMargins(5,5,5,5)
        header=W.QHBoxLayout();outer.addLayout(header)
        self.mode=W.QComboBox();self.mode.addItems([tr('Zoom')+' [Z]',tr('Add quantitative ROI')+' [I]',tr('Edit ROI boundaries')+' [M]',tr('Select baseline regions'),tr('Pan')+' [P]',tr('Split integral')+' [D]',tr('Set reference')])
        self.mode.currentIndexChanged.connect(self.set_mode);header.addWidget(self.mode)
        self.mode.setToolTip(tr('Z: zoom · P: pan · F: full spectrum · I: integrate · R: remove selected integral · M: move boundaries · D: split by dragging an edge inward.'))
        self.full_button=button(tr('Full spectrum')+' [F]',self.full_spectrum,header)
        self.phase_button=button(tr('Phase…'),self.phase,header)
        self.baseline_button=button(tr('Baseline…'),self.activate_baseline,header);self.baseline_button.setCheckable(True)
        self.process_toggle=button(tr('Processing controls'),self.toggle_processing,header);self.process_toggle.setCheckable(True)
        self.appearance_button=button(tr('Appearance…'),self.main.edit_spectrum_settings,header)
        button(tr('Add ROI…'),self.add_default_roi,header)
        button(tr('Export spectrum'),self.export_spectrum,header);header.addStretch()
        self.processing_panel=W.QGroupBox(tr('Live processing — changes update the spectrum automatically'));self.processing_panel.hide()
        grid=W.QGridLayout(self.processing_panel);outer.addWidget(self.processing_panel);self.controls={}
        fields=[('lb_Hz',tr('LB (Hz)'),0,1000),('gaussian_FWHM_Hz',tr('Gaussian FWHM (Hz)'),0,1000),
                ('phase0_deg',tr('PH0 (°)'),-36000,36000),('phase1_deg',tr('PH1 (°/SW)'),-1e6,1e6),
                ('pivot_ppm',tr('Pivot (ppm)'),-1000,1000),
                ('filter_delay_samples',tr('Filter delay (samples)'),0,250)]
        for i,(key,label,lo,hi) in enumerate(fields):
            box=spin(measurement.options.get(key,0),lo,hi)
            box.setKeyboardTracking(True)
            grid.addWidget(W.QLabel(label),i//4*2,(i%4)*2);grid.addWidget(box,i//4*2,(i%4)*2+1);self.controls[key]=box
        self.zf=W.QComboBox();self.zf.addItems(['1','2','4','8']);self.zf.setCurrentText(str(measurement.options.get('zero_fill_factor',1)))
        grid.addWidget(W.QLabel(tr('Zero fill factor')),2,6);grid.addWidget(self.zf,2,7)
        self.crop=W.QCheckBox(tr('Crop digital-filter band'));self.crop.setChecked(measurement.options.get('crop_filter',True));grid.addWidget(self.crop,4,0,1,2)
        self.degree=W.QComboBox();self.degree.addItems(['1','2','3','4','5']);self.degree.setCurrentText(str(measurement.options.get('baseline_degree',1)))
        grid.addWidget(W.QLabel(tr('Baseline polynomial degree')),4,2);grid.addWidget(self.degree,4,3)
        self.reference_target=spin(0,-1000,1000)
        grid.addWidget(W.QLabel(tr('Reference target (ppm)')),4,4);grid.addWidget(self.reference_target,4,5)
        self.reference_button=W.QPushButton(tr('Set reference on spectrum'));self.reference_button.setCheckable(True)
        self.reference_button.setToolTip(tr('Enter the desired ppm value, enable this tool and click the reference signal.'))
        self.reference_button.clicked.connect(lambda checked:self.mode.setCurrentIndex(6 if checked else 0));grid.addWidget(self.reference_button,4,6,1,2)
        self.base_label=W.QLabel();grid.addWidget(self.base_label,5,0,1,8)
        row=W.QHBoxLayout();grid.addLayout(row,6,0,1,8)
        self.apply_baseline_button=button(tr('Apply baseline subtraction'),lambda:self.submit_processing(baseline=True),row)
        button(tr('Remove baseline subtraction'),lambda:self.submit_processing(baseline=False),row)
        button(tr('Select baseline regions'),lambda:self.activate_baseline(True),row)
        button(tr('Enter baseline ranges…'),self.edit_baseline,row)
        button(tr('Clear baseline regions'),self.clear_baseline,row)
        self.copy_processing_button=W.QPushButton(tr('Copy processing from first acquisition'))
        self.copy_processing_button.clicked.connect(self.copy_first_processing);grid.addWidget(self.copy_processing_button,7,0,1,8)
        self.update_processing_source()
        self.baseline_help=W.QLabel(tr('BASELINE: drag over signal-free regions. Move blue regions or drag their edges; right-click a region to remove it. The yellow curve is the fitted baseline. Apply subtraction when ready.'))
        self.baseline_help.setWordWrap(True);self.baseline_help.hide();outer.addWidget(self.baseline_help)
        self.preview_note=W.QLabel(tr('Drag: ppm zoom. Wheel: display gain. Middle drag: pan. Quantification uses the corrected real spectrum and its zero baseline.'))
        self.preview_note.setWordWrap(True);outer.addWidget(self.preview_note)
        splitter=W.QSplitter(QtCore.Qt.Orientation.Vertical);outer.addWidget(splitter,1)
        self.view=SpectrumBox();self.plot=pg.PlotWidget(viewBox=self.view,background='#0a111c');self.view.bind_selection_feedback(self.plot)
        self.plot.invertX(True);self.plot.setLabel('bottom',tr('¹H chemical shift'),units='ppm');self.plot.setLabel('left',tr('Real intensity'),units=tr('a.u.'))
        self.main.appearance.apply_grid(self.plot);splitter.addWidget(self.plot);self.view.selected.connect(self.selected_region)
        self.view.split_requested.connect(self.split_roi);self.view.clicked.connect(self.spectrum_clicked)
        self.plot.viewport().installEventFilter(self)
        self.plot.setMinimumHeight(230)
        lower=W.QWidget();layout=W.QVBoxLayout(lower);splitter.addWidget(lower)
        row=W.QHBoxLayout();layout.addLayout(row)
        button(tr('Edit selected…'),self.edit_selected,row);button(tr('Delete selected')+' [R]',self.delete_selected,row)
        button(tr('ROI diagnostics…'),self.show_diagnostics,row)
        self.copy_roi_button=button(tr('Copy ROI definitions'),self.copy_rois,row)
        self.copy_roi_button.setToolTip(tr('Copy all ROI definitions in the exact format accepted by Paste ROI rows.'))
        button(tr('Paste ROI rows…'),self.paste_rois,row)
        row.addStretch();row=W.QHBoxLayout();layout.addLayout(row)
        self.compatible=W.QCheckBox(tr('I confirm that multiple IS signals are compatible for averaging'))
        self.compatible.setChecked(measurement.reference_compatibility_confirmed);self.compatible.toggled.connect(self.reference_confirmation)
        row.addWidget(self.compatible);row.addStretch()
        relative=W.QHBoxLayout();layout.addLayout(relative)
        relative.addWidget(W.QLabel(tr('Set selected integral to:')))
        self.integral_target=spin(measurement.integration_reference_value,.000001,1e12,6);relative.addWidget(self.integral_target)
        self.integral_calibration_button=button(tr('Calibrate relative integrals'),self.calibrate_integral,relative)
        self.reset_integral_button=button(tr('Reset relative calibration'),self.reset_integral_calibration,relative)
        self.integral_calibration_label=W.QLabel();self.integral_calibration_label.setWordWrap(True);relative.addWidget(self.integral_calibration_label,1)
        self.table=CopyTable(['ID',tr('Signal'),tr('Role'),tr('Range (ppm)'),tr('Signed area'),tr('Relative integral'),tr('Nuclei'),tr('Area / nucleus'),tr('Assay (%)'),tr('Use'),tr('QC')])
        self.table.setMinimumHeight(135)
        self.table.customContextMenuRequested.disconnect(self.table.menu);self.table.customContextMenuRequested.connect(self.roi_table_menu)
        layout.addWidget(self.table);self.table.cellDoubleClicked.connect(lambda row,col:self.edit_roi(row))
        self.table.itemSelectionChanged.connect(self.selection_changed)
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        splitter.setSizes([480,300])
        if measurement.arrays:self.redraw(reset=True)
        else:
            self.plot.hide();self.mode.setEnabled(False);self.process_toggle.setEnabled(False);self.baseline_button.setEnabled(False);self.phase_button.setEnabled(False)
            self.preview_note.setText(tr('REFERENCE WORKBOOK VALUES — integrals were normalized in the source workbook. No FID, original raw areas or integration boundaries were supplied for this record.'))
            self.refresh_table()
        self.base_label.setText(self.baseline_description())
        self.previous_pivot=self.m.options.get('pivot_ppm',0)
        self.controls['pivot_ppm'].valueChanged.connect(self.pivot_changed)
        for box in self.controls.values():box.valueChanged.connect(self.schedule_processing)
        self.zf.currentIndexChanged.connect(self.schedule_processing);self.degree.currentIndexChanged.connect(self.schedule_processing)
        self.crop.toggled.connect(self.schedule_processing)
        self.view.sigRangeChanged.connect(self.position_integral_labels)
        self.shortcuts=[]
        for key,callback in [('Z',lambda:self.mode.setCurrentIndex(0)),('P',lambda:self.mode.setCurrentIndex(4)),
            ('F',self.full_spectrum),('I',lambda:self.mode.setCurrentIndex(1)),('R',self.delete_selected),
            ('M',lambda:self.mode.setCurrentIndex(2)),('D',lambda:self.mode.setCurrentIndex(5))]:
            shortcut=QtGui.QShortcut(QtGui.QKeySequence(key),self)
            shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut);shortcut.setAutoRepeat(False)
            shortcut.activated.connect(lambda callback=callback:self.spectrum_shortcut(callback));self.shortcuts.append(shortcut)
    def spectrum_shortcut(self,callback):
        focus=W.QApplication.focusWidget()
        if isinstance(focus,(W.QLineEdit,W.QAbstractSpinBox,W.QPlainTextEdit,W.QTextEdit,W.QComboBox)):return
        if self.m.arrays:callback()
    def full_spectrum(self):
        self.view.hide_selection_preview();self.plot.autoRange()
    def eventFilter(self,watched,event):
        if watched is self.plot.viewport() and self.view.mode=='reference':
            if event.type()==QtCore.QEvent.Type.MouseMove:
                pos=self.plot.mapToScene(event.position().toPoint());inside=self.view.sceneBoundingRect().contains(pos)
                if inside:self.reference_guide.setValue(self.view.mapSceneToView(pos).x())
                self.reference_guide.setVisible(inside)
            elif event.type() in (QtCore.QEvent.Type.Leave,QtCore.QEvent.Type.Hide):self.reference_guide.hide()
        if watched is self.plot.viewport() and event.type()==QtCore.QEvent.Type.MouseButtonDblClick and event.button()==QtCore.Qt.MouseButton.LeftButton:
            self.full_spectrum();return True
        return super().eventFilter(watched,event)
    def pivot_changed(self,value):
        if self.m.arrays:
            width=self.m.metadata['x_sweep_Hz']/(self.m.metadata['x_frequency_Hz']/1e6)
            control=self.controls['phase0_deg']
            with QtCore.QSignalBlocker(control):control.setValue(control.value()+self.controls['phase1_deg'].value()*(value-self.previous_pivot)/width)
        self.previous_pivot=value
    def baseline_description(self):
        regions=self._requested_options.get('baseline_regions',[])
        return tr('Manual baseline regions: ')+('; '.join(tr('{p0:.5f} to {p1:.5f}', p0=min(a, b), p1=max(a, b)) for a,b in regions) or tr('none'))
    def toggle_processing(self):self.processing_panel.setVisible(self.process_toggle.isChecked())
    def activate_baseline(self,checked=True):
        self.mode.setCurrentIndex(3 if checked else 0)
        if checked:self.process_toggle.setChecked(True);self.toggle_processing()
    def set_mode(self,index):
        self.view.hide_selection_preview();self.view.mode=['zoom','roi','modify','baseline','pan','split','reference'][index]
        for item in self.regions.values():item.setMovable(index==2)
        for item in self.baseline_items:item.setMovable(index==3)
        with QtCore.QSignalBlocker(self.baseline_button):self.baseline_button.setChecked(index==3)
        with QtCore.QSignalBlocker(self.reference_button):self.reference_button.setChecked(index==6)
        self.baseline_help.setVisible(index==3)
        if index==3:self.process_toggle.setChecked(True);self.toggle_processing()
        if index==6:
            self.process_toggle.setChecked(True);self.toggle_processing()
        if self.m.arrays:self.redraw()
        if index==6:self.status.setText(tr('Click the reference signal to set it to {p0:.6f} ppm.',p0=self.reference_target.value()))
        self.plot.viewport().setCursor(QtCore.Qt.CursorShape.CrossCursor if index==6 else QtCore.Qt.CursorShape.ArrowCursor)
    def selected_region(self,a,b):
        if self.view.mode=='baseline':
            try:
                regions=self._requested_options.get('baseline_regions',[])+[list(sorted((a,b)))]
                validate_baseline_roi_overlap(regions,[(r.low,r.high) for r in self.m.rois])
                options=self.processing_options();options['baseline_regions']=regions
                self.submit_processing(options=options)
            except Exception as exc:error(self,exc)
        elif not self._processing_busy:self.create_roi(a,b)
    def add_default_roi(self):
        if not self.m.arrays:
            error(self,tr('Workbook reference records have no spectrum. Import a JDF for new integration.'));return
        a,b=self.view.viewRange()[0];width=(b-a)*.05;center=(a+b)/2
        self.create_roi(center-width,center+width)
    def create_roi(self,a,b):
        roi=ROI(low=min(a,b),high=max(a,b),compound_id=self.sample.analyte_id,signal=f'{(a+b)/2:.3f} ppm')
        dialog=ROIDialog(self.main.project,self.sample,self.m,roi,self)
        if dialog.exec():
            old=list(self.m.rois)
            try:
                self.m.rois.append(dialog.result);update_integrals(self.m)
                self.main.project.record('ROI created',measurement=self.m.id,roi=dialog.result.id)
                self.redraw();self.table.selectRow(len(self.m.rois)-1);self.changed.emit()
            except Exception as exc:self.m.rois=old;error(self,exc)
    def current_roi_index(self):
        row=self.table.currentRow()
        return row if 0<=row<len(self.m.rois) else None
    def edit_selected(self):
        index=self.current_roi_index()
        if index is not None:self.edit_roi(index)
    def edit_roi(self,index):
        if self.processing:return
        dialog=ROIDialog(self.main.project,self.sample,self.m,self.m.rois[index],self)
        if dialog.exec():
            old=self.m.rois[index]
            try:
                self.m.rois[index]=dialog.result;update_integrals(self.m)
                self.main.project.record('ROI edited',measurement=self.m.id,roi=old.id,
                    before=dict(low=old.low,high=old.high,protons=old.protons,accepted=old.accepted),
                    after=dict(low=dialog.result.low,high=dialog.result.high,protons=dialog.result.protons,accepted=dialog.result.accepted))
                self.redraw();self.changed.emit()
            except Exception as exc:self.m.rois[index]=old;error(self,exc)
    def delete_selected(self):
        index=self.current_roi_index()
        if index is None or self._processing_busy:return
        roi=self.m.rois.pop(index)
        # Keep references to a deleted IS in targets so quantification exposes the missing assignment.
        self.main.project.record('ROI deleted',measurement=self.m.id,roi=roi.id,signal=roi.signal)
        update_integrals(self.m);self.redraw();self.changed.emit()
        if self.m.rois:self.table.selectRow(min(index,len(self.m.rois)-1))
    def select_roi_at(self,ppm):
        matches=[(r.high-r.low,i) for i,r in enumerate(self.m.rois) if r.low<=ppm<=r.high]
        if matches:self.table.selectRow(min(matches)[1])
    def spectrum_clicked(self,ppm):
        if self.view.mode=='reference':self.calibrate_reference(ppm,self.reference_target.value())
        else:self.select_roi_at(ppm)
    def calibrate_reference(self,clicked_ppm,target_ppm):
        if self._processing_busy:
            self._reference_request=(clicked_ppm,target_ppm,self.m.options['ppm_shift']);self.live_timer.stop();self._start_processing();return
        if not self.m.arrays:return
        try:
            old=self.m.options;shift=round(old['ppm_shift']+target_ppm-clicked_ppm,6);delta=shift-old['ppm_shift']
            if not np.isfinite([clicked_ppm,target_ppm,shift]).all():raise ValueError(tr('Invalid reference position.'))
            options=deepcopy(old);options.update(ppm_shift=shift,pivot_ppm=old['pivot_ppm']+delta,
                baseline_regions=[[a+delta,b+delta] for a,b in old.get('baseline_regions',[])])
            if not self.controls['pivot_ppm'].minimum()<=options['pivot_ppm']<=self.controls['pivot_ppm'].maximum():
                raise ValueError(tr('Reference shift would move the pivot outside the supported range.'))
            staged=copy(self.m);staged.options=options;staged.arrays=dict(self.m.arrays);staged.rois=deepcopy(self.m.rois)
            ppm=self.m.arrays['ppm']+delta;ppm.setflags(write=False);staged.arrays['ppm']=ppm
            staged.diagnostics=deepcopy(self.m.diagnostics)
            fit=staged.diagnostics.get('baseline')
            if fit and 'fit_range_ppm' in fit:fit['fit_range_ppm']=[value+delta for value in fit['fit_range_ppm']]
            for roi in staged.rois:roi.low+=delta;roi.high+=delta
            update_integrals(staged)
            before=deepcopy(old);self.m.options=options;self.m.arrays=staged.arrays;self.m.rois=staged.rois;self.m.diagnostics=staged.diagnostics
            from .models import utc_now
            self.m.process_history.append(dict(time=utc_now(),action='Interactive reference',clicked_ppm=clicked_ppm,target_ppm=target_ppm,before=before,options=deepcopy(options)))
            self.main.project.record('Interactive reference',measurement=self.m.id,clicked_ppm=clicked_ppm,target_ppm=target_ppm,shift_ppm=delta)
            self._requested_options=deepcopy(options)
            with QtCore.QSignalBlocker(self.controls['pivot_ppm']):self.controls['pivot_ppm'].setValue(options['pivot_ppm'])
            self.previous_pivot=self.controls['pivot_ppm'].value()
            ranges=self.view.viewRange();self.mode.setCurrentIndex(0);self.redraw()
            self.view.setRange(xRange=[value+delta for value in ranges[0]],yRange=ranges[1],padding=0)
            self.changed.emit();self.status.setText(tr('Reference set to {p0:.6f} ppm; calibration shift {p1:+.6f} ppm.',p0=clicked_ppm+delta,p1=delta))
        except Exception as exc:error(self,exc)
    def split_roi(self,roi_id,cut):
        if self._processing_busy:return
        index=next((i for i,r in enumerate(self.m.rois) if r.id==roi_id),None)
        if index is None:return
        original=self.m.rois[index]
        if not original.low<cut<original.high:return
        previous=list(self.m.rois)
        try:
            bounds=[(original.low,cut),(cut,original.high)]
            for pair in bounds:signed_integrals(self.m.arrays['ppm'],self.m.arrays['spectrum'].real,pair)
            children=[]
            for part,(low,high) in enumerate(bounds,1):
                child=deepcopy(original);child.id=uid();child.low=low;child.high=high
                child.signal=f'{original.signal} ({part})';child.protons_confirmed=False
                child.atoms=[];child.group='';child.quality='Not reviewed';child.diagnostics={}
                child.comments=(original.comments+'\n' if original.comments else '')+'Split ROI: review assignment and confirm the contributing proton count for each part.'
                children.append(child)
            self.m.rois[index:index+1]=children;update_integrals(self.m)
            self.main.project.record('ROI split',measurement=self.m.id,parent_roi=original.id,cut_ppm=cut,children=[r.id for r in children])
            self.redraw();self.table.selectRow(index);self.changed.emit()
            self.status.setText(tr('Integral split. Review the assignments and confirm the proton count of both parts before calculating.'))
        except Exception as exc:self.m.rois=previous;error(self,exc)
    def selection_changed(self):
        selected=self.current_roi_index()
        for i,r in enumerate(self.m.rois):
            item=self.regions.get(r.id)
            if item:
                color=(52,211,153) if r.role=='standard' else (103,232,249)
                item.setBrush(pg.mkBrush(*color,75 if selected==i else 28))
    def boundary_changed(self,roi,item):
        if self.processing:return
        old=(roi.low,roi.high);a,b=sorted(item.getRegion())
        try:
            roi.low=a;roi.high=b;update_integrals(self.m)
            self.main.project.record('ROI boundary changed',roi=roi.id,before=old,after=(a,b))
            self.refresh_table();self.changed.emit()
        except Exception as exc:
            roi.low,roi.high=old;item.setRegion(old);error(self,exc)
    def redraw(self,reset=False):
        if not self.m.arrays:self.refresh_table();return
        self.m.assign_roi_labels()
        ranges=self.view.viewRange();self.plot.clear();self.regions={};self.baseline_items=[];self.signal_labels={};self.integral_labels={}
        x=self.m.arrays['ppm'];real=self.m.arrays['spectrum'][0].real
        self.spectrum_curve=self.plot.plot(x,real,pen=self.main.appearance.pen(),name=tr('Corrected real spectrum'))
        zero=pg.InfiniteLine(0,angle=0,pen=pg.mkPen('#8b9bb3',style=QtCore.Qt.PenStyle.DashLine));self.plot.addItem(zero)
        self.reference_guide=pg.InfiniteLine(angle=90,movable=False,pen=pg.mkPen('#fbbf24',style=QtCore.Qt.PenStyle.DashLine))
        self.reference_guide.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton);self.plot.addItem(self.reference_guide);self.reference_guide.hide()
        if self.m.options.get('baseline_regions') and (not self.m.options.get('baseline_enabled') or self.view.mode=='baseline'):
            self.plot.plot(x,self.m.arrays['baseline'][0],pen=pg.mkPen('#fbbf24',width=1.5),name=tr('Baseline PREVIEW'))
            if self.m.options.get('baseline_enabled'):
                self.plot.plot(x,self.m.arrays['phased'][0].real,pen=pg.mkPen('#94a3b8',style=QtCore.Qt.PenStyle.DashLine),name=tr('Before baseline subtraction'))
        self.draw_baseline_regions()
        for roi in self.m.rois:
            color='#34d399' if roi.role=='standard' else '#67e8f9'
            item=pg.LinearRegionItem((roi.low,roi.high),movable=self.mode.currentIndex()==2,
                brush=(52,211,153,28) if roi.role=='standard' else (103,232,249,28),pen='#34d399' if roi.role=='standard' else '#3e8291')
            buttons=QtCore.Qt.MouseButton.LeftButton if self.mode.currentIndex()==2 else QtCore.Qt.MouseButton.NoButton
            item.setAcceptedMouseButtons(buttons)
            for line in item.lines:line.setAcceptedMouseButtons(buttons)
            item.setZValue(10);self.plot.addItem(item);self.regions[roi.id]=item
            item.sigRegionChangeFinished.connect(lambda item=item,roi=roi:self.boundary_changed(roi,item))
            item.sigRegionChanged.connect(self.position_integral_labels)
            for labels,text in ((self.signal_labels,self.m.roi_label(roi)),(self.integral_labels,'')):
                label=pg.TextItem(text,anchor=(.5,1) if labels is self.integral_labels else (.5,0),color=color,fill=pg.mkBrush(16,24,39,220));label.setZValue(20)
                label.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton);label.textItem.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)
                self.plot.addItem(label,ignoreBounds=True);labels[roi.id]=label
        self.view.split_regions=self.regions
        if reset:self.plot.autoRange()
        else:self.view.setRange(xRange=ranges[0],yRange=ranges[1],padding=0)
        self.refresh_table();self.base_label.setText(self.baseline_description())
        self.update_integral_labels()
    def draw_baseline_regions(self):
        for item in self.baseline_items:self.plot.removeItem(item)
        self.baseline_items=[]
        for index,(a,b) in enumerate(self._requested_options.get('baseline_regions',[])):
            item=BaselineRegion((a,b),movable=self.view.mode=='baseline',brush=(96,165,250,45),pen='#60a5fa')
            item.setZValue(15);self.plot.addItem(item);self.baseline_items.append(item)
            item.sigRegionChangeFinished.connect(lambda item=item,index=index:self.baseline_region_changed(index,item))
            item.remove_requested.connect(lambda index=index:self.remove_baseline_region(index))
        self.base_label.setText(self.baseline_description())
    def baseline_region_changed(self,index,item):
        previous=deepcopy(self._requested_options.get('baseline_regions',[]))
        if index>=len(previous):return
        try:
            regions=deepcopy(previous);regions[index]=list(sorted(item.getRegion()))
            validate_baseline_roi_overlap(regions,[(r.low,r.high) for r in self.m.rois])
            o=self.processing_options();o['baseline_regions']=regions;self.submit_processing(options=o)
        except Exception as exc:
            with QtCore.QSignalBlocker(item):item.setRegion(previous[index])
            error(self,exc)
    def remove_baseline_region(self,index):
        o=self.processing_options();regions=o['baseline_regions']
        if not 0<=index<len(regions):return
        del regions[index]
        if not regions:o['baseline_enabled']=False
        self.submit_processing(options=o)
    def refresh_table(self):
        self.m.assign_roi_labels()
        selected=self.table.currentRow()
        rows=[]
        for r in self.m.rois:
            result=next((s for s in self.m.results.get('signals',[]) if s['roi_id']==r.id),None)
            fresh=is_current(self.main.project,self.sample,self.m)
            rows.append([self.m.roi_label(r),r.signal,tr(r.role),f'{r.low:.5f} – {r.high:.5f}' if self.m.arrays else tr('not supplied'),self.format_integral(r.area),self.format_integral(self.m.relative_integral(r)),r.protons,
                self.format_integral(r.area/r.protons) if r.area is not None and r.protons else None,
                (f'{result["assay_percent"]:.5f}'+(tr(' (stale)') if not fresh else '')) if result else None,
                tr('yes') if r.accepted else tr('excluded'), '; '.join(message(w) for w in r.diagnostics.get('warnings',[])) or message(r.quality)])
        self.table.fill(rows)
        if rows:self.table.selectRow(max(0,min(selected,len(rows)-1)))
        reference=next((r for r in self.m.rois if r.id==self.m.integration_reference_id),None)
        if not self.m.integration_reference_id:self.integral_calibration_label.setText(tr('No relative calibration — raw signed integrals are shown.'))
        elif reference is None or reference.area is None or reference.area<=0:self.integral_calibration_label.setText(tr('Relative reference is missing or nonpositive. Select a valid integral and recalibrate.'))
        else:self.integral_calibration_label.setText(tr('Relative integration: {p0} = {p1:g}.',p0=self.m.roi_label(reference),p1=self.m.integration_reference_value))
        self.status.setText((tr('Current calculated results') if is_current(self.main.project,self.sample,self.m) else tr('Calculation required — stored historical results are retained until explicit recalculation.'))+
            tr('   {p0} ROIs. Baseline subtraction: {p1}.', p0=len(self.m.rois), p1=tr('applied') if self.m.options.get('baseline_enabled') else tr('off')))
        self.update_integral_labels()
    def reference_confirmation(self,checked):
        self.m.reference_compatibility_confirmed=checked;self.changed.emit();self.refresh_table()
    def calibrate_integral(self):
        index=self.current_roi_index()
        if index is None:return
        if self._processing_busy:return
        roi=self.m.rois[index];target=self.integral_target.value()
        if roi.area is None or not np.isfinite(roi.area) or roi.area<=0:
            error(self,tr('Choose a positive integral for relative calibration; check phase and baseline.'));return
        self.m.integration_reference_id=roi.id;self.m.integration_reference_value=target
        self.main.project.record('Relative integral calibration',measurement=self.m.id,roi=roi.id,target=target)
        self.refresh_table();self.update_integral_labels();self.changed.emit()
    def reset_integral_calibration(self):
        self.m.integration_reference_id='';self.main.project.record('Relative integral calibration reset',measurement=self.m.id)
        self.refresh_table();self.update_integral_labels();self.changed.emit()
    def integral_display(self,roi):
        value=self.m.relative_integral(roi) if self.m.integration_reference_id else roi.area
        return self.format_integral(value)
    def format_integral(self,value):
        if value is None:return '—'
        text=f'{value:.2f}'
        return text.replace('.',',') if self.main.ui_language=='pl' else text
    def update_integral_labels(self):
        for roi in self.m.rois:
            if roi.id in self.integral_labels:
                self.integral_labels[roi.id].setText(self.integral_display(roi))
        self.position_integral_labels()
    def position_integral_labels(self,*args):
        if not self.m.arrays:return
        low,high=self.view.viewRange()[1];span=high-low
        for roi in self.m.rois:
            if roi.id not in self.signal_labels:continue
            region=self.regions.get(roi.id);a,b=region.getRegion() if region else (roi.low,roi.high);center=(a+b)/2
            self.signal_labels[roi.id].setPos(center,high-.04*span)
            x=self.m.arrays['ppm'];mask=(x>=a)&(x<=b);y=self.m.arrays['spectrum'][0].real[mask]
            floor=min(0,float(y.min())) if y.size else 0
            self.integral_labels[roi.id].setPos(center,max(low+.06*span,min(high-.06*span,floor-.025*span)))
    def show_diagnostics(self):
        index=self.current_roi_index()
        if index is None:return
        r=self.m.rois[index];ROIDiagnosticsDialog(r,self.m.roi_label(r),self).exec()
    def edit_baseline(self):
        initial='\n'.join(f'{min(a,b):.6f}, {max(a,b):.6f}' for a,b in self._requested_options.get('baseline_regions',[]))
        text,ok=W.QInputDialog.getMultiLineText(self,tr('Manual baseline regions'),tr('One low, high pair per line (ppm). Preview before subtraction.'),initial)
        if not ok:return
        try:
            regions=[]
            for line in text.splitlines():
                if not line.strip():continue
                a,b=map(float,line.split(','));regions.append(sorted((a,b)))
            validate_baseline_roi_overlap(regions,[(r.low,r.high) for r in self.m.rois])
            options=self.processing_options();options.update(baseline_regions=regions)
            if not regions:options['baseline_enabled']=False
            self.submit_processing(options=options)
        except Exception as exc:error(self,exc)
    def clear_baseline(self):
        options=self.processing_options();options.update(baseline_regions=[],baseline_enabled=False)
        self.submit_processing(options=options)
    def processing_options(self):
        o=deepcopy(self._requested_options)
        for key,box in self.controls.items():o[key]=box.value()
        o.update(zero_fill_factor=int(self.zf.currentText()),crop_filter=self.crop.isChecked(),baseline_degree=int(self.degree.currentText()))
        return o
    def schedule_processing(self,*args):
        self.submit_processing(debounce=True)
    def copy_first_processing(self):
        first=self.sample.measurements[0] if self.sample.measurements else None
        if first is None or first is self.m or not first.options or not self.m.arrays:return
        workspace=self.main.workspaces.get(first.id)
        if workspace and workspace._processing_busy:
            self.status.setText(tr('Wait for the first acquisition to finish processing, then copy its settings.'));return
        options=deepcopy(first.options)
        for key,box in self.controls.items():
            with QtCore.QSignalBlocker(box):box.setValue(options[key])
        for widget,value in ((self.zf,str(options['zero_fill_factor'])),(self.degree,str(options['baseline_degree']))):
            with QtCore.QSignalBlocker(widget):widget.setCurrentText(value)
        with QtCore.QSignalBlocker(self.crop):self.crop.setChecked(options['crop_filter'])
        self.previous_pivot=self.controls['pivot_ppm'].value()
        self._shift_rois_with_processing=True;self._processing_origin=first.id
        self.submit_processing(options=options)
    def update_processing_source(self):
        first=self.sample.measurements[0] if self.sample.measurements else None
        enabled=bool(first and first is not self.m and first.options and self.m.arrays)
        self.copy_processing_button.setEnabled(enabled);self.copy_processing_button.setVisible(enabled)
    def submit_processing(self,baseline=None,options=None,debounce=False):
        if not self.m.arrays:return
        o=deepcopy(options) if options is not None else self.processing_options()
        if baseline is not None:o['baseline_enabled']=baseline
        o['baseline_preview']=True
        self._requested_options=deepcopy(o);self._request_id+=1;self._pending_request=(self._request_id,o)
        if not self._processing_busy:self._processing_busy=True;self.main.busy+=1
        self.draw_baseline_regions()
        if debounce:self.live_timer.start()
        else:self.live_timer.stop();self._start_processing()
    def _start_processing(self):
        if self.processing or self._pending_request is None:return
        request_id,o=self._pending_request;self._pending_request=None;self._running_id=request_id
        self.processing=True
        self.status.setText(tr('Processing…'))
        self._running_shift=o['ppm_shift']-self.m.options['ppm_shift'] if self._shift_rois_with_processing else 0
        self.worker=ProcessWorker(RawData(self.m.arrays['fid'],self.m.metadata),o,[(r.low+self._running_shift,r.high+self._running_shift) for r in self.m.rois])
        self.worker.signals.done.connect(self.processing_done);QtCore.QThreadPool.globalInstance().start(self.worker)
    @QtCore.Slot(object,object)
    def processing_done(self,dataset,failure):
        self.processing=False
        # A newer edit wins even if an older FFT completes first.
        if self._running_id!=self._request_id:
            if not self.live_timer.isActive():self._start_processing()
            return
        from .models import utc_now
        applied=False
        try:
            if failure:raise ValueError(failure)
            staged=copy(self.m);staged.rois=deepcopy(self.m.rois)
            for r in staged.rois:r.low+=self._running_shift;r.high+=self._running_shift
            for r in staged.rois:signed_integrals(dataset.ppm,dataset.spectrum.real,(r.low,r.high))
            store_dataset(staged,dataset);update_integrals(staged)
            before=deepcopy(self.m.options);store_dataset(self.m,dataset);self.m.rois=staged.rois
            self.m.process_history.append(dict(time=utc_now(),before=before,options=deepcopy(self.m.options),source_measurement_id=self._processing_origin))
            for key,box in self.controls.items():
                with QtCore.QSignalBlocker(box):box.setValue(self.m.options[key])
            self.previous_pivot=self.m.options['pivot_ppm']
            self.main.project.record('Processing committed',measurement=self.m.id,options=self.m.options,source_measurement_id=self._processing_origin)
            self._shift_rois_with_processing=False;self._processing_origin=''
            self.redraw();self.changed.emit();applied=True
        except Exception as exc:
            self.refresh_table();self.status.setText(tr('Live processing could not be applied: ')+message(exc))
        finally:
            if self._processing_busy:self.main.busy-=1;self._processing_busy=False
            if self._reference_request:
                clicked,target,origin_shift=self._reference_request;self._reference_request=None
                if applied:self.calibrate_reference(clicked+self.m.options['ppm_shift']-origin_shift,target)
            if self._open_phase_when_ready:
                self._open_phase_when_ready=False
                if applied:QtCore.QTimer.singleShot(0,self.phase)
    def phase(self):
        if not self.m.arrays:return
        if self._processing_busy:
            self._open_phase_when_ready=True;self.live_timer.stop();self._start_processing();return
        dialog=PhaseWindow(dataset_from_measurement(self.m),self,appearance=self.main.appearance,language_code=self.main.ui_language)
        dialog.applied.connect(self.phase_applied);dialog.exec()
    def phase_applied(self,changes):
        o=self.processing_options();o.update(changes);self.submit_processing(options=o)
    def export_spectrum(self):
        path,kind=W.QFileDialog.getSaveFileName(self,tr('Export spectrum'),self.m.id+'.png',tr('PNG (*.png);;Spectrum values (*.csv)'))
        if path:
            try:
                if '*.csv' in kind:export_spectrum_csv(self.m,Path(path).with_suffix('.csv'))
                else:spectrum_png(self.m,Path(path).with_suffix('.png'))
            except Exception as exc:error(self,exc)
    def roi_table_menu(self,pos):
        menu=W.QMenu(self)
        menu.addAction(tr('Copy selected rows'),self.table.copy)
        menu.addAction(tr('Copy selected ROI definitions'),lambda:self.copy_rois(selected=True))
        menu.addAction(tr('Copy ROI definitions'),self.copy_rois)
        menu.addAction(tr('Paste ROI rows…'),self.paste_rois)
        menu.exec(self.table.viewport().mapToGlobal(pos))
    def copy_rois(self,checked=False,selected=False):
        if not self.m.arrays:
            error(self,tr('Workbook reference records have no spectral ROI boundaries to copy.'));return
        rois=self.m.rois
        if selected:
            indices=sorted({i.row() for i in self.table.selectedIndexes()});rois=[rois[i] for i in indices]
        lines=['\t'.join((r.signal,repr(r.low),repr(r.high),r.role,repr(r.protons),r.compound_id)) for r in rois]
        W.QApplication.clipboard().setText('\n'.join(lines))
        self.status.setText(tr('Copied {p0} ROI definitions. Open another spectrum and use Paste ROI rows.',p0=len(lines)))
    def paste_rois(self,checked=False,text=None):
        if not self.m.arrays:error(self,tr('Import a raw JDF to paste integration boundaries.'));return
        if text is None:
            text,ok=W.QInputDialog.getMultiLineText(self,tr('Paste ROI definitions'),
                tr('Tab-separated columns: signal, low ppm, high ppm, role, nuclei.\nRoles: analyte, standard, water, solvent, impurity, other, unassigned.\nOptional sixth column: compound ID. Proton counts remain unconfirmed until you review each ROI.'),
                W.QApplication.clipboard().text())
            if not ok:return
        previous=list(self.m.rois)
        try:
            added=[]
            for line in text.splitlines():
                if not line.strip():continue
                cells=line.split('\t')
                if len(cells) not in (5,6):raise ValueError(tr('Each row must contain five or six tab-separated columns.'))
                signal,a,b,role,nuclei=cells[:5];role=role.strip().lower()
                if role not in ('analyte','standard','water','solvent','impurity','other','unassigned'):raise ValueError(tr('Unknown ROI role: ')+role)
                compound_id=cells[5].strip() if len(cells)==6 else self.main.project.standard(self.sample.standard_id).compound.id if role=='standard' else self.sample.analyte_id
                if role=='standard':
                    if compound_id!=self.main.project.standard(self.sample.standard_id).compound.id:raise ValueError(tr('Standard compound ID does not match the selected reference material.'))
                elif role!='unassigned':self.main.project.compound(compound_id)
                low,high=sorted((float(a),float(b)));count=float(nuclei)
                if not np.isfinite(count) or count<=0:raise ValueError(tr('Proton counts must be positive.'))
                added.append(ROI(signal=signal,low=low,high=high,role=role,compound_id=compound_id,
                    protons=count,protons_confirmed=False,comments=tr('Pasted definitions. Review and confirm assignment before quantification.')))
            if not added:raise ValueError(tr('No ROI definitions were pasted.'))
            self.m.rois=previous+added;update_integrals(self.m)
            self.main.project.record('ROI definitions pasted',measurement=self.m.id,count=len(added))
            self.redraw();self.changed.emit()
        except Exception as exc:self.m.rois=previous;error(self,exc)

class MainWindow(W.QMainWindow):
    def __init__(self,project=None):
        super().__init__();self.project=project or Project();self.path=None;self.dirty=False;self.busy=0
        self.settings=QtCore.QSettings('qNMR Lab','Desktop');self.appearance=SpectrumAppearance.load(self.settings)
        self.workspaces={};configure_qt();self._build_ui()
    def _build_ui(self):
        self.ui_language=language()
        self.resize(1580,980);self.setMinimumSize(1050,700);self.setStyleSheet(THEME)
        toolbar=self.addToolBar(tr('Analysis'));toolbar.setMovable(False)
        for text,callback,shortcut in [(tr('New'),self.new_project,'Ctrl+N'),(tr('Open'),self.open_project,'Ctrl+O'),(tr('Save'),self.save,'Ctrl+S'),
            (tr('Add sample'),self.add_sample,''),(tr('Import JDF'),self.import_files,'Ctrl+I'),(tr('Repeat acquisition'),lambda:self.import_files(repeat=True),''),
            (tr('Calculate'),self.calculate,'F5'),(tr('Export report'),self.export_report,'')]:
            action=toolbar.addAction(text,callback)
            if shortcut:action.setShortcut(shortcut)
        spacer=W.QWidget();spacer.setSizePolicy(W.QSizePolicy.Policy.Expanding,W.QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        self.language_button=W.QToolButton()
        self.language_button.setObjectName('languageSwitch')
        self.language_button.setText('PL → ENG' if language()=='pl' else 'ENG → PL')
        self.language_button.setToolTip(tr('Switch interface language to English') if language()=='pl' else tr('Switch interface language to Polish'))
        self.language_button.clicked.connect(self.toggle_language);toolbar.addWidget(self.language_button)
        filemenu=self.menuBar().addMenu(tr('Project'))
        filemenu.addAction(tr('Project details…'),self.project_details);filemenu.addAction(tr('Save as…'),self.save_as)
        filemenu.addAction(tr('Import reference workbook…'),self.open_workbook)
        filemenu.addAction(tr('Open synthetic example'),self.open_reference_example)
        standardmenu=self.menuBar().addMenu(tr('Standards'))
        standardmenu.addAction(tr('Add reference material…'),self.add_standard);standardmenu.addAction(tr('Import standard library…'),self.import_library);standardmenu.addAction(tr('Export standard library…'),self.export_library)
        toolsmenu=self.menuBar().addMenu(tr('Spectra'))
        toolsmenu.addAction(tr('Spectrum appearance…'),self.edit_spectrum_settings)
        toolsmenu.addAction(tr('Copy ROI template to another acquisition…'),self.apply_template)
        toolsmenu.addAction(tr('Propose peak alignment for template…'),lambda:self.apply_template(align=True))
        self.sync_action=toolsmenu.addAction(tr('Synchronize ppm axes'));self.sync_action.setCheckable(True);self.sync_action.toggled.connect(self.sync_axes)
        toolsmenu.addAction(tr('Compare side by side…'),self.compare_spectra)
        toolsmenu.addAction(tr('Relink original source…'),self.relink_source)
        toolsmenu.addAction(tr('Exclude / include acquisition…'),self.measurement_inclusion)
        helpmenu=self.menuBar().addMenu(tr('Help'));helpmenu.addAction(tr('User manual'),self.open_manual)
        helpmenu.addAction(tr('About'),lambda:W.QMessageBox.information(self,'qNMR Lab',tr('qNMR Lab {p0}\nConventional quantitative proton NMR\nDOSY Lab processing attribution: THIRD_PARTY.md\nLocal desktop application. Source: github.com/Prospero1988/qNMR_Lab', p0=__version__)))
        root=W.QSplitter();self.root_splitter=root;self.setCentralWidget(root)
        left=W.QWidget();leftlayout=W.QVBoxLayout(left);root.addWidget(left)
        title=W.QLabel('qNMR LAB');title.setStyleSheet('font-size:21pt; font-weight:600; color:#8bd5e3; padding:8px;');leftlayout.addWidget(title)
        self.project_label=W.QLabel();self.project_label.setWordWrap(True);leftlayout.addWidget(self.project_label)
        self.tree=W.QTreeWidget();self.tree.setHeaderLabels([tr('Substance / preparation / acquisition')]);self.tree.setMinimumWidth(240)
        self.tree.itemDoubleClicked.connect(self.tree_double_clicked);self.tree.currentItemChanged.connect(lambda current,previous:self.tree_selected())
        self.tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu);self.tree.customContextMenuRequested.connect(self.tree_menu)
        leftlayout.addWidget(self.tree,1)
        row=W.QHBoxLayout();leftlayout.addLayout(row);button(tr('Compound +'),self.add_compound,row);button(tr('Edit selected'),self.edit_tree_selected,row)
        self.delete_tree_button=button(tr('Delete selected item'),self.delete_tree_selected,leftlayout)
        self.delete_tree_button.setEnabled(False)
        self.tree_delete_shortcut=QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Delete),self.tree)
        self.tree_delete_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.tree_delete_shortcut.activated.connect(self.delete_tree_selected)
        self.structure_thumbnail=W.QLabel(tr('Double-click a compound to inspect its structure'));self.structure_thumbnail.setWordWrap(True);self.structure_thumbnail.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter);self.structure_thumbnail.setMinimumHeight(160)
        self.structure_thumbnail.mouseDoubleClickEvent=lambda e:self.inspect_selected_structure();leftlayout.addWidget(self.structure_thumbnail)
        self.pages=W.QTabWidget();root.addWidget(self.pages);root.setSizes([285,1295])
        spectra=W.QWidget();spectralayout=W.QVBoxLayout(spectra);spectralayout.setContentsMargins(0,0,0,0)
        self.spectra_tabs=W.QTabWidget();self.spectra_tabs.setTabsClosable(True);self.spectra_tabs.tabCloseRequested.connect(self.close_spectrum_tab)
        self.spectra_tabs.currentChanged.connect(lambda _:self.update_status());spectralayout.addWidget(self.spectra_tabs)
        self.empty=W.QLabel(tr('Import a conventional JEOL 1H JDF to begin.\nCreate a compound and sample preparation, then assign quantitative signals.\n\nYou can also open the validated workbook example from the Project menu.'))
        self.empty.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter);self.empty.setStyleSheet('font-size:14pt;color:#8ea5bf;padding:40px;');spectralayout.addWidget(self.empty)
        self.pages.addTab(spectra,tr('Spectra'))
        results=W.QWidget();layout=W.QVBoxLayout(results)
        self.summary_label=W.QLabel();self.summary_label.setWordWrap(True);self.summary_label.setStyleSheet('font-size:13pt;padding:15px;color:#8bd5e3;');layout.addWidget(self.summary_label)
        layout.addWidget(W.QLabel(tr('Combined results by substance')))
        self.substances_table=CopyTable([tr('Substance'),tr('Independent preparations'),tr('Mean (% w/w)'),tr('SD (pp)'),'RSD (%)',tr('SEM (pp)'),tr('Confidence interval (% w/w)'),tr('Status')])
        self.substances_table.setMinimumHeight(110);self.substances_table.setMaximumHeight(190)
        self.substances_table.cellDoubleClicked.connect(self.open_substance_statistics_row);layout.addWidget(self.substances_table)
        layout.addWidget(W.QLabel(tr('Results of individual preparations')))
        self.samples_table=CopyTable([tr('Substance'),tr('Preparation'),tr('Mean assay (% w/w)'),tr('Acquisitions'),tr('Independent'),tr('Repeat-acquisition SD (pp)')])
        layout.addWidget(self.samples_table)
        self.results_table=CopyTable([tr('Preparation'),tr('Acquisition'),tr('Signal'),tr('Component'),tr('Reference'),tr('Molar ratio'),tr('Amount (mmol)'),tr('Mass (mg)'),tr('Assay (%)'),tr('Status')])
        layout.addWidget(self.results_table,2);self.pages.addTab(results,tr('Results'))
        stats=W.QWidget();layout=W.QVBoxLayout(stats)
        stats_split=W.QSplitter(QtCore.Qt.Orientation.Vertical);layout.addWidget(stats_split)
        self.stats_plot=pg.PlotWidget(background='#0a111c');self.stats_plot.setLabel('left',tr('Preparation mean assay'),units=tr('% w/w'))
        self.stats_plot.setMinimumHeight(200);stats_split.addWidget(self.stats_plot)
        self.statistics_panel=StatisticsPanel();stats_split.addWidget(self.statistics_panel);stats_split.setSizes([320,500])
        self.statistics_panel.substance_selected.connect(self.refresh_statistics_plot)
        self.pages.addTab(stats,tr('Statistics'))
        molecules=W.QWidget();layout=W.QVBoxLayout(molecules);row=W.QHBoxLayout();layout.addLayout(row)
        button(tr('Add compound'),self.add_compound,row);button(tr('Add standard'),self.add_standard,row)
        self.compound_table=CopyTable([tr('Type'),tr('Name'),'ID',tr('Formula'),tr('MW (g/mol)'),tr('Chemical form'),tr('Provenance')])
        self.compound_table.cellDoubleClicked.connect(lambda row,col:self.edit_molecule_row(row));layout.addWidget(self.compound_table)
        self.pages.addTab(molecules,tr('Structures and standards'))
        self.statusBar().showMessage(tr('Ready'));self.rebuild_tree();self.refresh_results()
    def toggle_language(self,checked=False):
        if self.busy:error(self,tr('Wait for processing before changing language.'));return
        geometry=self.saveGeometry();maximized=self.isMaximized();fullscreen=self.isFullScreen()
        page=self.pages.currentIndex();current=self.current_workspace()
        active=current.m.id if current else None;linked=self.sync_action.isChecked()
        tree_data=self.selected_data();root_sizes=self.root_splitter.sizes()
        statistics_analyte=self.statistics_panel.analyte_selector.currentData()
        opened=[]
        for index in range(self.spectra_tabs.count()):
            w=self.spectra_tabs.widget(index)
            opened.append(dict(sample=w.sample,measurement=w.m,ranges=w.view.viewRange(),mode=w.mode.currentIndex(),
                controls={key:box.value() for key,box in w.controls.items()},zf=w.zf.currentText(),degree=w.degree.currentText(),
                crop=w.crop.isChecked(),panel=w.process_toggle.isChecked(),roi=w.current_roi_index(),
                reference_target=w.reference_target.value(),integral_target=w.integral_target.value()))
        set_language('en' if language()=='pl' else 'pl',persist=True)
        # Rebuild presentation only. Keep the original domain objects, arrays,
        # calculated snapshots, dirty flag, path and every pending numeric edit.
        old=self.takeCentralWidget()
        if old:old.deleteLater()
        for action in self.menuBar().actions():
            menu=action.menu()
            if menu:menu.deleteLater()
        self.menuBar().clear()
        for bar in self.findChildren(W.QToolBar,options=QtCore.Qt.FindChildOption.FindDirectChildrenOnly):
            self.removeToolBar(bar);bar.deleteLater()
        self.workspaces={};self._build_ui()
        for state in opened:
            self.open_measurement(state['sample'],state['measurement']);w=self.workspaces[state['measurement'].id]
            for key,value in state['controls'].items():
                with QtCore.QSignalBlocker(w.controls[key]):w.controls[key].setValue(value)
            w.previous_pivot=state['controls']['pivot_ppm']
            w.zf.setCurrentText(state['zf']);w.degree.setCurrentText(state['degree']);w.crop.setChecked(state['crop'])
            w.mode.setCurrentIndex(state['mode']);w.process_toggle.setChecked(state['panel']);w.toggle_processing()
            w.reference_target.setValue(state['reference_target']);w.integral_target.setValue(state['integral_target'])
            if state['roi'] is not None:w.table.selectRow(state['roi'])
        if active in self.workspaces:self.spectra_tabs.setCurrentWidget(self.workspaces[active])
        self.pages.setCurrentIndex(page);self.sync_action.setChecked(linked)
        self.statistics_panel.select_substance(statistics_analyte)
        self.root_splitter.setSizes(root_sizes);self.restoreGeometry(geometry)
        if fullscreen:self.showFullScreen()
        elif maximized:self.showMaximized()
        if tree_data:
            iterator=W.QTreeWidgetItemIterator(self.tree)
            while iterator.value():
                item=iterator.value()
                if tuple(item.data(0,QtCore.Qt.ItemDataRole.UserRole) or ())==tree_data:
                    with QtCore.QSignalBlocker(self.tree):self.tree.setCurrentItem(item)
                    break
                iterator+=1
        self.show_thumbnail()
        self.delete_tree_button.setEnabled(bool(self.selected_data()))
        def restore_ranges():
            for state in opened:
                w=self.workspaces.get(state['measurement'].id)
                if w and w.m.arrays:w.view.setRange(xRange=state['ranges'][0],yRange=state['ranges'][1],padding=0)
        QtCore.QTimer.singleShot(0,restore_ranges)
        self.update_status()
    def mark_changed(self):
        self.dirty=True;self.update_status();self.refresh_results()
    def update_status(self):
        self.setWindowTitle(f'qNMR Lab {__version__} — {self.project.name}'+(' *' if self.dirty else ''))
        self.project_label.setText(self.project.name)
    def rebuild_tree(self):
        selected=self.selected_data()
        self.tree.clear()
        compounds=W.QTreeWidgetItem([tr('Substances')]);self.tree.addTopLevelItem(compounds);substance_nodes={}
        for c in self.project.compounds:
            item=W.QTreeWidgetItem([c.name]);item.setData(0,QtCore.Qt.ItemDataRole.UserRole,('compound',c.id));compounds.addChild(item);substance_nodes[c.id]=item
            assigned=[s for s in self.project.samples if s.analyte_id==c.id]
            item.setToolTip(0,tr('{p0} preparations; {p1} acquisitions. Statistics combine independent preparations of this substance.',p0=len(assigned),p1=sum(len(s.measurements) for s in assigned)))
        standards=W.QTreeWidgetItem([tr('Internal standards')]);self.tree.addTopLevelItem(standards)
        for s in self.project.standards:
            item=W.QTreeWidgetItem([s.compound.name]);item.setData(0,QtCore.Qt.ItemDataRole.UserRole,('standard',s.id));standards.addChild(item)
        unassigned=None
        for s in self.project.samples:
            parent=substance_nodes.get(s.analyte_id)
            if parent is None:
                if unassigned is None:
                    unassigned=W.QTreeWidgetItem([tr('Preparations without a substance assignment')]);self.tree.addTopLevelItem(unassigned)
                parent=unassigned
            suffix=tr(' [excluded]') if not s.include else tr(' [not independent]') if not s.independent else ''
            item=W.QTreeWidgetItem([s.name+suffix]);item.setData(0,QtCore.Qt.ItemDataRole.UserRole,('sample',s.id));parent.addChild(item)
            for m in s.measurements:
                child=W.QTreeWidgetItem([m.name+(tr(' [excluded]') if not m.include else '')]);child.setData(0,QtCore.Qt.ItemDataRole.UserRole,('measurement',s.id,m.id));item.addChild(child)
        self.tree.expandAll();self.update_status()
        self.compound_table.fill([[tr('Compound'),c.name,c.id,c.formula,c.molecular_weight,c.chemical_form,c.provenance] for c in self.project.compounds]+
            [[tr('Standard'),s.compound.name,s.id,s.compound.formula,s.compound.molecular_weight,s.compound.chemical_form,s.compound.provenance] for s in self.project.standards])
        if selected:self.select_tree_data(selected,notify=False)
        self.delete_tree_button.setEnabled(bool(self.selected_data()))
    def select_tree_data(self,data,*,notify=True):
        iterator=W.QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item=iterator.value()
            if tuple(item.data(0,QtCore.Qt.ItemDataRole.UserRole) or ())==tuple(data):
                if notify:self.tree.setCurrentItem(item)
                else:
                    with QtCore.QSignalBlocker(self.tree):self.tree.setCurrentItem(item)
                return
            iterator+=1
    def selected_data(self):
        item=self.tree.currentItem();data=item.data(0,QtCore.Qt.ItemDataRole.UserRole) if item else None
        return tuple(data) if data else None
    def selected_sample(self):
        data=self.selected_data()
        if data and data[0] in ('sample','measurement'):return next(s for s in self.project.samples if s.id==data[1])
        workspace=self.spectra_tabs.currentWidget()
        if isinstance(workspace,SpectrumWorkspace):return workspace.sample
        return None
    def current_workspace(self):
        widget=self.spectra_tabs.currentWidget();return widget if isinstance(widget,SpectrumWorkspace) else None
    def tree_selected(self):
        data=self.selected_data()
        self.delete_tree_button.setEnabled(bool(data))
        if not data:return
        if data[0]=='measurement':
            s=next(s for s in self.project.samples if s.id==data[1]);m=next(m for m in s.measurements if m.id==data[2]);self.open_measurement(s,m)
        self.show_thumbnail()
    def tree_double_clicked(self,item,column):
        data=item.data(0,QtCore.Qt.ItemDataRole.UserRole)
        if data and data[0] in ('compound','standard'):self.inspect_selected_structure()
        elif data and data[0]=='sample':self.edit_sample()
    def edit_tree_selected(self):
        data=self.selected_data()
        if not data:return
        if data[0]=='compound':self.edit_compound(self.project.compound(data[1]))
        elif data[0]=='standard':self.edit_standard(self.project.standard(data[1]))
        elif data[0] in ('sample','measurement'):self.edit_sample()
    def tree_menu(self,pos):
        item=self.tree.itemAt(pos)
        if item:self.tree.setCurrentItem(item)
        menu=W.QMenu(self);menu.addAction(tr('Edit selected…'),self.edit_tree_selected)
        menu.addAction(tr('Inspect structure…'),self.inspect_selected_structure)
        menu.addAction(tr('Add independent sample…'),self.add_sample)
        menu.addAction(tr('Import repeat acquisition…'),lambda:self.import_files(repeat=True))
        data=self.selected_data()
        if data and data[0] in ('compound','sample','measurement'):
            key=data[1] if data[0]=='compound' else self.selected_sample().analyte_id
            action=menu.addAction(tr('Substance statistics'),lambda:self.show_substance_statistics(key))
            action.setEnabled(any(s.analyte_id==key for s in self.project.samples))
        action=menu.addAction(tr('Delete selected item'),self.delete_tree_selected);action.setEnabled(bool(data))
        menu.exec(self.tree.viewport().mapToGlobal(pos))
    def delete_tree_selected(self,checked=False):
        if self.busy:error(self,tr('Wait for processing before deleting project records.'));return
        data=self.selected_data()
        if not data:return
        try:
            details=deletion_details(self.project,data);kind=details['kind']
            if kind=='sample':text=tr('Delete preparation "{p0}" and its {p1} acquisitions from this project?',p0=details['name'],p1=details['acquisitions'])
            elif kind=='measurement':text=tr('Delete acquisition "{p0}" from preparation "{p1}"? Its embedded data, ROIs and results will be removed from this project.',p0=details['name'],p1=details['sample_name'])
            elif kind=='compound':text=tr('Delete substance "{p0}"? It is assigned to {p1} preparations and {p2} signal ROIs. Those assignments will be cleared; spectra will remain. Recalculate after reviewing assignments.',p0=details['name'],p1=details['preparations'],p2=details['roi_count'])
            else:text=tr('Delete reference material "{p0}"? It is used by {p1} preparations. Their standard assignments will be cleared; spectra will remain.',p0=details['name'],p1=details['preparations'])
            if W.QMessageBox.question(self,tr('Delete from project'),text,W.QMessageBox.StandardButton.Yes|W.QMessageBox.StandardButton.No,W.QMessageBox.StandardButton.No)!=W.QMessageBox.StandardButton.Yes:return
            details=delete_record(self.project,data)
            for key in details['measurement_ids']:
                workspace=self.workspaces.get(key)
                if workspace:self.close_spectrum_tab(self.spectra_tabs.indexOf(workspace))
            for workspace in self.workspaces.values():workspace.update_processing_source();workspace.redraw()
            self.rebuild_tree();self.show_thumbnail();self.mark_changed()
        except (ValueError,StopIteration) as exc:error(self,exc)
    def selected_compound(self):
        data=self.selected_data()
        if data and data[0]=='compound':return self.project.compound(data[1])
        if data and data[0]=='standard':return self.project.standard(data[1]).compound
        sample=self.selected_sample()
        if sample and sample.analyte_id:
            return next((c for c in self.project.compounds if c.id==sample.analyte_id),None)
        return None
    def show_thumbnail(self):
        try:
            c=self.selected_compound()
            if c and (c.smiles or c.molblock):
                image=QtGui.QPixmap();image.loadFromData(depiction(c,width=500,height=270,png=True,indices=False)[0]);self.structure_thumbnail.setPixmap(image.scaled(260,150,QtCore.Qt.AspectRatioMode.KeepAspectRatio,QtCore.Qt.TransformationMode.SmoothTransformation))
            else:self.structure_thumbnail.clear();self.structure_thumbnail.setText(tr('No structure entered. Verified manual molecular weights are supported.'))
        except Exception:self.structure_thumbnail.setText(tr('Inspect molecular data to display a structure.'))
    def inspect_selected_structure(self):
        try:
            c=self.selected_compound()
            if c:StructureDialog(c,parent=self).exec()
        except Exception as exc:error(self,exc)
    def add_compound(self):self.edit_compound(None)
    def edit_compound(self,compound):
        dialog=CompoundDialog(compound,self)
        if not dialog.exec():return
        c=dialog.result
        if any(x.id==c.id and x is not compound for x in self.project.compounds):error(self,tr('Compound identifier must be unique.'));return
        if compound:
            old=compound.id;index=self.project.compounds.index(compound);self.project.compounds[index]=c
            for s in self.project.samples:
                if s.analyte_id==old:s.analyte_id=c.id
                for m in s.measurements:
                    for r in m.rois:
                        if r.compound_id==old:r.compound_id=c.id
        else:self.project.compounds.append(c)
        self.project.record('Compound updated',compound_id=c.id);self.rebuild_tree();self.mark_changed()
    def add_standard(self):self.edit_standard(None)
    def edit_standard(self,standard):
        dialog=StandardDialog(standard,self)
        if dialog.exec():
            if standard:self.project.standards[self.project.standards.index(standard)]=dialog.result
            else:self.project.standards.append(dialog.result)
            self.project.record('Standard updated',standard_id=dialog.result.id);self.rebuild_tree();self.mark_changed()
    def edit_molecule_row(self,row):
        if row<len(self.project.compounds):self.edit_compound(self.project.compounds[row])
        else:self.edit_standard(self.project.standards[row-len(self.project.compounds)])
    def add_sample(self):
        data=self.selected_data();selected=self.selected_sample()
        analyte_id=data[1] if data and data[0]=='compound' else selected.analyte_id if selected else self.project.compounds[0].id if self.project.compounds else ''
        standard_id=selected.standard_id if selected else self.project.standards[0].id if self.project.standards else ''
        dialog=SampleDialog(self.project,Sample(name=tr('Sample {p0}',p0=len(self.project.samples)+1),analyte_id=analyte_id,standard_id=standard_id),self)
        if dialog.exec():
            self.project.samples.append(dialog.result);self.project.record('Preparation created',sample_id=dialog.result.id)
            self.rebuild_tree();self.select_tree_data(('sample',dialog.result.id));self.mark_changed();return dialog.result
        return None
    def edit_sample(self):
        sample=self.selected_sample()
        if not sample:return
        dialog=SampleDialog(self.project,sample,self)
        if dialog.exec():
            replacement=dialog.result;replacement.measurements=sample.measurements
            self.project.samples[self.project.samples.index(sample)]=replacement
            for workspace in self.workspaces.values():
                if workspace.sample.id==sample.id:workspace.sample=replacement;workspace.refresh_table()
            self.project.record('Preparation edited',sample_id=sample.id)
            self.rebuild_tree();self.mark_changed()
    def import_files(self,checked=False,repeat=False):
        if self.busy:error(self,tr('Wait for spectral processing to finish.'));return
        paths,_=W.QFileDialog.getOpenFileNames(self,tr('Import conventional JEOL 1H FID'),'','JEOL JDF (*.jdf)')
        if not paths:return
        sample=self.selected_sample() if repeat else None
        if repeat and sample is None:error(self,tr('Select the physical sample preparation for this repeat acquisition.'));return
        for path in paths:
            try:
                measurement=import_jdf(path)
                if not repeat:
                    selected=self.selected_compound();preparation=self.selected_sample()
                    proposed=Sample(name=Path(path).stem,
                        analyte_id=selected.id if selected and selected in self.project.compounds else self.project.compounds[0].id if self.project.compounds else '',
                        standard_id=preparation.standard_id if preparation else self.project.standards[0].id if self.project.standards else '')
                    dialog=SampleDialog(self.project,proposed,self)
                    if not dialog.exec():continue
                    sample=dialog.result;self.project.samples.append(sample)
                sample.measurements.append(measurement);self.open_measurement(sample,measurement)
                self.project.record('JDF imported',sample_id=sample.id,measurement=measurement.id,source_sha256=measurement.source_sha256)
                self.dirty=True
            except Exception as exc:error(self,f'{Path(path).name}: {message(exc)}')
        self.rebuild_tree();self.mark_changed();self.pages.setCurrentIndex(0)
    def open_measurement(self,sample,measurement):
        if measurement.id in self.workspaces:
            self.spectra_tabs.setCurrentWidget(self.workspaces[measurement.id]);return
        workspace=SpectrumWorkspace(self,sample,measurement);workspace.changed.connect(self.mark_changed)
        self.workspaces[measurement.id]=workspace;self.spectra_tabs.addTab(workspace,f'{sample.name} / {measurement.name}');self.spectra_tabs.setCurrentWidget(workspace)
        self.empty.hide();self.sync_axes(self.sync_action.isChecked())
    def close_spectrum_tab(self,index):
        workspace=self.spectra_tabs.widget(index)
        if workspace._processing_busy:error(self,tr('Wait for processing to finish.'));return
        del self.workspaces[workspace.m.id];self.spectra_tabs.removeTab(index);workspace.deleteLater()
        self.empty.setVisible(self.spectra_tabs.count()==0)
    def refresh_results(self):
        summary=project_summary(self.project);st=summary['between']
        fmt=lambda x:'—' if x is None else f'{x:.5f}'
        self._substance_rows=substance_summaries(self.project)
        if len(self._substance_rows)==1:
            substance=self._substance_rows[0];st=substance['statistics']
            text=substance['name']+'\n'+tr('Mean: {p0}% w/w    SD: {p1} pp    RSD: {p2}%    n: {p3} independent preparations',p0=fmt(st['mean']),p1=fmt(st['sd']),p2=fmt(st['rsd_percent']),p3=st['n'])
            if substance['provisional']:text+='\n'+tr('Preliminary — at least three independent preparations with current results are required.')
            self.summary_label.setText(text)
        else:self.summary_label.setText(tr('Combined results are shown separately for each substance below.'))
        self.substances_table.fill([[row['name'],row['statistics']['n'],row['statistics']['mean'],row['statistics']['sd'],row['statistics']['rsd_percent'],row['statistics']['sem'],
            ' — '.join(fmt(v) for v in row['statistics']['ci']) if row['statistics']['ci'] else tr('not available'),
            tr('Complete (at least 3 preparations)') if row['complete'] else tr('Preliminary / incomplete')] for row in self._substance_rows])
        def compound_name(key):return next((c.name for c in self.project.compounds if c.id==key),tr('Unassigned'))
        self.samples_table.fill([[compound_name(s['analyte_id']),s['name'],s['assay_percent'],s['acquisitions'],enum_label(s['independent']),s['acquisition_statistics']['sd']] for s in summary['samples']])
        rows=[]
        for s in self.project.samples:
            for m in s.measurements:
                for r in m.results.get('signals',[]):
                    for p in r['pairs']:rows.append([s.name,m.name,r['signal'],r['compound_name'],p['reference_signal'],p['proton_normalized_ratio'],p['component_mmol'],p['component_mass_mg'],p['assay_percent'],tr('current') if is_current(self.project,s,m) else tr('historical/stale')])
        self.results_table.fill(rows)
        self.statistics_panel.set_summary(self.project,summary);self.refresh_statistics_plot()
        for workspace in self.workspaces.values():workspace.refresh_table()
    def refresh_statistics_plot(self,analyte_id=''):
        summary=self.statistics_panel.current_summary
        if summary is None:return
        self.stats_plot.clear();samples=summary['samples'];st=summary['between']
        self.stats_plot.plot(list(range(len(samples))),[s['assay_percent'] for s in samples],pen=None,symbol='o',symbolBrush='#67e8f9',symbolSize=12)
        self.stats_plot.getAxis('bottom').setTicks([[(i,s['name']) for i,s in enumerate(samples)]])
        if st['mean'] is not None:self.stats_plot.addItem(pg.InfiniteLine(st['mean'],angle=0,pen=pg.mkPen('#34d399',style=QtCore.Qt.PenStyle.DashLine)))
        self.stats_plot.setVisible(bool(samples))
    def show_substance_statistics(self,key):
        self.statistics_panel.select_substance(key);self.pages.setCurrentIndex(2)
    def open_substance_statistics_row(self,row,column=0):
        if 0<=row<len(self._substance_rows):self.show_substance_statistics(self._substance_rows[row]['analyte_id'])
    def calculate(self):
        if self.busy:error(self,tr('Wait for processing before calculating results.'));return
        try:
            for s in self.project.samples:
                for m in s.measurements:update_integrals(m)
            errors=calculate_project(self.project);self.mark_changed();self.pages.setCurrentIndex(1)
            if errors:error(self,tr('Some measurements could not be calculated:\n\n')+'\n'.join(message(e) for e in errors))
        except Exception as exc:error(self,exc)
    def project_details(self):
        dialog=W.QDialog(self);dialog.setWindowTitle(tr('Project details'));dialog.resize(630,500);form=W.QFormLayout(dialog)
        name=W.QLineEdit(self.project.name);analyst=W.QLineEdit(self.project.analyst);purpose=W.QPlainTextEdit(self.project.purpose);comments=W.QPlainTextEdit(self.project.comments)
        confidence=spin(self.project.statistics_settings['confidence']*100,1,99.99,2)
        for label,widget in [(tr('Name'),name),(tr('Analyst'),analyst),(tr('Purpose'),purpose),(tr('Comments'),comments),(tr('Confidence level (%)'),confidence)]:form.addRow(label,widget)
        from .dialogs import buttons
        buttons(dialog,form)
        if dialog.exec():
            self.project.name=name.text();self.project.analyst=analyst.text();self.project.purpose=purpose.toPlainText();self.project.comments=comments.toPlainText();self.project.statistics_settings['confidence']=confidence.value()/100
            self.project.record('Project details edited');self.mark_changed()
    def can_replace(self):
        if self.busy:error(self,tr('Wait for processing to finish.'));return False
        if not self.dirty:return True
        answer=W.QMessageBox.question(self,tr('Unsaved project'),tr('Save changes before continuing?'),W.QMessageBox.StandardButton.Save|W.QMessageBox.StandardButton.Discard|W.QMessageBox.StandardButton.Cancel)
        if answer==W.QMessageBox.StandardButton.Cancel:return False
        if answer==W.QMessageBox.StandardButton.Save:return self.save()
        return True
    def replace_project(self,project,path=None):
        for index in range(self.spectra_tabs.count()-1,-1,-1):self.close_spectrum_tab(index)
        self.project=project;self.path=Path(path) if path else None;self.dirty=False
        self.rebuild_tree();self.refresh_results()
        for sample in project.samples:
            if sample.measurements:self.open_measurement(sample,sample.measurements[0])
        self.update_status()
    def new_project(self):
        if self.can_replace():self.replace_project(Project())
    def open_project(self):
        if not self.can_replace():return
        path,_=W.QFileDialog.getOpenFileName(self,tr('Open qNMR project'),str(projects_directory()),tr('qNMR Lab project (*.qnmr)'))
        if path:
            try:
                project,warnings=load_project(path);self.replace_project(project,path)
                if warnings:W.QMessageBox.information(self,tr('Project source information'),'\n'.join(message(w) for w in warnings))
            except Exception as exc:error(self,exc)
    def save(self):
        if self.busy:error(self,tr('Wait for processing to finish before saving.'));return False
        if self.path is None:return self.save_as()
        try:
            save_project(self.project,self.path);self.dirty=False;self.update_status();self.statusBar().showMessage(tr('Saved ')+str(self.path),8000);return True
        except Exception as exc:error(self,exc);return False
    def save_as(self):
        if self.busy:error(self,tr('Wait for processing to finish before saving.'));return False
        path,_=W.QFileDialog.getSaveFileName(self,tr('Save qNMR project'),str(projects_directory()/(self.path.name if self.path else 'analysis.qnmr')),tr('qNMR Lab project (*.qnmr)'))
        if not path:return False
        self.path=Path(path).with_suffix('.qnmr');return self.save()
    def open_workbook(self):
        if not self.can_replace():return
        path,_=W.QFileDialog.getOpenFileName(self,tr('Import reference workbook'),'',tr('Excel workbook (*.xlsx)'))
        if not path:return
        try:
            from openpyxl import load_workbook
            book=load_workbook(path,read_only=True);names=book.sheetnames;book.close()
            sheet,ok=W.QInputDialog.getItem(self,tr('Workbook reference'),tr('Select one study (do not pool different compounds)'),names,0,False)
            if ok:self.replace_project(import_reference(path,sheet));self.mark_changed()
        except Exception as exc:error(self,exc)
    def open_reference_example(self):
        if not self.can_replace():return
        try:
            project,_=load_project(Path(__file__).resolve().parents[1]/'examples/synthetic_three_samples.qnmr')
            self.replace_project(project);self.pages.setCurrentIndex(1)
        except Exception as exc:error(self,exc)
    def export_report(self):
        if self.busy:error(self,tr('Wait for processing before exporting.'));return
        if not any(m.results for s in self.project.samples for m in s.measurements):error(self,tr('Calculate assay results before exporting.'));return
        path,selected=W.QFileDialog.getSaveFileName(self,tr('Export quantitative analysis'),str(reports_directory()/(self.project.id+'.docx')),tr('Word report (*.docx);;Extended technical Word report (*.docx);;Excel results (*.xlsx);;CSV integrals (*.csv);;Complete bundle (select *.folder)'))
        if not path:return
        try:
            if '*.folder' in selected:export_bundle(self.project,Path(path).with_suffix(''))
            elif selected==tr('Extended technical Word report (*.docx)'):export_docx(self.project,Path(path).with_suffix('.docx'),profile='extended')
            elif '*.docx' in selected:export_docx(self.project,Path(path).with_suffix('.docx'))
            elif '*.xlsx' in selected:export_xlsx(self.project,Path(path).with_suffix('.xlsx'))
            else:export_csv(self.project,Path(path).with_suffix('.csv'))
            self.statusBar().showMessage(tr('Export completed: ')+path,10000)
        except Exception as exc:error(self,exc)
    def import_library(self):
        path,_=W.QFileDialog.getOpenFileName(self,tr('Import standard library'),'','JSON (*.json)')
        if path:
            try:
                entries=load_standard_library(path)
                for s in entries:
                    if any(old.id==s.id for old in self.project.standards):s.id=uid()
                    self.project.standards.append(s)
                self.project.record('Standard library imported',count=len(entries));self.rebuild_tree();self.mark_changed()
            except Exception as exc:error(self,exc)
    def export_library(self):
        path,_=W.QFileDialog.getSaveFileName(self,tr('Export standard library'),'standards.json','JSON (*.json)')
        if path:
            try:save_standard_library(self.project.standards,path)
            except Exception as exc:error(self,exc)
    def apply_template(self,checked=False,align=False):
        if self.busy:error(self,tr('Wait for processing before editing templates.'));return
        source=self.current_workspace()
        if source is None or not source.m.arrays:error(self,tr('Select a source spectrum with quantitative ROIs.'));return
        targets=[(s,m) for s in self.project.samples for m in s.measurements if m.id!=source.m.id and m.arrays]
        if not targets:error(self,tr('Import another acquisition first.'));return
        labels=[f'{s.name} / {m.name} [{m.id}]' for s,m in targets]
        label,ok=W.QInputDialog.getItem(self,tr('ROI template'),tr('Target acquisition'),labels,0,False)
        if not ok:return
        sample,target=targets[labels.index(label)]
        try:
            rois=template_rois(source.m,target)
            if source.sample.analyte_id!=sample.analyte_id or source.sample.standard_id!=sample.standard_id:
                raise ValueError(tr('Template compounds and standard must match the target preparation.'))
            if align:
                proposal=alignment_proposal(source.m,target)
                text=tr('Review proposed peak-based ROI shifts (ppm):\n')+'\n'.join(tr('{p0}: {p1:.5f} to {p2:.5f}, shift {p3:+.5f}', p0=name, p1=a, p2=b, p3=delta) for name,a,b,delta in proposal)
                text+=tr('\n\nThis replaces the target ROI definitions. Confirm every assignment and boundary in the target spectrum.')
                if W.QMessageBox.question(self,tr('Confirm alignment'),text)!=W.QMessageBox.StandardButton.Yes:return
                for roi,(_,lo,hi,_) in zip(rois,proposal):roi.low=lo;roi.high=hi
            elif W.QMessageBox.question(self,tr('Confirm ROI template'),tr('Replace target ROI definitions with this template? Existing target results will become historical.'))!=W.QMessageBox.StandardButton.Yes:return
            if target.options.get('baseline_enabled'):validate_baseline_roi_overlap(target.options['baseline_regions'],[(r.low,r.high) for r in rois])
            old=target.rois;target.rois=rois
            try:update_integrals(target)
            except Exception:target.rois=old;raise
            self.project.record('ROI template applied',source=source.m.id,target=target.id,aligned=align)
            self.open_measurement(sample,target);self.workspaces[target.id].redraw();self.mark_changed()
        except Exception as exc:error(self,exc)
    def sync_axes(self,enabled):
        available=[w for w in self.workspaces.values() if w.m.arrays]
        if not available:return
        for workspace in available:workspace.plot.setXLink(None)
        if enabled:
            for workspace in available[1:]:workspace.plot.setXLink(available[0].plot)
    def apply_spectrum_appearance(self,appearance,*,persist=False):
        self.appearance=appearance
        for workspace in self.workspaces.values():
            appearance.apply_grid(workspace.plot)
            curve=getattr(workspace,'spectrum_curve',None)
            if curve is not None:curve.setPen(appearance.pen())
        if persist:appearance.save(self.settings)
    def edit_spectrum_settings(self):
        previous=self.appearance;dialog=SpectrumSettingsDialog(previous,self)
        dialog.changed.connect(self.apply_spectrum_appearance)
        if dialog.exec()==W.QDialog.DialogCode.Accepted:self.apply_spectrum_appearance(dialog.appearance(),persist=True)
        else:self.apply_spectrum_appearance(previous)
    def compare_spectra(self):
        available=[(s,m) for s in self.project.samples for m in s.measurements if m.arrays]
        if len(available)<2:error(self,tr('Import at least two spectra to compare.'));return
        dialog=W.QDialog(self);dialog.setWindowTitle(tr('Compare spectra — shared ppm axis, independent intensity'));dialog.resize(1400,700)
        layout=W.QVBoxLayout(dialog);split=W.QSplitter();layout.addWidget(split,1);plots=[]
        for s,m in available:
            plot=pg.PlotWidget(background='#0a111c',viewBox=SpectrumBox(),title=s.name+' / '+m.name);plot.invertX(True)
            plot.plot(m.arrays['ppm'],m.arrays['spectrum'][0].real,pen=self.appearance.pen());self.appearance.apply_grid(plot)
            plot.setLabel('bottom','¹H',units='ppm');plot.addItem(pg.InfiniteLine(0,angle=0,pen='#64748b'))
            for r in m.rois:plot.addItem(pg.LinearRegionItem((r.low,r.high),movable=False,brush=(52,211,153,25) if r.role=='standard' else (103,232,249,25)))
            if plots:plot.setXLink(plots[0])
            plots.append(plot);split.addWidget(plot)
        button(tr('Close'),dialog.accept,layout);dialog.exec()
    def relink_source(self):
        w=self.current_workspace()
        if not w:return
        path,_=W.QFileDialog.getOpenFileName(self,tr('Relink matching original source'),'',tr('Source files (*.jdf *.xlsx)'))
        if path:
            try:relink_measurement(w.m,path);self.project.record('Source relinked',measurement=w.m.id,path=path);self.mark_changed()
            except Exception as exc:error(self,exc)
    def measurement_inclusion(self):
        w=self.current_workspace()
        if not w:return
        if w.m.include:
            reason,ok=W.QInputDialog.getText(self,tr('Exclude acquisition'),tr('Record exclusion reason'))
            if not ok:return
            if not reason.strip():error(self,tr('A reason is required.'));return
            w.m.include=False;w.m.exclusion_reason=reason
        else:w.m.include=True
        self.project.record('Acquisition inclusion changed',measurement=w.m.id,include=w.m.include,reason=w.m.exclusion_reason)
        self.rebuild_tree();self.mark_changed()
    def open_manual(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(manual_path())))
    def closeEvent(self,event):
        if self.can_replace():event.accept()
        else:event.ignore()

def main():
    app=W.QApplication.instance() or W.QApplication(sys.argv);app.setApplicationName('qNMR Lab');app.setOrganizationName('qNMR Lab')
    load_preference()
    pg.setConfigOptions(antialias=False)
    window=MainWindow()
    if len(sys.argv)>1:
        try:
            project,warnings=load_project(sys.argv[1]);window.replace_project(project,sys.argv[1])
            if warnings:W.QMessageBox.information(window,tr('Source information'),'\n'.join(message(w) for w in warnings))
        except Exception as exc:error(window,exc)
    window.show()
    def exception_hook(exc_type,exc,tb):
        traceback.print_exception(exc_type,exc,tb);error(window,exc)
    sys.excepthook=exception_hook
    return app.exec()
