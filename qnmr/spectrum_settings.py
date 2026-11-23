"""Per-user display settings adapted from DOSY Lab (MIT; THIRD_PARTY.md)."""
from dataclasses import dataclass
from PySide6 import QtCore,QtGui,QtWidgets as W
import pyqtgraph as pg
from .i18n import tr

@dataclass(frozen=True)
class SpectrumAppearance:
    color: str = '#67e8f9'
    width: float = 1.3
    grid: bool = True

    @classmethod
    def load(cls,settings):
        default=cls();color=QtGui.QColor(settings.value('spectrum/color',default.color,type=str))
        width=settings.value('spectrum/width',default.width,type=float)
        grid=settings.value('spectrum/grid',default.grid,type=bool)
        return cls(color.name() if color.isValid() else default.color,
                   width if .5<=width<=6 else default.width,grid)

    def save(self,settings):
        settings.setValue('spectrum/color',self.color);settings.setValue('spectrum/width',self.width)
        settings.setValue('spectrum/grid',self.grid);settings.sync()

    def pen(self,color=None,style=QtCore.Qt.PenStyle.SolidLine):
        return pg.mkPen(color or self.color,width=self.width,style=style)

    def apply_grid(self,plot):
        plot.showGrid(x=self.grid,y=self.grid,alpha=.15)

class SpectrumSettingsDialog(W.QDialog):
    changed=QtCore.Signal(object)
    def __init__(self,appearance,parent=None):
        super().__init__(parent);self.setWindowTitle(tr('Spectrum appearance'));self.resize(430,260)
        self.color=appearance.color;form=W.QFormLayout(self)
        self.color_button=W.QPushButton();self.color_button.setIconSize(QtCore.QSize(28,18))
        self.color_button.clicked.connect(self.choose_color);self.show_color()
        form.addRow(tr('Main line color'),self.color_button)
        self.width=W.QDoubleSpinBox();self.width.setRange(.5,6);self.width.setDecimals(1)
        self.width.setSingleStep(.1);self.width.setSuffix(' px');self.width.setValue(appearance.width)
        form.addRow(tr('Line width'),self.width)
        self.grid=W.QCheckBox(tr('Show grid'));self.grid.setChecked(appearance.grid);form.addRow(self.grid)
        note=W.QLabel(tr('Preview updates immediately. Save remembers these display settings; Cancel restores the previous appearance.'))
        note.setWordWrap(True);form.addRow(note)
        bar=W.QDialogButtonBox(W.QDialogButtonBox.StandardButton.Save|W.QDialogButtonBox.StandardButton.Cancel)
        bar.button(W.QDialogButtonBox.StandardButton.Save).setText(tr('Save'))
        bar.button(W.QDialogButtonBox.StandardButton.Cancel).setText(tr('Cancel'))
        bar.accepted.connect(self.accept);bar.rejected.connect(self.reject);form.addRow(bar)
        self.width.valueChanged.connect(self.preview);self.grid.toggled.connect(self.preview)

    def show_color(self):
        swatch=QtGui.QPixmap(28,18);swatch.fill(QtGui.QColor(self.color))
        self.color_button.setIcon(QtGui.QIcon(swatch));self.color_button.setText(self.color)

    def choose_color(self):
        selected=W.QColorDialog.getColor(QtGui.QColor(self.color),self,tr('Spectrum color'),
            W.QColorDialog.ColorDialogOption.DontUseNativeDialog)
        if selected.isValid():self.color=selected.name();self.show_color();self.preview()

    def appearance(self):return SpectrumAppearance(self.color,self.width.value(),self.grid.isChecked())
    def preview(self,*args):self.changed.emit(self.appearance())
