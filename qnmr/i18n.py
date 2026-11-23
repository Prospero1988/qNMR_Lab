"""PL/EN presentation only. Canonical project keys and numerical data never translate."""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import re
from string import Formatter
from ._catalog import PL, LEGACY_EN

_language=ContextVar('qnmr_language',default='pl')
_formatter=Formatter()

def language() -> str:
    return _language.get()

def set_language(code: str, *, persist=False) -> None:
    if code not in ('pl','en'):raise ValueError('Unsupported language: '+str(code))
    _language.set(code)
    if persist:
        from PySide6.QtCore import QSettings
        settings=QSettings('qNMR Lab','Desktop');settings.setValue('interface/language',code);settings.sync()
    configure_qt()

def load_preference() -> None:
    import os
    from PySide6.QtCore import QSettings
    code=os.environ.get('QNMR_LAB_LANGUAGE') or QSettings('qNMR Lab','Desktop').value('interface/language','pl',type=str)
    set_language(code if code in ('pl','en') else 'pl')

@contextmanager
def using_language(code):
    previous=language();set_language(code)
    try:yield
    finally:set_language(previous)

def tr(source: str, **values) -> str:
    return translate(source,language(),**values)

def translate(source: str, code: str, **values) -> str:
    """An owned window can pin its language across Qt callback contexts."""
    canonical=LEGACY_EN.get(source,source)
    result=PL.get(canonical,canonical) if code=='pl' else canonical
    return result.format(**values) if values else result

_patterns=[]
for _source,_target in {**PL,**{key:PL.get(value,value) for key,value in LEGACY_EN.items()}}.items():
    if '{p' not in _source:continue
    _parts=[]
    for literal,field,spec,conversion in _formatter.parse(_source):
        _parts.append(re.escape(literal))
        if field:_parts.append('(?P<'+field+'>[\\s\\S]+?)')
    try:_patterns.append((re.compile('^'+''.join(_parts)+'$'),_source))
    except re.error:pass

def message(text: object) -> str:
    """Localize an exception or cached diagnostic without rewriting stored text."""
    text=str(text)
    if text in PL or text in LEGACY_EN:return tr(text)
    for prefix in (*LEGACY_EN,*PL):
        if prefix.endswith(' ') and '{' not in prefix and text.startswith(prefix):
            return tr(prefix)+message(text[len(prefix):])
    for pattern,source in _patterns:
        match=pattern.fullmatch(text)
        if not match:continue
        target=tr(source)
        pieces=[]
        for literal,field,spec,conversion in _formatter.parse(target):
            pieces.append(literal)
            if field:pieces.append(match.group(field))
        return ''.join(pieces)
    return text

def enum_label(value):
    return tr(value) if isinstance(value,str) else tr('Yes') if value is True else tr('No') if value is False else value

def enum_items(combo,values,current=None):
    """Translated labels keep stable canonical userData and editable custom values."""
    for value in values:combo.addItem(tr(value),value)
    if current is not None:
        index=combo.findData(current)
        if index>=0:combo.setCurrentIndex(index)
        elif combo.isEditable():combo.setEditText(current)

def enum_value(combo):
    value=combo.currentData()
    return value if value is not None and combo.currentText()==tr(value) else combo.currentText()

def manual_path(name='USER_MANUAL') -> Path:
    return Path(__file__).resolve().parents[1]/'docs'/f'{name}_{language().upper()}.md'

_field_labels={
    'mean':'Mean','sd':'Sample SD','sem':'SEM','ci':'Confidence interval','confidence':'Confidence level',
    'rsd_percent':'RSD (%)','samples':'Sample preparations','between':'Between-preparation statistics',
    'between_by_analyte':'Statistics by analyte','components':'Components','omitted':'Omitted samples',
    'excluded':'Excluded samples','provisional':'Provisional result','note':'Note','independent':'Independent',
    'acquisitions':'Acquisitions','acquisition_statistics':'Acquisition variation','assay_percent':'Assay (%)',
    'name':'Name','id':'ID','analyte_id':'Analyte ID','warnings':'Warnings','mixed_sign':'Mixed-sign region',
    'noise_rms_estimate':'Estimated noise RMS','snr_estimate':'Estimated S/N','noise_source':'Noise source',
    'baseline_mean':'Mean baseline intensity','overlapping_rois':'Overlapping ROIs',
    'imaginary_real_rms_ratio':'Imaginary/real RMS ratio','boundary_step_ppm':'Boundary step (ppm)',
    'boundary_area_change':'Boundary area change','boundary_sensitivity_percent':'Boundary sensitivity (%)',
    'lb_Hz':'LB (Hz)','gaussian_FWHM_Hz':'Gaussian FWHM (Hz)','zero_fill_factor':'Zero fill factor',
    'phase0_deg':'PH0 (°)','phase1_deg':'PH1 (°/SW)','pivot_ppm':'Pivot (ppm)',
    'ppm_shift':'Calibration shift (ppm)','filter_delay_samples':'Filter delay (samples)',
    'crop_filter':'Crop digital-filter band','baseline_degree':'Baseline polynomial degree',
    'baseline_enabled':'Baseline subtraction','baseline_preview':'Baseline preview',
    'baseline_regions':'Manual baseline regions','baseline_per_layer':'Separate baseline for the 1D trace',
    'reference_layer':'Reference trace',
}

def display_record(value):
    if isinstance(value,dict):return {tr(_field_labels.get(k,k)):display_record(v) for k,v in value.items()}
    if isinstance(value,list):return [display_record(v) for v in value]
    if isinstance(value,str):return message(value)
    return value

def configure_qt():
    """Qt's own standard controls and non-native file dialogs follow the UI language."""
    try:
        from PySide6 import QtCore,QtWidgets
        app=QtWidgets.QApplication.instance()
        if app is None:return
        from .file_dialogs import configure_file_dialogs
        configure_file_dialogs(app)
        QtCore.QLocale.setDefault(QtCore.QLocale('pl_PL' if language()=='pl' else 'en_GB'))
        previous=getattr(app,'_qnmr_qt_translator',None)
        if previous:
            app.removeTranslator(previous)
            previous.deleteLater()
        translator=QtCore.QTranslator(app)
        if language()=='pl':
            path=QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.TranslationsPath)
            if translator.load('qtbase_pl',path):app.installTranslator(translator)
        app._qnmr_qt_translator=translator
        app.setAttribute(QtCore.Qt.ApplicationAttribute.AA_DontUseNativeDialogs,True)
    except ImportError:pass
