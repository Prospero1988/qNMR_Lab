# qNMR Lab — instrukcja użytkownika (PL)

## Uproszczona edycja ROI i katalog raportów

Całki na widmie i w tabeli są pokazywane z dwoma miejscami po przecinku.
To format wyświetlania: dane projektu i obliczenia zachowują pełną dokładność.
XLSX przechowuje pełne liczby, wyświetlane w komórkach całek jako 0,00;
CSV zachowuje dokładność danych źródłowych.

Podaj **Liczbę jąder** i zapisz ROI. Osobne potwierdzanie liczby protonów nie
jest wymagane. Dotyczy to również starszych projektów z dawnym znacznikiem
potwierdzenia. Liczba jąder nadal musi być dodatnia i odpowiadać sygnałowi.
Przed użyciem podzielonych lub wklejonych ROI sprawdź przypisania i liczbę jąder.

Po wyłączeniu **Użyj tego sygnału w obliczeniach ilościowych** pole **Powód
wykluczenia (opcjonalnie)** można pozostawić puste. Sygnał pozostaje w projekcie.

**Eksportuj raport** domyślnie otwiera katalog **reports** obok aplikacji.
Można wybrać inny folder. Dotyczy to DOCX, XLSX, CSV i kompletnego zestawu raportów.

## Substancja, niezależna próbka i pomiar

Lewy panel grupuje dane jako **substancja → niezależna próbka → pomiar**.
Dla jednego związku dodaj co najmniej trzy osobno przygotowane próbki i przypisz
im tę samą substancję. Kolejny pomiar tego samego roztworu dodawaj przez
**Powtórny pomiar**, po zaznaczeniu właściwej próbki. Przycisk dodania próbki
korzysta z zaznaczonej substancji jako domyślnego przypisania.

Po **Oblicz** tabela **Zbiorcze wyniki dla substancji** pokazuje osobno dla
każdej substancji n, średnią, SD, RSD, SEM i przedział ufności. Dwuklik wiersza
otwiera jej statystykę; można ją też wybrać w zakładce **Statystyka** lub w menu
prawego przycisku lewego panelu. DOCX i XLSX zawierają takie same osobne wyniki.

Najpierw uśredniane są sygnały w pomiarze, potem powtórne pomiary tej samej
próbki, a na końcu średnie niezależnych próbek. Każda niezależna próbka ma równą
wagę, nawet jeśli różni się liczba powtórnych pomiarów. Trzy próbki z odpowiednio
2, 1 i 3 pomiarami dają **n = 3**, a nie 6. Różnych substancji nie łączy się.

Status **Kompletny (co najmniej 3 próbki)** wymaga minimum trzech niezależnych
próbek i aktualnych wyników wszystkich uwzględnionych pomiarów. Przy n = 2
program nadal pokazuje możliwe do obliczenia statystyki, ale oznacza wynik jako
wstępny. Brakujący lub nieaktualny pomiar wymaga sprawdzenia i przeliczenia.
Status kompletności danych nie stanowi zatwierdzenia metody laboratoryjnej.

## Usuwanie elementów projektu

Zaznacz element po lewej i wybierz **Usuń zaznaczony element**, polecenie menu
prawego przycisku lub klawisz **Delete** przy aktywnym drzewie. Potwierdzenie
opisuje, co zostanie usunięte. Usunięcie próbki usuwa także jej pomiary;
usunięcie pomiaru usuwa jego osadzone dane, ROI i wyniki z projektu. Pliki
źródłowe na dysku pozostają zachowane. Zmianę trzeba zapisać w pliku projektu.

Usunięcie substancji lub wzorca pozostawia widma, a czyści odpowiednie
przypisania próbek i ROI. Próbki bez substancji trafiają do osobnej grupy.
Przypisz właściwą substancję/wzorzec, sprawdź sygnały i ponownie oblicz wyniki.
Jeśli chcesz zachować element w projekcie i jedynie pominąć go w obliczeniach,
użyj wykluczenia z uzasadnieniem w edytorze zamiast usuwania.

## Czytelna diagnostyka i statystyka

**Diagnostyka ROI** przedstawia grupy jakości sygnału, bazy i stabilności granic
oraz obserwacji do oceny. Liczby mają do pięciu cyfr znaczących i opisane jednostki;
wartości niedostępne, Tak/Nie i ostrzeżenia są zapisane słownie. Źródłowe dane
pozostają zachowane z pełną dokładnością.

