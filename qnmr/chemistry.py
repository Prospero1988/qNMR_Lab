"""RDKit structures represent the entire entered chemical form, including fragments."""
from pathlib import Path
import hashlib
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
from .models import Compound

def molecule(compound: Compound):
    mol = Chem.MolFromMolBlock(compound.molblock, sanitize=True, removeHs=False) if compound.molblock else Chem.MolFromSmiles(compound.smiles)
    if mol is None or not mol.GetNumAtoms():
        raise ValueError('Invalid or empty structure. Check SMILES syntax, valence and charge.')
    Chem.SanitizeMol(mol)
    rdDepictor.Compute2DCoords(mol)
    return mol

def parse_smiles(smiles: str, name='Compound') -> Compound:
    c=Compound(name=name, smiles=smiles.strip(), provenance='Analyst-entered SMILES')
    mol=molecule(c)
    c.smiles=Chem.MolToSmiles(mol)
    c.formula=rdMolDescriptors.CalcMolFormula(mol)
    c.calculated_mw=c.molecular_weight=float(Descriptors.MolWt(mol))
    return c

def read_structures(path: str | Path) -> list[Compound]:
    path=Path(path);data=path.read_bytes()
    if path.suffix.lower()=='.sdf':
        molecules=list(Chem.SDMolSupplier(str(path),removeHs=False))
    elif path.suffix.lower()=='.mol':
        molecules=[Chem.MolFromMolFile(str(path),removeHs=False)]
    else:raise ValueError('Select a MOL or SDF structure file.')
    if not molecules:raise ValueError('The structure file has no records.')
    compounds=[]
    for i,mol in enumerate(molecules):
        if mol is None:raise ValueError(f'Cannot sanitize structure record {i+1}; check valence and file format.')
        name=mol.GetProp('_Name') if mol.HasProp('_Name') and mol.GetProp('_Name') else f'{path.stem} #{i+1}'
        c=parse_smiles(Chem.MolToSmiles(mol),name)
        c.molblock=Chem.MolToMolBlock(mol)
        c.source_path=str(path.resolve());c.source_sha256=hashlib.sha256(data).hexdigest()
        c.provenance=f'{path.name}, record {i+1}, SHA256 {c.source_sha256}'
        compounds.append(c)
    return compounds

def validate_mw(compound: Compound) -> None:
    import math
    if not math.isfinite(compound.molecular_weight) or compound.molecular_weight<=0:
        raise ValueError(f'Enter a positive verified molecular weight for {compound.name}.')
    if not compound.provenance.strip():raise ValueError('Record molecular-weight/structure provenance.')
    if compound.calculated_mw is None or abs(compound.molecular_weight-compound.calculated_mw)>1e-8:
        if not compound.mw_override_reason.strip():
            raise ValueError('Manual molecular weight requires an explanation of its source and chemical form.')

def depiction(compound: Compound, width=720, height=480, atoms=(), indices=True, png=False):
    mol=molecule(compound)
    if any(i<0 or i>=mol.GetNumAtoms() for i in atoms):raise ValueError('Selected atom index is outside this structure.')
    drawer=(rdMolDraw2D.MolDraw2DCairo if png else rdMolDraw2D.MolDraw2DSVG)(width,height)
    drawer.drawOptions().addAtomIndices=indices
    drawer.DrawMolecule(mol,highlightAtoms=list(atoms))
    positions=[(drawer.GetDrawCoords(i).x,drawer.GetDrawCoords(i).y) for i in range(mol.GetNumAtoms())]
    drawer.FinishDrawing()
    return drawer.GetDrawingText(),positions

def export_structure(compound, path, atoms=()):
    path=Path(path);data,_=depiction(compound,atoms=atoms,png=path.suffix.lower()=='.png')
    path.write_bytes(data if isinstance(data,bytes) else data.encode('utf-8'))
