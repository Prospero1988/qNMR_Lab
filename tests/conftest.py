import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import numpy as np
import pytest
from qnmr.models import Project, Sample, Measurement, ROI, Compound, Standard
from qnmr.jeol import RawData
from qnmr.processing import initial_dataset
from qnmr.analysis import store_dataset, update_integrals

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(autouse=True)
def english_for_existing_regressions():
    from qnmr.i18n import using_language
    with using_language('en'):yield

@pytest.fixture
def raw():
    n=2048;sw=1200.;time=np.arange(n)/sw
    fid=(np.exp(-np.pi*2*time)*(np.exp(2j*np.pi*120*time)+.5*np.exp(-2j*np.pi*180*time)))[None,:]
    return RawData(fid,dict(x_sweep_Hz=sw,x_frequency_Hz=600e6,offset_ppm=4.5,
        x_sweep_clipped_Hz=sw,digital_filter=False,source_name='synthetic',parameters={}))

@pytest.fixture
def project(raw):
    p=Project();p.compounds[0]=Compound(name='Synthetic analyte',molecular_weight=150.22,
        mw_override_reason='Synthetic test fixture',provenance='Known simulated MW',chemical_form='Synthetic')
    s=Sample(name='Preparation A',analyte_id=p.compounds[0].id,standard_id=p.standards[0].id,
        analyte_mass=10,standard_mass=10)
    m=Measurement(name='Synthetic acquisition');store_dataset(m,initial_dataset(raw))
    m.rois=[ROI(low=4.67,high=4.73,role='analyte',compound_id=s.analyte_id,protons=1,protons_confirmed=True,signal='A'),
            ROI(low=4.17,high=4.23,role='standard',compound_id=p.standards[0].compound.id,protons=1,protons_confirmed=True,signal='IS')]
    s.measurements=[m];p.samples=[s];update_integrals(m)
    return p

@pytest.fixture(scope='session')
def app():
    from PySide6.QtWidgets import QApplication
    application=QApplication.instance() or QApplication([])
    yield application
    application.processEvents()

@pytest.fixture
def substance_study():
    """Two substances, three independent preparations each, unequal repeats."""
    def compound(name):
        return Compound(name=name,molecular_weight=150,provenance='Known synthetic material',
            mw_override_reason='Synthetic fixture, no inferred structure')
    a=compound('Substance A');b=compound('Substance B')
    standard=Standard(compound=compound('Reference'),purity_fraction=1,certificate='Synthetic fixture')
    p=Project(compounds=[a,b],standards=[standard])
    for substance,values in [(a,[[80,100],[100],[110,110,110]]),(b,[[40],[50],[60]])]:
        for index,repeats in enumerate(values,1):
            sample=Sample(name=f'{substance.name} P{index}',analyte_id=substance.id,standard_id=standard.id,analyte_mass=10,standard_mass=10)
            for acquisition,assay in enumerate(repeats,1):
                measurement=Measurement(name=f'Acquisition {acquisition}',input_kind='workbook reference: normalized integrals; no raw spectrum')
                ref=ROI(signal='IS',role='standard',compound_id=standard.compound.id,area=1,protons=1,protons_confirmed=True)
                target=ROI(signal='A',role='analyte',compound_id=substance.id,area=assay/100,protons=1,protons_confirmed=True,reference_ids=[ref.id])
                measurement.rois=[target,ref];measurement.assign_roi_labels();sample.measurements.append(measurement)
            p.samples.append(sample)
    return p
