from copy import deepcopy
from pathlib import Path
import zipfile
import numpy as np
import pytest
from rdkit import Chem
from qnmr.models import Compound
from qnmr.chemistry import parse_smiles,read_structures,depiction,validate_mw
from qnmr.analysis import import_jdf
from qnmr.quantification import calculate_project,is_current
from qnmr.storage import save_project,load_project,relink_measurement,save_standard_library,load_standard_library

def test_smiles_mw_formula_and_salt():
    thymol=parse_smiles('CC(C)c1ccc(C)cc1O')
    assert thymol.formula=='C10H14O';assert thymol.molecular_weight==pytest.approx(150.221,.002)
    salt=parse_smiles('C[NH3+].[Cl-]')
    assert '.' in salt.smiles and salt.molecular_weight>60
    with pytest.raises(ValueError):parse_smiles('not a molecule')

def test_mol_sdf_and_depiction(tmp_path):
    mol=Chem.MolFromSmiles('CCO');mp=tmp_path/'ethanol.mol';Chem.MolToMolFile(mol,str(mp))
    assert read_structures(mp)[0].formula=='C2H6O'
    path=tmp_path/'multi.sdf'
    writer=Chem.SDWriter(str(path));writer.write(mol);writer.write(Chem.MolFromSmiles('O'));writer.close()
    compounds=read_structures(path);assert len(compounds)==2
    png,positions=depiction(compounds[0],atoms=[1],png=True)
    assert png.startswith(b'\x89PNG') and len(positions)==3
    svg,_=depiction(compounds[0]);assert '<svg' in svg
    with pytest.raises(ValueError):depiction(compounds[0],atoms=[99])

def test_manual_mw_requires_explanation_without_structure():
    c=Compound(molecular_weight=300,provenance='Certificate',mw_override_reason='Verified weighed salt formula')
    validate_mw(c)
    c.mw_override_reason=''
    with pytest.raises(ValueError):validate_mw(c)

def test_project_reopens_without_reprocessing_or_source(project,tmp_path):
    calculate_project(project);m=project.samples[0].measurements[0];m.source_path=str(tmp_path/'missing.jdf')
    path=tmp_path/'project.qnmr';save_project(project,path);loaded,warnings=load_project(path)
    restored=loaded.samples[0].measurements[0]
    np.testing.assert_array_equal(restored.arrays['spectrum'],m.arrays['spectrum'])
    assert not warnings and restored.results==m.results
    assert load_project(path,verify_sources=True)[1]
    assert is_current(loaded,loaded.samples[0],restored)
    assert not restored.arrays['spectrum'].flags.writeable

def test_source_hash_mismatch_and_relink(tmp_path):
    source=Path(__file__).resolve().parents[1]/'examples/synthetic_P01.jdf'
    m=import_jdf(source);target=tmp_path/'same.jdf';target.write_bytes(source.read_bytes());relink_measurement(m,target)
    target.write_bytes(b'bad')
    with pytest.raises(ValueError):relink_measurement(m,target)

def test_library_round_trip(project,tmp_path):
    path=tmp_path/'standards.json';save_standard_library(project.standards,path)
    restored=load_standard_library(path)
    assert restored==project.standards

def test_unknown_project_schema_fails_explicitly(project,tmp_path):
    project.schema_version=99;path=tmp_path/'future.qnmr';save_project(project,path)
    with pytest.raises(ValueError,match='schema'):load_project(path)
