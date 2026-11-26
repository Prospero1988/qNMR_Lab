# Software verification and scope

## Release 1.0.2

The local suite passed **154 tests**, including 21 resonance-diagnostic cases.
Two private-workbook checks are optional on GitHub. Coverage includes explicit
correspondence without invalidating stored results, no matching by local S IDs
or ppm alone, molecular atom assignments, ambiguity, exclusions, stale results,
missing identity, incomplete/unequal repeats, n = 0/1/2 and separate analytes.
Diagnostic SD uses n − 1 without significance testing. Figures preserve descending
ppm axes and unchanged spectral arrays.

The local reference project retained exactly 14,996 existing numerical values,
model fields, assay results, sample means, SD, RSD and confidence intervals.
Spectral-array and calculation-engine source hashes were identical. Confirmed
correspondence was added separately; the original project and report were preserved.
PL/ENG reports were rendered through Word → PDF → PNG and visually inspected.
Private laboratory data and documents are not distributed.

## Report generator 1.0.1

Public suite: **131 passed, 2 skipped** for the optional private workbook.
New checks cover number/unit formatting, both languages/profiles, no raw
dictionary/JSON prose, missing/nested values, exclusions, historical results,
independent preparation counts, A4, tables, captions, links and structures.
Model snapshots and spectral-array hashes remain identical. A local
three-preparation report was compared with its original DOCX in 238 numeric/state
checks, accounting for original printed rounding. Documents are rendered through
Word → PDF → PNG for layout review; private source documents stay off GitHub.

## Public release 1.0

Executed public suite: **112 passed, 2 skipped**. The skipped cases require the
optional private workbook. See validation/test_results.txt for the captured run.

This document distinguishes software verification from laboratory-method
validation. Release 1.0 packages the current application, operating manuals,
synthetic examples and reproducible public tests. It does not certify acquisition
conditions or a quantitative laboratory method. Application version and the
calculation convention are both 1.0.0 for this first public release.

## Reproducible checks

The public suite tests complex JDF import, parameter/header handling, FFT and
apodization, zero filling, phase and pivot conventions, baseline processing and
fractional-boundary signed integration. Frozen synthetic engine outputs are in
validation/engine_golden.npz. These permit regression checks without an external
DOSY Lab installation or access to the original authoring machine.

Chemistry tests exercise structures, molecular weights, salts, manually supplied
mass provenance and atom selections. Quantification tests use independently
calculated expected values and explicit mass/purity units, including invalid
inputs, negative integrals, reference selection and result freshness.

Hierarchical statistics are tested with three preparations whose means are
90, 100 and 110 and which have 2, 1 and 3 acquisitions. Their combined mean is
100, sample SD is 10 and n is 3. Another substance receives its own result.
Exclusions, missing/stale results and the minimum-three completeness rule are
checked separately. Repeated acquisitions do not become independent samples.

Qt tests cover ROI creation/editing/splitting, optional exclusion reasons,
implicit acceptance of entered nuclei counts, live processing, deletion,
relative calibration, appearance settings, PL/ENG switching and default folders.
Storage tests reopen self-contained projects after source files are removed.
Export checks reopen DOCX and XLSX and compare numeric results and traceability.

## Examples and optional local comparisons

The distributed three-preparation analysis and its JDF files are synthetic.
They exercise processing and the end-to-end workflow; they are not laboratory
measurements or evidence of a validated assay. Finite integration boundaries
produce a mean near the nominal 95 percent rather than a forced exact answer.

Two tests comparing an optional local reference workbook are skipped when
validation/reference/qNMR.xlsx is absent. Private workbooks, research reports,
their extracted data and local source-repository manifests are not distributed.
The complete local development suite previously passed 114 tests. The current
public-suite output is recorded in validation/test_results.txt; skipped private
fixtures must not be described as executed public verification.

## Visual and deployment checks

README images show the running application on synthetic data in Polish and
English. They cover the spectrum with integral IDs/values, aggregate results
and preparation statistics. Rendering tests are complemented by visual inspection.
Offscreen Qt tests do not establish every native mouse/window-manager behavior.

The small deployment contains runtime sources, manuals, examples and licenses,
with a file-hash manifest and archive checksum. The extracted copy is checked
for import, portable projects, language switching, calculations and deletion.
Dependencies are installed on the first run rather than embedded in the archive.

## Limits

Relaxation, quantitative signal equivalence, overlap, baseline suitability and
the weighed chemical form remain analyst decisions. Heuristic diagnostics do
not prove validity. SD/SEM/confidence intervals describe observed variation and
are not a complete uncertainty budget. Original laboratory FID reproduction,
all network/proxy failures and fresh installation without Python have not been
established by these tests. See the scientific methods and deployment manuals.
