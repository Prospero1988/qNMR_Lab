# Metody naukowe (PL)

## Wprowadzanie liczby jąder od 1.0

Podana liczba jąder jest używana bez dodatkowego checkboxa potwierdzenia.
Dawny znacznik w starszych projektach nie blokuje obliczeń. Analityk nadal
dobiera liczbę jąder do przypisanego sygnału; program sprawdza jej dodatnią,
skończoną wartość. Powód wykluczenia sygnału jest opcjonalny. Dwa miejsca po
przecinku dotyczą prezentacji całek i nie zmieniają precyzji oznaczenia.

## Wynik substancji i minimalna liczba próbek

Wynik końcowy dotyczy konkretnej substancji przypisanej do niezależnie
przygotowanych próbek. Średnie tych próbek mają równe wagi, niezależnie od
liczby powtórnych pomiarów. Wyniki różnych substancji są prezentowane osobno.
Powtórny pomiar tej samej fizycznej próbki nie jest nowym niezależnym
przygotowaniem i nie zwiększa n.

Od wersji interfejsu 1.0 status kompletności wymaga co najmniej trzech
niezależnych próbek z aktualnymi wynikami wszystkich uwzględnionych pomiarów.
To warunek przebiegu pracy, a nie nowy wzór statystyczny ani dowód walidacji
metody. Dla n = 2 opisowe SD, SEM i przedział Studenta nadal mogą być pokazane,
lecz wynik ma status wstępny. Wersja konwencji obliczeń pozostaje 1.0.0.

## 1.0 — całki względne i kalibracja

Wyświetlanie całek względnych używa `I_i × V_ref / I_ref` z dodatnim
sygnałem odniesienia. Surowe całki ze znakiem nie są nadpisywane. Skala
prezentacji nie zmienia ilorazów qNMR ani liczby protonów. Podział ROI nie
dziedziczy potwierdzenia protonów: obie części wymagają oceny analityka.
Kalibracja ppm przesuwa wszystkie współrzędne razem i zachowuje intensywności
oraz funkcję fazy. Zmiana parametrów nadal wymaga ponownego obliczenia oznaczenia.


[English methods](SCIENTIFIC_METHODS_EN.md)

## Konwencjonalne przetwarzanie 1D

Konwencje liczbowe pochodzą z konwencjonalnego silnika jednowymiarowego DOSY Lab.
Adaptacja nie zawiera obliczeń dyfuzji ani dedykowanych składników korekcji
presaturacji lub ogona rozpuszczalnika. Surowe dane pozostają niezmienne.

Zespolony FID JEOL odtwarza się jako sekcja 0 minus $i$ razy sekcja 1.
Sprawdzane są sekcje nagłówka, precyzja, kolejność bajtów, ważny zakres punktów,
jednostki parametrów i deklarowana długość pliku. Zapisywana jest suma SHA256.
Obsługiwany jest jeden konwencjonalny protonowy FID; nie rozpakowuje się danych
wielowymiarowych ani projektów `.jjh5`.

Dla częstotliwości próbkowania $SW$ w Hz i $t_j=j/SW$ okno apodyzacji ma postać

$$w(t)=\exp(-\pi LBt)\exp\left[-\frac{(\pi GBt)^2}{4\ln2}\right].$$

Stosuje się NumPy `fft`, dopełnienie zerami o współczynniku 1, 2, 4 lub 8 oraz
`fftshift`. Nie normalizuje się amplitud oddzielnie dla każdego sygnału. Oś ppm:

$$\delta=\delta_{offset}+f/\nu_0+\Delta\delta,$$

gdzie $\nu_0$ jest częstotliwością protonową w MHz, a $f$ przesuniętą częstotliwością
w Hz. Przycinanie pasma na podstawie metadanych zachowuje konwencję fazy na całej
zarejestrowanej szerokości. Dla obsługiwanej kaskady JEOL orders/factors modeluje
się opóźnienie liniowej fazy w próbkach. W innych przypadkach program nie
zgaduje uniwersalnego opóźnienia i nie deklaruje równoważności z oprogramowaniem
producenta.

