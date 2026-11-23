"""Read-only JEOL 1D reader adapted from DOSY Lab (MIT, Prospero1988)."""
from dataclasses import dataclass
from pathlib import Path
import hashlib,re,struct
import numpy as np

@dataclass
class RawData:
    fid: np.ndarray
    metadata: dict
    def __post_init__(self):
        if self.fid.ndim != 2 or self.fid.shape[0] != 1:
            raise ValueError('Exactly one conventional 1D FID is required.')
        self.fid.setflags(write=False)

def number(params,name,base=None):
    p=params[name]
    active=[u for u in p['units'] if u['base_code'] or u['power']]
    if base is not None and (len(active)!=1 or active[0]['base_code']!=base or active[0]['power']!=1):
        raise ValueError('Niewłaściwa jednostka parametru '+name)
    value=float(p['value'])*10.**p['decimal_scaler']
    # Unit prefixes are powers of 1000 (1=milli, 2=micro).
    if base!=26:value*=10.**(-3*sum(u['prefix_code']*u['power'] for u in active))
    if not np.isfinite(value):raise ValueError('Nieskończony parametr '+name)
    return value


def parameters(blob,start,length,endian):
    if start<1360 or length<16 or start+length>len(blob):raise ValueError('Uszkodzona sekcja parametrów JDF.')
    size,lo,hi,total=struct.unpack_from(endian+'4I',blob,start)
    count=(length-16)//64
    if size!=64 or hi-lo+1!=count or total!=64*count or (length-16)%64:
        raise ValueError('Nieobsługiwany układ parametrów JDF.')
    result={}
    for at in range(start+16,start+length,64):
        kind=struct.unpack_from(endian+'i',blob,at+32)[0]
        units=[]
        for code,base in zip(blob[at+6:at+16:2],blob[at+7:at+16:2]):
            pre,power=code>>4,code&15
            units.append(dict(prefix_code=pre-16 if pre>=8 else pre,power=power-16 if power>=8 else power,base_code=base))
        raw=blob[at+16:at+32]
        if kind==0:value=raw.split(b'\0')[0].decode('utf-8',errors='replace').rstrip()
        elif kind in (1,4):value=struct.unpack_from(endian+'i',raw)[0]
        elif kind==2:value=struct.unpack_from(endian+'d',raw)[0]
        elif kind==3:value=list(struct.unpack_from(endian+'2d',raw))
        else:value=None
        name=blob[at+36:at+64].decode('ascii',errors='replace').strip().lower()
        result[name]=dict(value=value,units=units,decimal_scaler=struct.unpack_from(endian+'h',blob,at+4)[0],value_type=kind)
    return result


def _has_full_filter_band(params, first_point, npoints, sweep, clipped_sweep):
    """Resolve a TRUE clipping flag only when the stored FID matches the full acquisition."""
    if first_point != 0 or not 0 < clipped_sweep < sweep:
        return False
    try:
        acquired = number(params, 'x_points')
        requested = number(params, 'x_points_input')
        duration = number(params, 'x_acq_duration', 28)
    except (KeyError, TypeError, ValueError):
        return False
    return (0 < requested < npoints == acquired
            and abs(npoints * clipped_sweep / sweep - requested) <= 1
            and abs(duration * sweep - npoints) <= 1)


def infer_filter_delay(params, first_point, npoints, *, full_filter_band=False):
    """Infer a linear-phase decimation delay for the supported raw JEOL metadata."""
    value=lambda key:params.get(key,{}).get('value')
    unclipped = value('clipped') == 'FALSE' or (value('clipped') == 'TRUE' and full_filter_band)
    if (first_point!=0 or value('digital_filter')!='TRUE'
            or not unclipped or value('digital_filter_status')!='Np'):
        return None
    try:
        stages,*taps=map(int,value('orders').split())
        factors=list(map(int,value('factors').split()))
    except (AttributeError,ValueError,TypeError):
        return None
    if not 1<=stages<=8 or len(taps)!=stages or len(factors)!=stages:
        return None
    if any(not 1<=n<=65536 for n in taps+factors):
        return None
    decimation=1;delay=0.
    for length,factor in zip(reversed(taps),reversed(factors)):
        decimation*=factor
        delay+=(length-1)/(2*decimation)
    if decimation!=value('filter_factor') or decimation<2 or not 0<delay<=250 or 2*delay+8>=npoints:
        return None
    return dict(samples=delay,taps=taps,factors=factors,
                source='Model kaskady liniowofazowej z JDF orders/factors (oszacowanie)')


