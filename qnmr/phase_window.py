"""Cached manual phase editor adapted from DOSY Lab (MIT)."""
from copy import deepcopy
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from .i18n import translate, language
from .processing import phase_radians
from .spectrum_view import PhaseBox
from .spectrum_settings import SpectrumAppearance

class PhaseWindow(QtWidgets.QDialog):
    applied = QtCore.Signal(dict)

    def tr(self,source,**values):
        return translate(source,self.language_code,**values)

    def __init__(self, dataset, parent=None, appearance=SpectrumAppearance(),language_code=None):
        super().__init__(parent)
        self.language_code=language_code or language()
        self.setLocale(QtCore.QLocale('pl_PL' if self.language_code=='pl' else 'en_GB'))
        self.setWindowTitle(self.tr('qNMR Lab · Interactive 1D phasing'))
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.resize(1350,850)
        if parent is not None:self.setStyleSheet(parent.styleSheet())
        self.dataset=dataset
        self.appearance = appearance
        self.initial=deepcopy(dataset.options)
        self.previous_pivot=self.initial['pivot_ppm']
        # Processing has already applied apodization, FFT, referencing and filters at this stage.
        self.before_baseline = dataset.phased
        self.initial_phase = phase_radians(dataset.ppm, dataset.metadata, self.initial)
        self.preview=None
        self.last_drag_dy = 0.
        layout=QtWidgets.QVBoxLayout(self)
        help_label=QtWidgets.QLabel(
            self.tr('<b>Left + vertical drag</b> — PH0 &nbsp;·&nbsp; <b>Right + vertical drag</b> — PH1 &nbsp;·&nbsp; <b>Shift + drag</b> — fine adjustment<br><b>Set pivot</b> — enable to select a pivot &nbsp;·&nbsp; <b>Middle + drag</b> — pan &nbsp;·&nbsp; <b>Wheel</b> — display gain'))
        help_label.setWordWrap(True);layout.addWidget(help_label)
        baseline_note = QtWidgets.QLabel(self.tr('Phase preview: baseline correction is disabled.'))
        baseline_note.setWordWrap(True)
        layout.addWidget(baseline_note)
        row=QtWidgets.QHBoxLayout();layout.addLayout(row)
        self.controls={}
        for key,label,value,low,high,step,decimals in [
            ('phase0_deg','PH0 [°]',self.initial['phase0_deg'],-3600,3600,.5,6),
            ('phase1_deg','PH1 [° / SW]',self.initial['phase1_deg'],-100000,100000,10,6),
            ('pivot_ppm','Pivot [ppm]',self.initial['pivot_ppm'],-1000,1000,.001,6)]:
            row.addWidget(QtWidgets.QLabel(label))
            control=QtWidgets.QDoubleSpinBox();control.setDecimals(decimals);control.setRange(low,high)
            control.setSingleStep(step);control.setValue(value);self.controls[key]=control
            control.valueChanged.connect(self.pivot_changed if key=='pivot_ppm' else self.refresh);row.addWidget(control)
        row.addWidget(QtWidgets.QLabel(self.tr('Preview:')))
        self.layer=QtWidgets.QComboBox()
        self.layer.addItem(self.tr('1D spectrum'),0)
        self.layer.setCurrentIndex(self.initial['reference_layer']);self.layer.currentIndexChanged.connect(self.draw)
        row.addWidget(self.layer,1)
        row=QtWidgets.QHBoxLayout();layout.addLayout(row)
        row.addWidget(QtWidgets.QLabel(self.tr('PH0 sensitivity (°/px):')))
        self.ph0_sensitivity=self.sensitivity(row,[.05,.1,.5,1,2],.5)
        row.addWidget(QtWidgets.QLabel(self.tr('PH1 sensitivity (°/px):')))
        self.ph1_sensitivity=self.sensitivity(row,[.5,2,10,50,100],10)
        self.imaginary=QtWidgets.QCheckBox(self.tr('Show imaginary spectrum'));self.imaginary.toggled.connect(self.draw);row.addWidget(self.imaginary)
        self.before=QtWidgets.QCheckBox(self.tr('Show phase before editing'));self.before.toggled.connect(self.draw);row.addWidget(self.before)
        self.zoom_button=QtWidgets.QPushButton(self.tr('Zoom range [Z]'));self.zoom_button.setCheckable(True)
        self.zoom_button.setToolTip(self.tr('Enable drag zoom; disable to return to PH0/PH1 gestures.'))
        row.addWidget(self.zoom_button)
        self.pan_button = QtWidgets.QPushButton(self.tr('Pan spectrum [P]'))
        self.pan_button.setCheckable(True)
        self.pan_button.setToolTip(self.tr('Drag with the left button to pan vertically or horizontally. Disable to return to phasing.'))
        row.addWidget(self.pan_button)
        self.pivot_button = QtWidgets.QPushButton(self.tr('Set pivot'))
        self.pivot_button.setCheckable(True)
        self.pivot_button.setToolTip(self.tr('Enable to click the spectrum, drag the guide or enter a pivot in ppm.'))
        row.addWidget(self.pivot_button)
        self.controls['pivot_ppm'].setEnabled(False)
        self.navigation_buttons = {'zoom': self.zoom_button, 'pan': self.pan_button, 'pivot': self.pivot_button}
        for mode, button in self.navigation_buttons.items():
            button.toggled.connect(lambda checked, mode=mode: self.set_navigation(mode, checked))
        row.addStretch()
        for text,callback in [(self.tr('Full range [F]'),self.reset_view),(self.tr('Full screen'),self.toggle_fullscreen),(self.tr('Reset PH0/PH1'),self.reset_phase)]:
            button=QtWidgets.QPushButton(text);button.clicked.connect(callback);row.addWidget(button)
        self.view=PhaseBox();self.plot=pg.PlotWidget(viewBox=self.view);layout.addWidget(self.plot,1)
        self.view.bind_selection_feedback(self.plot)
        self.plot.viewport().installEventFilter(self)
        for key, callback in [('Z', self.zoom_button.click), ('F', self.reset_view), ('P', self.pan_button.click)]:
            shortcut = QtGui.QShortcut(QtGui.QKeySequence(key), self)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(callback)
        self.plot.invertX(True)
        self.appearance.apply_grid(self.plot)
        self.plot.setLabel('bottom','¹H [ppm]');self.plot.setLabel('left',self.tr('Spectrum before baseline correction'),units=self.tr('a.u.'))
        self.view.phase_dragged.connect(self.drag_phase);self.view.clicked.connect(self.set_pivot)
        self.phase_label=QtWidgets.QLabel();self.phase_label.setWordWrap(True);layout.addWidget(self.phase_label)
        # The raw FID is diagnostic only. Never guess a vendor delay from its maximum.
        corrected_delay=self.initial['filter_delay_samples']
        self.filter_note=QtWidgets.QLabel(
            self.tr('Filter correction: {p0:.4f} samples. PH0/PH1 adjust the corrected spectrum. Change delay in Processing controls. Below: start of the raw FID.', p0=corrected_delay)
            if corrected_delay else
            self.tr('Start of the raw FID. If manual delay correction is needed, each sample corresponds to a 360° / SW ramp.'))
        self.filter_note.setWordWrap(True)
        self.filter_note.setStyleSheet('color:#fbbf24;');layout.addWidget(self.filter_note)
        self.fid_plot=pg.PlotWidget();self.fid_plot.setMaximumHeight(120);self.fid_plot.setMinimumHeight(90)
        self.fid_plot.setLabel('bottom',self.tr('FID sample index (starting at 0)'));self.fid_plot.setLabel('left','|FID|')
        n=min(100,dataset.raw.fid.shape[1]);ref=self.initial['reference_layer']
        self.fid_plot.plot(np.arange(n),abs(dataset.raw.fid[ref,:n]),pen='#fbbf24',symbol='o',symbolSize=3)
        layout.addWidget(self.fid_plot)
        row=QtWidgets.QHBoxLayout();layout.addLayout(row)
        row.addWidget(QtWidgets.QLabel(self.tr('Manual delay (samples)')))
        self.delay=QtWidgets.QDoubleSpinBox();self.delay.setRange(-250,250);self.delay.setDecimals(4);self.delay.setValue(0)
        row.addWidget(self.delay)
        button=QtWidgets.QPushButton(self.tr('Add 360° × delay ramp'));button.clicked.connect(self.add_delay);row.addWidget(button)
        self.delay.setEnabled(not corrected_delay);button.setEnabled(not corrected_delay)
        row.addStretch()
        cancel=QtWidgets.QPushButton(self.tr('Cancel'));cancel.clicked.connect(self.reject);row.addWidget(cancel)
        self.apply_button=QtWidgets.QPushButton(self.tr('Apply phase to this acquisition'))
        self.apply_button.clicked.connect(self.commit);row.addWidget(self.apply_button)
        self.refresh();self.plot.autoRange()

    @staticmethod
    def sensitivity(row,values,default):
        combo=QtWidgets.QComboBox()
        for value in values:combo.addItem(str(value),value)
        combo.setCurrentIndex(values.index(default));row.addWidget(combo);return combo

    def options(self):
        o=deepcopy(self.initial)
        for key,control in self.controls.items():o[key]=control.value()
        return o

    def refresh(self,*args):
        if not hasattr(self,'plot'):return
        o=self.options()
        phase_change = phase_radians(self.dataset.ppm, self.dataset.metadata, o) - self.initial_phase
        self.preview = self.before_baseline * np.exp(1j * phase_change)[None, :]
        self.draw()
        self.phase_label.setText(self.tr('PH0={p0:.3f}° · PH1={p1:.3f}° / full SW · pivot={p2:.6f} ppm. Changes apply to this acquisition. Vendor phase settings are not copied.', p0=o['phase0_deg'], p1=o['phase1_deg'], p2=o['pivot_ppm']))

    def draw(self,*args):
        if self.preview is None:return
        self.plot.clear();i=self.layer.currentIndex();x=self.dataset.ppm
        self.plot.plot(x,self.preview[i].real,pen=self.appearance.pen())
        if self.imaginary.isChecked():self.plot.plot(x,self.preview[i].imag,pen=self.appearance.pen('#fb923c',QtCore.Qt.PenStyle.DotLine))
        if self.before.isChecked():self.plot.plot(x,self.before_baseline[i].real,pen=self.appearance.pen('#64748b',QtCore.Qt.PenStyle.DashLine))
        self.pivot=pg.InfiniteLine(self.controls['pivot_ppm'].value(),movable=self.pivot_button.isChecked(),pen=pg.mkPen('#c084fc',width=2))
        self.pivot.sigPositionChangeFinished.connect(lambda line:self.set_pivot(line.value()))
        self.plot.addItem(self.pivot)

    def set_navigation(self, mode, checked):
        if checked:
            for name, button in self.navigation_buttons.items():
                if name != mode:
                    with QtCore.QSignalBlocker(button):
                        button.setChecked(False)
        self.view.hide_selection_preview()
        self.view.mode = mode if checked else 'zoom'
        self.view.phasing = not checked
        editing_pivot = self.pivot_button.isChecked()
        self.controls['pivot_ppm'].setEnabled(editing_pivot)
        self.pivot.setMovable(editing_pivot)

    def reset_view(self):
        self.view.hide_selection_preview()
        self.plot.autoRange()

    def eventFilter(self, watched, event):
        if (watched is self.plot.viewport() and event.type() == QtCore.QEvent.Type.MouseButtonDblClick
                and event.button() == QtCore.Qt.MouseButton.LeftButton):
            self.reset_view()
            return True
        return super().eventFilter(watched, event)

    def set_pivot(self,value):
        if self.pivot_button.isChecked():
            self.controls['pivot_ppm'].setValue(value)

    def pivot_changed(self,value):
        # Moving the pivot is a change of coordinates, not an extra phase edit.
        width=self.dataset.metadata['x_sweep_Hz']/(self.dataset.metadata['x_frequency_Hz']/1e6)
        control=self.controls['phase0_deg']
        ph0=control.value()+self.controls['phase1_deg'].value()*(value-self.previous_pivot)/width
        if abs(ph0)>3600:ph0=(ph0+180)%360-180
        control.blockSignals(True);control.setValue(ph0);control.blockSignals(False)
        self.previous_pivot=value;self.refresh()

    def drag_phase(self, which, dy, start, finish, fine):
        key = 'phase0_deg' if which == 0 else 'phase1_deg'
        sensitivity = self.ph0_sensitivity if which == 0 else self.ph1_sensitivity
        degrees_per_pixel = float(sensitivity.currentData())
        if fine:
            degrees_per_pixel = min(degrees_per_pixel / 20, .25)
        # Scale only the movement since the last event, so Shift can change mid-drag.
        movement = dy if start else dy - self.last_drag_dy
        control = self.controls[key]
        control.setValue(control.value() + movement * degrees_per_pixel)
        self.last_drag_dy = 0. if finish else dy

    def add_delay(self):
        control=self.controls['phase1_deg'];control.setValue(control.value()+360*self.delay.value())

    def reset_phase(self):
        for key in ('phase0_deg','phase1_deg'):self.controls[key].blockSignals(True);self.controls[key].setValue(0);self.controls[key].blockSignals(False)
        self.refresh()

    def toggle_fullscreen(self):
        if self.isFullScreen():self.showNormal()
        else:self.showFullScreen()

    def commit(self):
        self.applied.emit({key:control.value() for key,control in self.controls.items()})
        self.accept()
