# Software and scientific attribution

qNMR Lab adapts conventional one-dimensional processing from **DOSY Lab**,
Copyright (c) 2026 Prospero1988, MIT License. The complete original notice is
preserved in `licenses/DOSY_Lab_MIT.txt` and `LICENSE`.

The original MIT notice is included in licenses/DOSY_Lab_MIT.txt.
The public application runs independently of the original DOSY Lab installation.
Only synthetic JDF fixtures are distributed in this repository.

Adapted functions:

| qNMR module | Original source | Adaptation |
|---|---|---|
| `jeol.py` | `bin/jeol.py` | Preserved 1D section order, parameter units, raw sign, hashing and filter-delay inference; removed multidimensional and all diffusion metadata calculations. |
| `processing.py` | `bin/core.py` | Preserved apodization, ZF/FFT, ppm, phase, Legendre least squares and interpolated signed trapezoidal integration; retained only conventional baseline terms. |
| `spectrum_view.py` | `bin/spectrum_view.py` | Reused display-only gain, navigation and selection/phase gestures. |
| `phase_window.py` | `bin/phase_window.py`, `spectrum_settings.py` | Adapted cached phase preview and pivot re-expression to a single 1D acquisition. |
| `spectrum_settings.py` | `bin/spectrum_settings.py` | Adapted per-user line color/width and grid preferences, with live preview and cancel restoration. |
| Test JDF encoder | `bin/generate_demo.py` | Reused parameter/header conventions for ordinary 1D fixtures. |

Core dependencies retain their own licenses. The installed distributions contain
their original license files. Notable licenses include PySide6/Qt
LGPL-3.0/GPL/commercial alternatives, RDKit BSD, NumPy/SciPy BSD, pyqtgraph MIT,
openpyxl MIT, python-docx MIT and Matplotlib's project license. Dependencies are
dynamically imported from the local environment and are not bundled as a native
executable or modified. See [Qt licensing](https://doc.qt.io/qtforpython-6/licenses.html)
and [RDKit source](https://github.com/rdkit/rdkit).

Private laboratory workbooks, reports and source manifests are not part of
the public source or release assets. Synthetic examples are supplied for
software demonstration and testing, not as laboratory-method validation.
