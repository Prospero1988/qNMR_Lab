# Podręcznik dewelopera (PL)

## Warstwa raportów DOCX

`report_data.py` odczytuje zapisany model, `report_format.py` formatuje liczby
i wartości strukturalne, `report_text.py` zawiera etykiety PL/ENG,
`report_figures.py` rysuje istniejące tablice i cząsteczki, a
`report_document.py` składa dokument z powtarzalnych komponentów. `reports.py`
zachowuje publiczny punkt wejścia `export_docx(..., profile='standard')`.
Profil `extended` jest opcjonalny. Wersja formatu raportu to 2; konwencja
obliczeń pozostaje 1.0.0. Nie wywołuje się przetwarzania ani calculate_project.

## Uproszczenia w 1.0

Zapis ROIDialog oznacza podaną liczbę jąder jako zaakceptowaną. Zachowano pole
`protons_confirmed` dla zgodności starszych projektów i odcisków, ale jego dawna
wartość False nie blokuje obliczeń. Dodatnie i skończone liczby jąder nadal
sprawdza funkcja assay. Powód wykluczenia ROI jest opcjonalny; wymagania dotyczące
wykluczania całych próbek/pomiarów pozostają osobne.

Format całek .2f jest wyłącznie prezentacją. `reports_directory()` tworzy
domyślny katalog eksportu raportów. Deployment zawiera `reports/.gitkeep`.

## Zarządzanie rekordami i wyniki substancji w 1.0

`project_edit.py` zawiera `deletion_details` i `delete_record`. Usunięcie
próbki/pomiaru usuwa rekordy z modelu, nigdy pliki zewnętrzne. Usunięcie związku
lub wzorca czyści zależne przypisania. Wzorce mają osobne ID materiału i związku;
usunięcie jednej partii nie zmienia próbek przypisanych do innej partii tego
samego związku. Nie wybiera się zastępczego wzorca automatycznie.

GUI blokuje usuwanie podczas przetwarzania, potwierdza zależności, zamyka
usunięte zakładki i aktualizuje źródło kopiowania przetwarzania. Dane UserRole
drzewa są normalizowane do tuple po konwersji QVariantList przez Qt.

`project_summary(project, analyte_id=...)` ogranicza istniejącą hierarchię do
jednej substancji. `substance_summaries` dodaje stan kompletności n >= 3 bez
zmiany wzoru oznaczenia lub wersji odcisku obliczeń. `StatisticsPanel` udostępnia
wybór substancji, a GUI i eksporty DOCX/XLSX używają osobnych wyników. Testy
obejmują nierówne liczby powtórzeń, różne substancje, usuwanie i zmianę języka.

## Prezentacja w wersji 1.0

`spectrum_settings.py` zawiera model wyglądu i edytor z podglądem. Preferencje
są zapisywane w lokalnym QSettings użytkownika. Nie są częścią parametrów
przetwarzania, projektu ani odcisku obliczeń. `PhaseWindow` importuje ten sam
model. `ROIDiagnosticsDialog` i `StatisticsPanel` formatują istniejące dane,
bez ponownego obliczania lub modyfikowania ich źródła.


## Interakcja w wersji 1.0

Przetwarzanie ma jedno zadanie w tle, opóźnienie 75 ms łączące szybkie edycje
i numer żądania: wynik starszy od najnowszej edycji nie może zostać zatwierdzony.
Widżety pozostają aktywne. Zatwierdzanie tablic i całek jest atomowe; obliczenia
zawartości oraz eksport/zapis czekają na zakończenie żądań.

Fazowanie przechowuje język przekazany przez właściciela okna. Kalibracja ppm
przesuwa oś, ROI, maskę i pivot razem. Kopiowanie przetwarzania używa FID celu
i zachowuje ID pomiaru źródłowego w historii. ROI mają etykiety w
`Measurement.roi_labels` i rosnący `next_roi_number`; UUID pozostaje tożsamością
odniesień. `integration_reference_id/value` dotyczą prezentacji względnej.
Etykiety i względna skala nie wchodzą do odcisku obliczeń. Nowe pola są
opcjonalne podczas odczytu starszych projektów; konwencja obliczeń pozostaje 1.0.0.


