# Raporty naukowe qNMR Lab

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
