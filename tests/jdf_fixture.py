"""Conventional 1D JEOL fixture, adapted from DOSY Lab's tested section encoder."""
import struct
import numpy as np

def encode_1d(fid,parameters=None,*,little=True,dtype_code=0):
    fid=np.asarray(fid).reshape(-1);endian='<' if little else '>'
    parameters=parameters or dict(x_domain='Proton',x_sweep=1200.,x_freq=600e6,x_offset=4.5,digital_filter='FALSE')
    records=[]
    for name,value in parameters.items():
        r=bytearray(64)
        if name in ('x_sweep','x_sweep_clipped','x_freq'):r[6:8]=bytes((1,13))
        elif name=='x_offset':r[6:8]=bytes((1,26))
        elif name=='x_acq_duration':r[6:8]=bytes((1,28))
        if isinstance(value,str):r[16:32]=value.encode('ascii').ljust(16,b'\0')
        else:struct.pack_into(endian+'d',r,16,value);struct.pack_into(endian+'i',r,32,2)
        r[36:64]=name.encode().ljust(28,b' ');records.append(r)
    params=struct.pack(endian+'4I',64,0,len(records)-1,len(records)*64)+b''.join(records)
    data=np.concatenate((fid.real,-fid.imag)).astype(endian+('f8' if dtype_code==0 else 'f4')).tobytes()
    header=bytearray(1360);header[:8]=b'JEOL.NMR';header[8]=int(little);header[12]=1;header[14]=(dtype_code<<6)|1;header[24]=3
    struct.pack_into('>8I',header,176,len(fid),1,1,1,1,1,1,1)
    struct.pack_into('>8I',header,240,len(fid)-1,0,0,0,0,0,0,0)
    struct.pack_into('>2I',header,1212,1360,len(params));offset=1360+len(params)
    struct.pack_into('>I',header,1284,offset);struct.pack_into('>Q',header,1288,len(data))
    struct.pack_into('>Q',header,1296,offset+len(data));struct.pack_into('>Q',header,1320,offset+len(data))
    return bytes(header)+params+data