Przy szerokości $W=SW/\nu_0$ w ppm i częstotliwości nośnej
$c=\delta_{offset}+\Delta\delta$ korekcja fazy wynosi

$$\phi(\delta)=\frac{\pi}{180}\left[360d\frac{\delta-c}{W}
+PH0+PH1\frac{\delta-p}{W}\right].$$

Widmo mnoży się przez $\exp(i\phi)$. Zmiana punktu obrotu $p$ na $p'$ przelicza
$PH0'=PH0+PH1(p'-p)/W$, dzięki czemu istniejąca funkcja fazy pozostaje taka sama.
PH0 i PH1 są następnie świadomymi korektami ręcznymi. Początkowe zgrubne PH0
wykorzystuje spójne piki tylko w dopuszczonym oryginalnym przebiegu z obsługiwanym
modelem opóźnienia. Nie jest dowodem ilościowej poprawności fazy.

## Linia bazowa i całkowanie

Korekcja bazy dopasowuje wielomian Legendre'a stopnia 1–5 wyłącznie do ręcznie
wskazanych punktów tła. Pełny zakres ppm jest skalowany do $[-1,1]$.
Współczynniki wyznacza oryginalny algorytm najmniejszych kwadratów NumPy, z
kontrolą liczby punktów i uwarunkowania. Podgląd nie jest zatwierdzonym
odejmowaniem. Zatwierdzona maska tła nie może przecinać ROI ilościowych.
Nie stosuje się modelu ogona ani korekcji artefaktów presaturacji.

Dla skorygowanej części rzeczywistej $s(\delta)=\Re[z(\delta)]-b(\delta)$:

$$I=\int_{\delta_l}^{\delta_h}s(\delta)\,d\delta.$$

Oś jest sortowana i sprawdzana pod kątem ścisłej monotoniczności. Na ułamkowych
granicach ROI wstawia się intensywności interpolowane liniowo, a następnie
stosuje metodę trapezów. Całka zachowuje znak i odnosi się do matematycznego zera.
Nie używa się modułu intensywności, nie odejmuje linii łączącej końce ROI i nie
normalizuje niezależnie pików. ROI musi zawierać co najmniej dwa punkty siatki.
Powiększenie i wysokość wyświetlania nie zmieniają danych liczbowych.

## Oznaczenie ze wzorcem wewnętrznym

Dla zaakceptowanych sygnałów analitu i wzorca:

$$P_A=\frac{I_A}{I_{IS}}\frac{N_{IS}}{N_A}
\frac{MW_A}{MW_{IS}}\frac{m_{IS}}{m_A}P_{IS}.$$

Końcowa zawartość to $100P_A$ w % m/m. Czystość wzorca przechowywana jest jako
ułamek; GUI przyjmuje % m/m i przelicza je jawnie. Masy zachowują wprowadzoną
jednostkę i są spójnie przeliczane na mg. Wartość g/mol jest liczbowo równa mg/mmol:

$$n_{IS}[\mathrm{mmol}]=m_{IS}[\mathrm{mg}]P_{IS}/MW_{IS}.$$

Stosunek całek skorygowany o liczbę protonów daje mmol analitu i jego masę.
Zapisywane są wszystkie pośrednie ilorazy, ilości i masy dla każdej pary
sygnałów. Zerowa całka wzorca jest błędem. Całki ujemne pozostają ujemne i
powodują ostrzeżenie do oceny.

Masa molowa dotyczy całej odważonej postaci. RDKit oblicza średnią masę i wzór
wszystkich jawnie wpisanych fragmentów, ale nie zna niewpisanej wody, solwatu ani
stechiometrii. Wartość ręczna lub nadpisana wymaga źródła i uzasadnienia.
Powiązanie atomów z ROI dokumentuje decyzję analityka, nie wnioskuje automatycznie
równoważności chemicznej ani liczby jąder danego sygnału.

Kilka sygnałów wzorca wymaga wyboru konkretnego odniesienia dla ROI albo jawnego
potwierdzenia zgodności. Po potwierdzeniu wyniki par są uśredniane z równą wagą
dla sygnału analitu. Surowe całki pozostają niezmienione. Nie ma automatycznego
wykluczania nakładania lub wartości odstających, odejmowania wody ani wymuszania
bilansu masy.

