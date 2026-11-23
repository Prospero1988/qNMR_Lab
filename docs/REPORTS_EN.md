# qNMR Lab scientific reports

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
