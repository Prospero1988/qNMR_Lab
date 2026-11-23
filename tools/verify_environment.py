"""Verify the pinned application environment without changing packages."""
from pathlib import Path
import importlib.metadata
import platform
import struct
import sys

EN='--language' in sys.argv and sys.argv[sys.argv.index('--language')+1:][:1]==['en']
def text(pl,en):return en if EN else pl

def verify():
    if sys.version_info[:2]!=(3,12) or struct.calcsize('P')!=8 or platform.machine().lower() not in ('amd64','x86_64'):
        raise RuntimeError(text('qNMR Lab wymaga CPython 3.12 x64.','qNMR Lab requires CPython 3.12 x64.'))
    lock=Path(__file__).resolve().parents[1]/'requirements-lock.txt'
    for line in lock.read_text().splitlines():
        if not line.strip() or line.startswith('#'):continue
        name,expected=line.split('==',1)
        actual=importlib.metadata.version(name)
        if actual!=expected:raise RuntimeError(text(f'{name}: wymagana wersja {expected}, wykryta {actual}.',f'{name}: expected {expected}, found {actual}.'))
    import numpy, scipy, pyqtgraph, openpyxl, docx, matplotlib
    from PySide6 import QtWidgets
    from rdkit import Chem
    if Chem.MolFromSmiles('CCO') is None:raise RuntimeError(text('Weryfikacja RDKit nie powiodła się.','RDKit verification failed.'))

if __name__=='__main__':
    try:
        verify()
        if '--quiet' not in sys.argv:print(text('Zweryfikowano Python, biblioteki, Qt i RDKit.','Python, pinned dependencies, Qt and RDKit verified.'))
    except Exception as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)
