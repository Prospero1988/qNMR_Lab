"""Connect immutable processing arrays to measurement records and ROI diagnostics."""
from copy import deepcopy
from pathlib import Path
import numpy as np
from .jeol import read_jdf, RawData
from .models import Measurement, ROI, uid, utc_now
from .processing import Dataset, initial_dataset, process_fids, signed_integrals, validate_baseline_roi_overlap

def dataset_from_measurement(m: Measurement) -> Dataset:
    if 'fid' not in m.arrays:raise ValueError('No embedded FID; this record contains reference-workbook values only.')
    raw=RawData(m.arrays['fid'],m.metadata)
    return Dataset(raw,m.arrays['ppm'],m.arrays['phased'],m.arrays['baseline'],m.arrays['spectrum'],m.options,m.diagnostics)

def store_dataset(m: Measurement, d: Dataset) -> None:
    m.options=deepcopy(d.options);m.metadata=deepcopy(d.metadata);m.diagnostics=deepcopy(d.diagnostics)
    m.arrays=dict(fid=d.raw.fid,ppm=d.ppm,phased=d.phased,baseline=d.baseline,spectrum=d.spectrum)

def import_jdf(path: str | Path) -> Measurement:
    raw=read_jdf(path)
    params=raw.metadata.get('parameters',{})
    domain=params.get('x_domain',{}).get('value')
    if domain and domain not in ('Proton','1H','H1'):raise ValueError(f'Expected a proton acquisition, found {domain}.')
    if params.get('irr_mode',{}).get('value')=='Presaturation':
        raise ValueError('Presaturated acquisitions are outside the conventional qNMR workflow.')
    d=initial_dataset(raw)
    m=Measurement(name=Path(path).stem,source_path=str(Path(path).resolve()),source_sha256=raw.metadata['source_sha256'])
    store_dataset(m,d)
    m.process_history.append(dict(time=utc_now(),action='Initial processing',options=deepcopy(m.options)))
    return m

def reprocess(m: Measurement, options: dict) -> None:
    """Atomic processing commit. Errors leave the previous displayed arrays intact."""
    if m.input_kind!='raw JDF':raise ValueError('Workbook reference integrals cannot be reprocessed as FIDs.')
    old=deepcopy(m.options)
    d=process_fids(RawData(m.arrays['fid'],m.metadata),options,[(r.low,r.high) for r in m.rois])
    for r in m.rois:signed_integrals(d.ppm,d.spectrum.real,(r.low,r.high))
    store_dataset(m,d)
    m.process_history.append(dict(time=utc_now(),action='Processing changed',before=old,options=deepcopy(m.options)))
    update_integrals(m)

