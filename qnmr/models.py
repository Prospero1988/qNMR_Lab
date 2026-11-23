"""Versioned domain models. Masses retain their entered units; purity is a fraction."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4
import numpy as np

def uid() -> str:
    return uuid4().hex[:12]

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class Compound:
    id: str = field(default_factory=uid)
    name: str = 'Analyte'
    smiles: str = ''
    molblock: str = ''
    formula: str = ''
    molecular_weight: float = 0.0
    calculated_mw: float | None = None
    mw_override_reason: str = ''
    chemical_form: str = ''
    provenance: str = ''
    source_path: str = ''
    source_sha256: str = ''
    comments: str = ''

@dataclass
class Standard:
    id: str = field(default_factory=uid)
    compound: Compound = field(default_factory=lambda: Compound(name='Internal standard'))
    purity_fraction: float = 0.0
    purity_units: str = '% w/w'
    certificate: str = ''
    batch: str = ''
    reference_material_id: str = ''
    expiration: str = ''
    assigned_signals: list[dict] = field(default_factory=list)
    notes: str = ''
    validation_status: str = 'Unverified'

def example_thymol() -> Standard:
    return Standard(compound=Compound(name='Thymol (example material)',smiles='CC(C)c1ccc(C)cc1O',
        formula='C10H14O', molecular_weight=150.22, chemical_form='Thymol, as weighed',
        mw_override_reason='Illustrative molecular weight; verify the actual chemical form.',
        provenance='Illustrative reference material; verify your actual lot and certificate'),
        purity_fraction=.9957, certificate='Illustrative purity 99.57%; not a certificate for an actual lot',
        notes='Purity belongs only to the example material. Enter certificate and batch for your actual standard.',
        validation_status='Example only', assigned_signals=[dict(signal='Example reference',protons=1)])

@dataclass
class ROI:
    id: str = field(default_factory=uid)
    low: float = 0.0
    high: float = 1.0
    role: str = 'analyte'
    compound_id: str = ''
    signal: str = ''
    protons: float = 1.0
    protons_confirmed: bool = False
    atoms: list[int] = field(default_factory=list)
    group: str = ''
    accepted: bool = True
    exclusion_reason: str = ''
    quality: str = 'Not reviewed'
    comments: str = ''
    reference_ids: list[str] = field(default_factory=list)
    area: float | None = None
    diagnostics: dict = field(default_factory=dict)

@dataclass
class Measurement:
    id: str = field(default_factory=uid)
    name: str = 'Acquisition'
    source_path: str = ''
    source_sha256: str = ''
    metadata: dict = field(default_factory=dict)
    options: dict = field(default_factory=dict)
    rois: list[ROI] = field(default_factory=list)
    arrays: dict[str, np.ndarray] = field(default_factory=dict, repr=False)
    diagnostics: dict = field(default_factory=dict)
    process_history: list[dict] = field(default_factory=list)
    results: dict = field(default_factory=dict)
    result_fingerprint: str = ''
    results_at: str = ''
    notes: str = ''
    include: bool = True
    exclusion_reason: str = ''
    reference_compatibility_confirmed: bool = False
    input_kind: str = 'raw JDF'
    # Presentation metadata does not enter the quantitative fingerprint.
    roi_labels: dict[str,str] = field(default_factory=dict)
    next_roi_number: int = 1
    integration_reference_id: str = ''
    integration_reference_value: float = 1.0

    def assign_roi_labels(self):
        numbers=[int(label[1:]) for label in self.roi_labels.values() if label.startswith('S') and label[1:].isdigit()]
        self.next_roi_number=max(self.next_roi_number,max(numbers,default=0)+1)
        for roi in self.rois:
            if roi.id not in self.roi_labels:
                self.roi_labels[roi.id]=f'S{self.next_roi_number}';self.next_roi_number+=1

    def roi_label(self,roi):
        return self.roi_labels.get(roi.id,f'S{next(i+1 for i,r in enumerate(self.rois) if r.id==roi.id)}')

    def relative_integral(self,roi):
        reference=next((r for r in self.rois if r.id==self.integration_reference_id),None)
        if reference is None or reference.area is None or reference.area<=0 or roi.area is None:return None
        if not np.isfinite([reference.area,roi.area,self.integration_reference_value]).all() or self.integration_reference_value<=0:return None
        value=roi.area/reference.area*self.integration_reference_value
        return value if np.isfinite(value) else None

@dataclass
class Sample:
    id: str = field(default_factory=uid)
    name: str = 'Sample 1'
    analyte_id: str = ''
    standard_id: str = ''
    analyte_mass: float = 0.0
    standard_mass: float = 0.0
    mass_unit: str = 'mg'
    solvent: str = ''
    preparation_date: str = field(default_factory=lambda: date.today().isoformat())
    notes: str = ''
    independent: bool = True
    include: bool = True
    exclusion_reason: str = ''
    measurements: list[Measurement] = field(default_factory=list)

@dataclass
class Project:
    schema_version: int = 1
    id: str = field(default_factory=uid)
    name: str = 'Untitled qNMR project'
    purpose: str = 'Quantitative proton NMR using an internal standard'
    analyst: str = ''
    comments: str = ''
    created_at: str = field(default_factory=utc_now)
    compounds: list[Compound] = field(default_factory=lambda: [Compound()])
    standards: list[Standard] = field(default_factory=lambda: [example_thymol()])
    samples: list[Sample] = field(default_factory=list)
    statistics_settings: dict = field(default_factory=lambda: dict(confidence=.95,
        measurement_aggregation='equal measurement means',sample_aggregation='equal independent preparation means'))
    audit: list[dict[str, Any]] = field(default_factory=list)

    def compound(self, key: str) -> Compound:
        return next(c for c in self.compounds if c.id == key)

    def standard(self, key: str) -> Standard:
        return next(s for s in self.standards if s.id == key)

    def record(self, action: str, **details) -> None:
        self.audit.append(dict(time=utc_now(),action=action,**details))
