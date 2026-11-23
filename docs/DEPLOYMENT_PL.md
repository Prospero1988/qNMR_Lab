# qNMR Lab 1.0 PL/ENG — uruchomienie na drugim komputerze

## Domyślny zapis raportów

Raporty są domyślnie zapisywane w katalogu `reports` obok aplikacji. Można
wybrać inny katalog. Projekty nadal domyślnie trafiają do `projects`.

## Zmiany w tej paczce

Usuwanie elementów projektu z lewego panelu, drzewo substancja → próbka → pomiar,
wyniki łączne każdej substancji i przełączanie jej statystyk. Co najmniej trzy
niezależne próbki są wymagane do statusu kompletnego; powtórne pomiary nie
zwiększają n. Instrukcje PL i ENG opisują cały przebieg pracy.

## Nowe sterowanie i samodzielne projekty

Wersja 1.0 dodaje przetwarzanie na żywo, bazę edytowaną myszą, kalibrację ppm
przez wskazanie sygnału, skróty Z/P/F/I/R/M/D, ID i wartości całek na widmie,
kalibrację całek względnych, kopiowanie ROI i ustawień pierwszego pomiaru próbki.
Domyślny katalog projektów to `projects`. Jeden plik `.qnmr` wystarcza do
otwarcia i ponownej analizy — oryginalne widma nie są wymagane.


[English deployment instructions](DEPLOYMENT_EN.md)

1. Rozpakuj **cały** folder `qNMR_Lab`, np. do `C:\qNMR_Lab`.
   Nie uruchamiaj aplikacji bezpośrednio z okna WinRAR.
2. Kliknij dwukrotnie `Start_qNMR_Lab.bat`.
3. Pierwsze uruchomienie tworzy `.venv` i instaluje przypięte biblioteki.
   Potrzebny jest Internet. Później środowisko jest używane ponownie.

Wymagania: Windows x64 oraz Python 3.12 x64. DOSY Lab i dyski D:/J: autora nie
są potrzebne. Jeśli brakuje Pythona, launcher poda oficjalną stronę pobrania.
Opcjonalnie można uruchomić `Start_qNMR_Lab.bat -InstallLocalPython`, aby
pobrać podpisany instalator i zainstalować interpreter lokalnie w aplikacji.
Ta opcja nie była sprawdzana na komputerze bez Pythona i nie zmienia istniejących
instalacji. Komunikaty przygotowania środowiska można wybrać parametrem
`-Language pl` lub `-Language en`.

## PL / ENG

Polski jest domyślny. Przycisk **PL → ENG** w prawym górnym rogu przełącza
interfejs na angielski; **ENG → PL** przywraca polski. Wybór jest zapamiętywany.
Przełączanie zachowuje projekt, dane, wyniki, zakładki i powiększenie.
Nazwy i komentarze analityka nie są automatycznie tłumaczone.

Instrukcje i metody naukowe znajdują się w `docs` w obu wersjach. **Pomoc →
Instrukcja użytkownika** otwiera aktualny język. Raporty DOCX/XLSX i opisy
wykresów używają języka wybranego w momencie eksportu. Techniczne klucze JSON
i nagłówki CSV pozostają stabilne niezależnie od języka.

## Szybkie sprawdzenie

- **Projekt → Otwórz przykład syntetyczny**: obliczenia trzech syntetycznych próbek.
- **Otwórz → examples/synthetic_three_samples.qnmr**: trzy syntetyczne widma z ROI.
- **Importuj JDF → examples/synthetic_P01.jdf** (lub P02/P03): import surowego FID.
- Polska instrukcja: `docs/USER_MANUAL_PL.md`; angielska: `docs/USER_MANUAL_EN.md`.

Obsługiwany jest konwencjonalny surowy JEOL JDF 1D. `.jjh5` nie jest obsługiwany.
Przykłady syntetyczne nie są wynikami laboratoryjnymi. Zmianę statystyki względem
raportu referencyjnego opisują `docs/EXCEL_COMPARISON_PL.md` i wersja `_EN.md`.

Paczka zawiera aplikację, launcher, instrukcje, licencje, przykłady syntetyczne.
Nie zawiera `.venv`, Git, cache, testów ani raportów deweloperskich. Pełne dowody
walidacyjne pozostają w repozytorium źródłowym. Manifest zapisuje rewizję i sumy.
Biblioteki Qt, RDKit, NumPy i SciPy po instalacji ponownie zajmą kilkaset MB lub
więcej — mały RAR nie jest pojedynczym samodzielnym EXE.