Zakładka **Statystyka** pokazuje n, średnią, SD, RSD, SEM i przedział ufności,
tabelę przygotowań i statystykę składników. Wyjaśnia brak wyników, n < 2,
pominięte lub wykluczone próbki. Wartości historyczne nie stają się aktualnymi
wynikami wskutek samego wyświetlania.


## Kopiowanie ROI

**Kopiuj definicje ROI** kopiuje wszystkie obszary aktywnego widma do schowka
w formacie sześciu kolumn przyjmowanym przez **Wklej definicje ROI**: nazwa
sygnału, dolna granica, górna granica, stały identyfikator roli, liczba jąder,
ID związku. Otwórz docelowe widmo i użyj wklejania. Menu prawego przycisku tabeli
pozwala także skopiować tylko zaznaczone definicje. Zwykłe Ctrl+C nadal kopiuje
widoczne komórki tabeli. Wklejane ROI otrzymują nowe ID; sprawdź ich przypisania
i liczbę protonów. Kopiowanie przetwarzania jest osobnym działaniem.


## Skróty widma i oznaczenia całek

| Klawisz | Działanie |
|---|---|
| Z | Powiększanie zakresu ppm |
| P | Przesuwanie widma |
| F | Całe widmo |
| I | Zaznaczanie całki myszą |
| R | Usunięcie zaznaczonej całki |
| M | Interaktywna zmiana granic całki |
| D | Podział: przeciągnij krawędź całki do środka i puść w miejscu podziału |

Skróty działają na aktywnym widmie i nie usuwają ROI podczas wpisywania tekstu
w kontrolkach. Dwuklik na wykresie przywraca całe widmo.

Każdy obszar ma stałe ID **S1, S2, S3…**, widoczne na wykresie i w pierwszej
kolumnie tabeli. Usunięcie nie zmienia numerów pozostałych obszarów. Dwie części
podzielonego ROI otrzymują nowe ID; trzeba sprawdzić przypisania i ponownie
wpisać właściwą liczbę protonów każdej części.

Przy obszarze całki widnieje sama liczba, bez przedrostka. Stan kalibracji
opisuje panel pod widmem. Aby uzyskać całki względne, zaznacz
sygnał w tabeli lub kliknij jego obszar, wpisz np. **1** w **Ustaw zaznaczoną
całkę na** i kliknij **Kalibruj całki względne**. Inne wartości są równe
`I_i × wartość odniesienia / I_ref`. Po zmianie przetwarzania odniesienie nadal
ma przypisaną wartość, a pozostałe całki są aktualizowane. **Wyłącz kalibrację
względną** przywraca surowe wartości. Brak/usunięcie wzorca kalibracji nie
powoduje automatycznego wybrania innego sygnału.

Kolumna **Całka ze znakiem** zawsze zawiera surowe pole. Kalibracja względna
nie zmienia pól wejściowych do oznaczenia qNMR, liczby protonów ani wyników
zawartości. ID i kalibracja względna są zachowywane w projekcie.


[English manual](USER_MANUAL_EN.md)

## Instalacja i pierwsze uruchomienie

Rozpakuj cały katalog aplikacji i kliknij dwukrotnie `Start_qNMR_Lab.bat`.
Wymagany jest Windows x64 i CPython 3.12 x64. Przy pierwszym uruchomieniu program
tworzy lokalne środowisko `.venv`, instaluje wersje bibliotek wskazane w
`requirements-lock.txt`, sprawdza Qt i RDKit, a następnie otwiera aplikację.
Instalacja wymaga dostępu do Internetu lub kompletnego zestawu bibliotek w cache
pip. Kolejne uruchomienia wykorzystują gotowe środowisko bez ponownej instalacji.

Jeśli Python nie jest dostępny, launcher poda oficjalny adres pobrania.
Opcjonalne polecenie `Start_qNMR_Lab.bat -InstallLocalPython` pobiera podpisany
instalator Python Software Foundation, sprawdza podpis i instaluje interpreter
w katalogu `.runtime` aplikacji. Ta opcja nie została sprawdzona na komputerze
bez Pythona. Nie zmienia istniejących instalacji systemowych ani PATH.

`-PrepareOnly` przygotowuje środowisko bez otwierania programu. `-CheckOnly`
sprawdza już przygotowane środowisko. Uszkodzone lub niezgodne `.venv` nie jest
usuwane automatycznie — zmień nazwę tego lokalnego folderu przed odbudową.
Przy braku sieci działające środowisko nadal pozwala uruchomić aplikację.

## Język PL / ENG

