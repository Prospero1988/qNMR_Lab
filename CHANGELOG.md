# Changelog

## 1.0.2 — 2026-11-26

- Expanded the editable Word equation with normalized-integral fractions and
  explicit definitions, including total weighed sample mass and fractional purity.
- Retained full spectra and added enlargements of clustered quantitative ROIs.
- Added descriptive resonance consistency tables and assay/deviation plots using
  independent preparations with equal weights, without changing assay calculations.
- Added Project → Resonance correspondence for explicit analyst confirmation.
  Unambiguous molecular atom assignments are also supported; local S IDs and ppm
  names alone never establish identity. Correspondence is portable and requires
  reconfirmation after changes to the chemical structure or ROI assignment.
- Added regression coverage for incomplete acquisitions, missing assignments,
  exclusions, unequal repeats, nonindependent samples and small sample counts.
- Report format is 3; calculation convention remains 1.0.0. Reporting and diagnostics
  preserve stored results, sample statistics and spectral arrays.

## 1.0.1 — 2026-11-23

Scientific report redesign integrated into the application.

- Redesigned A4 DOCX reports: identification, executive summary, balanced
  structures, common/differing methodology, sample preparation, Office Math
  equation, consolidated signal matrix, per-preparation results, statistics
  and factual observations, with traceability appendices.
- Centralized PL/ENG scientific number/date/unit formatting, superscript
  notation, readable diagnostics, repeatable table headers and page numbers.
- Added optional extended technical reports and selected-region enlargements;
  retained full-precision machine records in bundle JSON.
- Reporting consumes stored results without processing, recalculation or changes
  to molecular records, integrals, inclusion decisions or independent sample counts.
- Added report-format, localization, missing-data, export and read-only regression tests.

## 1.0 — 2026-11-23

First public release / Pierwsze wydanie publiczne. Application version: 1.0.0.

- PL/ENG interface and manuals, Polish default; reports follow the selected language.
- Conventional JEOL 1D proton NMR import and live processing, interactive phase,
  baseline regions, ppm calibration and signed integration.
- Stable signal IDs, relative calibration, two-decimal integral presentation,
  ROI copy/edit/split/delete, nuclei entry without an extra checkbox and optional exclusion reasons.
- Substance/preparation/acquisition hierarchy, equal preparation weights and
  separate substance statistics with at least three preparations for complete status.
- Self-contained projects, default projects/reports folders and DOCX/XLSX/CSV exports.
- Spectrum appearance controls and formatted diagnostics/statistics.
- Synthetic examples, screenshots, tests, MIT license and retained DOSY attribution.

This release incorporates the previously tested local development iterations.
Calculation convention remains 1.0.0. Private laboratory documents and local
development history are not part of the public distribution.
