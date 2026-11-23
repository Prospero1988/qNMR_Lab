"""Analyst-facing editors; validation occurs before committing edited records."""
from copy import deepcopy
from pathlib import Path
import math
from PySide6 import QtCore, QtGui, QtWidgets as W, QtSvgWidgets
from .i18n import tr, message, enum_items, enum_value, enum_label
from .models import Compound, Standard, Sample, ROI
from .chemistry import parse_smiles, read_structures, molecule, depiction, validate_mw, export_structure
from .quantification import purity_fraction

def error(parent, exc):
    W.QMessageBox.warning(parent,'qNMR Lab',message(exc))

def spin(value=0, minimum=0, maximum=1e9, decimals=6):
    box=W.QDoubleSpinBox();box.setDecimals(decimals);box.setRange(minimum,maximum);box.setValue(value)
    box.setKeyboardTracking(False);box.setMinimumWidth(110)
    return box

def buttons(dialog,form):
    bar=W.QDialogButtonBox(W.QDialogButtonBox.StandardButton.Ok|W.QDialogButtonBox.StandardButton.Cancel)
    bar.accepted.connect(dialog.accept);bar.rejected.connect(dialog.reject)
    form.addRow(bar)

class StructureView(W.QGraphicsView):
    atom_clicked=QtCore.Signal(int)
    def __init__(self,parent=None):
        super().__init__(parent);self.setScene(W.QGraphicsScene(self));self.positions=[]
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing);self.setDragMode(self.DragMode.ScrollHandDrag)
        self.setBackgroundBrush(QtGui.QColor('white'))
    def wheelEvent(self,event):
        factor=1.15 if event.angleDelta().y()>0 else 1/1.15
        self.scale(factor,factor);event.accept()
    def mouseDoubleClickEvent(self,event):self.fitInView(self.sceneRect(),QtCore.Qt.AspectRatioMode.KeepAspectRatio)
    def mousePressEvent(self,event):
        pos=self.mapToScene(event.position().toPoint())
        if event.button()==QtCore.Qt.MouseButton.LeftButton and self.positions:
            distances=[math.hypot(pos.x()-x,pos.y()-y) for x,y in self.positions]
            if min(distances)<18:self.atom_clicked.emit(distances.index(min(distances)))
        super().mousePressEvent(event)

class StructureDialog(W.QDialog):
    def __init__(self,compound,atoms=(),parent=None):
        super().__init__(parent);self.compound=compound;self.atoms=set(atoms)
        self.setWindowTitle(tr('Structure — ')+compound.name);self.resize(900,680)
        layout=W.QVBoxLayout(self);self.view=StructureView();layout.addWidget(self.view,1)
        self.label=W.QLabel();self.label.setWordWrap(True);layout.addWidget(self.label)
        layout.addWidget(W.QLabel(tr('Click numbered atoms to highlight. Wheel: zoom. Drag: pan. Double-click: fit. Atom indices start at 0. Proton equivalence and contributing nuclei require analyst confirmation.')))
        row=W.QHBoxLayout();layout.addLayout(row)
        export=W.QPushButton(tr('Export PNG / SVG'));export.clicked.connect(self.export);row.addWidget(export)
        clear=W.QPushButton(tr('Clear atom selection'));clear.clicked.connect(lambda:(self.atoms.clear(),self.draw()));row.addWidget(clear)
        ok=W.QPushButton(tr('Use selected atoms'));ok.clicked.connect(self.accept);row.addWidget(ok)
        close=W.QPushButton(tr('Cancel'));close.clicked.connect(self.reject);row.addWidget(close)
        self.view.atom_clicked.connect(self.select);self.draw()
        QtCore.QTimer.singleShot(0,lambda:self.view.fitInView(self.view.sceneRect(),QtCore.Qt.AspectRatioMode.KeepAspectRatio))
    def select(self,index):
        if index in self.atoms:self.atoms.remove(index)
        else:self.atoms.add(index)
        self.draw()
    def draw(self):
        svg,positions=depiction(self.compound,width=820,height=500,atoms=sorted(self.atoms))
        self.view.scene().clear();self.svg=QtSvgWidgets.QGraphicsSvgItem()
        from PySide6.QtSvg import QSvgRenderer
        self.renderer=QSvgRenderer(svg.encode('utf-8'));self.svg.setSharedRenderer(self.renderer)
        self.view.scene().addItem(self.svg);self.view.setSceneRect(self.svg.boundingRect());self.view.positions=positions
        self.label.setText(tr('{p0}   MW {p1:g} g/mol   Selected atoms: {p2}\nForm: {p3}', p0=self.compound.formula, p1=self.compound.molecular_weight, p2=sorted(self.atoms), p3=self.compound.chemical_form or tr('not recorded')))
    def export(self):
        path,_=W.QFileDialog.getSaveFileName(self,tr('Export structure'),self.compound.id+'.png','PNG (*.png);;SVG (*.svg)')
        if path:
            try:export_structure(self.compound,path,sorted(self.atoms))
            except Exception as exc:error(self,exc)

