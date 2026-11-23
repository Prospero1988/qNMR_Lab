# Workbook comparison guide

## Scope and data availability

The public application can import a local reference workbook in the supported
layout. This is a numerical comparison path, not an alternative way of reading
an arbitrary workbook or reconstructing a raw NMR acquisition. The original
private research documents are not distributed. A user supplies their own local
workbook and chooses one study sheet; different analytes are never pooled.

## Quantitative equation

Assay percent = (analyte integral / standard integral) × (standard nuclei /
analyte nuclei) × (analyte molecular weight / standard molecular weight) ×
(standard mass / analyte mass) × standard purity fraction × 100.

Use masses in the same units and the actual weighed chemical forms. Purity
expressed in percent is converted to a fraction exactly once. A molecular-weight
override needs provenance; a generic chemical name is insufficient to distinguish
salts, hydrates and solvates. An integral normalized to a one-proton standard
reference is a reference value, not a raw signed area with known ppm boundaries.

## Supported layout

The importer follows the specific row/column structure implemented in
qnmr/excel_reference.py. It reads preparation IDs and masses, analyte/standard
molecular weights, reference purity and signal-specific integral/proton factors.
Review that layout before adapting another workbook. Import selects one sheet
and creates preparation and reference-integral records with source provenance.
No FID, phase, baseline model or original integration boundaries can be inferred
from normalized integral ratios alone. Such missing data remain explicitly absent.

## Independent numerical checks

Compare each accepted analyte/reference pair before comparing aggregate values.
For a simple synthetic case, equal molecular weights and masses, unit purity,
one contributing nucleus on each side and an integral ratio of 0.95 produce
95 percent assay. Changing the nuclei ratio or purity should scale that answer
once, according to the equation above. Never tune processing to match a target.

Average accepted signals within an acquisition and acquisitions within their
physical preparation. Then average independent preparation means with equal
weights. For preparation means 90, 100 and 110, mean = 100, sample SD = 10 and
n = 3, even if acquisition counts differ. A population SD of pooled signals is
a different quantity and should not be substituted for between-preparation SD.

## Regression evidence and limits

The public tests cover hand-calculated assay cases and unequal repeat counts.
Two optional tests exercise the original local workbook when it is placed at
validation/reference/qNMR.xlsx; otherwise they skip. Do not commit that folder.
Public synthetic examples exercise the spectrum workflow separately.

Agreement with a workbook checks arithmetic and data mapping. It does not prove
appropriate relaxation, absence of overlap, quantitative signal equivalence,
correct baselines or a complete measurement uncertainty budget. Those require
independent experimental and analyst review. See SCIENTIFIC_METHODS_EN.md and
VALIDATION_EN.md for the statistical hierarchy and stated verification scope.