Na czystej instalacji domyślnym językiem jest polski. Przycisk **PL → ENG**
w prawym górnym rogu przełącza program na angielski. Przycisk **ENG → PL**
przywraca język polski. Wybór jest zapamiętywany dla bieżącego użytkownika.

Zmiana języka zachowuje otwarty projekt, zakładki widm, zaznaczone ROI, zakresy
powiększenia i niewprowadzone jeszcze ustawienia przetwarzania. Nie powoduje
przeliczenia widm ani zmiany wyniku. W trakcie przetwarzania trzeba poczekać na
jego zakończenie przed przełączeniem języka.

Język obejmuje menu, przyciski, etykiety, okna edycji, komunikaty, diagnostykę,
opisy wykresów oraz nagłówki i stały tekst raportów DOCX/XLSX. **Pomoc →
Instrukcja użytkownika** otwiera wersję instrukcji odpowiadającą językowi
interfejsu. Raport jest generowany w języku wybranym w chwili eksportu.

Nazwy związków, identyfikatory, komentarze, SMILES, treść certyfikatów i pozostałe
zapisane dane analityka pozostają w oryginalnym języku. Nie są automatycznie
tłumaczone. Klucze JSON, identyfikatory ról oraz techniczne nagłówki CSV zachowują
stałą postać angielską, aby pliki można było odczytywać niezależnie od języka.

## Projekt i tożsamość chemiczna

Wybierz **Projekt → Dane projektu**, aby podać nazwę badania, cel, analityka,
komentarze i poziom ufności. Panel projektu rozdziela związki, materiały
odniesienia i niezależnie przygotowane próbki.

Zaznacz analit i wybierz **Edytuj zaznaczone** albo kliknij dwukrotnie wiersz
w zakładce **Struktury i wzorce**. Wprowadź nazwę i identyfikator. Wklej SMILES
i wybierz **Odczytaj SMILES / oblicz masę molową** lub wczytaj MOL/SDF.
Jeśli SDF zawiera kilka rekordów, wybierz właściwą strukturę. Program sprawdza
wartościowość i ładunki; odłączone fragmenty, np. przeciwjony, uwzględnia w masie
molowej i wzorze sumarycznym.

Zapisz postać materiału rzeczywiście odważonego. Sprawdź stechiometrię soli,
hydratację i solwatację. Obojętna cząsteczka macierzysta może nie odpowiadać
odważce. Można podać masę molową ręcznie bez struktury, lecz trzeba zapisać
źródło i uzasadnienie. Zmiana wartości wyliczonej przez RDKit również wymaga
uzasadnienia. Program podaje średnią masę molową w g/mol, nie masę monoizotopową.

Dwukrotne kliknięcie związku lub miniatury otwiera większą strukturę. Klikaj
numery atomów, aby je zaznaczać, używaj rolki do powiększania i przeciągaj, aby
przesuwać obraz. Numeracja zaczyna się od 0. W tym oknie można eksportować PNG
lub SVG. Symetria grafu nie jest traktowana jako dowód równoważności protonów NMR.

## Wzorzec wewnętrzny

Edytuj przykładowy tymol lub wybierz **Wzorce → Dodaj materiał odniesienia**.
Zapisz rzeczywistą certyfikowaną czystość w **% m/m**, certyfikat, serię,
identyfikator materiału, termin ważności, sygnały i liczbę protonów, uwagi oraz
status weryfikacji. Związek wzorca ma osobny edytor struktury i masy molowej.
Czystość 99,57% dotyczy tylko dostarczonego przykładowego materiału.

**Eksportuj bibliotekę wzorców** zapisuje lokalny JSON do wykorzystania w innym
projekcie. **Importuj bibliotekę wzorców** wczytuje takie materiały. Zmiana
wzorca przypisanego do próbki unieważnia aktualność wcześniejszych wyników.
Trzeba jawnie sprawdzić i zmienić przypisania istniejących ROI wzorca.

## Próbki i pomiary

**Dodaj próbkę** tworzy rekord niezależnego przygotowania. Wybierz analit
i wzorzec, podaj obie odważki, wspólną jednostkę masy (mg, g lub ug), rozpuszczalnik,
datę oraz uwagi. Wykluczenie próbki wymaga powodu. Tylko próbki oznaczone jako
przygotowane niezależnie zwiększają końcowe n.

