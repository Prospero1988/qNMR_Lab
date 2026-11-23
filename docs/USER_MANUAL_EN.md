# qNMR Lab user manual

## Redesigned scientific reports

The default **Word report** uses A4 with an executive summary, methodology,
structures, results and traceability appendices. The export dialog also offers
**Extended technical Word report**, adding complete ROI diagnostics, settings,
parameter history and enlarged spectral regions. Export does not change the
calculation model. See [Scientific reports](REPORTS_EN.md).

## Simpler ROI editing and report folder

Spectrum and table integrals show two decimal places. This is display formatting:
project data and calculations retain full precision. XLSX stores full numbers
with a 0.00 integral-cell format; CSV retains source precision.

Enter **Contributing nuclei** and save the ROI. No separate proton-count
confirmation is required, including for older projects with a legacy confirmation
flag. Counts must still be positive and appropriate for the resonance.
Review assignments and counts before using pasted or split ROIs.

After clearing **Use this resonance for quantification**, **Exclusion reason
(optional)** can remain blank. The signal stays in the project.

**Export report** defaults to **reports** beside the application. Another folder
can be selected. This applies to DOCX, XLSX, CSV and complete report bundles.

## Substance, independent preparation and acquisition

The left panel groups records as **substance → independent preparation → acquisition**.
For one compound, create at least three separately prepared samples assigned
to the same substance. To measure the same solution again, select its
preparation and use **Repeat acquisition**. Adding a preparation uses the
selected substance as its default assignment.

After **Calculate**, **Combined results by substance** shows each substance's
n, mean, SD, RSD, SEM and confidence interval. Double-click a row to open its
statistics, use the **Statistics** substance selector, or choose the substance
statistics action in the left-panel context menu. DOCX and XLSX contain the
same separate substance results.

Signals are averaged within an acquisition, repeat acquisitions within their
preparation, then independent preparation means are averaged with equal weights.
Different repeat counts do not change those weights. Three preparations with
2, 1 and 3 acquisitions give **n = 3**, not 6. Different substances are not pooled.

**Complete (at least 3 preparations)** requires at least three independent
preparations and current results for every included acquisition. At n = 2,
available statistics are still displayed but the result remains preliminary.
Missing or stale acquisitions require review and recalculation. Data completeness
does not constitute laboratory method approval.

## Deleting project records

Select an item on the left and use **Delete selected item**, the context menu,
or **Delete** while the tree has focus. Confirmation explains the effect.
Deleting a preparation also removes its acquisitions; deleting an acquisition
removes its embedded data, ROIs and results from the project. External source
files remain on disk. Save the project to retain the deletion.

Deleting a substance or reference material preserves spectra and clears the
corresponding preparation and ROI assignments. Preparations without a substance
appear in a separate group. Assign the correct chemical/reference material,
review signals and recalculate. To retain a record while omitting it from
calculations, use exclusion with a reason in its editor instead of deletion.

## Readable diagnostics and statistics

**ROI diagnostics** groups signal quality, baseline/boundary stability and
review flags. Numbers use up to five significant digits with units; missing
values, Yes/No flags and warnings are readable text. Full-precision source
records remain unchanged.

**Statistics** shows n, mean, SD, RSD, SEM and confidence intervals, preparation
results and component statistics. It explains missing results, n < 2 and
omitted/excluded preparations. Displaying historical records does not make
them current results.


## Copying ROIs

**Copy ROI definitions** copies all regions to the clipboard in the six-column
format accepted by **Paste ROI rows**: signal name, low boundary, high boundary,
canonical role, nuclei, compound ID. Open the target spectrum and paste. The
table context menu can copy selected definitions only. Ordinary Ctrl+C still
copies displayed table cells. Pasted ROIs receive fresh IDs; review their assignments
and proton counts. Processing settings are copied separately.


## Spectrum shortcuts and integral labels

| Key | Action |
|---|---|
| Z | Zoom ppm range |
| P | Pan spectrum |
| F | Full spectrum |
| I | Draw an integral with the mouse |
| R | Remove selected integral |
| M | Modify integral boundaries interactively |
| D | Split: drag an integral edge inward and release at the cut |

Shortcuts act on the active spectrum and do not delete ROIs while typing in
input controls. Double-click the plot to show the full spectrum.

