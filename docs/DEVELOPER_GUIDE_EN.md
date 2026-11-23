# Developer guide

## Workflow simplification in 1.0

Saving ROIDialog accepts the entered nuclei count. `protons_confirmed` is
retained for old projects/fingerprints, but a legacy False value no longer
blocks calculations. The assay function still validates positive finite counts.
ROI exclusion reasons are optional; preparation/acquisition exclusion rules are separate.

The .2f integral format affects presentation only. `reports_directory()` creates
the default report export folder. Deployment includes `reports/.gitkeep`.

## Record management and substance results in 1.0

`project_edit.py` provides `deletion_details` and `delete_record`. Preparation
and acquisition deletion removes model records, never external files. Chemical
or reference-material deletion clears dependent assignments. Reference-material
IDs are distinct from chemical IDs: deleting one batch does not change samples
assigned to another batch of the same compound. No substitute is selected silently.

The GUI guards processing, confirms dependencies, closes deleted tabs and
updates the first-acquisition processing source. Tree UserRole data are
normalized to tuples after Qt QVariantList conversion.

`project_summary(project, analyte_id=...)` scopes the existing hierarchy to one
substance. `substance_summaries` adds n >= 3 workflow completeness without
changing assay equations or the calculation fingerprint version. `StatisticsPanel`
selects a substance; GUI and DOCX/XLSX exports expose separate results. Tests
cover unequal repeat counts, multiple substances, deletion and language switching.

## Presentation in version 1.0

`spectrum_settings.py` owns appearance preferences and their preview editor.
Preferences use per-user QSettings, independently of processing parameters,
project data and calculation fingerprints. `PhaseWindow` shares that model.
`ROIDiagnosticsDialog` and `StatisticsPanel` format existing records without
recalculating or modifying scientific inputs.


## Interaction in version 1.0

Live processing uses one worker, a 75 ms debounce and request generations:
superseded results cannot commit. Controls remain active. Dataset/ROI commits
are atomic, while assay calculation, export and save wait for pending requests.

The phase window owns an explicit language from its parent. Referencing moves
axis, ROIs, masks and pivot together. Processing copying uses the target FID
and records the source measurement ID. `Measurement.roi_labels` and
`next_roi_number` provide stable display IDs while UUIDs retain reference
identity. `integration_reference_id/value` control relative presentation.
Display labels/scales do not enter the quantitative fingerprint. Added fields
default when reading old projects; the calculation convention remains 1.0.0.
Ordinary `load_project()` does not access original files; `verify_sources=True`
is an optional explicit audit. `projects_directory()` provides the Open/Save
default folder. Tests remove all source JDFs and reprocess embedded FIDs.


## Localization and compatibility in 1.0

`qnmr/i18n.py` controls presentation language and Qt standard-dialog translation;
`qnmr/_catalog.py` holds the reviewed Polish catalog. Polish is the default;
QSettings remembers a button selection, and `QNMR_LAB_LANGUAGE` can override it
for one launch. The launcher exposes this as `-Language pl|en`.

Translate display labels only. Combo boxes keep canonical roles and quality
values in userData. File export routing uses extensions from the selected filter.
Language changes rebuild widgets around the same domain objects, preserving
open tabs, active ROI, ranges, pending controls and project freshness. No
calculation is triggered. Translate cached diagnostics only when displaying them.
CSV/JSON schemas remain stable; DOCX/XLSX captions use the current language.

Application version is 1.0; the unchanged numerical fingerprint convention
remains `CALCULATION_VERSION = '1.0.0'`. Older calculated demonstration projects
therefore stay current. `tests/test_i18n.py` checks state, canonical enums,
report values, default/preference behavior and both-language manuals.


[Wersja polska](DEVELOPER_GUIDE_PL.md)

## Environment and commands

