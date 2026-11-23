"""Generate three explicitly synthetic conventional JDF preparations for workflow QA."""
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.jdf_fixture import encode_1d
from qnmr.models import Project,Sample,ROI
from qnmr.chemistry import parse_smiles
from qnmr.analysis import import_jdf,update_integrals,reprocess
from qnmr.quantification import calculate_project,project_summary
from qnmr.storage import save_project
from qnmr.reports import export_bundle

def main():
    project=Project(name='Synthetic qNMR workflow — three preparations')
    project.comments='SIMULATED DATA. The three preparations and their spectra are generated for software workflow testing, not laboratory results. Peak equivalence is specified by the simulator.'
    c=parse_smiles('Cn1c(=O)c2c(ncn2C)n(C)c1=O','Caffeine (synthetic demonstration)')
    c.chemical_form='Anhydrous caffeine (simulated)';project.compounds=[c]
    standard=project.standards[0];standard.validation_status='Synthetic demonstration only'
    sw=12000.;frequency=600e6;n=32768;time=np.arange(n)/sw
    for i,(purity,mass_a,mass_is) in enumerate([(.95,10,1.5),(.96,10.2,1.6),(.94,9.8,1.4)],1):
        ratio=purity/standard.purity_fraction*standard.compound.molecular_weight/c.molecular_weight*mass_a/mass_is
        fid=np.zeros(n,complex)
        for ppm,amplitude in [(7.9,ratio),(3.3,ratio*3),(6.5,1)]:
            fid+=amplitude*np.exp(2j*np.pi*(ppm-5)*600*time-np.pi*1*time)
        path=ROOT/f'examples/synthetic_P0{i}.jdf'
        path.write_bytes(encode_1d(fid,dict(x_domain='Proton',x_sweep=sw,x_freq=frequency,x_offset=5.,digital_filter='FALSE')))
        m=import_jdf(path);m.notes=f'Simulated nominal analyte assay {purity*100}%; finite-ROI truncation can change the measured value.'
        sample=Sample(name=f'Synthetic P0{i}',analyte_id=c.id,standard_id=standard.id,
            analyte_mass=mass_a,standard_mass=mass_is,solvent='Simulated DMSO-d6',notes='Synthetic independent preparation record')
        for signal,low,high,nuclei,role in [('A 7.9',7.82,7.98,1,'analyte'),('A 3.3',3.22,3.38,3,'analyte'),('IS 6.5',6.42,6.58,1,'standard')]:
            m.rois.append(ROI(signal=signal,low=low,high=high,role=role,
                compound_id=standard.compound.id if role=='standard' else c.id,protons=nuclei,
                protons_confirmed=True,quality='Simulator assignment',comments='Known synthetic assignment; not an inferred chemical equivalence.'))
        sample.measurements=[m]
        # Explicit simulator-specified signal-free background regions remove the
        # constant discrete-FFT pedestal. No expected assay enters the fit.
        reprocess(m,dict(m.options,baseline_regions=[[-4.,-1.],[11.,14.]],baseline_degree=1,baseline_enabled=True))
        update_integrals(m);project.samples.append(sample)
    errors=calculate_project(project)
    if errors:raise RuntimeError(errors)
    save_project(project,ROOT/'examples/synthetic_three_samples.qnmr')
    export_bundle(project,ROOT/'outputs/synthetic_validation')
    print(project_summary(project)['between'])

if __name__=='__main__':main()