Each ROI has a stable **S1, S2, S3…** ID on the plot and in the first table
column. Deleting a region never renumbers the others. Split children receive
new IDs; review assignments and enter the correct proton counts for each part.

Only the numeric integral value is shown beside its region. Calibration status
is shown below the spectrum. To normalize, select a signal
in the table or click its region, enter e.g. **1** in **Set selected integral to**
and click **Calibrate relative integrals**. Other values are
`I_i × reference value / I_ref`. Reprocessing retains the assigned reference
value and updates the other relative integrals. **Reset relative calibration**
restores raw display values. A missing/deleted reference never silently selects
another signal.

The **Signed area** column always retains raw areas. Relative display calibration
does not change qNMR assay inputs, proton counts or calculated assays. IDs and
relative calibration are preserved in the project.


## PL / ENG language button

Polish is the default on a new installation. Use **PL → ENG** at the top right
to switch to English and **ENG → PL** to return to Polish. The choice is saved.
Switching preserves the project, calculated results, open spectra, selected ROI,
zoom and pending processing controls. Names and analyst-entered comments retain
their original text. **Help → User manual** opens the selected language.

DOCX/XLSX reports and plot captions follow the language selected at export time.
CSV headers and JSON/project identifiers remain canonical for interoperability.
The launcher accepts `-Language pl` or `-Language en` to choose the startup
language explicitly; otherwise the application restores the remembered choice.


[Wersja polska](USER_MANUAL_PL.md)

## Installation and launch

Open `Start_qNMR_Lab.bat`. The launcher requires CPython 3.12 x64, creates `.venv`,
installs `requirements-lock.txt`, checks Qt/RDKit and starts the application.
Subsequent launches verify imports and versions without network installation.
`-PrepareOnly` prepares without opening a window; `-CheckOnly` verifies an
already prepared environment. An incompatible existing `.venv` is reported and
left intact. Rename that project-local folder before rebuilding it.

When offline, an existing verified environment still launches. A new environment
can be prepared from pip's cache if every required wheel is available; otherwise
installation stops with a network/dependency error. No system Python is modified.

## Project and chemical identity

Use **Project → Project details** to record the study name, purpose, analyst,
comments and confidence level. The project panel separates compounds, reference
materials and independently prepared samples.

Select **Analyte → Edit selected**, or double-click a row on **Structures and
standards**. Enter the name and identifier. Paste SMILES and choose **Parse
SMILES / calculate MW**, or load a MOL/SDF. For an SDF with multiple molecules,
choose the required record. Parsing sanitizes valence and charges. Disconnected
fragments such as counterions are retained in formula/MW calculations.

Record the chemical form actually weighed. Check counterion stoichiometry,
hydration and solvation. A neutral parent molecule may not describe the sample.
Manual MW is allowed without a structure, but requires a source/provenance and
an explanation. An override of the RDKit-calculated MW also requires a reason.
MW is the average molar mass in g/mol, not monoisotopic exact mass.

Double-click a compound or its thumbnail to inspect the larger structure. Click
numbered atoms to select/highlight them, use the wheel to zoom, and drag to pan.
Atom indices start at zero. Export PNG or SVG from this viewer. Molecular graph
symmetry is never treated as proof of NMR chemical equivalence.

## Internal standards

Edit the example thymol material or choose **Standards → Add reference material**.
Record the actual certified purity as **% w/w**, certificate, batch, material ID,
expiry, signals/protons, notes and validation status. A material's compound has
its own structure/MW editor. The purity value 99.57% describes only the supplied
example, not every thymol batch.

Use **Standards → Export standard library** to reuse materials in another
project, and **Import standard library** to load them. Libraries are local JSON
files. Changing a sample's standard invalidates old results; existing ROI
compound assignments must be reviewed and reassigned explicitly.

## Preparations and acquisitions

**Add sample** creates an independent preparation record. Select analyte/IS,
enter both weighed masses with their common unit (mg, g or ug), solvent,
preparation date and notes. A sample can be excluded with a recorded reason.
Only preparations marked independent contribute to the final n.

**Import JDF** accepts several conventional proton FIDs. Each prompts for its
preparation record. For a second acquisition of the same physical preparation,
select that preparation and use **Repeat acquisition**. It appears as another
child under the same sample and does not increase n. A sample without a spectrum
remains visible and is reported as incomplete rather than silently counted.

