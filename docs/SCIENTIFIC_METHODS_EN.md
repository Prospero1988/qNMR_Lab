# Scientific methods

## Nuclei entry from 1.0

The entered nuclei count is used without an extra confirmation checkbox.
Legacy flags do not block calculations. The analyst still chooses an appropriate
count for the assigned resonance; the application validates positive finite
values. Signal exclusion reasons are optional. Two-decimal integral presentation
does not change assay calculation precision.

## Substance result and minimum preparation count

The final result belongs to one substance assigned to independently prepared
samples. Their preparation means receive equal weights regardless of repeat
acquisition counts. Different substances have separate results. Measuring the
same physical sample again is not an independent preparation and does not increase n.

Interface version 1.0 requires at least three independent preparations with
current results for all included acquisitions for complete status. This is a
workflow condition, not a new statistical equation or evidence of method
validation. At n = 2, available SD, SEM and Student intervals remain descriptive
outputs and the result is preliminary. Calculation convention remains 1.0.0.

## 1.0 — relative integrals and referencing

Relative display integration is `I_i × V_ref / I_ref`, with a positive
reference. Raw signed areas are never overwritten. Presentation scaling does
not alter qNMR ratios or proton counts. Split children require reviewed proton
assignments. Ppm referencing moves all coordinates together, preserving trace
intensities and phase. Parameter edits still require explicit assay recalculation.


## Language and numerical version

Application 1.0 provides Polish and English presentation. The calculation
convention remains 1.0.0. Language switching never changes arrays, integral
signs, nuclei, masses, purity, calculations or stored fingerprints. Numeric
exports retain the same values; report captions follow the current language.


[Wersja polska](SCIENTIFIC_METHODS_PL.md)

## Conventional 1D processing

The source of numerical conventions is DOSY Lab's conventional one-dimensional
engine. Adaptation excludes all diffusion calculations and dedicated
presaturation artifact/solvent-tail terms. Original raw data remain immutable.

JEOL complex FID is reconstructed as section 0 minus $i$ times section 1. Header
sections, precision, byte order, valid ranges, parameter units and declared file
length are checked. The file SHA256 is recorded. Only a single conventional
proton FID is accepted; neither multidimensional data nor `.jjh5` are unpacked.

For sampling rate $SW$ Hz and $t_j=j/SW$, the apodization window is

$$w(t)=\exp(-\pi LBt)\exp\left[-\frac{(\pi GBt)^2}{4\ln2}\right].$$

The FFT uses NumPy `fft`, zero filling by an integer factor 1, 2, 4 or 8, and
`fftshift`. No per-signal amplitude normalization is applied. The ppm axis is

$$\delta=\delta_{offset}+f/\nu_0+\Delta\delta,$$

where $\nu_0$ is the proton frequency in MHz and $f$ is the shifted frequency in
Hz. A metadata-supported filter crop preserves the original full-SW phase
convention. When a known raw JEOL orders/factors cascade is supported, its
linear-phase delay is modeled in samples. Other acquisitions receive no guessed
universal delay, and there is no vendor-equivalence claim.

With full acquired width $W=SW/\nu_0$ in ppm and carrier
$c=\delta_{offset}+\Delta\delta$, the phase is

$$\phi(\delta)=\frac{\pi}{180}\left[360d\frac{\delta-c}{W}
+PH0+PH1\frac{\delta-p}{W}\right].$$

The spectrum is multiplied by $\exp(i\phi)$. Moving pivot $p$ to $p'$ re-expresses
$PH0'=PH0+PH1(p'-p)/W$ so the phase function remains unchanged. PH0 and PH1 then
remain deliberate manual adjustments. Coarse initial PH0 uses coherent peaks
only when the original supported-delay workflow allows it; it is editable and
does not establish quantitative phase quality.

## Baseline and integration

Baseline correction fits a Legendre polynomial of degree 1–5 to only the
analyst-selected background points. The full ppm span maps to $[-1,1]$.
Coefficients use the original NumPy least-squares algorithm, with minimum-point
and condition-number checks. Baseline preview and committed subtraction are
distinct. Committed masks cannot cross quantitative ROIs. No solvent-specific
tail model or presaturation correction is present.

For corrected real spectrum $s(\delta)=\Re[z(\delta)]-b(\delta)$, the area is

$$I=\int_{\delta_l}^{\delta_h}s(\delta)\,d\delta.$$

