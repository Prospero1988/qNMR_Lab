"""Explicit analyst confirmation of diagnostic correspondence, separate from ROIs."""
from collections import defaultdict
from PySide6 import QtCore, QtWidgets as W
from .i18n import tr
from .resonance_consistency import confirm_correspondence, identities


class ResonanceCorrespondenceDialog(W.QDialog):
    def __init__(self, project, parent=None):
        super().__init__(parent);self.project=project;self.result=None
        self.setWindowTitle(tr('Resonance correspondence'));self.resize(1050,630)
        layout=W.QVBoxLayout(self)
        note=W.QLabel(tr('Enter the same resonance name only for corresponding analyte signals. Atom assignments are used automatically when unambiguous. Local S IDs and chemical shifts alone do not establish identity. Confirming saves diagnostic correspondence without changing assay results. Empty names are not compared.'))
        note.setWordWrap(True);layout.addWidget(note)
        self.table=W.QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels([tr('Substance'),tr('Preparation'),tr('Acquisition'),tr('Signal'),tr('¹H count'),tr('Confirmed resonance name')])
        self.entries=[];mapping=identities(project)
        for sample in project.samples:
            for measurement in sample.measurements:
                for roi in measurement.rois:
                    if roi.role!='analyte' or roi.compound_id!=sample.analyte_id:continue
                    row=self.table.rowCount();self.table.insertRow(row)
                    match=mapping.get((measurement.id,roi.id))
                    name=match[1] if match and match[0][0]=='confirmed' else ''
                    values=[project.compound(sample.analyte_id).name,sample.name,measurement.name,
                            measurement.roi_label(roi)+' / '+roi.signal,str(roi.protons),name]
                    for col,value in enumerate(values):
                        item=W.QTableWidgetItem(value)
                        if col!=5:item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                        self.table.setItem(row,col,item)
                    self.entries.append((sample,measurement,roi))
        self.table.horizontalHeader().setSectionResizeMode(W.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5,W.QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        suggest=W.QPushButton(tr('Suggest names from current signal names'))
        suggest.clicked.connect(self.suggest);layout.addWidget(suggest)
        buttons=W.QDialogButtonBox(W.QDialogButtonBox.StandardButton.Ok|W.QDialogButtonBox.StandardButton.Cancel)
        buttons.button(W.QDialogButtonBox.StandardButton.Ok).setText(tr('Confirm correspondence and save'))
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)

    def suggest(self):
        for row,(_,_,roi) in enumerate(self.entries):
            if not self.table.item(row,5).text().strip():self.table.item(row,5).setText(roi.signal)

    def accept(self):
        groups=defaultdict(list)
        for row,(sample,measurement,roi) in enumerate(self.entries):
            name=self.table.item(row,5).text().strip()
            if name:groups[(sample.analyte_id,name)].append((measurement.id,roi.id))
        try:self.result=confirm_correspondence(self.project,[dict(label=name,members=members) for (_,name),members in groups.items()])
        except (ValueError,KeyError) as exc:
            W.QMessageBox.warning(self,tr('Resonance correspondence'),tr(str(exc)));return
        super().accept()