Only conventional raw complex 1D JDF is supported. For a `.jjh5` JEOL project,
export the conventional 1H raw FID as `.jdf` using the vendor software. No vendor
software or original DOSY Lab installation is needed by qNMR Lab.

## Processing and calibration

Use **Appearance…** above the spectrum or **Spectra → Spectrum appearance…**
to choose the main line color, width (0.5–6 px) and grid visibility. Preview
updates immediately. **Save** remembers per-user preferences and **Cancel**
restores the previous appearance. Settings apply to current/new spectra,
phasing and comparisons without changing data, boundaries, integrals or assays.

Each open acquisition has a spectrum tab. **Processing controls** exposes LB,
Gaussian FWHM, zero filling, PH0, PH1, pivot, interactive ppm referencing, filter-delay
samples and digital-filter cropping. Parameter edits automatically update the
spectrum in a worker, without an Apply button. Rapid edits are combined and the
latest request wins. Invalid settings leave the previous valid dataset intact.
Assay results still require the explicit **Calculate** action.

For later acquisitions of the same sample, **Copy processing from first
acquisition** applies the first acquisition's settings to the target's own FID.
The baseline mask/state and ppm calibration are included. Target ROI coordinates
move with the axis when the copied calibration changes.

The initial supported JEOL delay model and coarse PH0 seed are visible and
editable. Unsupported metadata does not trigger a guessed delay. Manual phase
and chemical shift calibration must be reviewed against appropriate references.

**Phase** opens cached phase preview. Left/right vertical drags change PH0/PH1;
Shift allows finer movement. The pivot tool moves the phase coordinate origin
while re-expressing PH0 so the existing phase function is preserved. Apply once
or cancel without altering the project. Baseline subtraction is not part of the
phase preview.

For interactive calibration, enter **Reference target (ppm)**, enable **Set
reference on spectrum** and click the reference peak. The clicked point receives
the requested ppm value. Axis, ROIs, baseline regions and phase pivot move
together. FID, intensities and the existing phase function are preserved.
There is no manual calibration-shift entry field.

## Baseline

Click **Baseline…** and drag across signal-free background. Blue regions can
be moved or resized using their edges. Right-click a region to remove it.
The fit updates automatically when regions or polynomial degree change. The
preview displays the fitted Legendre polynomial in yellow on the uncorrected
spectrum; it has not yet been subtracted. Choose degree 1–5 and inspect the
preview before **Apply baseline subtraction**. The corrected real spectrum is
cyan by default and its mathematically corrected zero is shown as a dashed horizontal line.

Edit exact background intervals with **Enter baseline ranges…**. Committed masks
cannot intersect integration ROIs. The fit rejects too few points and unstable
designs. Extrapolated quantitative regions should be reviewed. Ordinary baseline
correction is available; no presaturation or solvent-tail correction is present.

## Quantitative ROIs

Default left dragging zooms ppm. The wheel changes display gain without changing
data/integrals. Middle dragging pans. Select **Add quantitative ROI**, then drag
an interval. Enter signal identifier, role, compound, contributing nuclei,
optional atoms/groups, review status and comments. Saving the entered
proton count suffices. Structure atoms can be highlighted from the ROI editor, but the
analyst determines how many nuclei contribute to that resonance.

Select **Edit ROI boundaries** to activate handles. In zoom mode they cannot
steal ordinary zoom gestures. Double-click an ROI table row to edit exact limits
and assignments. Exclude unsuitable resonances with an optional reason; the ROI
and its signed integral stay in the project. Delete removes the definition and
records an audit event. Missing/deleted assigned IS signals cause a calculation
error instead of silently choosing a substitute.

Roles are analyte, standard, water, solvent, impurity, other and unassigned.
Additional quantified components require a compound record with verified MW.
Unassigned signals can remain in the project without contributing to assays.

**Paste ROI rows** accepts tab-separated `signal`, `low ppm`, `high ppm`, `role`,
`nuclei`, optionally `compound ID`. Review pasted counts and assignments; no separate confirmation is required.
For example:

```text
Analyte CH2	5.01	5.10	analyte	2
IS aromatic	6.47	6.55	standard	1
```

Input text boxes support normal clipboard paste. Tables support row selection,
Ctrl+C and a copy context menu. Calculated cells are read-only; edit the source
assignment/preparation rather than overwriting a calculated result.

