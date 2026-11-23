"""Atomic, self-contained project archives. Opening never reprocesses historical data."""
from dataclasses import asdict, fields
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import zipfile
import numpy as np
from . import __version__
from .models import Project, Compound, Standard, Sample, Measurement, ROI

def projects_directory() -> Path:
    directory=Path(__file__).resolve().parents[1]/'projects'
    directory.mkdir(parents=True,exist_ok=True)
    return directory

def reports_directory() -> Path:
    directory=Path(__file__).resolve().parents[1]/'reports'
    directory.mkdir(parents=True,exist_ok=True)
    return directory

def _json_default(value):
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,np.ndarray):return value.tolist()
    raise TypeError(f'Cannot serialize {type(value)}')

def project_dict(project: Project) -> dict:
    doc={f.name:getattr(project,f.name) for f in fields(project) if f.name not in ('samples','compounds','standards')}
    doc['compounds']=[asdict(c) for c in project.compounds]
    doc['standards']=[asdict(s) for s in project.standards]
    doc['samples']=[]
    for sample in project.samples:
        record={f.name:getattr(sample,f.name) for f in fields(sample) if f.name!='measurements'}
        record['measurements']=[]
        for m in sample.measurements:
            record['measurements'].append({f.name:( [asdict(r) for r in m.rois] if f.name=='rois' else getattr(m,f.name))
                for f in fields(m) if f.name!='arrays'})
        doc['samples'].append(record)
    return doc

def restore_project(doc: dict) -> Project:
    doc=dict(doc)
    if doc.get('schema_version')!=1:raise ValueError('Unsupported qNMR schema version. Use the matching application version.')
    doc['compounds']=[Compound(**c) for c in doc['compounds']]
    doc['standards']=[Standard(**dict(s,compound=Compound(**s['compound']))) for s in doc['standards']]
    samples=[]
    for s in doc['samples']:
        measurements=[]
        for m in s['measurements']:
            measurements.append(Measurement(**dict(m,rois=[ROI(**r) for r in m['rois']])))
            measurements[-1].assign_roi_labels()
        samples.append(Sample(**dict(s,measurements=measurements)))
    doc['samples']=samples
    return Project(**doc)

def save_project(project: Project, path: str | Path) -> None:
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    payload=dict(application='qNMR Lab',version=__version__,project=project_dict(project),array_hashes={})
    temporary=path.with_name(path.name+'.tmp')
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for s in project.samples:
                for m in s.measurements:
                    key=f'arrays/{s.id}_{m.id}.npz'
                    stream=BytesIO();np.savez_compressed(stream,**m.arrays);data=stream.getvalue()
                    payload['array_hashes'][key]=hashlib.sha256(data).hexdigest();z.writestr(key,data)
            z.writestr('project.json',json.dumps(payload,indent=2,ensure_ascii=False,allow_nan=False,default=_json_default))
        os.replace(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()

def load_project(path: str | Path, *, verify_sources=False) -> tuple[Project,list[str]]:
    warnings=[]
    with zipfile.ZipFile(path) as z:
        payload=json.loads(z.read('project.json'))
        if payload.get('application')!='qNMR Lab':raise ValueError('Not a qNMR Lab project.')
        project=restore_project(payload['project'])
        for s in project.samples:
            for m in s.measurements:
                key=f'arrays/{s.id}_{m.id}.npz';data=z.read(key)
                if hashlib.sha256(data).hexdigest()!=payload['array_hashes'].get(key):raise ValueError('Embedded spectral data checksum mismatch.')
                with np.load(BytesIO(data),allow_pickle=False) as arr:
                    m.arrays={key:arr[key] for key in arr.files}
                for arr in m.arrays.values():arr.setflags(write=False)
                # Source paths are provenance, never runtime dependencies. Avoid
                # even probing unavailable network drives during ordinary open.
                if verify_sources and m.source_path:
                    p=Path(m.source_path)
                    if not p.is_file():warnings.append(f'{m.name}: original source unavailable; embedded data and historical results retained.')
                    elif hashlib.sha256(p.read_bytes()).hexdigest()!=m.source_sha256:
                        warnings.append(f'{m.name}: source SHA256 changed; embedded historical data retained. Relink only to a matching file.')
    return project,warnings

def relink_measurement(m: Measurement, path: str | Path):
    p=Path(path)
    if hashlib.sha256(p.read_bytes()).hexdigest()!=m.source_sha256:raise ValueError('This file does not match the original source SHA256.')
    m.source_path=str(p.resolve())

def save_standard_library(standards: list[Standard], path: str | Path):
    Path(path).write_text(json.dumps(dict(schema_version=1,standards=[asdict(s) for s in standards]),indent=2),encoding='utf-8')

def load_standard_library(path: str | Path) -> list[Standard]:
    doc=json.loads(Path(path).read_text(encoding='utf-8'))
    if doc.get('schema_version')!=1:raise ValueError('Unsupported standard library schema.')
    return [Standard(**dict(s,compound=Compound(**s['compound']))) for s in doc['standards']]
