"""Frozen original DOSY Lab conventional spectra; no original repo dependency."""
from pathlib import Path
import numpy as np
from qnmr.jeol import RawData
from qnmr.processing import default_options,process_fids,signed_integrals

def test_original_engine_golden_regression():
    golden=np.load(Path(__file__).resolve().parents[1]/'validation/engine_golden.npz',allow_pickle=False)
    n=4096;sw=1600.;t=np.arange(n)/sw
    raw=RawData((np.exp(-np.pi*2*t)*(np.exp(2j*np.pi*210*t)+.7*np.exp(-2j*np.pi*150*t)))[None,:],
        dict(x_sweep_Hz=sw,x_frequency_Hz=600e6,offset_ppm=4.5,x_sweep_clipped_Hz=1200.,digital_filter=True))
    for i,changes in enumerate([{},dict(lb_Hz=1.5,gaussian_FWHM_Hz=.8,zero_fill_factor=2),
        dict(phase0_deg=25.,phase1_deg=-90.,pivot_ppm=4.2,ppm_shift=.03,filter_delay_samples=.7),
        dict(baseline_regions=[[3.55,3.7],[5.2,5.4]],baseline_enabled=True,baseline_degree=2)]):
        o=default_options(raw);o.update(changes);d=process_fids(raw,o,[(4.8,4.9)])
        np.testing.assert_allclose(d.ppm,golden[f'ppm_{i}'],rtol=0,atol=1e-12)
        np.testing.assert_allclose(d.spectrum,golden[f'spectrum_{i}'],rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(signed_integrals(d.ppm,d.spectrum.real,(4.815,4.895)),golden[f'area_{i}'],rtol=1e-12)