## Reference signals, ratios and QC

At least one accepted IS and analyte signal is needed. An analyte ROI can select
one or more specific IS ROIs in its editor. An empty selection means all accepted
IS signals. If more than one is used, explicitly confirm their compatibility in
the acquisition workspace. Otherwise calculation stops. Pairwise intermediate
calculations remain visible; the accepted references are averaged with equal
weight for that resonance.

Signed measured areas are preserved. The displayed area/nucleus and molar ratios
do not modify them. No endpoint-intensity subtraction or separate analyte peak
normalization is performed. Negative/mixed-sign signals generate warnings and
can still be inspected and deliberately retained. A zero IS denominator is a
mathematical error.

**ROI diagnostics** shows noise/SNR estimates, baseline-region mean, ROI overlap,
imaginary/real RMS ratio, mixed signs and sensitivity to a one-grid-step boundary
change. These are review aids. An imaginary component is not by itself proof of
incorrect phase; absence of a warning does not establish absence of overlap.
Warnings never automatically reject a resonance.

## Comparing spectra and templates

Switch acquisition tabs or use **Spectra → Compare side by side**. The comparison
shares ppm axes and retains independent intensity scales. **Synchronize ppm
axes** links open analytical tabs. ROI templates can be copied to another
acquisition with the same analyte and standard; replacement requires confirmation.

**Propose peak alignment** matches local absolute maxima within ±0.04 ppm and
shows the suggested shift for each interval. Confirm before applying, then review
the target spectrum. This simple maximum search can match an impurity or overlap;
it does not establish chemical identity. Boundaries remain independently editable.

## Results and statistics

Choose **Calculate** (F5) after review. For each accepted analyte resonance, qNMR
Lab calculates every selected analyte/IS pair, then an explicitly compatible
reference average. Accepted analyte resonances are averaged within the acquisition.
Repeated acquisitions are averaged within their physical preparation. Independent
preparation means receive equal weight in final statistics.

**Results** shows pairwise ratios, mmol, analyte mass and assay. **Statistics**
shows preparation means, sample SD (ddof=1), RSD, SEM and a Student-t confidence
interval. Within-acquisition SD describes resonance variation; no inferential
SEM/CI is reported for correlated resonances or repeated acquisitions. Multiple
analytes are not pooled; select their separate summaries in Statistics.

Changes to measured inputs or numerical settings mark old results historical.
They remain stored, but are excluded from current final statistics until explicit
recalculation. Included preparations with missing/stale measurements cause a
provisional summary. Excluded preparations retain their reason and history.

## Storage and exports

Save a `.qnmr` archive with Ctrl+S. It stores structures, standards, masses,
source SHA256, embedded FID and processed arrays, processing history, ROI/atom
assignments, exclusions and calculated snapshots. Reopening does not silently
reprocess. Both Open and Save default to **projects** beside the application;
the file dialog still allows another folder.

The project is self-contained: one `.qnmr` is sufficient to reopen, reprocess
and analyze its embedded acquisitions. Original JDFs, source folders, network
drives and the author's computer are not required. Ordinary open does not even
probe source availability. Stored paths and SHA256 are provenance only.
Optional **Relink original source** accepts only a matching SHA256 file.

**Export report** offers DOCX, XLSX, CSV and a complete bundle. The bundle includes
the report, tables, numerical integrals, spectrum PNGs and JSON traceability.
The spectrum's **Export spectrum** button offers PNG or all processed spectral
values as CSV. Structure PNG/SVG export is in its viewer.

Reports label historical/stale results and provisional summaries. Analyst names
come from the project only; no signatures, approvals, accreditation, relaxation
validation or outlier conclusions are invented. DOCX export does not need Word
or LibreOffice installed. Integrated PDF export is not implemented.

## Synthetic example and workbook import

**Project → Open synthetic example** opens three preparations with embedded
FIDs, processing, ROIs and current results. These are simulated training/test
data, not laboratory measurements. Open the project in examples or import its
three synthetic JDFs individually to practice the complete workflow.

**Import reference workbook** accepts a local workbook in the documented
layout and one study per project. Integral ratios cannot reconstruct raw FIDs.
Private comparison workbooks and reports are not included in the public
distribution. See [EXCEL_COMPARISON_EN.md](EXCEL_COMPARISON_EN.md).