class CompoundDialog(W.QDialog):
    def __init__(self,compound=None,parent=None):
        super().__init__(parent);self.result=deepcopy(compound or Compound());c=self.result
        self.setWindowTitle(tr('Chemical structure and weighed form'));self.resize(650,650)
        form=W.QFormLayout(self);form.setFieldGrowthPolicy(W.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.name=W.QLineEdit(c.name);form.addRow(tr('Name'),self.name)
        self.identifier=W.QLineEdit(c.id);form.addRow(tr('Internal identifier'),self.identifier)
        self.smiles=W.QLineEdit(c.smiles);self.smiles.setPlaceholderText(tr('Paste SMILES including counterions / hydrates as appropriate'))
        form.addRow('SMILES',self.smiles)
        row=W.QHBoxLayout();form.addRow(row)
        parse=W.QPushButton(tr('Parse SMILES / calculate MW'));parse.clicked.connect(self.parse);row.addWidget(parse)
        load=W.QPushButton(tr('Load MOL / SDF'));load.clicked.connect(self.load_structure);row.addWidget(load)
        view=W.QPushButton(tr('Inspect structure'));view.clicked.connect(self.inspect);row.addWidget(view)
        self.formula=W.QLineEdit(c.formula);form.addRow(tr('Formula'),self.formula)
        self.mw=spin(c.molecular_weight);form.addRow(tr('MW of weighed form (g/mol)'),self.mw)
        self.chemical_form=W.QLineEdit(c.chemical_form);form.addRow(tr('Chemical form / salt / solvate'),self.chemical_form)
        self.reason=W.QLineEdit(c.mw_override_reason);form.addRow(tr('Manual MW / override explanation'),self.reason)
        self.provenance=W.QPlainTextEdit(c.provenance);self.provenance.setMaximumHeight(85);form.addRow(tr('Molecular data provenance'),self.provenance)
        self.comments=W.QPlainTextEdit(c.comments);self.comments.setMaximumHeight(85);form.addRow(tr('Comments'),self.comments)
        note=W.QLabel(tr('A structure is optional if a verified MW and an explanation are entered. The MW must describe the material actually weighed. Neutral parent structures may omit salts, hydrates or solvates.'))
        note.setWordWrap(True);form.addRow(note);buttons(self,form)
    def populate_chemical(self,c):
        self.result.smiles=c.smiles;self.result.molblock=c.molblock;self.result.calculated_mw=c.calculated_mw
        self.result.source_path=c.source_path;self.result.source_sha256=c.source_sha256
        self.smiles.setText(c.smiles);self.formula.setText(c.formula);self.mw.setValue(c.molecular_weight)
        self.provenance.setPlainText(c.provenance);self.reason.clear()
    def parse(self):
        try:self.populate_chemical(parse_smiles(self.smiles.text(),self.name.text()))
        except Exception as exc:error(self,exc)
    def load_structure(self):
        path,_=W.QFileDialog.getOpenFileName(self,tr('Load chemical structures'),'',tr('Structures (*.mol *.sdf)'))
        if not path:return
        try:
            compounds=read_structures(path);selected=compounds[0]
            if len(compounds)>1:
                labels=[f'{i+1}: {c.name}' for i,c in enumerate(compounds)]
                name,ok=W.QInputDialog.getItem(self,tr('SDF records'),tr('Choose a structure'),labels,0,False)
                if not ok:return
                selected=compounds[labels.index(name)]
            self.populate_chemical(selected);self.name.setText(selected.name)
        except Exception as exc:error(self,exc)
    def inspect(self):
        try:
            c=deepcopy(self.result);c.smiles=self.smiles.text()
            if c.smiles!=self.result.smiles:c.molblock=''
            c.name=self.name.text();c.molecular_weight=self.mw.value();c.formula=self.formula.text()
            StructureDialog(c,parent=self).exec()
        except Exception as exc:error(self,exc)
    def accept(self):
        try:
            c=deepcopy(self.result)
            if self.smiles.text().strip()!=c.smiles:
                if self.smiles.text().strip():
                    parsed=parse_smiles(self.smiles.text(),self.name.text())
                    c.smiles=parsed.smiles;c.molblock='';c.calculated_mw=parsed.calculated_mw;c.formula=parsed.formula
                else:c.smiles='';c.molblock='';c.calculated_mw=None
            c.name=self.name.text().strip();c.id=self.identifier.text().strip()
            if not c.name or not c.id:raise ValueError(tr('Name and identifier are required.'))
            c.formula=self.formula.text();c.molecular_weight=self.mw.value();c.chemical_form=self.chemical_form.text()
            c.mw_override_reason=self.reason.text();c.provenance=self.provenance.toPlainText();c.comments=self.comments.toPlainText()
            validate_mw(c)
            if c.smiles or c.molblock:molecule(c)
            self.result=c;super().accept()
        except Exception as exc:error(self,exc)

class StandardDialog(W.QDialog):
    def __init__(self,standard=None,parent=None):
        super().__init__(parent);self.result=deepcopy(standard or Standard());s=self.result
        self.setWindowTitle(tr('Internal-standard reference material'));self.resize(620,560)
        form=W.QFormLayout(self)
        self.compound_button=W.QPushButton(s.compound.name);self.compound_button.clicked.connect(self.edit_compound)
        form.addRow(tr('Compound / structure'),self.compound_button)
        self.purity=spin(100*s.purity_fraction,0,100,6);form.addRow(tr('Certified purity (% w/w)'),self.purity)
        self.fields={}
        for key,label in [('certificate',tr('Certificate information')),('batch',tr('Batch')),('reference_material_id',tr('Reference material ID')),('expiration',tr('Expiration (YYYY-MM-DD)')),('validation_status',tr('Validation status'))]:
            widget=W.QLineEdit(getattr(s,key));self.fields[key]=widget;form.addRow(label,widget)
        self.notes=W.QPlainTextEdit(s.notes);self.notes.setMaximumHeight(90);form.addRow(tr('Notes'),self.notes)
        self.signals=W.QPlainTextEdit('\n'.join(f"{r.get('signal','')};{r.get('protons',1)}" for r in s.assigned_signals));self.signals.setMaximumHeight(70)
        form.addRow(tr('Assigned signals (one signal;protons per line)'),self.signals)
        warning=W.QLabel(tr('Thymol purity 99.57% belongs only to the supplied example material. Enter the actual certificate and batch used for your measurements.'));warning.setWordWrap(True);form.addRow(warning)
        buttons(self,form)
    def edit_compound(self):
        dialog=CompoundDialog(self.result.compound,self)
        if dialog.exec():self.result.compound=dialog.result;self.compound_button.setText(dialog.result.name)
    def accept(self):
        try:
            validate_mw(self.result.compound);s=deepcopy(self.result)
            s.purity_fraction=purity_fraction(self.purity.value(),'% w/w')
            for key,widget in self.fields.items():setattr(s,key,widget.text())
            if s.expiration:
                from datetime import date
                date.fromisoformat(s.expiration)
            s.notes=self.notes.toPlainText();s.assigned_signals=[]
            for line in self.signals.toPlainText().splitlines():
                name,protons=line.rsplit(';',1);n=float(protons)
                if not math.isfinite(n) or n<=0:raise ValueError(tr('Assigned proton counts must be positive.'))
                s.assigned_signals.append(dict(signal=name,protons=n))
            self.result=s;super().accept()
        except Exception as exc:error(self,exc)

class SampleDialog(W.QDialog):
    def __init__(self,project,sample=None,parent=None):
        super().__init__(parent);self.result=deepcopy(sample or Sample());self.project=project;s=self.result
        self.setWindowTitle(tr('Independent sample preparation'));self.resize(580,570);form=W.QFormLayout(self)
        self.name=W.QLineEdit(s.name);form.addRow(tr('Sample identifier'),self.name)
        self.analyte=W.QComboBox();self.standard=W.QComboBox()
        for c in project.compounds:self.analyte.addItem(c.name,c.id)
        for c in project.standards:self.standard.addItem(c.compound.name,c.id)
        for box,key in [(self.analyte,s.analyte_id),(self.standard,s.standard_id)]:
            index=box.findData(key)
            if index>=0:box.setCurrentIndex(index)
        form.addRow(tr('Analyte'),self.analyte);form.addRow(tr('Internal standard'),self.standard)
        self.ma=spin(s.analyte_mass);self.mi=spin(s.standard_mass)
        form.addRow(tr('Weighed analyte mass'),self.ma);form.addRow(tr('Weighed standard mass'),self.mi)
        self.unit=W.QComboBox();self.unit.addItems(['mg','g','ug']);self.unit.setCurrentText(s.mass_unit);form.addRow(tr('Units for both masses'),self.unit)
        self.solvent=W.QLineEdit(s.solvent);form.addRow(tr('Solvent'),self.solvent)
        self.date=W.QLineEdit(s.preparation_date);form.addRow(tr('Preparation date (YYYY-MM-DD)'),self.date)
        self.independent=W.QCheckBox(tr('Independently prepared sample (counts toward n)'));self.independent.setChecked(s.independent);form.addRow(self.independent)
        self.include=W.QCheckBox(tr('Include preparation in final results'));self.include.setChecked(s.include);form.addRow(self.include)
        self.reason=W.QLineEdit(s.exclusion_reason);form.addRow(tr('Exclusion reason'),self.reason)
        self.notes=W.QPlainTextEdit(s.notes);self.notes.setMaximumHeight(90);form.addRow(tr('Notes'),self.notes)
        note=W.QLabel(tr('Repeat acquisitions of the same physical sample belong under this preparation. They do not increase the number of independent preparations.'));note.setWordWrap(True);form.addRow(note)
        buttons(self,form)
    def accept(self):
        try:
            s=deepcopy(self.result);s.name=self.name.text().strip()
            if not s.name:raise ValueError(tr('Enter a sample identifier.'))
            if not self.analyte.currentData() or not self.standard.currentData():raise ValueError(tr('Select an analyte and internal standard.'))
            if not self.include.isChecked() and not self.reason.text().strip():raise ValueError(tr('Record a sample exclusion reason.'))
            if self.date.text():
                from datetime import date
                date.fromisoformat(self.date.text())
            s.analyte_id=self.analyte.currentData();s.standard_id=self.standard.currentData();s.analyte_mass=self.ma.value();s.standard_mass=self.mi.value()
            s.mass_unit=self.unit.currentText();s.solvent=self.solvent.text();s.preparation_date=self.date.text()
            s.independent=self.independent.isChecked();s.include=self.include.isChecked();s.exclusion_reason=self.reason.text();s.notes=self.notes.toPlainText()
            self.result=s;super().accept()
        except Exception as exc:error(self,exc)

class ROIDialog(W.QDialog):
    def __init__(self,project,sample,measurement,roi=None,parent=None):
        super().__init__(parent);self.project=project;self.sample=sample;self.measurement=measurement
        self.result=deepcopy(roi or ROI(compound_id=sample.analyte_id));r=self.result
        self.setWindowTitle(tr('Quantitative resonance assignment'));self.resize(650,700);form=W.QFormLayout(self)
        self.signal=W.QLineEdit(r.signal);form.addRow(tr('Signal identifier'),self.signal)
        self.low=spin(r.low,-1000,1000);self.high=spin(r.high,-1000,1000)
        form.addRow(tr('Low boundary (ppm)'),self.low);form.addRow(tr('High boundary (ppm)'),self.high)
        self.low.setEnabled(bool(measurement.arrays));self.high.setEnabled(bool(measurement.arrays))
        self.role=W.QComboBox();enum_items(self.role,['analyte','standard','water','solvent','impurity','other','unassigned'],r.role)
        form.addRow(tr('Signal role'),self.role)
        self.compound=W.QComboBox();form.addRow(tr('Compound assignment'),self.compound)
        self.role.currentIndexChanged.connect(self.populate_compounds);self.populate_compounds()
        idx=self.compound.findData(r.compound_id)
        if idx>=0:self.compound.setCurrentIndex(idx)
        self.protons=spin(r.protons,.000001,10000);form.addRow(tr('Contributing nuclei'),self.protons)
        self.atoms=W.QLineEdit(','.join(map(str,r.atoms)));form.addRow(tr('Atom indices (0-based, comma-separated)'),self.atoms)
        inspect=W.QPushButton(tr('Select / highlight atoms in structure'));inspect.clicked.connect(self.select_atoms);form.addRow(inspect)
        self.group=W.QLineEdit(r.group);form.addRow(tr('Group assignment'),self.group)
        self.refs=W.QListWidget();self.refs.setSelectionMode(W.QAbstractItemView.SelectionMode.MultiSelection);self.refs.setMaximumHeight(80)
        for ref in measurement.rois:
            if ref.role=='standard' and ref.accepted and ref.id!=r.id:
                item=W.QListWidgetItem(ref.signal or ref.id);item.setData(QtCore.Qt.ItemDataRole.UserRole,ref.id);self.refs.addItem(item)
                item.setSelected(ref.id in r.reference_ids)
        form.addRow(tr('Reference signals (none selected = all accepted)'),self.refs)
        self.accepted=W.QCheckBox(tr('Use this resonance for quantification'));self.accepted.setChecked(r.accepted);form.addRow(self.accepted)
        self.reason=W.QLineEdit(r.exclusion_reason);form.addRow(tr('Exclusion reason (optional)'),self.reason)
        self.quality=W.QComboBox();self.quality.setEditable(True);enum_items(self.quality,['Not reviewed','Reviewed — suitable','Overlap suspected','Baseline unstable','Phase concern','Reference values only'],r.quality);form.addRow(tr('Integration quality'),self.quality)
        self.comments=W.QPlainTextEdit(r.comments);self.comments.setMaximumHeight(70);form.addRow(tr('Comments'),self.comments)
        buttons(self,form)
    def populate_compounds(self):
        self.compound.clear()
        if enum_value(self.role)=='standard':
            standard=next((s for s in self.project.standards if s.id==self.sample.standard_id),None)
            if standard:self.compound.addItem(standard.compound.name,standard.compound.id)
            else:self.compound.addItem(tr('Select a standard for the preparation first.'),'')
        else:
            for c in self.project.compounds:self.compound.addItem(c.name,c.id)
            if enum_value(self.role)=='unassigned':self.compound.addItem(tr('Unassigned'),'')
    def chosen_compound(self):
        try:
            if enum_value(self.role)=='standard':return self.project.standard(self.sample.standard_id).compound
            return self.project.compound(self.compound.currentData())
        except StopIteration:raise ValueError(tr('Select a compound or reference material before assigning this ROI.')) from None
    def select_atoms(self):
        try:
            atoms=[int(x) for x in self.atoms.text().split(',') if x.strip()]
            dialog=StructureDialog(self.chosen_compound(),atoms,self)
            if dialog.exec():self.atoms.setText(','.join(map(str,sorted(dialog.atoms))))
        except Exception as exc:error(self,exc)
    def accept(self):
        try:
            r=deepcopy(self.result);r.low,r.high=sorted((self.low.value(),self.high.value()))
            if self.measurement.arrays and r.low==r.high:raise ValueError(tr('ROI boundaries must be different.'))
            r.signal=self.signal.text().strip() or f'{r.low:.3f} ppm';r.role=enum_value(self.role);r.compound_id=self.compound.currentData() or ''
            if r.role!='unassigned' and not r.compound_id:raise ValueError(tr('Select a compound or reference material before assigning this ROI.'))
            r.protons=self.protons.value();r.protons_confirmed=True;r.atoms=sorted(set(int(x) for x in self.atoms.text().split(',') if x.strip()))
            if r.atoms:
                mol=molecule(self.chosen_compound())
                if min(r.atoms)<0 or max(r.atoms)>=mol.GetNumAtoms():raise ValueError(tr('Invalid atom index.'))
            r.group=self.group.text();r.accepted=self.accepted.isChecked();r.exclusion_reason=self.reason.text()
            r.quality=enum_value(self.quality);r.comments=self.comments.toPlainText()
            r.reference_ids=[item.data(QtCore.Qt.ItemDataRole.UserRole) for item in self.refs.selectedItems()]
            self.result=r;super().accept()
        except Exception as exc:error(self,exc)

class ROIDiagnosticsDialog(W.QDialog):
    """Human-readable diagnostics; no change to the stored scientific record."""
    def __init__(self,roi,signal_id='',parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('ROI diagnostics — ')+(signal_id+' / ' if signal_id else '')+roi.signal)
        self.resize(720,680);self.metrics={};outer=W.QVBoxLayout(self)
        subtitle=W.QLabel((signal_id+' · ' if signal_id else '')+roi.signal+' · '+tr(roi.role))
        subtitle.setWordWrap(True);outer.addWidget(subtitle)
        scroll=W.QScrollArea();scroll.setWidgetResizable(True);outer.addWidget(scroll,1)
        content=W.QWidget();body=W.QVBoxLayout(content);scroll.setWidget(content)
        diagnostics=roi.diagnostics or {}
        if diagnostics:
            groups=[(tr('Signal quality'),[
                ('snr_estimate',tr('Estimated S/N'),''),
                ('noise_rms_estimate',tr('Estimated noise RMS'),tr('a.u.')),
                ('noise_source',tr('Noise source'),''),
                ('imaginary_real_rms_ratio',tr('Imaginary/real RMS ratio'),'')]),
                (tr('Baseline and boundary stability'),[
                ('baseline_mean',tr('Mean baseline intensity'),tr('a.u.')),
                ('boundary_step_ppm',tr('Boundary step (ppm)'),''),
                ('boundary_area_change',tr('Boundary area change'),tr('a.u. × ppm')),
                ('boundary_sensitivity_percent',tr('Boundary sensitivity (%)'),'')]),
                (tr('Review flags'),[
                ('mixed_sign',tr('Mixed-sign region'),''),
                ('overlapping_rois',tr('Overlapping ROIs'),'')])]
            for title,rows in groups:
                group=W.QGroupBox(title);form=W.QFormLayout(group);form.setVerticalSpacing(8)
                form.setRowWrapPolicy(W.QFormLayout.RowWrapPolicy.WrapLongRows)
                for key,label,unit in rows:
                    value=self.format_value(diagnostics.get(key))
                    field=W.QLabel(value+(' '+unit if unit and value!=tr('not available') else ''))
                    field.setWordWrap(True);field.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
                    self.metrics[key]=field;form.addRow(label,field)
                body.addWidget(group)
            warning_group=W.QGroupBox(tr('Warnings'));layout=W.QVBoxLayout(warning_group)
            warnings=diagnostics.get('warnings') or []
            if isinstance(warnings,str):warnings=[warnings]
            self.warnings_label=W.QLabel('\n'.join('• '+message(w) for w in warnings) if warnings else tr('No diagnostic warnings.'))
            self.warnings_label.setWordWrap(True)
            if warnings:self.warnings_label.setStyleSheet('color:#fbbf24;')
            layout.addWidget(self.warnings_label);body.addWidget(warning_group)
            if diagnostics.get('note'):
                note=W.QLabel(message(diagnostics['note']));note.setWordWrap(True);body.addWidget(note)
        else:
            note=W.QLabel(tr('No spectral diagnostics are available for this record.'));note.setWordWrap(True);body.addWidget(note)
        body.addStretch()
        note=W.QLabel(tr('No heuristic automatically excludes a resonance. Review the displayed spectrum and record your decision in the ROI editor.'))
        note.setWordWrap(True);outer.addWidget(note)
        close=W.QDialogButtonBox(W.QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject);outer.addWidget(close)

    def format_value(self,value):
        if value is None:return tr('not available')
        if isinstance(value,bool):return enum_label(value)
        if isinstance(value,(int,float)):
            return self.locale().toString(float(value),'g',5) if math.isfinite(value) else tr('not available')
        if isinstance(value,(list,tuple)):return ', '.join(message(v) for v in value) if value else tr('none')
        return message(value)

class CopyTable(W.QTableWidget):
    """Read-only calculated tables with selection copying and a context menu."""
    def __init__(self,headers,parent=None):
        super().__init__(0,len(headers),parent);self.setHorizontalHeaderLabels(headers)
        self.setEditTriggers(W.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(W.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True);self.verticalHeader().hide()
        self.setWordWrap(False)
        self.horizontalHeader().setMinimumSectionSize(75)
        self.setHorizontalScrollMode(W.QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.horizontalHeader().setStretchLastSection(True);self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.menu)
    def fill(self,rows):
        self.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,value in enumerate(row):
                item=W.QTableWidgetItem('' if value is None else f'{value:.7g}' if isinstance(value,float) else str(value))
                item.setToolTip(item.text())
                if isinstance(value,(int,float)):item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.setItem(i,j,item)
        self.resizeColumnsToContents()
    def showEvent(self,event):
        super().showEvent(event)
        # Native Windows font/style metrics settle when a tab is first shown.
        self.resizeColumnsToContents()
    def copy(self):
        indices=self.selectedIndexes()
        if not indices:return
        rows=sorted(set(i.row() for i in indices));cols=sorted(set(i.column() for i in indices))
        text='\n'.join('\t'.join(self.item(r,c).text() if self.item(r,c) else '' for c in cols) for r in rows)
        W.QApplication.clipboard().setText(text)
    def keyPressEvent(self,event):
        if event.matches(QtGui.QKeySequence.StandardKey.Copy):self.copy();event.accept()
        else:super().keyPressEvent(event)
    def menu(self,pos):
        menu=W.QMenu(self);menu.addAction(tr('Copy selected rows'),self.copy);menu.exec(self.viewport().mapToGlobal(pos))