[English developer guide](DEVELOPER_GUIDE_EN.md)

## Środowisko i polecenia

Windows x64, CPython 3.12. Punkt wejścia to `python -m qnmr` uruchomiony z katalogu
projektu. `Start_qNMR_Lab.bat` wywołuje `tools/bootstrap.ps1`.
Pełne zależności z przypiętymi wersjami są w `requirements-lock.txt`; bezpośrednie
w `requirements.txt`. Zestaw deweloperski dodaje pytest.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools\create_demo.py
```


## Granice modułów

| Moduł | Odpowiedzialność |
|---|---|
| `models.py` | Modele projektu, związków, materiałów, przygotowań, pomiarów i ROI. |
| `jeol.py` | Import surowego JDF 1D, metadane i model opóźnienia filtra. |
| `processing.py` | Niezmienne przetwarzanie widma i całka trapezowa z interpolacją. |
| `analysis.py` | Powiązanie pomiaru z przetwarzaniem, diagnostyka, szablony i propozycje dopasowania. |
| `chemistry.py` | RDKit, SMILES/MOL/SDF, walidacja, średnia masa i rysunki. |
| `quantification.py` | Jednostki, równanie, odciski wyników, agregacja i statystyka hierarchiczna. |
| `storage.py` | Wersjonowany ZIP projektu, SHA256, NPZ i biblioteka wzorców. |
| `excel_reference.py` | Odczyt i porównanie dostarczonego laboratoryjnego układu arkusza. |
| `reports.py` | Eksport DOCX/XLSX/CSV/PNG/JSON po jawnym obliczeniu. |
| `dialogs.py` | Edytory struktur, próbek i ROI oraz przeglądarka atomów. |
| `gui.py` | Okno główne, zakładki pomiarów i zadanie przetwarzania w tle. |
| `spectrum_view.py`, `phase_window.py` | Nawigacja i buforowany podgląd fazy zaadaptowane z DOSY Lab. |
| `i18n.py`, `_catalog.py` | PL/EN, ustawienie języka, komunikaty, prezentacja danych i katalog tłumaczeń. |

Moduły naukowe nie importują klas GUI. Wykresy raportowe używają Matplotlib Agg,
a struktury RDKit Cairo/SVG. Nowe tablice są zatwierdzane dopiero po poprawnym
przetworzeniu i sprawdzeniu ROI. Oczekujące wyniki nie są eksportowane jako gotowe.

## Lokalizacja

`tr()` tłumaczy stały klucz angielski i podstawia nazwane parametry. Dane
analityka nie są tłumaczone. `message()` tłumaczy przechowywane komunikaty przy
wyświetleniu. `LEGACY_EN` mapuje pierwotne polskie komunikaty DOSY na angielskie
klucze, aby angielski interfejs nie pozostał częściowo polski.

Role i stany mają stałe wartości. `enum_items()` przechowuje identyfikator w
`QComboBox.userData`; `enum_value()` zwraca identyfikator, nie widoczną etykietę.
Nie używaj przetłumaczonego `currentText()` w obliczeniach lub zapisanym modelu.
Tak samo wybór formatu eksportu rozpoznaje wzorzec rozszerzenia, a nie nazwę
filtra w danym języku.

Przełączanie języka odbudowuje wyłącznie widżety w tym samym oknie. Zachowuje
tożsamość projektu i tablic, ścieżkę, stan niezapisanego projektu, otwarte
zakładki, zakresy, wybrane ROI i oczekujące parametry. Nie wolno przełączać
w trakcie przetwarzania. Ustawienie użytkownika znajduje się w oddzielnym
`QSettings('qNMR Lab', 'Desktop')`; brak ustawienia oznacza PL. Standardowe
dialogi Qt używają tłumaczenia `qtbase_pl` lub oryginalnego angielskiego tekstu.

Wersja interfejsu `__version__` jest oddzielona od `CALCULATION_VERSION`.
Wydanie tłumaczeń 1.0 nadal używa obliczeń 1.0.0, więc zapisane wyniki nie
stają się nieaktualne tylko z powodu języka. Zmiana algorytmu wymaga świadomej
zmiany wersji obliczeń i sprawdzenia zgodności historycznych projektów.

## Schemat projektu 1

`.qnmr` to ZIP z `project.json` i NPZ dla każdego pomiaru. Koperta JSON zapisuje
wersję aplikacji, model i SHA256 tablic. Tablice obejmują FID, ppm, widmo po
fazowaniu, bazę i skorygowane widmo zespolone. NPZ odczytuje się z
`allow_pickle=False`; pliki nie są wypakowywane na dowolne ścieżki. Zapis do
pliku tymczasowego kończy się atomowym zastąpieniem celu.

Nieznany schemat jest błędem. Migracja wymaga jawnej decyzji; nie interpretuj
starych brakujących ustawień nowymi automatycznymi domyślnymi parametrami.
Zwykłe `load_project()` nie wykonuje dostępu do plików źródłowych. Opcjonalne
`verify_sources=True` włącza audyt ich dostępności i SHA256. Osadzony FID jest
jedynym wejściem ponownego przetwarzania projektu. `projects_directory()` tworzy
lokalny katalog `projects` używany przez okna Otwórz/Zapisz jako.

Odcisk obliczeń uwzględnia związki, materiał odniesienia, dane próbki,
parametry, definicje i całki ROI, diagnostykę, SHA widma oraz potwierdzenie
zgodności wzorców. Zmiana odcisku zachowuje wynik jako historyczny i wyłącza go
z aktualnej statystyki. Zmiana ścieżki źródła lub języka nie przetwarza danych.

## Testy i wydawanie paczek

Testy obejmują import 1D w obu kolejnościach bajtów i precyzjach, rzeczywisty JDF,
regresję zamrożonych tablic oryginalnego silnika, fazę, bazę, całkę ze znakiem,
masy molowe i struktury, jednostki i czystość, hierarchię powtórzeń, wszystkie
wyniki referencyjnego arkusza, zapis/odczyt, eksporty i launcher.

Testy Qt offscreen używają rzeczywistych widżetów, ale nie zastępują oceny
zachowania natywnych okien. Dodatkowe testy PL/EN sprawdzają zapisane wyniki,
przypisania ról, otwarte widma, powiększenie, oczekujące ustawienia, raporty obu
języków, kompletność katalogu i wybór instrukcji. Nie zapisują preferencji
językowej rzeczywistego użytkownika.

`tools/build_deployment.py --output pełna_ścieżka.rar` tworzy mały RAR z jawnej
listy plików, sprawdza integralność i zapisuje manifest. Nie pakuje `.venv`,
Git, cache, testów ani wyników. Wersje PL i EN dokumentów oraz katalog tłumaczeń
muszą znaleźć się w paczce. Komercyjny program RAR jest używany lokalnie,
nie jest redystrybuowany.

Repozytorium lokalne pracuje na `main`, bez remote. Przed tagiem wydania należy
wykonać wymagane testy, porównanie naukowe, audyt źródła i sprawdzenie GUI oraz
raportów. Nie deklaruj pełnej walidacji laboratoryjnej bez odtworzenia pracy
na oryginalnych FID badania. Aktualny stan: [VALIDATION_PL.md](VALIDATION_PL.md).

## Wydanie publiczne

Kod publiczny jest w https://github.com/Prospero1988/qNMR_Lab. Oryginalna
lokalna historia i prywatne materiały laboratoryjne pozostają poza repozytorium.
Publiczne przykłady są syntetyczne; testy arkusza lokalnego są opcjonalne.
Sprawdź PL/ENG, testy Windows i świeżo wypakowany deployment przed wydaniem.
Użyj CONTRIBUTING.md dla poleceń instalacji, testów i budowania paczki.
