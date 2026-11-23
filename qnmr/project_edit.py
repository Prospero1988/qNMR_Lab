"""Remove project records without deleting external files or orphaning assignments."""

def deletion_details(project,selection):
    kind=selection[0]
    if kind=='sample':
        sample=next(s for s in project.samples if s.id==selection[1])
        return dict(kind=kind,name=sample.name,preparations=1,acquisitions=len(sample.measurements),
                    measurement_ids=[m.id for m in sample.measurements],roi_count=0)
    if kind=='measurement':
        sample=next(s for s in project.samples if s.id==selection[1])
        m=next(m for m in sample.measurements if m.id==selection[2])
        return dict(kind=kind,name=m.name,sample_name=sample.name,preparations=0,acquisitions=1,
                    measurement_ids=[m.id],roi_count=0)
    if kind=='compound':
        compound=project.compound(selection[1])
        return dict(kind=kind,name=compound.name,
            preparations=sum(s.analyte_id==compound.id for s in project.samples),acquisitions=0,measurement_ids=[],
            roi_count=sum(r.compound_id==compound.id and r.role!='standard' for s in project.samples for m in s.measurements for r in m.rois))
    if kind=='standard':
        standard=project.standard(selection[1]);samples=[s for s in project.samples if s.standard_id==standard.id]
        return dict(kind=kind,name=standard.compound.name,preparations=len(samples),acquisitions=0,measurement_ids=[],
            roi_count=sum(r.role=='standard' and r.compound_id==standard.compound.id for s in samples for m in s.measurements for r in m.rois))
    raise ValueError('Select a preparation, acquisition, compound or reference material to delete.')

def _unassign(roi):
    roi.compound_id='';roi.role='unassigned';roi.protons_confirmed=False;roi.atoms=[];roi.group=''
    # Keep integrals, user comments and reference UUIDs. A removed standard is
    # never silently replaced with another signal/material.

def delete_record(project,selection):
    details=deletion_details(project,selection);kind=details['kind'];key=selection[1]
    if kind=='sample':project.samples[:]=[s for s in project.samples if s.id!=key]
    elif kind=='measurement':
        sample=next(s for s in project.samples if s.id==key)
        sample.measurements[:]=[m for m in sample.measurements if m.id!=selection[2]]
    elif kind=='compound':
        project.compounds[:]=[c for c in project.compounds if c.id!=key]
        for sample in project.samples:
            if sample.analyte_id==key:sample.analyte_id=''
            for m in sample.measurements:
                for roi in m.rois:
                    if roi.compound_id==key and roi.role!='standard':_unassign(roi)
    elif kind=='standard':
        standard=project.standard(key)
        for sample in project.samples:
            if sample.standard_id!=key:continue
            sample.standard_id=''
            for m in sample.measurements:
                for roi in m.rois:
                    if roi.role=='standard' and roi.compound_id==standard.compound.id:_unassign(roi)
        project.standards[:]=[s for s in project.standards if s.id!=key]
    project.record('Project record deleted',selection=list(selection),**details)
    return details