def roi_diagnostics(m: Measurement, r: ROI) -> dict:
    x=m.arrays['ppm'];z=m.arrays['spectrum'][0];y=z.real
    mask=(x>=r.low)&(x<=r.high)
    base_regions=m.options.get('baseline_regions',[])
    noise_mask=np.zeros(len(x),bool)
    for lo,hi in base_regions:noise_mask|=(x>=min(lo,hi))&(x<=max(lo,hi))
    sample=y[noise_mask] if noise_mask.sum()>=8 else y
    diff=np.diff(sample)
    noise=float(np.median(abs(diff-np.median(diff)))/(.67448975*np.sqrt(2))) if len(diff)>1 else 0.
    selected=y[mask];warnings=[]
    snr=float(np.max(abs(selected))/noise) if noise>0 and len(selected) else None
    mixed=bool(len(selected) and np.min(selected)<-3*noise and np.max(selected)>3*noise)
    if r.area is not None and r.area<=0:warnings.append('Nonpositive signed integral')
    if mixed:warnings.append('Mixed-sign region: inspect phase and overlap')
    overlapping=[other.signal or other.id for other in m.rois if other.id!=r.id and max(other.low,r.low)<min(other.high,r.high)]
    if overlapping:warnings.append('ROI overlaps another assigned ROI')
    sensitivity=[];step=float(np.median(np.diff(x)))
    for delta in (-step,step):
        lo,hi=r.low-delta,r.high+delta
        try:sensitivity.append(float(signed_integrals(x,m.arrays['spectrum'].real,(lo,hi))[0]))
        except ValueError:pass
    change=max((abs(v-r.area) for v in sensitivity),default=0.) if r.area is not None else None
    rel=100*change/abs(r.area) if r.area and change is not None else None
    if snr is not None and snr<100:warnings.append('S/N estimate below 100; analyst review only')
    if rel is not None and rel>2:warnings.append('Boundary sensitivity exceeds 2%; analyst review only')
    baseline_mean=float(np.mean(sample)) if noise_mask.any() else None
    imag_ratio=float(np.sqrt(np.mean(z[mask].imag**2))/max(np.sqrt(np.mean(selected**2)),np.finfo(float).tiny)) if mask.any() else None
    return dict(noise_rms_estimate=noise,snr_estimate=snr,noise_source='manual baseline regions' if noise_mask.sum()>=8 else 'whole-spectrum first differences (approximate)',
        baseline_mean=baseline_mean,mixed_sign=mixed,overlapping_rois=overlapping,
        imaginary_real_rms_ratio=imag_ratio,boundary_step_ppm=step,boundary_area_change=change,
        boundary_sensitivity_percent=rel,warnings=warnings,
        note='Heuristics do not establish signal equivalence, lack of overlap, or quantitative validity.')

def update_integrals(m: Measurement) -> None:
    m.assign_roi_labels()
    if 'spectrum' not in m.arrays:return
    x=m.arrays['ppm']
    if m.options.get('baseline_enabled'):
        validate_baseline_roi_overlap(m.options['baseline_regions'],[(r.low,r.high) for r in m.rois])
    areas=[float(signed_integrals(x,m.arrays['spectrum'].real,(r.low,r.high))[0]) for r in m.rois]
    for r,area in zip(m.rois,areas):r.area=area
    for r in m.rois:r.diagnostics=roi_diagnostics(m,r)

def template_rois(source: Measurement, target: Measurement) -> list[ROI]:
    mapping={r.id:uid() for r in source.rois}
    result=deepcopy(source.rois)
    for r in result:
        original=r.id;r.id=mapping[original];r.area=None;r.diagnostics={}
        r.reference_ids=[mapping[key] for key in r.reference_ids if key in mapping]
    if 'ppm' not in target.arrays:raise ValueError('Target needs a processed spectrum.')
    for r in result:signed_integrals(target.arrays['ppm'],target.arrays['spectrum'].real,(r.low,r.high))
    if target.options.get('baseline_enabled'):
        validate_baseline_roi_overlap(target.options['baseline_regions'],[(r.low,r.high) for r in result])
    return result

def alignment_proposal(source: Measurement, target: Measurement, search_ppm=.04) -> list[tuple[str,float,float,float]]:
    """Suggest a rigid ROI shift from local absolute maxima. Never mutate data."""
    if not np.isfinite(search_ppm) or not 0<search_ppm<=1:raise ValueError('Search window must be >0 and <=1 ppm.')
    proposals=[]
    for r in source.rois:
        sx=source.arrays['ppm'];sy=source.arrays['spectrum'][0].real
        sm=(sx>=r.low)&(sx<=r.high)
        if not sm.any():raise ValueError('Template ROI has no spectral points.')
        peak=float(sx[sm][np.argmax(abs(sy[sm]))])
        tx=target.arrays['ppm'];ty=target.arrays['spectrum'][0].real
        tm=(tx>=peak-search_ppm)&(tx<=peak+search_ppm)
        if not tm.any():raise ValueError('Alignment search is outside target spectrum.')
        found=float(tx[tm][np.argmax(abs(ty[tm]))]);delta=found-peak
        signed_integrals(tx,target.arrays['spectrum'].real,(r.low+delta,r.high+delta))
        proposals.append((r.signal,r.low+delta,r.high+delta,delta))
    return proposals
