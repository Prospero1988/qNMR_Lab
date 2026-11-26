# qNMR Lab scientific reports

## Refinements in version 1.0.2

The editable Word equation uses nested normalized-integral fractions and a
symbol-definition table. Sample mass means the total weighed test material;
standard purity is a mass fraction from 0 to 1. The assay calculation is unchanged.

Full spectra are retained. Standard reports add enlargements of clustered
included analyte ROIs, showing boundaries, local IDs and recorded ppm assignments
on descending chemical-shift axes. Zoom intensity scales are independent;
spectral data are not reprocessed.

Use **Project → Resonance correspondence…** to give corresponding ROIs the same
resonance name. Suggested signal names require **Confirm correspondence and save**.
Unambiguous assignments to the same molecular atoms of the same compound are
also supported; group assignments can distinguish resonances on the same atom.
Neither local S IDs nor ppm names alone establish identity. Editing the chemical
structure, ROI bounds, nuclei count or assignment requires reconfirmation.
Correspondence is stored in the portable project without invalidating assay results.

Diagnostics compare each stored resonance assay with the official mean of the
same preparation. Repeat acquisitions are averaged within a preparation, then
preparations receive equal weights. The table shows mean assay, mean deviation
in percentage points, sample SD of deviations (n − 1), and independent-preparation
count. A resonance must be represented in every included acquisition of a given
preparation. Missing data are not imputed; excluded, stale and nonindependent
preparations do not increase n.

The preparation mean contains the tested resonance, making deviations dependent
and partially attenuated. No significance test or assay correction is performed.
For n < 3, direction is not classified as persistent; SD is undefined at n = 1.
Plots require at least two resonances sharing at least two independent preparations.
Pairwise observations require a consistent direction in at least three shared
preparations. No chemical explanation or signal-suitability decision is inferred.

Bundle export records diagnostics in `traceability.json` (report format 3),
separately from unchanged assay results.

The default **Word report** presents the analytical summary, chemical records
and structures, methodology, preparations, signal selection, individual results,
statistics and observations. Technical identifiers and data provenance appear
in appendices.

Choose **Extended technical Word report** in the export dialog for detailed
processing tables, ROI bounds/integrals, quality metrics, atom assignments,
parameter-change history and enlarged spectral regions. Both profiles use the
same stored results. Export does not process spectra, recalculate assays or
alter inclusion/exclusion decisions.

Documents use A4, Word paragraph styles, a running header, page numbers,
repeated table headers and captioned figures. The assay equation uses true
fractions and subscripts. Chemical drawings preserve stereochemistry, charges
and disconnected counterions.

Numbers are formatted for reading with decimal commas in PL and points in ENG.
Assay, SD and RSD normally use three decimal places, distinguishing relative
percentages from percentage points. Small/large quantities can use × 10 with
superscript exponents. The model retains its original precision. Acquisition
and processing parameters are compared before rounding so real differences
are not silently described as a common methodology.

Signal-selection tables group bounds with identical four-decimal presentation.
Acquisition columns retain local signal IDs. Smaller differences remain in the
project and JSON; the extended profile provides detailed bounds. Grouping is a
display convention and never changes integration intervals or calculations.

Observations describe stored signal variation, exclusions and warnings. They
do not exclude signals automatically or assign unsupported chemical causes.
Historical results are clearly identified. Nonindependent observations do not
increase the number of independent preparations.

**Complete bundle** additionally retains CSV, XLSX and `traceability.json` with
full data precision, profile name and report-format version. DOCX supports human
review; JSON and the self-contained project preserve exact machine-readable
records. Reports default to the `reports` folder.
