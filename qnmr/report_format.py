"""Presentation-only scientific formatting. Never rounds stored project values."""
from datetime import datetime,date
from numbers import Real
import math,re
from .i18n import language,message

SUPER=str.maketrans('-+0123456789','⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹')
FIELD_LABELS={
    'nfft':('Liczba punktów FFT','FFT points'),
    'window':('Funkcja apodyzacji','Apodization function'),
    'baseline':('Dopasowanie bazy','Baseline fit'),
    'condition':('Wskaźnik uwarunkowania','Condition number'),
    'points':('Liczba punktów','Point count'),
    'coefficients':('Współczynniki','Coefficients'),
    'fit_range_ppm':('Zakres dopasowania (ppm)','Fit range (ppm)'),
    'extrapolated_roi_indices':('ROI poza obszarem dopasowania','ROIs outside fit coverage'),
    'source_measurement_id':('Pomiar źródłowy','Source acquisition ID'),
    'clicked_ppm':('Wskazane położenie (ppm)','Clicked position (ppm)'),
    'target_ppm':('Docelowe położenie (ppm)','Target position (ppm)'),
}

def field_label(key):
    if key in FIELD_LABELS:return FIELD_LABELS[key][0 if language()=='pl' else 1]
    result=message(str(key))
    if result==key and re.fullmatch(r'[a-z][a-z0-9_]*',result):result=result.replace('_',' ').capitalize()
    return result

def text(value):
    """Only text belongs in prose; containers must go through structured_rows."""
    if value is None:return ''
    if not isinstance(value,str):raise TypeError('Report prose requires a string')
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',value).strip()

def missing():return 'nie podano' if language()=='pl' else 'not recorded'
def yesno(value):return ('Tak' if value else 'Nie') if language()=='pl' else ('Yes' if value else 'No')
def number(value,decimals=None,*,significant=5,scientific=None):
    if value is None or not isinstance(value,Real) or not math.isfinite(value):return missing()
    v=float(value)
    if scientific is None:scientific=bool(v and (abs(v)<1e-3 or abs(v)>=1e5)) and decimals is None
    if scientific and v:
        mantissa,exponent=f'{v:.{significant-1}e}'.split('e')
        result=mantissa+' × 10'+str(int(exponent)).translate(SUPER)
    elif decimals is not None:
        result=f'{v:.{decimals}f}'
        if float(result)==0:result=result.lstrip('-')
    else:
        result=f'{v:.{significant}g}'
        if 'e' in result.lower():
            mantissa,exponent=result.lower().split('e')
            result=mantissa+' × 10'+str(int(exponent)).translate(SUPER)
    return result.replace('.',',') if language()=='pl' else result

def value(v,unit='',decimals=None,*,significant=5):
    rendered=number(v,decimals,significant=significant)
    return rendered+(' '+unit if unit and rendered!=missing() else '')

def interval(values,decimals=3):
    return '–'.join(number(v,decimals) for v in values) if values is not None else missing()

def signal_name(raw):
    """Localize a numeric ppm label without editing analyst-entered identifiers."""
    if raw is None:return missing()
    matched=re.fullmatch(r'\s*([-+]?\d+(?:[.,]\d+)?)\s*ppm\s*',raw)
    return number(float(matched[1].replace(',','.')),3)+' ppm' if matched else text(raw)

def readable_date(raw,*,time=False):
    if not raw:return missing()
    if isinstance(raw,(date,datetime)):parsed=raw
    else:
        try:parsed=datetime.fromisoformat(raw.replace('Z','+00:00'))
        except (ValueError,TypeError):return text(raw) if isinstance(raw,str) else missing()
    if isinstance(parsed,datetime) and parsed.tzinfo:
        from zoneinfo import ZoneInfo
        parsed=parsed.astimezone(ZoneInfo('Europe/Warsaw'))
    result=parsed.strftime('%d.%m.%Y') if language()=='pl' else f'{parsed.day:02d} '+('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[parsed.month-1])+f' {parsed.year}'
    if time and isinstance(parsed,datetime):result+=parsed.strftime(' %H:%M')+(' '+parsed.tzname() if parsed.tzinfo else '')
    return result

def scalar(v,*,significant=7):
    if v is None:return missing()
    if isinstance(v,bool):return yesno(v)
    if isinstance(v,Real):return number(v,significant=significant)
    if isinstance(v,str):return signal_name(message(v)) or missing()
    raise TypeError('Structured value requires dedicated table formatting')

def structured_rows(record,prefix='',*,significant=8):
    """Flatten nested diagnostics into labeled table rows, including empty values."""
    rows=[]
    if isinstance(record,dict):
        if not record:return [(prefix,'Brak' if language()=='pl' else 'None recorded')]
        for key,item in record.items():
            label=field_label(key)
            label=(prefix+' / ' if prefix else '')+label
            precision=3 if ('S/N' in key or key=='snr_estimate') or isinstance(item,Real) and item and abs(item)<1e-10 else significant
            rows.extend(structured_rows(item,label,significant=precision))
    elif isinstance(record,(list,tuple)):
        if not record:return [(prefix,'Brak' if language()=='pl' else 'None recorded')]
        for i,item in enumerate(record,1):rows.extend(structured_rows(item,f'{prefix} / {i}',significant=significant))
    else:rows.append((prefix,scalar(record,significant=significant)))
    return rows
