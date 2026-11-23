"""Build a small RAR deployment from an explicit runtime file list.

The Python environment, Git history, tests, caches and generated reports never
enter the archive. RAR is supplied by the locally installed WinRAR; it is not
redistributed. Run with the project interpreter to relocate the sample project.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qnmr import __version__
from qnmr.quantification import is_current, project_summary, CALCULATION_VERSION
from qnmr.storage import load_project, save_project


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output: Path, rar: Path) -> dict:
    output = output.resolve()
    if output.suffix.lower() != '.rar':
        raise ValueError('Output must use the .rar extension.')
    if output.exists():
        raise FileExistsError(f'Archive already exists; select a new output name: {output}')
    if not rar.is_file():
        raise FileNotFoundError(f'RAR encoder unavailable: {rar}')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    staging = ROOT / 'outputs' / f'deployment_{stamp}'
    package = staging / 'qNMR_Lab'
    package.mkdir(parents=True)
    files = [Path(p) for p in (
        'Start_qNMR_Lab.bat', 'requirements-lock.txt', 'requirements.txt', 'projects/.gitkeep', 'reports/.gitkeep',
        'LICENSE', 'THIRD_PARTY.md', 'CHANGELOG.md',
        'tools/bootstrap.ps1', 'tools/verify_environment.py',
        'licenses/DOSY_Lab_MIT.txt',
        'docs/USER_MANUAL.md', 'docs/SCIENTIFIC_METHODS.md',
        'docs/EXCEL_COMPARISON.md', 'docs/VALIDATION.md',
        'validation/test_results.txt',
        'examples/synthetic_three_samples.qnmr',
        'examples/synthetic_P01.jdf', 'examples/synthetic_P02.jdf',
        'examples/synthetic_P03.jdf',
    )]
    files += [Path('docs/DEVELOPER_GUIDE.md')]
    files += sorted(Path('docs') / p.name for p in (ROOT / 'docs').glob('*_PL.md'))
    files += sorted(Path('docs') / p.name for p in (ROOT / 'docs').glob('*_EN.md'))
    files += sorted(Path('qnmr') / p.name for p in (ROOT / 'qnmr').glob('*.py'))
    files += sorted(p.relative_to(ROOT) for p in (ROOT/'qnmr/icons').glob('*.svg'))
    for relative in files:
        source = ROOT / relative
        target = package / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for code in ('PL','EN'):
        text=(ROOT / 'docs' / f'DEPLOYMENT_{code}.md').read_text(encoding='utf-8')
        text=text.replace('](DEPLOYMENT_PL.md)','](README_PL.md)').replace('](DEPLOYMENT_EN.md)','](README_EN.md)')
        (package / f'README_{code}.md').write_text(text, encoding='utf-8')
        if code=='PL':(package / 'README.md').write_text(text, encoding='utf-8')
    # Relocate the staged copy only. Raw source checksums and numerical results
    # remain identical; the original sample project is never rewritten.
    demo_path = package / 'examples/synthetic_three_samples.qnmr'
    project, _ = load_project(demo_path)
    before = project_summary(project)['between']
    for sample in project.samples:
        for measurement in sample.measurements:
            relative = Path('examples') / Path(measurement.source_path).name
            if digest(package / relative) != measurement.source_sha256:
                raise ValueError('Packaged example source does not match its recorded checksum.')
            measurement.source_path = relative.as_posix()
            measurement.metadata['source_path'] = relative.as_posix()
            if not is_current(project, sample, measurement):
                raise ValueError('Relocation unexpectedly invalidated example numerical results.')
    save_project(project, demo_path)
    if project_summary(project)['between'] != before:
        raise ValueError('Example statistics changed during packaging.')
    revision = subprocess.check_output(
        ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    manifest = dict(application='qNMR Lab', version=__version__, build_utc=stamp,
                    default_language='pl', interface_languages=['pl','en'], calculation_version=CALCULATION_VERSION,
                    source_commit=revision, installation='online bootstrap; CPython 3.12 Windows x64',
                    files={p.relative_to(package).as_posix(): dict(bytes=p.stat().st_size, sha256=digest(p))
                           for p in sorted(package.rglob('*')) if p.is_file()})
    (package / 'DEPLOYMENT_MANIFEST.json').write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [str(rar), 'a', '-ma5', '-m5', '-r', '-ep1', '-idq', '-y', str(output), 'qNMR_Lab']
    subprocess.run(command, cwd=staging, check=True)
    subprocess.run([str(rar), 't', '-idq', str(output)], check=True)
    expected = {'qNMR_Lab/' + p.relative_to(package).as_posix()
                for p in package.rglob('*') if p.is_file()}
    listing = subprocess.check_output([str(rar), 'lb', str(output)], text=True)
    members = {line.strip().replace('\\', '/') for line in listing.splitlines() if line.strip()}
    if not expected.issubset(members):
        raise ValueError('The archive is missing files from the staged deployment.')
    if any(any(part in ('.venv', '.git', '__pycache__', 'outputs', 'tests')
               for part in member.split('/')) for member in members):
        raise ValueError('A development-only directory entered the archive.')
    report = dict(archive=str(output), archive_bytes=output.stat().st_size,
                  uncompressed_bytes=sum(p.stat().st_size for p in package.rglob('*') if p.is_file()),
                  packaged_files=len(expected), sha256=digest(output), source_commit=revision,
                  staging=str(package), archive_integrity='RAR test passed')
    output.with_suffix('.rar.sha256').write_text(f'{report["sha256"]}  {output.name}\n', encoding='ascii')
    output.with_suffix('.build.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--rar', type=Path, default=Path(r'C:\Program Files\WinRAR\Rar.exe'))
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.rar), indent=2))


if __name__ == '__main__':
    main()