Use Windows x64 and CPython 3.12. Application entry point is `python -m qnmr` from
the project root; `Start_qNMR_Lab.bat` wraps `tools/bootstrap.ps1`. Runtime
dependencies and transitives are pinned in `requirements-lock.txt`. The shorter
`requirements.txt` records direct dependencies. Development adds pytest.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools\create_demo.py
```


## Module boundaries

| Module | Responsibility |
|---|---|
| `models.py` | Project, compound, reference material, preparation, acquisition and ROI dataclasses. |
| `jeol.py` | Conventional 1D raw JDF parsing and metadata/filter-delay model. |
| `processing.py` | Immutable spectral numerical pipeline and signed interpolation/trapezoid integration. |
| `analysis.py` | Measurement/processing bridge, diagnostics, template copying and alignment proposals. |
| `chemistry.py` | RDKit parsing, sanitization, average MW, formula and depictions. |
| `quantification.py` | Unit-aware assay, fingerprints, accepted-signal aggregation and hierarchical statistics. |
| `storage.py` | Versioned ZIP project archive, hashes, array payloads and reference libraries. |
| `excel_reference.py` | Supplied workbook-layout inspection/import and cached-output comparison. |
| `reports.py` | DOCX/XLSX/CSV/PNG/JSON exports from explicit calculations. |
| `dialogs.py` | Validated chemical/preparation/ROI editors and structure selection. |
| `gui.py` | Main window, acquisition workspaces, processing worker and explicit user actions. |
| `spectrum_view.py`, `phase_window.py` | Adapted DOSY Lab navigation and cached phase preview. |

Scientific modules do not import GUI classes. Report plotting uses Matplotlib
Agg without Qt or an interactive backend. Molecular depictions use RDKit Cairo
or SVG. Processing returns new immutable arrays; the GUI commits them only
after successful processing and ROI validation. Pending calculations are not
exported as completed results.

## Native project schema 1

A `.qnmr` is a ZIP containing `project.json` and an NPZ per sample/acquisition.
The JSON envelope records application/version, the complete serializable domain
model and SHA256 for each NPZ payload. Arrays include original FID, ppm,
pre-baseline phased spectrum, fitted baseline and corrected complex spectrum.
NPZ loads use `allow_pickle=False`; archive contents are never extracted to
arbitrary filesystem paths. Saving writes a temporary sibling and atomically
replaces the target.

Unknown schema versions fail explicitly. Changing schema requires a deliberate
migration; do not reinterpret missing old scientific options using new automatic
defaults. Ordinary project opening never probes source availability. Explicit
`verify_sources=True` enables source auditing; relinking requires an exact SHA256
match. Embedded FIDs are used for all project reprocessing.

The calculation fingerprint contains compound data, selected reference material,
sample inputs, current options, ROI definitions/areas/diagnostics, processed
spectrum hash and reference compatibility. A changed fingerprint retains the
old result snapshot and makes it ineligible for current final statistics.
Project source relocation alone does not reprocess data. The JSON stores no
automatic remote account or shared DOSY settings.

## Tests

- Reader fixtures cover both byte orders and float32/float64 section order,
  malformed metadata/payloads and a genuine copied 1H JDF.
- Processing tests cover exact FFT/window, ZF, phase/pivot, digital-filter support,
  baseline preview/commit, fractional bounds, signed areas and atomic failures.
- Frozen conventional spectra in `validation/engine_golden.npz` were produced
  from read-only original source; independent regression does not import it.
- Quantification tests cover hand calculations, explicit percent conversion,
  units, negative areas, confirmed protons, multiple references, freshness,
  exclusions and preparation/acquisition distinctions.
- All reference workbook signal/water outputs are compared to independent engine
  calculations. Descriptive between-preparation statistics deliberately differ
  from legacy pooled population formulas.
- Offscreen Qt tests exercise real widgets, dialogs, phase cancellation, workers,
  ROI updates, imports, clipboard definitions, results and reopening.
- Export tests reopen DOCX/XLSX/CSV/JSON and verify numerical content and images.
- Launcher tests prepare/check the environment, verify cache reuse and are
  supplemented by an isolated first-run trial in a path containing spaces.

Offscreen tests do not establish native window-manager behavior or usability.
Native smoke/visual checks and unperformed tests belong in `VALIDATION_EN.md`.


## Public releases

Public source is hosted at https://github.com/Prospero1988/qNMR_Lab. Original
local history and private laboratory materials are not distributed. Public
examples are synthetic; local workbook comparisons are optional. Check PL/ENG,
Windows tests and a freshly extracted deployment before release. CONTRIBUTING.md
contains environment, test and package-building commands.