def read_jdf(path):
    path=Path(path).resolve();blob=path.read_bytes();digest=hashlib.sha256(blob).hexdigest()
    if len(blob)<1360 or blob[:8]!=b'JEOL.NMR' or blob[8] not in (0,1):raise ValueError('To nie jest poprawny JEOL JDF.')
    dimension,code,dtype_code=blob[12],blob[14]&63,blob[14]>>6
    if dimension != 1:raise ValueError('qNMR Lab accepts conventional complex 1D FID only; export a 1D JDF.')
    if dtype_code not in (0,1) or blob[24] not in (3,4) or (dimension==2 and blob[25]!=1):
        raise ValueError('Nieobsługiwane typy osi lub brak zespolonego FID.')
    endian='<' if blob[8] else '>'
    dtype=np.dtype(endian+('f8' if dtype_code==0 else 'f4'))
    pts=struct.unpack_from('>8I',blob,176)[:dimension]
    starts=struct.unpack_from('>8I',blob,208)[:dimension];stops=struct.unpack_from('>8I',blob,240)[:dimension]
    ds=struct.unpack_from('>I',blob,1284)[0];dl=struct.unpack_from('>Q',blob,1288)[0]
    cs=struct.unpack_from('>Q',blob,1296)[0];cl=struct.unpack_from('>I',blob,1304)[0]
    declared=struct.unpack_from('>Q',blob,1320)[0]
    if declared!=len(blob) or ds<1360 or ds+dl>len(blob) or cs+cl>len(blob):raise ValueError('Uszkodzone rozmiary sekcji JDF.')
    if any(a>b or b>=n for n,a,b in zip(pts,starts,stops)):raise ValueError('Nieprawidłowy zakres ważnych punktów JDF.')
    if dl!=2*int(np.prod(pts))*dtype.itemsize:raise ValueError('Niezgodna liczba sekcji zespolonych JDF.')
    raw=np.frombuffer(blob,dtype=dtype,count=dl//dtype.itemsize,offset=ds)
    if dimension==1 and code==1:
        sections=raw.reshape(2,pts[0])[:,None,:]
    else:raise ValueError(f'Nieobsługiwany format JDF {code}; nie zgadujemy kolejności danych.')
    pstart,plen=struct.unpack_from('>2I',blob,1212);params=parameters(blob,pstart,plen,endian)
    context='\n'.join(s.decode('ascii') for s in re.findall(rb'[\x09\x0a\x0d\x20-\x7e]{6,}',blob[cs:cs+cl]))
    xsl=slice(starts[0],stops[0]+1);gsl=slice(starts[1],stops[1]+1) if dimension==2 else slice(None)
    fid=np.array((sections[0]-1j*sections[1])[gsl,xsl],copy=True)
    if not np.isfinite(fid).all():raise ValueError('FID zawiera NaN/Inf.')
    sw=number(params,'x_sweep',13);freq=number(params,'x_freq',13);off=number(params,'x_offset',26)
    if min(sw,freq)<=0:raise ValueError('Nieprawidłowa częstotliwość lub szerokość widma.')
    clipped_sw=number(params,'x_sweep_clipped',13) if 'x_sweep_clipped' in params else sw
    clip_flag=params.get('clipped',{}).get('value')=='TRUE'
    digital_filter=params.get('digital_filter',{}).get('value')=='TRUE'
    filter_status=params.get('digital_filter_status',{}).get('value')
    full_band=(clip_flag and digital_filter and filter_status=='Np'
               and _has_full_filter_band(params,starts[0],fid.shape[1],sw,clipped_sw))
    meta={'source_name':path.name,'source_path':str(path),'source_sha256':digest,'parameters':params,
          'x_sweep_Hz':sw,'x_frequency_Hz':freq,'offset_ppm':off,
          'x_sweep_clipped_Hz':clipped_sw,'digital_filter':digital_filter,
          'already_clipped':clip_flag and not full_band,'full_fid_despite_clip_flag':full_band,
          'filter_delay_model':infer_filter_delay(params,starts[0],fid.shape[1],full_filter_band=full_band),
          'complex_convention':'section_0 - 1j*section_1','stored_shape':list(pts[::-1]),
          'valid_shape':list(fid.shape),'context':context,
          'limitations':['Oś ppm z x_offset i x_freq; odnośnik chemiczny wymaga potwierdzenia.',
                         'Korekcja fazy filtra to model opóźnienia, bez odtwarzania pełnej odpowiedzi Delty.']}
    return RawData(fid,meta)