**Importuj JDF** pozwala wybrać kilka konwencjonalnych FID protonowych. Dla
każdego nowego pliku otwiera się edytor przygotowania próbki. Jeśli kolejny
pomiar dotyczy tej samej fizycznej próbki, zaznacz ją i wybierz **Powtórny
pomiar**. Trafi pod ten sam rekord i nie zwiększy liczby niezależnych próbek.
Próbka bez pomiaru pozostaje widoczna jako niekompletna.

Obsługiwany jest wyłącznie surowy zespolony 1D JDF. Projekt `.jjh5` trzeba
wyeksportować w oprogramowaniu producenta jako konwencjonalny surowy FID ¹H
w formacie `.jdf`. qNMR Lab nie wymaga instalacji DOSY Lab ani oprogramowania
producenta do późniejszego przetwarzania plików JDF.

## Przetwarzanie i kalibracja

Przycisk **Wygląd…** nad widmem lub **Widma → Wygląd widma…** otwiera wybór
koloru głównej linii, grubości 0,5–6 px i siatki. Podgląd zmienia się od razu.
**Zapisz** zapamiętuje preferencje użytkownika, a **Anuluj** przywraca poprzedni
wygląd. Ustawienia dotyczą wszystkich otwartych i nowych widm, fazowania oraz
porównywania. Nie zmieniają danych, granic, całek ani wyników oznaczenia.

Każdy pomiar ma własną zakładkę widma. **Przetwarzanie** udostępnia LB, FWHM
Gaussa, dopełnienie zerami, PH0, PH1, punkt obrotu, przesunięcie kalibracji ppm,
opóźnienie filtra w próbkach oraz przycinanie pasma filtra cyfrowego.
Zmiana parametru automatycznie aktualizuje widmo, bez osobnego zatwierdzania.
Obliczenia pracują w tle; szybkie zmiany są łączone i wygrywa ostatnie ustawienie.
Nieprawidłowe ustawienia nie zastępują dotychczas wyświetlanego widma.
Wynik zawartości nadal wymaga świadomego użycia **Oblicz**.

Na kolejnych pomiarach tej samej próbki przycisk **Kopiuj przetwarzanie z
pierwszego widma próbki** stosuje parametry pierwszego pomiaru do własnego FID
otwartego pomiaru. Kopiowane są również maska i stan bazy oraz kalibracja ppm;
przy zmianie kalibracji granice ROI przesuwają się razem z osią. Początkowy model opóźnienia JEOL i zgrubna
faza PH0 są widoczne i edytowalne. Nieobsługiwane metadane nie uruchamiają
zgadywania uniwersalnego opóźnienia. Analityk sprawdza fazę i kalibrację wobec
odpowiednich odniesień.

**Faza** otwiera podgląd na buforowanym FFT. Lewy i prawy pionowy ruch zmieniają
PH0 i PH1; Shift zwiększa precyzję. Przesunięcie punktu obrotu przelicza PH0 tak,
aby nie zmieniać istniejącej funkcji fazy. Zastosuj fazę albo anuluj bez zmian
w projekcie. Podgląd fazy nie obejmuje odejmowania linii bazowej.

Kalibrację wykonuje się interaktywnie. Wpisz **Docelowe ppm wzorca**, włącz
**Wskaż wzorzec na widmie** i kliknij wybrany sygnał. Kliknięty punkt otrzyma
podaną wartość ppm. Oś, ROI, maski bazy i punkt obrotu fazy przesuną się razem;
FID, intensywności i istniejąca funkcja fazy pozostaną zachowane. Nie wpisuje
się ręcznie przesunięcia osi.

## Linia bazowa

Kliknij widoczny przycisk **Baza…** i przeciągnij po fragmentach bez sygnałów.
Niebieskie obszary można przesuwać i zmieniać ich granice myszą. Prawy przycisk
na obszarze udostępnia jego usunięcie. Po zmianie obszarów lub stopnia wielomianu
dopasowanie aktualizuje się automatycznie. Żółty podgląd pokazuje dopasowany wielomian na widmie bez korekcji —
nie został jeszcze odjęty. Wybierz stopień 1–5, sprawdź podgląd i dopiero wtedy
użyj **Zastosuj korekcję bazy**. Skorygowane widmo rzeczywiste jest domyślnie turkusowe,
a matematyczne zero ma poziomą linię przerywaną.

Dokładne przedziały można wpisać przez **Wpisz zakresy bazy…**. Zatwierdzona
maska nie może przecinać ilościowych ROI. Program odrzuca dopasowanie przy zbyt
małej liczbie punktów lub niestabilnym układzie. Oceń ROI poza zakresem tła,
gdzie model jest ekstrapolowany. Dostępna jest zwykła korekcja bazy, bez usuwania
artefaktów presaturacji i bez modelu ogona rozpuszczalnika.

