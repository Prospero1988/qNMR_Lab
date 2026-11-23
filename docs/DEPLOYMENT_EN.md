# qNMR Lab 1.0.1 PL/ENG — deployment on another computer

## Default report location

Reports default to `reports` beside the application; another folder can be
selected. Projects continue to default to `projects`.

## Changes in this package

Release **1.0.1** includes the complete redesigned DOCX generator: scientific A4
layout, structures, quantitative equation, results and statistics tables,
figures and optional technical profile. Reports follow the selected PL/ENG
language. See `docs/REPORTS_EN.md` and `docs/REPORTS_PL.md` in the package.
Use **Export report** in the application; no additional scripts are required.

The package also lets you delete records from the left panel, use the substance → preparation → acquisition
tree and review each substance's combined result and statistics. Complete
status requires at least three independent preparations; repeat acquisitions
do not increase n. PL and ENG manuals explain the complete workflow.

## New controls and portable projects

Version 1.0 adds live processing, mouse-editable baseline regions, click-based
ppm referencing, Z/P/F/I/R/M/D shortcuts, spectrum IDs/integral values, relative
integral calibration, ROI copying and processing copying from a sample's first
acquisition. Open/Save default to `projects`. One `.qnmr` is sufficient for
reopening and reanalysis; original spectra are not required.


[Polska instrukcja wdrożenia](DEPLOYMENT_PL.md)

1. Extract the **entire** `qNMR_Lab` folder, for example to `C:\qNMR_Lab`.
   Do not launch the application directly inside WinRAR.
2. Double-click `Start_qNMR_Lab.bat`.
3. The first launch creates `.venv` and installs pinned dependencies. Internet
   access is required. Subsequent launches reuse that environment.

Requirements: Windows x64 and CPython 3.12 x64. DOSY Lab and the author's D:/J:
drives are not needed. If Python is absent, the launcher provides the official
download page. Optionally run `Start_qNMR_Lab.bat -InstallLocalPython` to download
a signature-verified installer and install a project-local interpreter. This
option has not been tested on a Python-free computer and does not change existing
installations. Bootstrap messages accept `-Language pl` or `-Language en`.

## PL / ENG

Polish is the default. The **PL → ENG** button at the top right switches to
English; **ENG → PL** switches back. The choice is remembered. Switching preserves
the project, data, calculated results, open tabs and zoom. Analyst-entered names
and comments are not automatically translated.

Manuals and scientific methods are provided in both languages in `docs`.
**Help → User manual** opens the current language. DOCX/XLSX reports and plot
captions use the language active at export. Technical JSON keys and CSV headers
remain stable across languages.

## Quick check

- **Project → Open synthetic example**: calculations for three samples.
- **Open → examples/synthetic_three_samples.qnmr**: three synthetic spectra with ROIs.
- **Import JDF → examples/synthetic_P01.jdf** (or P02/P03): raw FID import.
- English manual: `docs/USER_MANUAL_EN.md`; Polish: `docs/USER_MANUAL_PL.md`.

Only conventional raw complex 1D JEOL JDF is supported. `.jjh5` is not supported.
Synthetic examples are not laboratory results. The statistical difference from
the source report is explained in `docs/EXCEL_COMPARISON_EN.md` and its PL version.

The archive includes the application, launcher, instructions, licenses, small
synthetic examples. It excludes `.venv`, Git history, caches, tests
and development reports. Full validation evidence remains in the source
repository. The manifest records the source revision and checksums. Qt, RDKit,
NumPy and SciPy will occupy hundreds of MB or more after installation: the small
RAR is not a single self-contained EXE.
