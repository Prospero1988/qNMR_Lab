from pathlib import Path
from copy import deepcopy
import hashlib
import struct
import numpy as np
import pytest
from qnmr.jeol import read_jdf,infer_filter_delay
from qnmr.processing import (default_options,process_fids,phase_radians,baseline_fit,signed_integrals,initial_dataset)
from qnmr.analysis import import_jdf,reprocess,alignment_proposal,template_rois,update_integrals
from .jdf_fixture import encode_1d

@pytest.mark.parametrize('little',[True,False])
@pytest.mark.parametrize('dtype_code',[0,1])
def test_jeol_endian_precision(raw,tmp_path,little,dtype_code):
    path=tmp_path/'measurement.jdf';path.write_bytes(encode_1d(raw.fid,little=little,dtype_code=dtype_code))
    actual=read_jdf(path);np.testing.assert_allclose(actual.fid,raw.fid,atol=1e-7)
    assert actual.metadata['source_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert not actual.fid.flags.writeable

def test_reject_corrupt_and_multidimensional(raw,tmp_path):
    path=tmp_path/'bad.jdf'
    for mutate in ('signature','dimension','size','nan'):
        data=bytearray(encode_1d(raw.fid))
        if mutate=='signature':data[0]=0
        elif mutate=='dimension':data[12]=2
        elif mutate=='size':data.pop()
        else:
            offset=struct.unpack_from('>I',data,1284)[0];struct.pack_into('<d',data,offset,float('nan'))
        path.write_bytes(data)
        with pytest.raises(ValueError):read_jdf(path)

def test_synthetic_1h_fixture_self_contained():
    path=Path(__file__).resolve().parents[1]/'examples/synthetic_P01.jdf'
    m=import_jdf(path)
    assert m.arrays['fid'].shape==(1,32768)
    assert m.options['filter_delay_samples']==0
    assert np.isfinite(m.arrays['spectrum']).all()

def test_fft_apodization_zero_fill_exact(raw):
    options=default_options(raw);options.update(lb_Hz=1.8,gaussian_FWHM_Hz=.7,zero_fill_factor=4)
    d=process_fids(raw,options);n=raw.fid.shape[1];time=np.arange(n)/1200
    w=np.exp(-np.pi*1.8*time-(np.pi*.7*time)**2/(4*np.log(2)))
    expected=np.fft.fftshift(np.fft.fft(raw.fid*w,n=n*4,axis=1),axes=1)
    np.testing.assert_allclose(d.spectrum,expected,rtol=0,atol=0)
    assert abs(d.ppm[np.argmax(d.spectrum[0].real)]-4.7)<.001

def test_phase_and_pivot_preserve_function(raw):
    o=default_options(raw);o.update(phase0_deg=27,phase1_deg=-63,pivot_ppm=4.2)
    d=process_fids(raw,o);other=dict(o,pivot_ppm=4.9,phase0_deg=27-63*(4.9-4.2)/2)
    np.testing.assert_allclose(phase_radians(d.ppm,raw.metadata,o),phase_radians(d.ppm,raw.metadata,other),atol=1e-15)
    original=process_fids(raw)
    np.testing.assert_allclose(d.spectrum,original.spectrum*np.exp(1j*phase_radians(d.ppm,raw.metadata,o)))

def test_baseline_legendre_recovers_polynomial():
    x=np.linspace(-1,1,2001);base=2+3*x-5*x*x
    baseline,diag=baseline_fit(x,base[None,:],[(-1,-.5),(.5,1)],2)
    np.testing.assert_allclose(baseline[0],base,atol=1e-13)
    assert diag['points']>900
    with pytest.raises(ValueError):baseline_fit(x,base[None,:],[],2)

def test_signed_fractional_integrals_no_endpoint_subtraction():
    x=np.linspace(0,10,101);y=np.array([2*x+3,-2*x-3])
    bounds=(2.035,7.087);lo,hi=bounds;exact=hi**2+3*hi-lo**2-3*lo
    np.testing.assert_allclose(signed_integrals(x,y,bounds),[exact,-exact],atol=1e-12)
    np.testing.assert_allclose(signed_integrals(x[::-1],y[:,::-1],bounds),[exact,-exact],atol=1e-12)
    assert signed_integrals(x,np.ones((1,len(x))),(2,7))[0]==5

def test_bad_bounds_are_not_clipped():
    x=np.arange(10.)
    for bounds in [(-1,4),(2,2),(8,12),(2.1,2.2),(float('nan'),3)]:
        with pytest.raises(ValueError):signed_integrals(x,x[None,:],bounds)

def test_supported_filter_delay_only():
    p={key:{'value':value} for key,value in dict(digital_filter='TRUE',clipped='FALSE',
        digital_filter_status='Np',orders='2 54 73',factors='8 2',filter_factor=16).items()}
    assert infer_filter_delay(p,0,2048)['samples']==19.65625
    assert infer_filter_delay(p,1,2048) is None
    for key,value in [('orders','3 54 73'),('factors','4 2'),('clipped','TRUE'),('digital_filter_status','unknown')]:
        changed=dict(p,**{key:{'value':value}});assert infer_filter_delay(changed,0,2048) is None

def test_baseline_commit_rejects_roi_overlap_and_is_atomic(project):
    m=project.samples[0].measurements[0];old=m.arrays['spectrum'].copy()
    o=dict(m.options,baseline_regions=[[4.67,4.73]],baseline_enabled=True)
    with pytest.raises(ValueError):reprocess(m,o)
    np.testing.assert_array_equal(m.arrays['spectrum'],old)
    assert not m.options['baseline_enabled']

def test_preview_is_not_subtracted(project):
    m=project.samples[0].measurements[0];before=m.arrays['spectrum'].copy()
    reprocess(m,dict(m.options,baseline_regions=[[3.6,3.9],[5.1,5.4]],baseline_preview=True,baseline_enabled=False))
    np.testing.assert_array_equal(m.arrays['spectrum'],before)
    reprocess(m,dict(m.options,baseline_enabled=True))
    np.testing.assert_allclose(m.arrays['spectrum'],m.arrays['phased']-m.arrays['baseline'])

def test_alignment_requires_separate_apply_and_templates_new_ids(project):
    source=project.samples[0].measurements[0];target=deepcopy(source)
    target.arrays=dict(target.arrays,ppm=target.arrays['ppm']+.012)
    original=[(r.low,r.high) for r in source.rois]
    proposed=alignment_proposal(source,target)
    assert all(abs(r[3]-.012)<.001 for r in proposed)
    assert original==[(r.low,r.high) for r in source.rois]
    copied=template_rois(source,target)
    assert {r.id for r in copied}.isdisjoint({r.id for r in source.rois})

def test_signed_diagnostics_do_not_reject(project):
    m=project.samples[0].measurements[0]
    m.arrays=dict(m.arrays,spectrum=-m.arrays['spectrum']);update_integrals(m)
    assert all(r.area<0 and r.accepted for r in m.rois)
    assert any('Nonpositive' in w for w in m.rois[0].diagnostics['warnings'])
