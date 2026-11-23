# Contributing

Use an issue to describe a reproducible problem or proposed improvement. Include
the application version, Windows/Python versions, steps and expected behavior.
Use synthetic or otherwise shareable examples in issues and pull requests.

## Development

Use CPython 3.12 x64 on Windows. The normal launcher prepares pinned runtime
dependencies. Install the development requirements in that environment:

```powershell
.\Start_qNMR_Lab.bat -PrepareOnly
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

The public suite covers synthetic raw import, processing, chemistry, signed
assay, hierarchical statistics, portable projects, Qt interactions and exports.
Tests needing an optional private reference workbook skip when it is absent.
Do not commit virtual environments, project/report content, credentials or local outputs.

For numerical changes, document the equation/convention and include an independent
expected result. For interface changes, verify PL and ENG and inspect the result.
Preserve existing scientific snapshots unless an explicit recalculation is requested.

## Distribution

The repository is MIT licensed; preserve the original DOSY Lab notice and
third-party attribution. Build a small deployment using a locally installed
WinRAR encoder; it excludes environments, caches and private reference files:

```powershell
.\.venv\Scripts\python.exe tools/build_deployment.py --output outputs/qNMR_Lab_1.0_PL_EN_deployment.rar
```

The deployment includes a file-hash manifest and an archive checksum. Test a
freshly extracted copy before publishing a release. Run the Windows test workflow
for pull requests and changes on main.
