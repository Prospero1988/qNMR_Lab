"""White-background report figures from existing arrays and molecular records."""
from io import BytesIO
import numpy as np
from .report_data import sample_code
from .report_text import label
from .report_format import number
from .i18n import language

NAVY='#183e5b';TEAL='#197c78';GRAY='#929ca6'

def canvas(width,height):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    fig=Figure(figsize=(width,height),layout='constrained',facecolor='white');FigureCanvasAgg(fig)
    return fig

def style(ax):
    from matplotlib.ticker import FuncFormatter
    ax.tick_params(labelsize=8,length=3,color='#637080')
    ax.spines[['top','right']].set_visible(False)
    for side in ('left','bottom'):ax.spines[side].set_color('#9ca8b4')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,pos:number(x,significant=3)))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:number(x,significant=4)))

def png(fig):
    stream=BytesIO();fig.savefig(stream,format='png',dpi=240,facecolor='white')
    return stream.getvalue()

def spectrum(measurement,*,zoom=False):
    if 'spectrum' not in measurement.arrays or 'ppm' not in measurement.arrays:return None
    x=measurement.arrays['ppm'];y=measurement.arrays['spectrum'][0].real
    if zoom:
        ranges=[]
        for roi in sorted(measurement.rois,key=lambda r:r.low):
            if not roi.accepted:continue
            if ranges and roi.low-ranges[-1][1]<.45:ranges[-1][1]=max(ranges[-1][1],roi.high)
            else:ranges.append([roi.low,roi.high])
        if not ranges:return None
        fig=canvas(6.6,1.45*((len(ranges)+1)//2));axes=fig.subplots((len(ranges)+1)//2,2,squeeze=False).ravel()
        for ax,bounds in zip(axes,ranges):
            padding=max(.04,(bounds[1]-bounds[0])*.12);mask=(x>=bounds[0]-padding)&(x<=bounds[1]+padding)
            draw_spectrum(ax,measurement,x[mask],y[mask]);ax.set_xlabel('δ ¹H (ppm)',fontsize=8)
        for ax in axes[len(ranges):]:ax.set_visible(False)
    else:
        fig=canvas(6.6,2.1);ax=fig.add_subplot();draw_spectrum(ax,measurement,x,y)
        ax.set_xlabel('δ ¹H (ppm)',fontsize=9)
        ax.set_ylabel('Intensywność (j.u.)' if language()=='pl' else 'Intensity (a.u.)',fontsize=8)
    return png(fig)

def draw_spectrum(ax,m,x,y):
    style(ax)
    if not len(x):return
    ax.plot(x,y,lw=.55,color=NAVY);ax.axhline(0,color=GRAY,lw=.45)
    ax.set_xlim(float(np.max(x)),float(np.min(x)))
    ax.margins(y=.22)
    previous=[];span=max(np.ptp(x),1e-9)
    for roi in sorted(m.rois,key=lambda r:r.low):
        mid=(roi.low+roi.high)/2
        if mid<min(x) or mid>max(x):continue
        color=GRAY if not roi.accepted else TEAL if roi.role=='standard' else NAVY
        ax.axvspan(roi.low,roi.high,color=color,alpha=.12 if roi.accepted else .05)
        ax.axvline(roi.low,color=color,lw=.45,alpha=.7);ax.axvline(roi.high,color=color,lw=.45,alpha=.7)
        level=next((level for level in range(4) if all(abs(mid-other)>.055*span or level!=used for other,used in previous)),len(previous)%4)
        previous.append((mid,level))
        ax.text(mid,.97-.105*level,m.roi_label(roi),transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=7,color=color,
            bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=.3))

def statistics(summary):
    rows=summary['samples']
    if not rows:return None
    fig=canvas(6.6,2.1);ax=fig.add_subplot();style(ax)
    for i,row in enumerate(rows):
        ax.plot(i,row['assay_percent'],'o',color=NAVY if row['independent'] else GRAY,markersize=5)
    mean=summary['between']['mean']
    if mean is not None:ax.axhline(mean,color=TEAL,ls='--',lw=1)
    if any(not row['independent'] for row in rows):
        ax.plot([],[],'o',color=NAVY,label=label('independent'))
        ax.plot([],[],'o',color=GRAY,label=label('nonindependent'))
        ax.legend(frameon=False,fontsize=7,loc='best')
    labels=[sample_code(r['name']) for r in rows]
    ax.set_xticks(range(len(rows)),labels,rotation=0 if max(map(len,labels))<16 else 20)
    ax.tick_params(axis='x',labelsize=8)
    ax.set_ylabel(label('assay'),fontsize=9);ax.margins(x=.12,y=.2)
    return png(fig)

def structure(compound):
    if not (compound.smiles or compound.molblock):return None
    from .chemistry import molecule
    from rdkit.Chem.Draw import rdMolDraw2D
    from PIL import Image,ImageChops
    drawer=rdMolDraw2D.MolDraw2DCairo(1200,950)
    options=drawer.drawOptions();options.addAtomIndices=False;options.bondLineWidth=2
    options.minFontSize=30;options.maxFontSize=36
    drawer.DrawMolecule(molecule(compound));drawer.FinishDrawing();data=drawer.GetDrawingText()
    image=Image.open(BytesIO(data)).convert('RGB')
    bbox=ImageChops.difference(image,Image.new('RGB',image.size,'white')).getbbox()
    if bbox:
        margin=22;bbox=(max(0,bbox[0]-margin),max(0,bbox[1]-margin),min(image.width,bbox[2]+margin),min(image.height,bbox[3]+margin))
        image=image.crop(bbox)
    output=BytesIO();image.save(output,format='PNG')
    return output.getvalue()
