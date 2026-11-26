# Raporty naukowe qNMR Lab

## Uzupełnienia w wersji 1.0.2

Równanie zawiera edytowalne ułamki i indeksy matematyczne oraz tabelę symboli.
Odważka próbki oznacza cały badany materiał, a czystość wzorca jest ułamkiem
masowym 0–1. Nie zmieniono sposobu obliczania oznaczenia.

Pełne widma pozostają w raporcie. Jeśli kilka uwzględnionych ROI analitu jest
skupionych, raport standardowy dodaje powiększenie tego obszaru z granicami,
lokalnymi ID i zapisanymi przypisaniami ppm. Skala intensywności powiększenia
jest niezależna; widma nie są ponownie przetwarzane.

**Projekt → Odpowiedniki rezonansów…** pozwala wpisać wspólną nazwę dla
odpowiadających sobie ROI w różnych pomiarach. Propozycje z nazw sygnałów są
tylko propozycjami: zapis następuje po **Potwierdź odpowiedniki i zapisz**.
Jednoznaczne przypisania do tych samych atomów tego samego związku są używane
automatycznie; grupy mogą rozróżniać rezonanse na tym samym atomie. Lokalne
S1/S2 oraz sama zgodność ppm nie potwierdzają tożsamości. Zmiana struktury,
granic, liczby jąder lub przypisania ROI wymaga ponownego potwierdzenia.
Zapisane odpowiedniki są częścią samodzielnego projektu i nie zmieniają
aktualności wyników oznaczenia.

Diagnostyka porównuje zapisany wynik z rezonansu z oficjalną średnią tej samej
próbki. Najpierw uśrednia powtórne pomiary danego rezonansu w próbce, potem
próbki z równymi wagami. Tabela podaje średnią zawartość, średnie odchylenie
w punktach procentowych, SD odchyleń z mianownikiem n − 1 i liczbę niezależnych
próbek. Rezonans musi być obecny we wszystkich uwzględnionych pomiarach danej
próbki. Nie uzupełnia się braków. Próbki wykluczone, nieaktualne i niebędące
niezależnymi przygotowaniami nie zwiększają n.

Średnia próbki zawiera oceniany rezonans, więc odchylenia są zależne i częściowo
tłumione. Nie wykonuje się testów istotności ani korekcji wyników. Dla n < 3
nie opisuje się kierunku jako powtarzalnego; SD dla n = 1 nie jest określone.
Wykres powstaje dopiero, gdy co najmniej dwa rezonanse mają co najmniej dwie
wspólne niezależne próbki. Opis stałej różnicy między dwoma rezonansami
wymaga co najmniej trzech wspólnych próbek i zgodnego kierunku we wszystkich.
To opis obserwacji, bez wnioskowania o przyczynie lub przydatności sygnału.

Eksport zestawu zawiera diagnostykę w `traceability.json` (format raportu 3),
oddzielnie od niezmienionych wyników oznaczenia.

Domyślny **Raport Word** przedstawia podsumowanie, substancje i struktury,
metodykę, przygotowanie próbek, dobór sygnałów, wyniki próbek, statystykę
i obserwacje. Identyfikatory techniczne i pochodzenie danych są w dodatkach.

W oknie **Eksportuj raport** można wybrać **Rozszerzony raport techniczny Word**.
Zawiera on dodatkowo pełne tabele parametrów, granic i całek, ocenę jakości ROI,
przypisania atomów, historię zmian parametrów i powiększenia obszarów widma.
Oba profile korzystają z tych samych zapisanych wyników. Eksport nie uruchamia
przetwarzania ani ponownego obliczenia i nie zmienia wykluczeń.

Raport używa A4, stylów Worda, nagłówka i numerów stron, powtarzanych nagłówków
tabel oraz ilustracji z podpisami. Wzór oznaczenia zawiera ułamki i indeksy
matematyczne. Struktury zachowują stereochemię, ładunki i odłączone przeciwjony.

Wartości są formatowane do czytania, z przecinkiem dziesiętnym w PL i kropką
w ENG. Zawartość, SD i RSD są zwykle pokazywane do trzech miejsc po przecinku;
jednostki odróżniają procent względny od punktów procentowych. Małe i duże
wielkości mogą używać zapisu × 10 z wykładnikiem. Liczby w modelu pozostają
niezmienione. Parametry akwizycji i przetwarzania są porównywane przed
zaokrągleniem, dzięki czemu rzeczywiste różnice nie stają się wspólną metodyką.

Tabela doboru ROI grupuje jednakową prezentację granic do czterech miejsc
po przecinku. Osobne kolumny pomiarów zachowują lokalne ID sygnałów. Drobne
różnice poza dokładnością prezentacji pozostają w projekcie i eksporcie JSON;
profil rozszerzony podaje szczegółowe granice. To uproszczenie tabeli nie
zmienia zakresów całkowania ani liczonych wyników.

Obserwacje opisują zapisany rozrzut sygnałów oraz wykluczenia i ostrzeżenia.
Nie wykluczają samodzielnie sygnałów i nie ustalają chemicznej przyczyny różnic.
Pomiary historyczne są wyraźnie oznaczone. Obserwacje niebędące niezależnymi
przygotowaniami nie zwiększają n.

**Pełny zestaw** zachowuje dodatkowo CSV, XLSX i `traceability.json` z pełną
precyzją danych, nazwą profilu i wersją formatu raportu. DOCX jest dokumentem
do oceny przez człowieka; JSON i samodzielny projekt umożliwiają sprawdzenie
dokładnych danych maszynowych. Raporty domyślnie zapisują się w `reports`.
