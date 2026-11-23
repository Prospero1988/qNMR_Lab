"""Conventional 1D processing extracted from DOSY Lab. See THIRD_PARTY.md."""
from dataclasses import dataclass
from copy import deepcopy
import numpy as np
from scipy.integrate import trapezoid
from scipy.signal import find_peaks
from .jeol import RawData

def baseline_mask(ppm, regions):
    mask = np.zeros(len(ppm), bool)
    for lo, hi in regions:
        lo, hi = sorted((lo, hi))
        mask |= (ppm >= lo) & (ppm <= hi)
    return mask

def baseline_fit(ppm, real, regions, degree, reference=0, per_layer=True):
    mask = baseline_mask(ppm, regions)
    if np.count_nonzero(mask) < degree + 2:
        raise ValueError('Wskaż więcej punktów bazowych; potrzeba co najmniej rząd+2.')
    span = np.ptp(ppm)
    if span <= 0:
        raise ValueError('Zerowa szerokość osi ppm.')
    x = 2 * (ppm - (ppm.min() + ppm.max()) / 2) / span
    full = np.polynomial.legendre.legvander(x, degree)
    if np.count_nonzero(mask) <= full.shape[1]:
        raise ValueError('Wskaż więcej punktów bazowych; liczba punktów musi przewyższać liczbę parametrów.')
    design = full[mask]
    condition = float(np.linalg.cond(design))
    if not np.isfinite(condition) or condition > 10000000000.0:
        raise ValueError('Niestabilna baza: rozmieść obszary szerzej po widmie.')
    if per_layer:
        coeff = np.linalg.lstsq(design, real[:, mask].T, rcond=None)[0].T
    else:
        one = np.linalg.lstsq(design, real[reference, mask], rcond=None)[0]
        coeff = np.repeat(one[None, :], len(real), axis=0)
    diagnostics = dict(condition=condition, points=int(mask.sum()), coefficients=coeff.tolist(), fit_range_ppm=(float(ppm[mask].min()), float(ppm[mask].max())))
    return (coeff @ full.T, diagnostics)

def default_options(raw):
    return dict(lb_Hz=0.,gaussian_FWHM_Hz=0.,zero_fill_factor=1,
                phase0_deg=0.,phase1_deg=0.,pivot_ppm=raw.metadata['offset_ppm'],
                ppm_shift=0.,reference_layer=0,crop_filter=True,filter_delay_samples=0.,
                baseline_enabled=False,baseline_preview=True,baseline_degree=1,
                baseline_per_layer=True,baseline_regions=[])


def validate_options(options,nlayers=None):
    o=deepcopy(options)
    # Older projects already contain their full manual phase ramp.
    o.setdefault('filter_delay_samples',0.)
    o.setdefault('baseline_degree',1)
    o.setdefault('baseline_per_layer',True)
    for k in ('lb_Hz','gaussian_FWHM_Hz','phase0_deg','phase1_deg','pivot_ppm','ppm_shift','filter_delay_samples'):
        if not np.isfinite(float(o[k])):raise ValueError('Nieprawidłowy parametr '+k)
        o[k]=float(o[k])
    if min(o['lb_Hz'],o['gaussian_FWHM_Hz'])<0:raise ValueError('LB i szerokość Gaussa muszą być nieujemne.')
    if not 0<=o['filter_delay_samples']<=250:raise ValueError('Opóźnienie filtra musi być w zakresie 0–250 próbek.')
    for k,allowed in [('zero_fill_factor',(1,2,4,8)),('baseline_degree',(1,2,3,4,5))]:
        if o[k] not in allowed:raise ValueError('Nieprawidłowy parametr '+k)
    ref=o['reference_layer']
    if not isinstance(ref,int) or ref<0 or (nlayers is not None and ref>=nlayers):raise ValueError('Nieprawidłowa warstwa referencyjna.')
    for key in ('crop_filter','baseline_enabled','baseline_preview','baseline_per_layer'):
        if not isinstance(o[key],bool):raise ValueError('Nieprawidłowa flaga '+key)
    if o['baseline_enabled']:
        o['baseline_per_layer']=True
    for region in o['baseline_regions']:
        if len(region)!=2 or not np.isfinite(region).all() or region[0]==region[1]:raise ValueError('Nieprawidłowy obszar bazy.')
    return o


@dataclass
class Dataset:
    raw: RawData
    ppm: np.ndarray
    phased: np.ndarray
    baseline: np.ndarray
    spectrum: np.ndarray
    options: dict
    diagnostics: dict

    @property
    def metadata(self):return self.raw.metadata
    @property
    def name(self):return self.metadata['source_name']


def phase_radians(ppm,metadata,options):
    """One correction on the full acquired SW, increasing ppm, for every layer."""
    width=metadata['x_sweep_Hz']/(metadata['x_frequency_Hz']/1e6)
    carrier=metadata['offset_ppm']+options['ppm_shift']
    filter_ramp=360*options['filter_delay_samples']*(ppm-carrier)/width
    return np.deg2rad(filter_ramp+options['phase0_deg']+options['phase1_deg']*(ppm-options['pivot_ppm'])/width)


def validate_baseline_roi_overlap(regions, roi_bounds):
    for a,b in regions:
        for c,d in roi_bounds:
            if max(min(a,b),min(c,d))<min(max(a,b),max(c,d)):
                raise ValueError('Obszar bazy przecina ROI. Zmień maskę bazy przed zatwierdzeniem. '
                                 f'Zakres maski bazy {min(a,b):.5f}–{max(a,b):.5f} ppm · ROI {min(c,d):.6f}–{max(c,d):.6f} ppm.')