The implementation sorts the axis, validates strict monotonicity and ROI extent,
inserts linearly interpolated intensities at fractional boundaries, and applies
the trapezoidal rule. Integration is signed, relative to mathematical zero. It
does not take absolute intensities, remove an endpoint-to-endpoint line, or
normalize peaks independently. At least two acquired/processed grid points are
required in an ROI. Display gain, zoom and pan never modify numerical data.

## Internal-standard assay

For accepted target and IS signals,

$$P_A=\frac{I_A}{I_{IS}}\frac{N_{IS}}{N_A}
\frac{MW_A}{MW_{IS}}\frac{m_{IS}}{m_A}P_{IS}.$$

The final assay is $100P_A$ in % w/w. Standard purity is stored as a fraction;
the GUI accepts certified purity in % w/w and converts it explicitly. Masses
retain their input unit and convert consistently to mg. Numerically, g/mol
equals mg/mmol, so

$$n_{IS}[\mathrm{mmol}]=m_{IS}[\mathrm{mg}]P_{IS}/MW_{IS}$$

and the proton-normalized area ratio yields target mmol and target mass. Every
intermediate ratio, amount and mass is retained in pairwise results. Zero IS
integral is invalid. Negative integrals remain signed and produce review warnings.

Molecular weights describe the entire weighed chemical form. RDKit calculates
average molar mass and formula for every explicitly entered fragment. It does
not know unentered solvent/stoichiometry. Manual MW or override requires an
explanation/provenance. Atom linkage records an analyst assignment and never
infers chemical equivalence or the number of contributing protons.

Multiple accepted IS resonances require either specific per-target reference
selection or explicit compatibility confirmation. Pairwise assay estimates are
averaged equally for each target resonance only after that confirmation. Raw
areas are unchanged. No automatic overlap rejection, outlier rejection,
water subtraction or mass-balance correction is applied.

## Hierarchy and statistical unit

For an acquisition, accepted analyte resonance estimates are averaged equally.
For one physical preparation, acquisition-level means are averaged equally.
Each independent preparation then contributes one value $x_j$ to final results.
Different analytes are not pooled. The source of this statistical unit is the
preparation identifier and independent flag, not the number of signal rows.

$$\bar{x}=\frac1n\sum_jx_j,\qquad
s=\sqrt{\frac{\sum_j(x_j-\bar{x})^2}{n-1}}.$$

$$RSD=100s/|\bar{x}|,\qquad SEM=s/\sqrt{n}.$$

An optional descriptive confidence interval uses
$\bar{x}\pm t_{(1+c)/2,n-1}SEM$. It assumes independent preparation-level
observations and a suitable approximately normal sampling model. With n=1, SD,
RSD, SEM and CI are unavailable. RSD is unavailable for zero mean.

Within-acquisition resonance variation and between-acquisition variation within
one preparation are reported descriptively. No inferential SEM or CI is assigned
to those correlated observations. SD/SEM are not a complete measurement
uncertainty budget: balance, purity certification, relaxation, chemical form,
overlap, baseline and other systematic components need separate assessment.

Excluded resonances/acquisitions/preparations remain stored with reasons.
Included preparations with any missing or stale included-acquisition result are
omitted from the current summary and trigger a provisional status. Historical
results are retained and labeled; opening a project never silently reprocesses.

## Diagnostics

Noise is estimated from robust first differences in selected baseline regions,
or approximately from the whole spectrum if insufficient manual background is
available. Estimated S/N compares local maximum absolute amplitude to this noise.
Apodization and spectral correlations affect that estimate. Mean background,
imaginary/real RMS ratio and mixed-sign points are displayed for review.

Boundary sensitivity expands/contracts the ROI by one local grid step and
compares signed areas. ROI overlap detects intersecting assigned intervals; it
does not resolve chemically overlapping peaks. All thresholds are heuristic
warnings. None is a scientific acceptance criterion or automatic exclusion.

Peak alignment compares local absolute maxima within ±0.04 ppm by default. It
proposes interval translations and never changes ROIs before analyst confirmation.

## Traceability and limitations

Projects preserve source SHA256, embedded acquired and processed arrays,
processing settings/history, molecule provenance, reference-material data,
assignment/exclusion state and fingerprinted result snapshots. A checksum checks
identity, not scientific suitability. It is not a tamper-proof electronic
signature, validated audit system or regulatory approval workflow.

Calculation validation against the supplied examples is documented separately
in [EXCEL_COMPARISON_EN.md](EXCEL_COMPARISON_EN.md). Original vendor raw assay spectra
were not supplied in JDF, so their original integrations cannot be reconstructed
from normalized Excel ratios or report images.
