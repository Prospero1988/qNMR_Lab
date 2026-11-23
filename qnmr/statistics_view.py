"""Readable presentation of the existing preparation-level statistics."""
import math
from PySide6 import QtCore,QtWidgets as W
from .dialogs import CopyTable
from .i18n import tr,message,enum_label
from .quantification import project_summary

class StatisticsPanel(W.QScrollArea):
    substance_selected=QtCore.Signal(str)
    def __init__(self,parent=None):
        super().__init__(parent);self.setWidgetResizable(True)
        content=W.QWidget();self.setWidget(content);layout=W.QVBoxLayout(content)
        self._project=None;self.current_summary=None
        choose=W.QHBoxLayout();choose.addWidget(W.QLabel(tr('Substance')))
        self.analyte_selector=W.QComboBox();choose.addWidget(self.analyte_selector,1);layout.addLayout(choose)
        guide=W.QLabel(tr('Signals → acquisition → independent preparation → substance result. Each independent preparation has equal weight; repeated acquisitions do not increase n.'))
        guide.setWordWrap(True);layout.addWidget(guide)
        self.status=W.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.summary_group=W.QGroupBox(tr('Between-preparation statistics'));grid=W.QGridLayout(self.summary_group)
        self.metrics={};self.ci_caption=W.QLabel()
        fields=[('n',tr('Independent preparations')),('mean',tr('Mean assay (% w/w)')),
                ('sd',tr('Sample SD (percentage points)')),('rsd_percent','RSD (%)'),
                ('sem',tr('SEM (percentage points)')),('ci',self.ci_caption)]
        for index,(key,caption) in enumerate(fields):
            row=index//2;column=(index%2)*2
            label=caption if isinstance(caption,W.QLabel) else W.QLabel(caption)
            label.setWordWrap(True);grid.addWidget(label,row,column)
            value=W.QLabel();value.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            self.metrics[key]=value;grid.addWidget(value,row,column+1)
        layout.addWidget(self.summary_group)
        self.small_sample_note=W.QLabel(tr('SD, SEM and confidence intervals require at least two independent preparations.'))
        self.small_sample_note.setWordWrap(True);layout.addWidget(self.small_sample_note)
        self.three_sample_note=W.QLabel(tr('The substance result is preliminary until at least three independent preparations have current results.'))
        self.three_sample_note.setWordWrap(True);layout.addWidget(self.three_sample_note)
        layout.addWidget(W.QLabel(tr('Preparation results')))
        self.preparations=CopyTable([tr('Preparation'),tr('Assay (% w/w)'),tr('Acquisitions'),tr('Independent'),tr('SD across acquisitions (pp)')])
        self.preparations.setMinimumHeight(130);self.preparations.setMaximumHeight(250);layout.addWidget(self.preparations)
        self.components_heading=W.QLabel(tr('Statistics by component'))
        layout.addWidget(self.components_heading)
        self.components=CopyTable([tr('Component'),'n',tr('Mean (% w/w)'),tr('SD (pp)'),'RSD (%)',tr('SEM (pp)'),tr('Confidence interval (% w/w)')])
        self.components.setMinimumHeight(130);self.components.setMaximumHeight(250);layout.addWidget(self.components)
        self.omissions=W.QLabel();self.omissions.setWordWrap(True);layout.addWidget(self.omissions)
        self.note=W.QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
        layout.addStretch()
        self.analyte_selector.currentIndexChanged.connect(self.selection_changed)

    def number(self,value):
        if value is None or not math.isfinite(value):return tr('not available')
        return self.locale().toString(float(value),'g',6)

    def interval(self,values):
        if values is None:return tr('not available')
        return self.number(values[0])+' — '+self.number(values[1])

    def set_summary(self,project,summary):
        self._project=project;selected=self.analyte_selector.currentData()
        keys=list(dict.fromkeys(s.analyte_id for s in project.samples if s.analyte_id))
        with QtCore.QSignalBlocker(self.analyte_selector):
            self.analyte_selector.clear()
            for key in keys:
                compound=next((c for c in project.compounds if c.id==key),None)
                if compound:self.analyte_selector.addItem(compound.name,key)
            if not self.analyte_selector.count():self.analyte_selector.addItem(tr('No assigned substances'),'')
            index=self.analyte_selector.findData(selected)
            if index>=0:self.analyte_selector.setCurrentIndex(index)
        self.analyte_selector.setEnabled(bool(keys));self.render_current()
    def select_substance(self,key):
        index=self.analyte_selector.findData(key)
        if index>=0:self.analyte_selector.setCurrentIndex(index)
    def selection_changed(self,*args):
        if self._project is None:return
        self.render_current();self.substance_selected.emit(self.analyte_selector.currentData() or '')
    def render_current(self):
        project=self._project;key=self.analyte_selector.currentData()
        summary=project_summary(project,analyte_id=key or None);self.current_summary=summary
        between=summary['between'];rows=summary['samples']
        name=self.analyte_selector.currentText()
        self.summary_group.setTitle(tr('Substance result: {p0}',p0=name) if key else tr('Between-preparation statistics'))
        self.status.setText(tr('No current calculated results. Complete the assignments and use Calculate.') if not rows
            else tr('Provisional results — review omitted samples below.') if summary['provisional']
            else tr('Combined substance result: {p0} independent preparations.',p0=between['n']))
        self.ci_caption.setText(tr('Confidence interval ({p0:g}%)',p0=100*between['confidence']))
        for key,field in self.metrics.items():
            field.setText(str(between['n']) if key=='n' else self.interval(between['ci']) if key=='ci' else self.number(between[key]))
        self.small_sample_note.setVisible(between['n']<2 and len(summary['between_by_analyte'])<=1)
        self.three_sample_note.setVisible(bool(rows) and between['n']<3)
        self.preparations.fill([[row['name'],self.number(row['assay_percent']),row['acquisitions'],enum_label(row['independent']),
            self.number(row['acquisition_statistics']['sd'])] for row in rows])
        component_rows=[]
        for key,values in summary['components'].items():
            try:name=project.compound(key).name
            except StopIteration:name=key
            component_rows.append([name,values['n'],self.number(values['mean']),self.number(values['sd']),
                self.number(values['rsd_percent']),self.number(values['sem']),self.interval(values['ci'])])
        self.components.fill(component_rows);self.components.setVisible(bool(component_rows));self.components_heading.setVisible(bool(component_rows))
        notes=[]
        if summary['omitted']:notes.append(tr('Omitted samples')+':\n'+'\n'.join('• '+message(row) for row in summary['omitted']))
        if summary['excluded']:notes.append(tr('Excluded samples')+':\n'+'\n'.join('• '+message(row) for row in summary['excluded']))
        self.omissions.setText('\n\n'.join(notes));self.omissions.setVisible(bool(notes))
        self.note.setText(message(summary['note']))