def process_fids(raw,options=None,roi_bounds=()):
    o=validate_options(options or default_options(raw),len(raw.fid))
    roi_bounds = tuple(roi_bounds)
    sw=raw.metadata['x_sweep_Hz'];freq=raw.metadata['x_frequency_Hz']/1e6
    n=raw.fid.shape[1];time=np.arange(n)/sw
    window=np.exp(-np.pi*o['lb_Hz']*time-(np.pi*o['gaussian_FWHM_Hz']*time)**2/(4*np.log(2)))
    nfft=n*o['zero_fill_factor']
    z=np.fft.fftshift(np.fft.fft(raw.fid*window[None,:],n=nfft,axis=1),axes=1)
    f=np.fft.fftshift(np.fft.fftfreq(nfft,1/sw))
    ppm=raw.metadata['offset_ppm']+f/freq+o['ppm_shift']
    z*=np.exp(1j*phase_radians(ppm,raw.metadata,o))[None,:]
    keep=np.ones(nfft,bool)
    if o['crop_filter'] and raw.metadata.get('digital_filter') and not raw.metadata.get('already_clipped'):
        half_band=raw.metadata['x_sweep_clipped_Hz']/2
        keep=(f>=-half_band)&(f<half_band)
    ppm=ppm[keep];z=z[:,keep]
    base=np.zeros(z.shape,float);diag={'nfft':nfft,'window':'exp(-pi*LB*t) * exp(-(pi*GB*t)^2/(4*ln(2)))',
                                     'baseline':None,'warnings':[]}
    if o['baseline_regions'] and (o['baseline_preview'] or o['baseline_enabled']):
        if o['baseline_enabled']:
            validate_baseline_roi_overlap(o['baseline_regions'], roi_bounds)
        base,diag['baseline']=baseline_fit(ppm,z.real,o['baseline_regions'],o['baseline_degree'],
                                          o['reference_layer'],o['baseline_per_layer'])
        if o['baseline_enabled']:
            first, last = diag['baseline']['fit_range_ppm']
            diag['baseline']['extrapolated_roi_indices'] = [
                i for i, bounds in enumerate(roi_bounds) if min(bounds) < first or max(bounds) > last
            ]
    elif o['baseline_enabled']:raise ValueError('Najpierw zaznacz obszary linii bazowej.')
    corrected=z-base if o['baseline_enabled'] else z.copy()
    if not np.isfinite(corrected).all():raise ValueError('Processing wygenerował NaN/Inf.')
    for a in (ppm,z,base,corrected):a.setflags(write=False)
    return Dataset(raw,ppm,z,base,corrected,o,diag)


def starting_phase0(dataset):
    """Coarse positive absorption phase from coherent peaks in the reference only."""
    z=dataset.phased[dataset.options['reference_layer']]
    if len(z)<32:return None
    magnitude=abs(z)
    noise=np.median(abs(np.diff(z)))
    df=abs(dataset.ppm[1]-dataset.ppm[0])*dataset.metadata['x_frequency_Hz']/1e6
    peaks,_=find_peaks(magnitude,prominence=max(.04*magnitude.max(),12*noise),
                       distance=max(3,round(3.5/df)))
    peaks=peaks[(peaks>=.04*len(z))&(peaks<.96*len(z))]
    if len(peaks)<2:return None
    amplitudes=magnitude[peaks]
    weights=np.sqrt(amplitudes)
    direction=np.sum(weights*z[peaks]/amplitudes)/weights.sum()
    if abs(direction)<.70:return None
    return -float(np.angle(direction,deg=True))


def initial_dataset(raw):
    """New JDF only: visible filter correction and a shared editable PH0 seed."""
    options=default_options(raw)
    model=raw.metadata.get('filter_delay_model')
    if model is None:return process_fids(raw,options)
    options['filter_delay_samples']=model['samples']
    dataset=process_fids(raw,options)
    phase0=starting_phase0(dataset)
    if phase0 is None:return dataset
    options['phase0_deg']=round(phase0,6)
    return process_fids(raw,options)


def validate_integral_bounds(x, bounds):
    lo,hi=sorted(map(float,bounds))
    if not np.isfinite([lo,hi]).all() or lo>=hi or lo<x[0] or hi>x[-1]:raise ValueError('ROI poza widmem lub zerowej szerokości.')
    if np.searchsorted(x,hi,side='right')-np.searchsorted(x,lo)<2:raise ValueError('ROI zawiera mniej niż dwa punkty widma.')
    return lo, hi


def signed_integrals(ppm,spectra,bounds):
    ppm=np.asarray(ppm);z=np.asarray(spectra)
    if ppm.ndim!=1 or z.ndim!=2 or z.shape[1]!=len(ppm):raise ValueError('Niezgodne wymiary integracji.')
    if not np.isfinite(ppm).all() or not np.isfinite(z).all():raise ValueError('NaN/Inf w integracji.')
    order=np.argsort(ppm);x=ppm[order];y=z[:,order]
    if np.any(np.diff(x)<=0):raise ValueError('Oś ppm musi być ściśle monotoniczna.')
    lo,hi=validate_integral_bounds(x,bounds)
    inside=(x>lo)&(x<hi);xx=np.r_[lo,x[inside],hi]
    yy=np.column_stack(([np.interp(lo,x,row) for row in y],y[:,inside],
                        [np.interp(hi,x,row) for row in y]))
    return trapezoid(yy,x=xx,axis=1)