## Ilościowe ROI i przypisania

Domyślnie lewy przycisk powiększa zakres ppm. Rolka zmienia tylko wysokość
wyświetlania; środkowy przycisk przesuwa widmo. W trybie **Dodawanie ROI
ilościowego** przeciągnij przedział i podaj identyfikator sygnału, rolę, związek,
liczbę jąder, ewentualne atomy lub grupy, ocenę jakości oraz komentarze.
Zapisanie podanej liczby protonów wystarcza. Wybór atomów nie wyznacza automatycznie
równoważności chemicznej ani liczby jąder danego sygnału.

**Edycja granic ROI** uaktywnia uchwyty. W trybie powiększania nie przechwytują
one gestów. Dwukrotne kliknięcie wiersza ROI otwiera edytor dokładnych granic
i przypisań. Niewłaściwy sygnał można wykluczyć; powód jest opcjonalny, a ROI i jego
całka pozostają zapisane. Usunięcie definicji zapisuje zdarzenie audytowe.
Brak wybranego sygnału wzorca powoduje błąd obliczenia, a nie automatyczny wybór
zastępczego sygnału.

Role obejmują analit, wzorzec, wodę, rozpuszczalnik, zanieczyszczenie, inny
składnik i sygnał nieprzypisany. Dodatkowy oznaczany składnik wymaga własnego
rekordu związku ze zweryfikowaną masą molową. Sygnały nieprzypisane mogą pozostać
w projekcie bez udziału w obliczeniu zawartości.

**Wklej definicje ROI** przyjmuje kolumny oddzielone tabulatorami: `sygnał`,
`dolna granica ppm`, `górna granica ppm`, `rola`, `liczba jąder` i opcjonalnie
`ID związku`. Używaj stałych identyfikatorów ról: `analyte`, `standard`, `water`,
`solvent`, `impurity`, `other`, `unassigned`. Liczby w tym formacie używają kropki
dziesiętnej. Sprawdź wklejone przypisania i liczby protonów; nie ma osobnego potwierdzenia.

```text
Analit CH2	5.01	5.10	analyte	2
Wzorzec aromatyczny	6.47	6.55	standard	1
```

Pola tekstowe obsługują zwykłe wklejanie. W tabelach można zaznaczać wiersze
i kopiować Ctrl+C lub z menu kontekstowego. Komórki obliczone są tylko do
odczytu — edytuj dane źródłowe zamiast nadpisywać wynik.

## Sygnały wzorca, ilorazy i diagnostyka

Potrzebny jest przynajmniej jeden zaakceptowany sygnał analitu i wzorca.
W edytorze ROI wybierz konkretny sygnał lub sygnały wzorca. Brak wyboru oznacza
wszystkie zaakceptowane sygnały wzorca. Użycie kilku wymaga jawnego potwierdzenia
ich zgodności; bez niego obliczenie się zatrzyma. Obliczenia parami są zachowane,
a dopiero potem zgodne sygnały wzorca otrzymują równą wagę w średniej dla ROI.

Surowe zmierzone całki zachowują znak. Wyświetlane całki na jądro i stosunki
molowe ich nie zmieniają. Nie odejmuje się linii łączącej końce ROI i nie
normalizuje pików analitu oddzielnie. Całki ujemne lub obszary o obu znakach
powodują ostrzeżenie, ale mogą zostać świadomie zachowane. Zerowy mianownik
wzorca jest błędem matematycznym.

**Diagnostyka ROI** pokazuje oszacowanie szumu i S/N, średnią w tle, nakładanie
ROI, stosunek RMS części urojonej do rzeczywistej, oba znaki i wrażliwość na
zmianę granic o jeden krok siatki. Są to wskazówki do oceny. Część urojona nie
dowodzi sama w sobie błędu fazy, a brak ostrzeżenia nie dowodzi braku nakładania.
Żadna heurystyka nie wyklucza sygnału automatycznie.

## Porównywanie widm i szablony

Przełączaj zakładki lub wybierz **Widma → Porównaj widma obok siebie**.
Porównanie ma wspólną oś ppm i niezależne skale intensywności.
**Synchronizuj osie ppm** łączy otwarte zakładki analityczne. Szablon ROI można
skopiować do pomiaru z tym samym analitem i wzorcem; zastąpienie wymaga
potwierdzenia.

