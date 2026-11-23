from pathlib import Path
from copy import deepcopy
import hashlib
from unittest.mock import patch
import numpy as np
from PySide6 import QtWidgets as W
from qnmr.gui import MainWindow
from qnmr.storage import load_project,save_project,projects_directory
from qnmr.analysis import reprocess
from qnmr.quantification import is_current,project_summary,calculate_project

ROOT=Path(__file__).resolve().parents[1]

def test_project_remains_complete_after_all_original_jdfs_are_removed(tmp_path):
    project,_=load_project(ROOT/'examples/synthetic_three_samples.qnmr')
    for sample in project.samples:
        for m in sample.measurements:
            source=tmp_path/Path(m.source_path).name;source.write_bytes((ROOT/'examples'/source.name).read_bytes())
            m.source_path=str(source)
            assert hashlib.sha256(source.read_bytes()).hexdigest()==m.source_sha256
    before=deepcopy(project_summary(project));archive=tmp_path/'complete.qnmr';save_project(project,archive)
    for source in tmp_path.glob('*.jdf'):source.unlink()
    # Even a source-existence probe is forbidden during ordinary project open.
    with patch.object(Path,'is_file',side_effect=AssertionError('Unexpected external source access')):
        restored,warnings=load_project(archive)
    assert not warnings and project_summary(restored)==before
    assert restored.compounds==project.compounds and restored.standards==project.standards
    for old_sample,sample in zip(project.samples,restored.samples):
        for old,m in zip(old_sample.measurements,sample.measurements):
            assert is_current(restored,sample,m) and m.options==old.options and m.rois==old.rois
            for key,value in old.arrays.items():np.testing.assert_array_equal(m.arrays[key],value)
            expected=m.arrays['spectrum'].copy()
            reprocess(m,m.options);np.testing.assert_array_equal(m.arrays['spectrum'],expected)
    assert not calculate_project(restored)
    np.testing.assert_allclose(project_summary(restored)['between']['mean'],before['between']['mean'])

def test_open_and_save_dialogs_start_in_projects_folder(app,project,tmp_path):
    folder=tmp_path/'projects';folder.mkdir();window=MainWindow(project)
    with patch('qnmr.gui.projects_directory',return_value=folder):
        with patch.object(W.QFileDialog,'getOpenFileName',return_value=('','')) as dialog:
            window.open_project();assert Path(dialog.call_args.args[2])==folder
        with patch.object(W.QFileDialog,'getSaveFileName',return_value=('','')) as dialog:
            window.save_as();assert Path(dialog.call_args.args[2])==folder/'analysis.qnmr'
        window.path=tmp_path/'elsewhere'/'named.qnmr'
        with patch.object(W.QFileDialog,'getSaveFileName',return_value=('','')) as dialog:
            window.save_as();assert Path(dialog.call_args.args[2])==folder/'named.qnmr'
    assert projects_directory()==ROOT/'projects' and projects_directory().is_dir()
    window.close()
