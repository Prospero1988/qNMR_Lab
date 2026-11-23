# Porównywanie wyników z arkuszem

## Zakres i dostępność danych

Publiczna aplikacja pozwala importować lokalny arkusz referencyjny w obsługiwanym
układzie. Służy to porównaniu liczbowemu, nie odczytowi dowolnego Excela ani
odtworzeniu surowego widma. Prywatne dokumenty badawcze nie są dystrybuowane.
Użytkownik wskazuje własny arkusz i jedno badanie; różnych analitów nie łączy się.

## Równanie ilościowe

Zawartość procentowa = (całka analitu / całka wzorca) × (liczba jąder wzorca /
liczba jąder analitu) × (masa molowa analitu / masa molowa wzorca) ×
(odważka wzorca / odważka analitu) × ułamek czystości wzorca × 100.

Używaj jednakowych jednostek masy i rzeczywistej postaci odważanego materiału.
Czystość procentową przelicza się na ułamek tylko raz. Ręczna masa molowa wymaga
pochodzenia; sama nazwa związku nie określa soli, hydratu ani solwatu.
Całka znormalizowana do jednego protonu wzorca jest wartością referencyjną,
a nie surowym polem ze znakiem i znanymi granicami ppm.

## Obsługiwany układ

Importer realizuje konkretną strukturę wierszy i kolumn opisaną w
qnmr/excel_reference.py. Odczytuje identyfikatory i odważki przygotowań, masy
molowe analitu i wzorca, czystość oraz współczynniki całek i liczby protonów.
Przed dopasowaniem innego arkusza trzeba sprawdzić tę strukturę. Import dotyczy
jednego arkusza i tworzy rekordy niezależnych próbek z pochodzeniem danych.
Nie da się ustalić FID, fazy, modelu bazy ani oryginalnych granic całkowania
z samych znormalizowanych ilorazów. Brakujące dane pozostają jawnie nieobecne.

## Niezależne sprawdzenia liczbowe

Najpierw porównaj każdą zaakceptowaną parę analit–wzorzec, potem średnie.
Prosty przykład syntetyczny: jednakowe masy molowe i odważki, czystość równa
jedności, po jednym jądrze w obu sygnałach i iloraz całek 0,95 dają zawartość
95 procent. Zmiana stosunku jąder albo czystości skaluje ten wynik dokładnie
według równania. Nie dopasowuj przetwarzania tak, aby uzyskać wartość docelową.

Uśredniaj sygnały w pomiarze, pomiary jednej fizycznej próbki, a na końcu średnie
niezależnych przygotowań z równymi wagami. Dla średnich 90, 100 i 110 wynik ma
średnią 100, SD próby 10 i n równe 3, nawet gdy liczby pomiarów są różne.
Populacyjne SD wszystkich połączonych sygnałów opisuje inną wielkość i nie
zastępuje SD między niezależnymi przygotowaniami.

## Dowody regresji i ograniczenia

Publiczne testy obejmują równanie sprawdzane ręcznie i nierówne liczby powtórzeń.
Dwa opcjonalne testy używają pierwotnego arkusza lokalnego, jeśli znajduje się on
w validation/reference/qNMR.xlsx; w przeciwnym razie są pomijane. Tego katalogu
nie należy dodawać do repozytorium. Przykłady syntetyczne sprawdzają osobno
pełny przebieg przetwarzania widma i zapisu samodzielnego projektu.

Zgodność z arkuszem sprawdza rachunki i mapowanie danych. Nie dowodzi właściwej
relaksacji, braku nakładania, równoważności ilościowej, poprawności bazy ani pełnego
budżetu niepewności. Wymagają one oceny eksperymentalnej i analitycznej.
Szczegóły podają SCIENTIFIC_METHODS_PL.md oraz VALIDATION_PL.md.