**Zaproponuj dopasowanie szablonu do pików** wyszukuje lokalne maksimum modułu
w zakresie domyślnie ±0,04 ppm. Pokazuje propozycję przesunięcia każdego ROI.
Potwierdź ją i sprawdź granice na widmie docelowym. Prosta metoda maksimum może
wybrać zanieczyszczenie lub nakładający się sygnał; nie ustala tożsamości chemicznej.
Granice pozostają niezależnie edytowalne.

## Wyniki i statystyka

Po ocenie sygnałów wybierz **Oblicz** (F5). Dla każdego zaakceptowanego sygnału
program liczy wszystkie wybrane pary analit–wzorzec, a następnie średnią zgodnych
sygnałów wzorca. Zaakceptowane sygnały analitu są uśredniane w obrębie pomiaru,
powtórne pomiary — w obrębie tej samej fizycznej próbki. Na końcu niezależne
próbki otrzymują równą wagę.

**Wyniki** pokazują ilorazy, mmol, masę składnika i zawartość. **Statystyka**
przedstawia średnie próbek, SD z ddof=1, RSD, SEM i przedział ufności Studenta.
SD w obrębie pomiaru opisuje rozrzut sygnałów. Dla skorelowanych sygnałów
i powtórnych pomiarów nie podaje się inferencyjnego SEM ani przedziału ufności.
Różnych analitów nie łączy się we wspólnej średniej; wybierz ich osobne wyniki
w zakładce Statystyka.

Zmiana danych lub ustawień liczbowych oznacza wcześniejsze wyniki jako
historyczne. Pozostają zapisane, lecz do czasu jawnego przeliczenia nie wchodzą
do aktualnej statystyki końcowej. Brak aktualnego wyniku któregokolwiek
uwzględnionego pomiaru powoduje wstępny status podsumowania. Zmiana samego języka
nie zmienia aktualności wyników. SD i SEM nie są pełnym budżetem niepewności.

## Zapis i eksport

Zapisz `.qnmr` przez Ctrl+S. Archiwum zawiera struktury, wzorce, odważki,
SHA256 źródeł, osadzony FID i widmo przetworzone, historię przetwarzania,
przypisania ROI/atomów, wykluczenia i zapisane wyniki. Otwarcie nie powoduje
cichego przetwarzania. Domyślny katalog zapisu i otwierania to **projects** obok
aplikacji. Wybór innego katalogu jest możliwy w oknie plików.

Projekt jest całkowicie samodzielny: do otwarcia, przetwarzania i analizy
wystarczy jeden plik `.qnmr`. Oryginalne JDF, katalogi źródłowe, dyski sieciowe
ani komputer autora nie są potrzebne. Zwykłe otwieranie nie próbuje czytać ani
sprawdzać dostępności źródeł. Zachowane ścieżki i SHA256 służą identyfikowalności.
Opcjonalne ponowne wskazanie źródła wymaga zgodnej sumy SHA256.

**Eksportuj raport** udostępnia DOCX, XLSX, CSV i komplet plików. Komplet zawiera
raport, tabele, całki, obrazy widm PNG i JSON identyfikowalności. **Eksportuj
widmo** pozwala zapisać PNG lub wszystkie przetworzone punkty widma w CSV.
PNG/SVG struktur eksportuje się z przeglądarki struktury.

Raport ma język bieżącego interfejsu, przy zachowaniu oryginalnych danych
analityka. Wskazuje wyniki historyczne i wstępne. Nie wymyśla podpisów,
zatwierdzeń, akredytacji, potwierdzenia relaksacji ani wniosków o wartościach
odstających. Generowanie DOCX nie wymaga Worda ani LibreOffice. Wbudowany
eksport do PDF nie jest dostępny.

## Przykład syntetyczny i import arkusza

**Projekt → Otwórz przykład syntetyczny** otwiera gotowe trzy próbki z FID,
przetwarzaniem, ROI i aktualnymi wynikami. Dane służą do ćwiczeń i testów;
nie są wynikiem badania laboratoryjnego. Można też otworzyć projekt z katalogu
examples albo importować osobno trzy dołączone syntetyczne JDF.

**Importuj arkusz referencyjny** przyjmuje lokalny arkusz w opisanym układzie
i jedno badanie na projekt. Nie odtwarza surowego FID z ilorazów całek.
Prywatne arkusze i raporty porównawcze nie są częścią publicznej dystrybucji.
Opis formatu i porównań: [EXCEL_COMPARISON_PL.md](EXCEL_COMPARISON_PL.md).
