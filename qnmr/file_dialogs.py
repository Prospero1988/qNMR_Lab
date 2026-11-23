"""Readable file-dialog tools on the application's dark background."""
from functools import lru_cache
from PySide6 import QtCore,QtGui,QtWidgets as W
from PySide6.QtSvg import QSvgRenderer

_SHAPES={
    'backButton':'<path d="M11 5 4 12l7 7M4 12h16"/>',
    'forwardButton':'<path d="m13 5 7 7-7 7M20 12H4"/>',
    'toParentButton':'<path d="m5 11 7-7 7 7M12 4v16"/>',
    'newFolderButton':'<path d="M3 8V5h6l3 3h9v12H3zM15 11v6m-3-3h6"/>',
    'listModeButton':'<rect x="3" y="4" width="3" height="3"/><rect x="3" y="10" width="3" height="3"/><rect x="3" y="16" width="3" height="3"/><path d="M10 5.5h11M10 11.5h11M10 17.5h11"/>',
    'detailModeButton':'<rect x="3" y="4" width="18" height="16"/><path d="M9 4v16M3 9h18M3 14h18"/>',
}

@lru_cache(maxsize=6)
def _icon(name):
    icon=QtGui.QIcon()
    for mode,color in ((QtGui.QIcon.Mode.Normal,'#dce5f2'),(QtGui.QIcon.Mode.Disabled,'#71839a')):
        svg=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
             f'fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
             f'stroke-linejoin="round">{_SHAPES[name]}</svg>').encode()
        renderer=QSvgRenderer(svg)
        for ratio in (1,2,3):
            pixmap=QtGui.QPixmap(24*ratio,24*ratio);pixmap.setDevicePixelRatio(ratio)
            pixmap.fill(QtCore.Qt.GlobalColor.transparent)
            painter=QtGui.QPainter(pixmap);renderer.render(painter,QtCore.QRectF(0,0,24,24));painter.end()
            icon.addPixmap(pixmap,mode)
    return icon

class _FileDialogStyler(QtCore.QObject):
    def eventFilter(self,watched,event):
        if event.type()==QtCore.QEvent.Type.Show and isinstance(watched,W.QFileDialog):
            for name in _SHAPES:
                button=watched.findChild(W.QToolButton,name)
                if button is None:continue
                # General text-button padding otherwise squeezes Qt's 16 px
                # system icons into only a few pixels of the available width.
                button.setStyleSheet('QToolButton { padding: 4px; min-width: 24px; min-height: 24px; }')
                button.setIcon(_icon(name));button.setIconSize(QtCore.QSize(24,24))
        return super().eventFilter(watched,event)

def configure_file_dialogs(app):
    if not hasattr(app,'_qnmr_file_dialog_styler'):
        app._qnmr_file_dialog_styler=_FileDialogStyler(app)
        app.installEventFilter(app._qnmr_file_dialog_styler)
