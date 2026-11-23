"""Capture README images from the running Qt app using only synthetic data."""
from pathlib import Path
import os
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6 import QtGui,QtWidgets as W
from qnmr.gui import MainWindow
from qnmr.i18n import set_language
from qnmr.storage import load_project

def main():
    app=W.QApplication([])
    for name in ('segoeui.ttf','seguisb.ttf','segoeuib.ttf','arial.ttf'):
        path=Path('C:/Windows/Fonts')/name
        if path.is_file():QtGui.QFontDatabase.addApplicationFont(str(path))
    app.setFont(QtGui.QFont('Segoe UI',10))
    output=ROOT/'docs/images';output.mkdir(exist_ok=True)
    for code in ('pl','en'):
        set_language(code)
        project,_=load_project(ROOT/'examples/synthetic_three_samples.qnmr')
        window=MainWindow(project);window.replace_project(project)
        window.resize(1480,960);window.show();app.processEvents()
        if code=='pl':
            workspace=window.current_workspace()
            workspace.m.integration_reference_id=workspace.m.rois[0].id
            workspace.m.integration_reference_value=1
            workspace.refresh_table();workspace.view.setXRange(2.8,8.4,padding=.02)
            app.processEvents();window.grab().save(str(output/'spectrum-pl.png'))
            window.pages.setCurrentIndex(1);app.processEvents()
            window.grab().save(str(output/'results-pl.png'))
        else:
            window.show_substance_statistics(project.compounds[0].id);app.processEvents()
            window.grab().save(str(output/'statistics-en.png'))
        window.dirty=False;window.close();app.processEvents()
    print(output)

if __name__=='__main__':main()