## Hierarchia i jednostka statystyczna

Najpierw uśrednia się zaakceptowane sygnały analitu w jednym pomiarze. Potem
uśrednia się wyniki powtórnych pomiarów tej samej fizycznej próbki. Każda
niezależnie przygotowana próbka wnosi jedną wartość $x_j$ do statystyki końcowej.
Różnych analitów nie łączy się. Jednostkę statystyczną wyznacza przygotowanie
próbki i jego flaga niezależności, a nie liczba wierszy sygnałów.

$$\bar{x}=\frac1n\sum_jx_j,\qquad
s=\sqrt{\frac{\sum_j(x_j-\bar{x})^2}{n-1}}.$$

$$RSD=100s/|\bar{x}|,\qquad SEM=s/\sqrt{n}.$$

Opcjonalny opisowy przedział ufności:
$\bar{x}\pm t_{(1+c)/2,n-1}SEM$. Zakłada niezależne przygotowania i odpowiedni,
w przybliżeniu normalny model próbkowania. Dla n=1 SD, RSD, SEM i przedział
ufności są niedostępne. Przy zerowej średniej RSD nie jest wyznaczane.

Rozrzut sygnałów w pomiarze i rozrzut powtórnych pomiarów jednej próbki są
opisowe. Nie przypisuje się im inferencyjnego SEM ani przedziału ufności.
SD/SEM nie stanowią pełnego budżetu niepewności: wagę, certyfikowaną czystość,
relaksację, postać chemiczną, nakładanie, bazę i inne składowe systematyczne
trzeba ocenić osobno.

Wykluczone sygnały, pomiary i próbki pozostają z uzasadnieniem. Jeśli włączona
próbka ma brakujący lub nieaktualny wynik któregokolwiek włączonego pomiaru,
nie wchodzi do aktualnego podsumowania i powoduje status wstępny. Otwarcie
projektu nie uruchamia cichego przetwarzania.

## Diagnostyka

Szum szacuje się odporną metodą pierwszych różnic w ręcznie wybranym tle albo
w przybliżeniu z całego widma. S/N porównuje lokalne maksimum modułu amplitudy
z szumem. Na oszacowanie wpływają apodyzacja i korelacje punktów. Program pokazuje
średnią tła, stosunek RMS części urojonej do rzeczywistej oraz oba znaki.

Wrażliwość granic bada rozszerzenie i zwężenie ROI o jeden krok siatki.
Nakładanie ROI wykrywa przecięcie przedziałów, nie rozdziela nakładających się
chemicznie pików. Progi są ostrzeżeniami heurystycznymi, a nie naukowymi
kryteriami akceptacji lub automatycznego odrzucenia.

Dopasowanie do pików szuka lokalnych maksimów modułu domyślnie w ±0,04 ppm.
Proponuje przesunięcia i nigdy nie wprowadza ich bez potwierdzenia analityka.

## Identyfikowalność, język i ograniczenia

Projekt zachowuje SHA256 źródła, surowe i przetworzone tablice, parametry,
historię, pochodzenie danych molekularnych, materiał odniesienia, przypisania,
wykluczenia i zapisane wyniki z odciskiem parametrów. Suma kontrolna sprawdza
tożsamość, nie przydatność naukową. Nie jest podpisem elektronicznym,
zatwierdzonym systemem audytowym ani zatwierdzeniem regulacyjnym.

PL/ENG dotyczy warstwy prezentacji. Wersja obliczeń pozostaje 1.0.0 przy wydaniu
interfejsu 1.0. Zmiana języka lub tłumaczeń nie zmienia odcisku obliczeń,
protonów, ról, jednostek, tablic widmowych ani wcześniej zapisanych wyników.

Walidacja obliczeń znajduje się w [EXCEL_COMPARISON_PL.md](EXCEL_COMPARISON_PL.md).
Nie dostarczono oryginalnych FID badania w JDF; integracji producenta nie można
odtworzyć z ilorazów Excel ani obrazów raportu.
