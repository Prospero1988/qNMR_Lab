# Weryfikacja oprogramowania i zakres

## Wydanie 1.0.2

Lokalny zestaw: **154 testy zaliczone**, w tym 21 przypadków nowej diagnostyki.
Na GitHubie dwa testy prywatnego arkusza są opcjonalne. Sprawdzono potwierdzanie
i zapis odpowiedników bez unieważniania wyników, brak utożsamiania sygnałów po
S1/S2 lub ppm, przypisania atomowe, niejednoznaczności, wykluczenia, nieaktualne
wyniki, brakujące przypisania, niepełne i nierówne liczby powtórnych pomiarów,
n = 0/1/2 oraz oddzielne substancje. SD diagnostyczne używa n − 1, bez testu
istotności. Wykresy zachowują malejącą oś ppm i nie zmieniają tablic.

Na lokalnym projekcie referencyjnym porównano dokładnie 14 996 istniejących
wartości liczbowych, model, wyniki, średnie, SD, RSD i przedziały ufności.
Skróty tablic widm oraz źródeł silnika pozostały identyczne. Potwierdzenia
odpowiedników zapisano oddzielnie od wyników; oryginalny projekt i raport
pozostały niezmienione. Raporty PL/ENG wyrenderowano Word → PDF → PNG i
sprawdzono wizualnie. Prywatne dokumenty i dane nie trafiają do dystrybucji.

## Generator raportów 1.0.1

Publiczny zestaw: **131 testów zaliczonych, 2 pominięte** z powodu opcjonalnego
prywatnego arkusza. Nowe testy sprawdzają formaty liczb i jednostek, oba języki
i profile, brak słowników/JSON w treści, dane brakujące i zagnieżdżone,
wykluczenia, wyniki historyczne, niezależność próbek, A4, tabele, podpisy,
hiperłącza i struktury. Snapshoty danych i skróty tablic pozostają identyczne.
Na lokalnym raporcie trzech próbek porównano 238 wartości/stanów z oryginalnym
DOCX, z uwzględnieniem jego drukowanego zaokrąglenia. Dokumenty są renderowane
Word → PDF → PNG do kontroli układu; źródła prywatne pozostają poza GitHubem.

## Wydanie publiczne 1.0

Wykonany zestaw publiczny: **112 testów zaliczonych, 2 pominięte**. Pominięte
przypadki wymagają prywatnego arkusza. Zapis jest w validation/test_results.txt.

Dokument rozróżnia sprawdzenie programu od walidacji metody laboratoryjnej.
Wydanie 1.0 zawiera aplikację, instrukcje, przykłady syntetyczne i odtwarzalne
testy publiczne. Nie zatwierdza warunków pomiaru ani metody oznaczenia.
Numer aplikacji i konwencji obliczeń pierwszego wydania publicznego to 1.0.0.

## Odtwarzalne sprawdzenia

Testy obejmują import zespolonych JDF, metadane i nagłówki, FFT, apodyzację,
dopełnienie zerami, fazę i pivot, korekcję bazy oraz całkowanie ze znakiem
z interpolacją granic. Zamrożone wyniki syntetyczne silnika znajdują się w
validation/engine_golden.npz. Sprawdzenie regresji nie wymaga DOSY Lab ani
dostępu do komputera autora.

Testy chemiczne obejmują struktury, masy molowe, sole, pochodzenie ręcznych
wartości masy i wybór atomów. Testy ilościowe porównują wyniki z niezależnie
wyliczonymi wartościami, z jawnymi jednostkami masy i czystości. Sprawdzane są
błędne dane, ujemne całki, wybór wzorca i aktualność wyników.

Hierarchię sprawdza przykład trzech próbek o średnich 90, 100 i 110, z liczbami
pomiarów odpowiednio 2, 1 i 3. Wynik substancji ma średnią 100, SD próby 10
i n równe 3. Druga substancja otrzymuje osobny wynik. Wykluczenia, brakujące
lub historyczne wyniki oraz minimalna liczba trzech próbek są sprawdzane
osobno. Powtórny pomiar nie staje się nową niezależną próbką.

Testy Qt obejmują edycję i podział ROI, opcjonalny powód wykluczenia, zapis
liczby jąder bez dodatkowego checkboxa, przetwarzanie na żywo, usuwanie,
kalibrację względną, wygląd widma, PL/ENG i domyślne katalogi. Testy projektu
otwierają zapisane dane po usunięciu źródeł. Sprawdzenia eksportu ponownie
odczytują DOCX/XLSX i porównują liczby oraz identyfikowalność.

## Przykłady i opcjonalne porównania lokalne

Dołączona analiza trzech próbek oraz pliki JDF są syntetyczne. Sprawdzają
przebieg pracy programu; nie są pomiarami laboratoryjnymi ani dowodem walidacji
oznaczenia. Skończone granice całek dają średnią bliską nominalnym 95 procentom,
zamiast wartości dopasowanej sztucznie do dokładnie 95.

Dwa testy opcjonalnego arkusza lokalnego są pomijane, jeśli brakuje pliku
validation/reference/qNMR.xlsx. Prywatne arkusze, raporty, wyciągnięte dane i
manifesty lokalnego repozytorium źródłowego nie są dystrybuowane. Lokalny komplet
deweloperski wcześniej zaliczył 114 testów. Wynik bieżącego zestawu publicznego
jest w validation/test_results.txt. Pominięcie danych prywatnych nie oznacza
wykonania związanych z nimi sprawdzeń w publicznym wydaniu.

## Wygląd i deployment

Obrazki README przedstawiają działającą aplikację na danych symulowanych,
w obu językach. Obejmują widmo z ID i wartościami całek, wyniki substancji
i statystykę niezależnych próbek. Testy poza ekranem nie zastępują pełnej oceny
natywnego zachowania myszy i menedżera okien.

Mała paczka zawiera kod wykonawczy, instrukcje, przykłady i licencje, manifest
sum plików oraz sumę archiwum. Wypakowana kopia jest sprawdzana pod względem
importu, samodzielności projektów, języków, obliczeń i usuwania rekordów.
Biblioteki są instalowane przy pierwszym uruchomieniu.

## Ograniczenia

Relaksacja, równoważność sygnałów, nakładanie, baza i postać odważonego materiału
pozostają do oceny analityka. Heurystyki nie dowodzą poprawności ilościowej.
SD/SEM i przedziały ufności nie są pełnym budżetem niepewności. Nie wykazano
odtworzenia oznaczeń z oryginalnych FID laboratoryjnych ani działania we wszystkich
awariach sieci/proxy i świeżej instalacji bez Pythona. Szczegóły podają metody
naukowe i instrukcja instalacji.
