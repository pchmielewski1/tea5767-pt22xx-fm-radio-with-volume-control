# RDS MPX Plan

## Cel

Dodac funkcje odbioru i dekodowania RDS na podstawie sygnalu MPX z TEA5767 z wykorzystaniem jednego wolnego wejscia ADC Flippera bez konfliktu z I2C i liniami sterujacymi PAM8406.

Docelowy procesor:
- STM32WB55RGV6TR

Docelowe zasoby CPU do wykorzystania:
- ADC z DMA do ciaglego zrzutu probek
- DSP i FPU rdzenia Cortex-M4 do filtracji i obrobki sygnalu
- minimalizacja obciazenia CPU przez przetwarzanie blokowe zamiast probka po probce w przerwaniu

## Wybrany pin

Wybrane wejscie ADC:
- pin 4 Flippera
- PA4
- ADC1_IN9
- nazwa sygnalu na PCB: RDS_MPX_ADC

Powod wyboru:
- nie koliduje z I2C na PC0 i PC1
- nie koliduje z liniami PAM_MUTE, PAM_SHDN i PAM_MODE_ABD na PB3, PB2 i PC3
- jest potwierdzonym wejsciem ADC w STM32WB55RGV6TR

## Funkcja sprzetowa

Sekcja ma sluzyc do odbioru sygnalu MPX z TEA5767 i przygotowania go do probkowania przez ADC Flippera na potrzeby dekodowania RDS.

Nazwy robocze sekcji:
- RDS z MPX
- MPX front-end
- RDS_MPX_ADC

## Plan analog front-end

### Kluczowe odkrycia z pomiarow (RRD-102BC)

Pomiary praktyczne wykazaly, ze modul TEA5767 na PCB RRD-102BC ma juz wlasne elementy toru wyjsciowego MPX, a dodatkowe elementy na naszej plytce moga pogorszyc sygnal.

Zaobserwowane fakty:
- po dolaczeniu dodatkowego kondensatora odsprzegajacego na MPX przebieg na wyjsciu zanikl,
- bez dodatkowego kondensatora przebieg jest obecny i poprawny,
- dolaczenie zewnetrznego dzielnika 100k/100k do 3.3 V i GND (punkt srodkowy do MPX) obnizalo punkt pracy i amplitude,
- przy takim polaczeniu zmierzone napiecie DC bylo okolo 0.8 V,
- zmierzona rezystancja widziana od MPX do zasilania i do masy byla okolo 50k, co wskazuje na polaczenie rownolegle z rezystorami juz obecnymi w module,
- bez dodatkowych rezystorow pomiar MPX do VCC i GND dawal symetrycznie okolo 5.3 MOhm,
- bez dodatkowych rezystorow punkt DC na MPX byl okolo 1.2 V,
- bez dodatkowych rezystorow amplituda na oscyloskopie byla wyzsza, okolo 200 do 300 mV.

Wniosek praktyczny:
- wyjscie MPX nie powinno byc dodatkowo dociagane dzielnikiem 100k/100k na naszej plytce,
- nie nalezy dodawac "na slepo" kolejnego kondensatora odsprzegajacego MPX,
- wariant startowy powinien byc mozliwie wysokoomowy i niedociagajacy.

### Wariant startowy

Najprostszy wariant do pierwszych prob:
- pobrac sygnal MPX z TEA5767
- na bazie aktualnych pomiarow NIE dokladac zewnetrznego dzielnika 100k/100k do MPX
- na bazie aktualnych pomiarow NIE dokladac dodatkowego kondensatora odsprzegajacego MPX bez potwierdzenia na oscyloskopie
- najpierw zmierzyc przebieg bezposrednio i ocenic czy naturalny punkt DC z modulu (okolo 1.2 V) i amplituda (okolo 200 do 300 mV) mieszcza sie bezpiecznie w zakresie ADC 0 do 3.3 V
- dopiero jesli zajdzie potrzeba, dodawac bufor o bardzo duzej impedancji wejsciowej

Cel wariantu startowego:
- sprawdzic, czy MPX z TEA5767 ma wystarczajaca jakosc do probkowania i dekodowania RDS bez dodatkowego aktywnego toru analogowego

### Wariant preferowany

Preferowany wariant do wersji bardziej dopracowanej:
- uzyc MCP6001 jako bufora i wzmacniacza nieodwracajacego
- ustawic przesuniecie DC na polowe zakresu ADC
- ustawic wzmocnienie okolo x4 jako punkt startowy do testow

Dlaczego MCP6001:
- rail-to-rail
- pracuje od 1.8 V do 6 V
- nadaje sie do pojedynczego zasilania 3.3 V
- jest wystarczajacy do pasma RDS przy 57 kHz

Uwagi praktyczne:
- wzmocnienie x4 to punkt startowy, nie wartosc ostateczna
- nalezy przewidziec mozliwosc korekty rezystorow wzmacniacza po pierwszych pomiarach MPX z rzeczywistego TEA5767
- wejscie ADC powinno miec lokalny rezystor szeregowy ochronny i maly kondensator tylko jesli nie pogorszy to zbytnio pasma dla 57 kHz
- kluczowe jest, aby wejscie front-endu nie obciazalo MPX; preferowany jest bufor o wysokiej impedancji wejsciowej zamiast pasywnego dzielnika podpietego bezposrednio do MPX

## Zalozenia dla sygnalu

Sygnal MPX zawiera:
- audio L plus R w niskim pasmie
- pilot 19 kHz
- skladnik stereo L minus R wokol 38 kHz
- RDS na 57 kHz

Wniosek:
- tor analogowy i probkowanie nie moga za mocno ucinac pasma w okolicy 57 kHz
- prosty filtr dolnoprzepustowy na wejsciu ADC, jesli w ogole bedzie, musi miec czestotliwosc graniczna wyraznie powyzej 57 kHz

## Plan probkowania ADC

Strategia:
- ADC pracuje w trybie ciaglym
- DMA zapisuje probki do bufora kolowego
- obrobka sygnalu jest wykonywana blokowo po polowie i calosci bufora DMA

Zalecenia robocze:
- start od czestotliwosci probkowania z zapasem ponad 114 kHz, praktycznie lepiej 171 kHz do 228 kHz lub wyzej, jesli firmware i budzet CPU na to pozwoli
- format probek 12-bit ADC z zapisem do 16-bit bufora
- przetwarzanie na blokach o stalej dlugosci, aby ograniczyc narzut przerwan

Cel:
- nie obciazac mocno CPU obsluga pojedynczych probek
- wykorzystac DMA do transportu danych i DSP/FPU do obliczen na blokach

### Proponowany sample rate

Rekomendacja startowa dla runtime:
- 228 kS/s nominal

Uzasadnienie matematyczne:
- nosna RDS: f_RDS = 57 kHz = 3 x 19 kHz,
- bitrate RDS: R_s = 1187.5 bit/s = 57 kHz / 48,
- dla f_s = 228 kS/s mamy:
- f_s / f_RDS = 228000 / 57000 = 4 probki na okres 57 kHz,
- f_s / R_s = 228000 / 1187.5 = 192 probki na symbol.

To jest glowny powod wyboru 228 kS/s:
- dostajemy calkowite relacje probkowania do nosnej i do symbolu,
- upraszcza to generator lokalnej nosnej 57 kHz,
- upraszcza to synchronizacje symbolowa i testy debug,
- zmniejsza ryzyko bledu numerycznego wzgledem bardziej przypadkowych sample rate,
- daje wiekszy zapas probek na okres nosnej i na symbol niz 171 kS/s.

Porownanie z 171 kS/s:
- 171000 / 57000 = 3 probki na okres 57 kHz,
- 171000 / 1187.5 = 144 probki na symbol,
- jest to rowniez bardzo wygodna wartosc obliczeniowo,
- ale daje mniejszy zapas probek na okres nosnej i na symbol niz 228 kS/s.

Powod wyboru:
- jest wyraznie powyzej minimum Nyquist dla 57 kHz,
- daje dokladnie 4 probki na okres nosnej 57 kHz,
- upraszcza obliczenia i daje wiekszy zapas dla synchronizacji symbolowej,
- zwieksza obciazenie CPU i przeplyw danych wzgledem 171 kS/s, ale pozostaje wartoscia bardzo wygodna obliczeniowo.

Rekomendacja zapasowa:
- jesli obciazenie CPU okaze sie zbyt wysokie, obnizyc do 171 kS/s w trybie testowym,
- 171 kS/s traktowac jako tryb alternatywny o mniejszym koszcie obliczeniowym.

Wniosek implementacyjny:
- pierwszy target runtime: 228 kS/s,
- pierwszy target debug capture: 228 kS/s,
- drugi target debug / eksperymentalny: 171 kS/s.

### Proponowany rozmiar buforow DMA

Rekomendowany uklad buforow:
- jeden bufor kolowy DMA: 2048 probek typu uint16_t,
- przetwarzanie blokowe po 1024 probki na half-transfer i full-transfer.

Rozmiary:
- 2048 probek x 2 bajty = 4096 bajtow bufora ADC DMA,
- blok obrobki = 1024 probki = 2048 bajtow surowych danych.

Czas jednego bloku przy 228 kS/s:
- 1024 / 228000 ~= 4.49 ms

Wniosek:
- modul dostaje jeden blok do obrobki mniej wiecej co 4.5 ms,
- to jest wystarczajaco rzadko, aby nie zalewac CPU przerwaniami,
- a jednoczesnie wystarczajaco czesto, aby utrzymac ciaglosc dekodowania.

Wariant alternatywny tylko jesli zajdzie potrzeba:
- 4096 probek DMA z blokami po 2048 probek,
- mniejszy narzut schedulerowy kosztem wiekszej latencji.

Domyslna rekomendacja:
- runtime: 2048 probek DMA / 1024 probki na blok.

Wygodna relacja do symboli RDS:
- przy 228 kS/s i 1024 probkach na blok mamy 1024 / 192 ~= 5.33 symbolu RDS na blok,
- blok nie jest calkowita wielokrotnoscia symbolu, wiec dekoder musi trzymac stan miedzy blokami,
- to jest poprawne i oczekiwane,
- warto przechowywac faze symbol clock i reszte probek z poprzedniego bloku.

### Szacowane uzycie RAM

Szacunek dla pierwszej implementacji runtime bez przesadnej rozbudowy:

1. Bufor DMA ADC:
- 2048 x uint16_t = 4096 B

2. Bufor roboczy jednego bloku po konwersji do sygnalu signed:
- 1024 x int16_t = 2048 B

3. Bufor / workspace dla filtracji i obrobki blokowej:
- okolo 2048 B do 4096 B

4. Stan dekodera RDS, historia bitow, synchronizacja blokow, PI / PS / RT:
- okolo 512 B do 1024 B

5. Debug staging buffer dla lekkiego dumpa lub kolejkowania zapisu:
- okolo 1024 B do 2048 B

Suma praktyczna dla wersji startowej:
- minimum runtime bez dumpa: okolo 8 KB
- komfortowy budzet runtime z podstawowym debugiem: okolo 10 KB do 12 KB

Rekomendacja projektowa:
- przyjac budzet 12 KB RAM dla modulu RDS jako bezpieczny target planistyczny,
- jesli implementacja zacznie rosnac powyzej 16 KB, nalezy uproscic pipeline albo debug.

## Plan dekodowania RDS na CPU

Docelowy kierunek implementacji:
- pobrac strumien MPX przez ADC
- cyfrowo odfiltrowac okolice 57 kHz
- wykonac odzyskanie podnosnej RDS na podstawie zaleznosci od pilota 19 kHz albo przez bezposrednia metode cyfrowa
- zdemodulowac BPSK RDS
- odzyskac zegar symbolowy
- skladac bloki RDS i sprawdzac syndromy

Zasoby STM32WB55RGV6TR, ktore warto wykorzystac:
- FPU do szybkich obliczen na float, jesli finalny algorytm bedzie tego potrzebowal
- DSP instructions do filtrow FIR/IIR, mieszania i korelacji
- DMA do stalego odbioru probek bez duzego obciazenia CPU

Wniosek implementacyjny:
- dekoder ma byc projektowany jako pipeline blokowy oparty o DMA i DSP
- celem nie jest dekodowanie w stylu tight loop na przerwaniu od kazdej probki
- pierwsza wersja ma byc zoptymalizowana pod stabilny odbior PS, nie pod pelny feature set RDS.

### Wzory robocze dla toru dekodowania

1. Usuniecie offsetu DC z ADC:
- x_ac[n] = x_adc[n] - mean(x_adc)

2. Cyfrowe zejscie z 57 kHz do baseband:
- I[n] = x_ac[n] * cos(2 * pi * f_0 * n / f_s)
- Q[n] = x_ac[n] * -sin(2 * pi * f_0 * n / f_s)
- gdzie f_0 = 57 kHz

3. Filtracja dolnoprzepustowa po mieszaniu:
- I_lp[n] = LPF(I[n])
- Q_lp[n] = LPF(Q[n])
- pasmo uzyteczne po demodulacji powinno obejmowac okolice bitrate 1187.5 Hz i zapas na synchronizacje

4. Czestotliwosc symbolowa RDS:
- R_s = 1187.5 bit/s = 57 kHz / 48
- liczba probek na symbol:
- N_s = f_s / R_s
- dla 171 kS/s: N_s = 144
- dla 228 kS/s: N_s = 192

5. Integracja po symbolu / matched filter w wersji startowej:
- z[k] = sum od m=0 do N_s-1 z_bb[k * N_s + m]
- gdzie z_bb[n] = I_lp[n] + j * Q_lp[n]

6. Prosta decyzja bitowa przy detekcji roznicowej BPSK:
- d[k] = sign(real(z[k] * conj(z[k-1])))
- taka postac pomaga, gdy absolutna faza nosnej nie jest jeszcze idealnie ustalona

7. Pilot 19 kHz jako referencja pomocnicza:
- f_RDS = 3 * f_pilot
- jesli pilot jest stabilnie wykryty, lokalna nosna 57 kHz moze byc odzyskana jako trzecia harmoniczna pilota
- wtedy faza pomocnicza spelnia relacje:
- phi_RDS ~= 3 * phi_pilot

8. Rozdzielczosc czestotliwosci dla analizy FFT bloku 1024:
- delta_f = f_s / N
- dla 228 kS/s i N = 1024:
- delta_f ~= 222.7 Hz
- to wystarcza do potwierdzenia obecnosci pilota 19 kHz i energii w okolicy 57 kHz podczas debugowania

Wniosek praktyczny:
- 228 kS/s nie zostalo wybrane dlatego, ze ADC nie potrafi szybciej,
- zostalo wybrane dlatego, ze daje bardzo wygodne relacje calkowite do 57 kHz i 1187.5 bit/s,
- a jednoczesnie daje wiecej probek na okres nosnej i na symbol.

### Co oznacza priorytet PS zamiast pelnego RDS

PS oznacza Program Service:
- to krotka nazwa stacji,
- standardowo 8 znakow ASCII,
- w praktyce to tekst typu RMF FM, ZET CHR, JAZZRAD.

Dlaczego PS najpierw:
- jest najbardziej widocznym efektem dla uzytkownika,
- wymaga znacznie mniejszego zakresu funkcji niz pelna obsluga wszystkich grup RDS,
- dobrze nadaje sie jako pierwszy test stabilnosci calego toru: ADC, DMA, synchronizacji, detekcji blokow i korekcji.

Co zwykle wchodzi do pelnego feature set RDS:
- PI: Program Identification,
- PS: Program Service,
- PTY: Program Type,
- RT: RadioText,
- CT: Clock Time,
- TP i TA: flagi traffic,
- AF: Alternative Frequencies,
- obsluga wiekszej liczby typow grup i ich wariantow.

Dlaczego nie pelny set od razu:
- najtrudniejsza czesc nie lezy w samym parsowaniu pol, tylko w stabilnym odzyskaniu danych z analogowego MPX,
- PS pozwala szybko zweryfikowac, czy odbiornik lapie poprawne bloki 0A lub 0B,
- RT, AF i pozostale elementy wymagaja dluzszego utrzymania synchronizacji, skladania danych z wielu grup i lepszej obslugi bledow,
- jesli od razu wrzucimy caly stos funkcji, trudniej bedzie odroznic blad DSP od bledu parsera protokolu,
- podejscie PS-first skraca czas do pierwszego wiarygodnego wyniku i upraszcza debug.

Minimalny cel dla pierwszej wersji:
- stabilnie wykryc pilot 19 kHz,
- stabilnie wykryc energie i lock dla 57 kHz,
- odzyskac poprawne bloki RDS,
- pokazac PI i PS na ekranie,
- dopiero potem rozszerzac na RT, PTY, AF i pozostale grupy.

### Porownanie z SAA6588

SAA6588 jest bardzo dobrym wzorcem architektury dekodera RDS:
- pokazuje prawidlowy podzial funkcji,
- pokazuje kolejnosc przetwarzania,
- pokazuje, jakie mechanizmy stabilizuja odbior przy slabym lub zaszumionym sygnale.

Nie nalezy jednak kopiowac go 1:1:
- SAA6588 ma specjalizowany tor analogowy i dedykowane bloki cyfrowe,
- my budujemy dekoder software na ogolnym MCU z ADC i DMA,
- dlatego kopiujemy architekture i logike, a nie konkretna implementacje ukladowa.

Mapowanie blokow SAA6588 na nasz projekt:

1. Selection of the RDS/RBDS signal from MPX:
- SAA6588 wybiera pasmo RDS z MPX w torze analogowym,
- u nas odpowiada za to analog front-end plus cyfrowa filtracja pasmowa wokol 57 kHz.

2. 57 kHz carrier regeneration:
- SAA6588 robi regeneracje nosnej 57 kHz przez Costas loop,
- u nas trzeba przewidziec dwa tryby:
- prostszy tryb startowy: referencja 57 kHz z pilota 19 kHz, czyli 3 x pilot,
- tryb docelowy: cyfrowa petla typu Costas lub rownowazna synchronizacja fazy na 57 kHz.

3. Demodulation of the RDS signal:
- SAA6588 po band-pass i comparatorze odzyskuje strumien danych,
- u nas odpowiednikiem jest cyfrowe mieszanie I/Q, LPF i detekcja DBPSK.

4. Symbol decoding and symbol integration:
- SAA6588 jawnie integruje po jednym okresie zegara RDS,
- to bardzo wazna wskazowka dla nas,
- nasz matched filter lub integrator powinien pracowac na oknie jednego symbolu:
- N_s = f_s / 1187.5
- czyli dla 228 kS/s mamy N_s = 192.

5. Block detection:
- SAA6588 stale przeszukuje strumien pod katem 26-bitowych blokow i offset words,
- u nas trzeba przewidziec dokladnie ten sam model logiczny,
- najpierw sliding syndrome search bit po bicie,
- po zlapaniu synchronizacji przejscie na krok co 26 bitow.

6. Error detection and correction:
- SAA6588 wykorzystuje syndromy i korekcje bledow burst do 5 bitow,
- to nie jest opcjonalny dodatek,
- to jest centralna czesc prawdziwego dekodera RDS,
- nasz plan powinien od razu przewidywac syndrome, offset words i status: valid, corrected, uncorrectable.

7. Fast block synchronization and synchronization hold:
- SAA6588 synchronizuje sie po dwoch kolejnych poprawnych blokach w prawidlowej sekwencji,
- potem utrzymuje sync przez flywheel,
- to jest bardzo dobry wzorzec dla nas,
- nie wystarczy pojedynczy poprawny blok,
- trzeba miec osobny stan SEARCH, PRE_SYNC, SYNC oraz licznik bledow do utrzymania synchronizacji.

8. Bit slip correction:
- SAA6588 koryguje przesuniecie o +1 lub -1 bit,
- to jest bardzo cenna wskazowka praktyczna,
- nasz software dekoder tez powinien sprawdzac wariant nominalny oraz przesuniety o jeden bit w lewo i w prawo, jesli jakosc lock spada.

9. Signal quality and multipath information:
- SAA6588 nie ogranicza sie do samych danych RDS,
- mierzy tez jakosc sygnalu i sytuacje wielodrogowe,
- u nas nie musimy kopiowac tego 1:1, ale warto miec chociaz software metrics:
- pilot_snr,
- rds_band_power,
- corrected_block_rate,
- uncorrectable_block_rate,
- sync_loss_count.

10. Mode control and data output pacing:
- SAA6588 ma tryby pracy, fast PI search, overflow control i sygnal DAVN,
- to jest bardzo dobra lekcja architektoniczna,
- u nas oznacza to, ze dekoder nie powinien bezposrednio zalewac UI czy glownej aplikacji kazdym blokiem,
- trzeba rozdzielic warstwe demodulacji od warstwy publikacji wynikow,
- publikowac tylko stabilne i istotne zmiany, np. nowy PI, nowy PS, utrata sync.

Wniosek:
- tak, zdecydowanie warto uczyc sie na SAA6588,
- ale jako na referencji architektury dekodera, nie jako na gotowym schemacie do przepisania linia po linii.

### Co dokladnie warto przejac z SAA6588

Elementy, ktore warto przejac prawie bez zmian na poziomie koncepcji:
- pasmowe wydzielenie 57 kHz,
- odzyskanie nosnej,
- integracja po symbolu,
- detekcja roznicowa bitow,
- syndrome-based block detection,
- korekcja bledow i status corrected versus uncorrectable,
- synchronizacja po sekwencji blokow, nie po pojedynczym trafieniu,
- flywheel do utrzymania synchronizacji,
- bit-slip correction,
- metryki jakosci sygnalu i sterowanie trybem pracy.

Elementy, ktorych nie warto kopiowac doslownie:
- analogowy switched-capacitor band-pass filter,
- comparator jako osobny blok sprzetowy przed demodulatorem,
- szczegoly czasowe I2C/DAVN charakterystyczne dla gotowego ukladu scalonego,
- wewnetrzne rejestry i nazwy trybow wynikajace z tej konkretnej implementacji Philipsa.

### Zaktualizowany docelowy model naszego dekodera

Na bazie SAA6588 nasz dekoder powinien miec warstwy:

1. Front-end sygnalowy:
- ADC DMA,
- usuniecie DC,
- pomiar poziomu i clippingu,
- cyfrowy band-pass lub zejscie do baseband.

2. Demodulator:
- regeneracja 57 kHz,
- I/Q,
- LPF,
- symbol timing,
- DBPSK differential decode.

3. Decoder core:
- shift register bitow,
- syndrome search,
- block type A, B, C, C', D,
- korekcja bledow,
- sync state machine,
- flywheel,
- bit-slip recovery.

4. Parser danych RDS:
- PI,
- PS,
- potem PTY, RT, AF i dalsze grupy.

5. Warstwa raportowania do aplikacji FM:
- publikacja tylko ustabilizowanych danych,
- zdarzenia lock i loss,
- metryki jakosci dla debug i ewentualnej diagnostyki UI.

Najwazniejszy wniosek projektowy z SAA6588:
- prawdziwy dekoder RDS to nie jest tylko filtr 57 kHz plus parser grup,
- to pelny pipeline z odzyskiwaniem nosnej, synchronizacja, korekcja bledow i polityka utrzymania lock.

### Maszyna stanow dekodera inspirowana SAA6588

Docelowe stany runtime:
- SEARCH
- PRE_SYNC
- SYNC
- LOST

#### SEARCH

Cel:
- szukac poprawnego 26-bitowego bloku bit po bicie w przesuwanym oknie,
- dla kazdego nowego bitu liczyc syndrome dla ostatnich 26 bitow,
- sprawdzac zgodnosc z offset words A, B, C, C' albo D.

Wejscie do stanu:
- start dekodera,
- restart po zmianie czestotliwosci,
- restart po overflow flywheel,
- restart po dluzszej utracie lock.

Przejscie SEARCH -> PRE_SYNC:
- gdy znaleziony zostanie pierwszy blok uznany za valid albo corrected,
- zapamietac jego typ offsetu i pozycje bitowa,
- wyznaczyc, jaki blok powinien pojawic sie jako nastepny w sekwencji.

#### PRE_SYNC

Cel:
- potwierdzic, ze pierwszy trafiony blok nie byl przypadkowym false positive,
- sprawdzic, czy kolejny blok pojawia sie po dokladnie 26 bitach i ma poprawny nastepny offset.

Regula synchronizacji:
- dekoder uznajemy za zsynchronizowany dopiero po dwoch kolejnych poprawnych blokach w prawidlowej sekwencji,
- to jest bezposrednio zgodne z filozofia SAA6588.

Przejscie PRE_SYNC -> SYNC:
- drugi kolejny blok po 26 bitach jest valid albo corrected,
- jego typ offsetu zgadza sie z oczekiwana sekwencja.

Przejscie PRE_SYNC -> SEARCH:
- drugi blok nie pasuje,
- drugi blok jest uncorrectable,
- albo wykryta pozycja bitowa rozjechala sie wzgledem oczekiwanego kroku 26 bitow.

#### SYNC

Cel:
- pracowac w trybie blokowym co 26 bitow zamiast przeszukiwania bit po bicie,
- dekodowac bloki, korygowac bledy, skladac grupy i utrzymywac synchronizacje przez flywheel.

Zasada:
- po zlapaniu synchronizacji syndrome liczymy tylko na granicach oczekiwanych blokow,
- pozycja bloku i oczekiwany offset sa juz przewidywalne.

Przejscie SYNC -> LOST:
- licznik flywheel przekroczy prog,
- seria uncorrectable blocks wskazuje na utrate synchronizacji,
- albo wykryto powtarzajace sie niespojne offsety mimo prob korekcji bit slip.

#### LOST

Cel:
- zarejestrowac utrate synchronizacji,
- opublikowac zdarzenie do aplikacji,
- wykonac szybki restart algorytmu bez zawieszania UI.

Przejscie LOST -> SEARCH:
- natychmiast po odnotowaniu zdarzenia lock_lost,
- wyzerowac kontekst blokow, licznik flywheel, oczekiwany offset i lokalne okno bitowe,
- rozpoczac nowe przesuwane szukanie.

Wniosek implementacyjny:
- stan LOST moze byc bardzo krotkim stanem technicznym,
- ale warto go miec jawnie, bo upraszcza debug i logi.

### Sekwencja blokow i offset words

Warstwa linkowa RDS pracuje na blokach 26-bitowych:
- 16 bitow danych,
- 10 bitow checkword.

Cztery kolejne bloki tworza grupe 104-bit:
- A, B, C, D dla grup typu A,
- A, B, C', D dla grup typu B.

Generator polynomial dla checkword:
- g(x) = x^10 + x^8 + x^7 + x^5 + x^4 + x^3 + 1

Postac binarna wielomianu:
- 10110111001

Stale offset words dla RDS:
- A = 0x0FC
- B = 0x198
- C = 0x168
- C' = 0x350
- D = 0x1B4

Uwagi:
- w RBDS istnieje tez offset E = 0x000,
- dla pierwszej implementacji mozemy skupic sie na klasycznym RDS: A, B, C, C', D.

Sekwencja oczekiwana podczas synchronizacji:
- po A oczekiwany jest B,
- po B oczekiwany jest C albo C',
- po C oczekiwany jest D,
- po C' oczekiwany jest D,
- po D oczekiwany jest A.

Wniosek praktyczny:
- trzeci blok grupy jest specjalny,
- dopuszcza dwa poprawne offsety: C dla wersji A albo C' dla wersji B,
- stan synchronizacji musi to akceptowac bez gubienia lock.

### Syndrome i reguly walidacji bloku

Dla odebranego slowa 26-bitowego r(x):
- syndrome = r(x) mod g(x)

Blok jest uznany za valid, gdy:
- syndrome == expected_offset

Podczas SEARCH:
- expected_offset nie jest jeszcze znany,
- sprawdzamy zgodnosc z kazdym z offset words A, B, C, C', D.

Podczas PRE_SYNC i SYNC:
- expected_offset wynika z aktualnej pozycji w sekwencji blokow,
- test validacji jest ostrzejszy, bo sprawdzamy tylko oczekiwany typ bloku.

Wlasnosc liniowa przydatna do korekcji:
- syndrome(received) = expected_offset xor syndrome(error)

Czyli:
- error_syndrome = syndrome(received) xor expected_offset

To pozwala zbudowac tablice korekcji:
- dla wszystkich dopuszczalnych wzorcow bledow e(x) liczymy syndrome(e),
- jesli error_syndrome pasuje do wpisu w tabeli, wiemy, ktore bity odwrocic.

### Korekcja bledow blokow A, B, C, C', D

Minimalny model zgodny z duchem SAA6588:
- valid: blok bez bledow,
- corrected: blok poprawiony na podstawie syndrome,
- uncorrectable: blok z bledem poza zakresem korekcji.

Zakres korekcji planowany dla pierwszej pelnej wersji:
- burst errors o dlugosci do 5 bitow w obrebie 26-bitowego bloku,
- zgodnie z typowa praktyka RDS i opisem SAA6588.

Strategia implementacyjna:
- precompute lookup table dla burst error patterns o dlugosci 1 do 5,
- dla kazdego wzorca zapamietac:
- mask_error_bits,
- syndrome(error),
- burst_length,
- first_bit_index.

Procedura korekcji jednego bloku:
1. policzyc syndrome odebranego 26-bit slowa,
2. porownac z expected_offset,
3. jesli pasuje, status = valid,
4. jesli nie pasuje, policzyc error_syndrome = syndrome xor expected_offset,
5. sprawdzic tablice korekcji,
6. jesli znaleziono dopasowanie, odwrocic wskazane bity i status = corrected,
7. jesli nie znaleziono dopasowania, status = uncorrectable.

Wniosek implementacyjny:
- korekcja musi dzialac na warstwie block decoder, nie w parserze grup,
- parser PI, PS, RT i innych pol powinien dostawac tylko bloki valid albo corrected.

### Flywheel i bit slip correction

Flywheel dla utrzymania synchronizacji:
- aktywny tylko w stanie SYNC,
- valid lub corrected block zmniejsza licznik bledow,
- uncorrectable block zwieksza licznik bledow,
- po przekroczeniu progu przejscie do LOST.

Rekomendacja startowa dla progu flywheel:
- start od wartosci 8 do 12,
- domyslnie 8 dla szybszej reakcji podczas debug,
- pozniej mozna poluznic, jesli okaze sie zbyt agresywny.

Bit slip correction:
- jesli w SYNC oczekiwany blok nie przechodzi walidacji,
- sprawdzic wariant nominalny,
- sprawdzic blok przesuniety o +1 bit,
- sprawdzic blok przesuniety o -1 bit,
- jesli jedna z tych wersji daje valid albo corrected dla oczekiwanego offsetu, skorygowac faze bitowa i pozostac w SYNC.

Wniosek:
- bit slip correction powinna byc uruchamiana oszczednie,
- najlepiej tylko wtedy, gdy jakosc lock spada,
- nie jako stale skanowanie wszystkich wariantow dla kazdego bloku.

### Budowa tabeli korekcji burst error

Docelowo tablica korekcji nie powinna byc wpisywana recznie.

Algorytm generacji tabeli dla burst errors o dlugosci 1 do 5:
1. dla kazdej dlugosci burst `L` od 1 do 5,
2. dla kazdej pozycji startowej `p` od 0 do `26 - L`,
3. zbudowac 26-bitowa maske bledu z `L` kolejnymi jedynkami,
4. policzyc syndrome dla tej maski,
5. zapisac wpis: `syndrome -> maska, burst_length, first_bit_index`.

Liczba wzorcow do wygenerowania:
- dla `L = 1`: 26,
- dla `L = 2`: 25,
- dla `L = 3`: 24,
- dla `L = 4`: 23,
- dla `L = 5`: 22,
- razem: 120 wpisow.

Wniosek praktyczny:
- tabela jest mala,
- mozna ja generowac offline i wkleic jako `static const`,
- albo generowac raz przy starcie modulu i zachowac w RAM.

Rekomendacja dla tego projektu:
- wygenerowac ja offline i trzymac jako `static const`,
- unikamy kosztu startowego i ryzyka roznic miedzy buildami,
- latwiej tez testowac poprawne syndromy na hostowym skrypcie.

Minimalny kontrakt wpisu tabeli:
- `syndrome10`,
- `mask26`,
- `burst_length`,
- `first_bit_index`.

Wymaganie testowe:
- generator tabeli musi byc sprawdzony na zestawie kontrolnym,
- dla kazdego wpisu po poprawce blok ma dawac `syndrome == expected_offset`.

### Kontrakt zdarzen RDSCore -> radio.c

RDSCore nie powinien bezposrednio modyfikowac UI ani stanu aplikacji FM.

Zamiast tego powinien publikowac lekkie zdarzenia:
- `DecoderStarted`,
- `PilotDetected`,
- `RdsCarrierDetected`,
- `SyncAcquired`,
- `SyncLost`,
- `PiUpdated`,
- `PsUpdated`,
- `PtyUpdated`,
- `BlockStatsUpdated`.

Minimalna struktura zdarzenia:
- `type`,
- `tick_ms`,
- `pi`,
- `ps[9]`,
- `pty`,
- `sync_state`,
- `block_counters`.

Zasada publikacji:
- `PiUpdated` tylko przy zmianie stabilnego PI,
- `PsUpdated` dopiero po potwierdzeniu kompletnego i stabilnego 8-znakowego PS,
- `SyncLost` tylko przy realnej utracie lock, nie przy pojedynczym slabym bloku,
- `BlockStatsUpdated` rzadko, np. co 250 ms albo co 500 ms.

Wniosek architektoniczny:
- `radio.c` powinno dostawac juz odfiltrowane zdarzenia wysokiego poziomu,
- dzieki temu dekoder nie zaleje glownej petli i nie utrudni debugowania UI.

### Szkic struktury RDSCore

Proponowany podzial struktur:

```c
#define RDS_PS_LEN 8U
#define RDS_RT_LEN 64U
#define RDS_EVENT_QUEUE_SIZE 8U

typedef enum {
	RdsSyncStateSearch = 0,
	RdsSyncStatePreSync,
	RdsSyncStateSync,
	RdsSyncStateLost,
} RdsSyncState;

typedef enum {
	RdsBlockTypeUnknown = 0,
	RdsBlockTypeA,
	RdsBlockTypeB,
	RdsBlockTypeC,
	RdsBlockTypeCp,
	RdsBlockTypeD,
} RdsBlockType;

typedef enum {
	RdsBlockStatusInvalid = 0,
	RdsBlockStatusValid,
	RdsBlockStatusCorrected,
	RdsBlockStatusUncorrectable,
} RdsBlockStatus;

typedef enum {
	RdsEventTypeNone = 0,
	RdsEventTypeDecoderStarted,
	RdsEventTypePilotDetected,
	RdsEventTypeRdsCarrierDetected,
	RdsEventTypeSyncAcquired,
	RdsEventTypeSyncLost,
	RdsEventTypePiUpdated,
	RdsEventTypePsUpdated,
	RdsEventTypeRtUpdated,
	RdsEventTypePtyUpdated,
	RdsEventTypeBlockStatsUpdated,
} RdsEventType;

typedef struct {
	uint32_t raw26;
	uint16_t data16;
	uint16_t syndrome10;
	uint16_t expected_offset10;
	uint16_t error_syndrome10;
	uint32_t correction_mask26;
	RdsBlockType type;
	RdsBlockStatus status;
	uint8_t corrected_bits;
} RdsBlock;

typedef struct {
	RdsBlock blocks[4];
	uint8_t count;
	uint16_t pi;
	uint8_t group_type;
	bool version_b;
	bool complete;
} RdsGroup;

typedef struct {
	char ps[RDS_PS_LEN + 1U];
	char ps_candidate[RDS_PS_LEN + 1U];
	char rt[RDS_RT_LEN + 1U];
	char rt_candidate[RDS_RT_LEN + 1U];
	uint16_t pi;
	uint16_t rt_segment_mask;
	uint8_t pty;
	uint8_t rt_length;
	bool rt_ab_flag;
	bool tp;
	bool ta;
	bool ps_ready;
	bool rt_ready;
} RdsProgramInfo;

typedef struct {
	uint16_t syndrome10;
	uint32_t mask26;
	uint8_t burst_length;
	uint8_t first_bit_index;
} RdsCorrectionEntry;

typedef struct {
	RdsEventType type;
	uint32_t tick_ms;
	uint16_t pi;
	char ps[RDS_PS_LEN + 1U];
	char rt[RDS_RT_LEN + 1U];
	uint8_t pty;
	RdsSyncState sync_state;
	uint32_t total_blocks;
	uint32_t valid_blocks;
	uint32_t corrected_blocks;
	uint32_t uncorrectable_blocks;
} RdsEvent;

typedef struct {
	RdsSyncState sync_state;
	RdsBlockType expected_next_block;
	uint8_t block_index_in_group;
	uint8_t flywheel_errors;
	uint8_t flywheel_limit;

	uint32_t bit_window;
	uint64_t bit_history;
	uint8_t bit_count;
	int8_t bit_phase;

	float pilot_level;
	float rds_band_level;
	float lock_quality;

	uint32_t total_blocks;
	uint32_t valid_blocks;
	uint32_t corrected_blocks;
	uint32_t uncorrectable_blocks;
	uint32_t sync_losses;
	uint32_t bit_slip_repairs;

	RdsGroup current_group;
	RdsProgramInfo program;
	uint8_t ps_segment_mask;
	bool slip_retry_pending;
	RdsEvent event_queue[RDS_EVENT_QUEUE_SIZE];
	uint8_t event_read_idx;
	uint8_t event_write_idx;
	uint8_t event_count;
} RDSCore;
```

Minimalny zestaw funkcji dla RDSCore:

```c
void rds_core_reset(RDSCore* core);
void rds_core_restart_sync(RDSCore* core);
void rds_core_push_bit(RDSCore* core, uint8_t bit);
bool rds_core_consume_demod_bit(RDSCore* core, uint8_t bit, RdsBlock* decoded_block);
bool rds_core_try_decode_block(RDSCore* core, RdsBlock* block, uint32_t raw26);
void rds_core_handle_block(RDSCore* core, const RdsBlock* block);
void rds_core_handle_group(RDSCore* core, const RdsGroup* group);
bool rds_core_pop_event(RDSCore* core, RdsEvent* event);
```

Podzial odpowiedzialnosci:
- front-end DSP produkuje strumien bitow po DBPSK,
- RDSCore zajmuje sie tylko warstwa linkowa i parserem grup,
- aplikacja FM dostaje juz przetworzone zdarzenia i ustabilizowane pola typu PI i PS.

Wniosek architektoniczny:
- taki podzial jest zgodny i z SAA6588, i z rozsadowa architektura software,
- pozwala testowac osobno:
- tor DSP,
- block decoder,
- parser grup,
- warstwe UI.

Plan implementacyjny dla kodu:
- `RDS/RDSCore.h`: definicje typow, struktur i API rdzenia,
- `RDS/RDSCore.c`: maszyna stanow, liczniki, kolejka pojedynczego zdarzenia i dekoder blokow,
- przyszle rozszerzenie: `RDS/RDSDsp.h/.c` dla toru I/Q i synchronizacji symbolowej.

### Aktualny status implementacji

Stan na teraz dla `RDSCore`:

Juz zaimplementowane:
- struktury i API rdzenia w `RDS/RDSCore.h`,
- maszyna stanow `SEARCH -> PRE_SYNC -> SYNC -> LOST`,
- liczenie syndrome dla 26-bitowych blokow,
- rozpoznawanie blokow `A/B/C/C'/D`,
- korekcja burst errors do 5 bitow przez tablice korekcji,
- statusy `valid`, `corrected`, `uncorrectable`,
- flywheel do utrzymania synchronizacji,
- `bit slip correction` w dwoch kierunkach: natychmiastowy retry dla -1 bit i opozniony retry dla +1 bit,
- szybsze odzyskiwanie synchronizacji przez `fast resync`,
- skladanie grup z blokow `A/B/C(C')/D`,
- parser grup `0A/0B` dla `PI`, `PS`, `PTY`, `TP`, `TA`,
- parser grup `2A/2B` dla `RadioText`,
- ring buffer zdarzen (zamiast pojedynczego `pending_event`) i odczyt FIFO przez `rds_core_pop_event()`,
- zdarzenia `PiUpdated`, `PsUpdated`, `RtUpdated`, `PtyUpdated`, `SyncAcquired`, `SyncLost`,
- wejscie bitowe z DSP do rdzenia przez `rds_core_consume_demod_bit()`.

To oznacza, ze warstwa linkowa i parser grup sa juz w duzej mierze gotowe.

Jeszcze niezaimplementowane:
- rzeczywisty tor DSP od probek ADC do bitow `0/1`,
- wydzielenie tego toru do osobnego modulu `RDS/RDSDsp.h/.c`,
- doprowadzenie realnych bitow z demodulatora do `rds_core_consume_demod_bit()`,
- integracja zdarzen `RDSCore` z `radio.c`,
- opcja `RDS On/Off` w menu konfiguracji,
- wyswietlanie `PS` i pozniej `RT` w UI aplikacji,
- debug dump z prawdziwego runtime na karte SD,
- testy offline dla znanych ramek RDS oraz testy z rzeczywistym MPX,
- ewentualne rozszerzenia na dalsze grupy: `CT`, `AF`, `EON`, `TA/TP` logika wyzszego poziomu.

Wniosek:
- `RDSCore` nie jest jeszcze pelnym systemem RDS,
- ale jest juz prawie pelna warstwa linkowa i parser podstawowych grup,
- najwieksza brakujaca czesc przed integracja z aplikacja to front-end DSP.

Rekomendowana kolejnosc dalszych prac:
1. zbudowac `RDSDsp` produkujacy stabilne bity do `rds_core_consume_demod_bit()`,
2. podlaczyc zdarzenia `RDSCore` do `radio.c`,
3. uruchomic pierwsza prezentacje `PI/PS` w UI,
4. potem dopiero stroic `RadioText`, jakosc lock i debug dump runtime.

## Plan firmware

Etap 1:
- uruchomic ADC na PA4
- zrzucac MPX do bufora DMA
- zapisac probki do debug loga lub prostego dumpa do analizy offline

Etap 2:
- potwierdzic widmo: pilot 19 kHz, skladnik stereo, nosna 57 kHz RDS

Etap 3:
- napisac cyfrowy front-end RDS
- wydzielic kanal 57 kHz
- uruchomic pierwsza detekcje bitow

Etap 4:
- dekodowac grupy RDS
- pokazac podstawowe pola: PI, PS, RT, PTY

Etap 5:
- zoptymalizowac obciazenie CPU
- sprawdzic czy implementacja nie psuje responsywnosci aplikacji FM

### Budzet danych dla runtime i debugu

Przy 228 kS/s i probkach uint16_t:
- strumien danych ADC = 228000 x 2 B/s = 456000 B/s
- czyli okolo 445 KiB/s

Wniosek:
- ciagly dump wszystkiego do pliku nie powinien byc aktywny stale w normalnym runtime,
- raw dump musi byc trybem diagnostycznym uruchamianym czasowo,
- w normalnym trybie pracy nalezy zapisywac tylko lekkie logi zdarzen dekodera.

## Proponowany format plikow debug dump

Lokalizacja katalogu:
- /ext/apps_data/fmradio_controller_pt2257/rds_debug/

Rekomendowany uklad plikow jednej sesji debug:
- session_meta.txt
- mpx_adc_u16le.raw
- rds_events.csv

### 1. session_meta.txt

Czytelny tekstowy plik metadanych, format key=value, np.:
- app_version=
- utc_or_tick=
- station_freq_10khz=
- sample_rate_hz=228000
- adc_bits=12
- adc_storage=u16le
- adc_pin=PA4
- adc_channel=ADC1_IN9
- input_mode=dc_offset_only albo mcp6001_x4
- dc_bias_mv=
- gain_nominal=
- dma_samples=2048
- block_samples=1024

Cel:
- szybka diagnoza bez potrzeby domyslania sie parametrow nagrania.

### 2. mpx_adc_u16le.raw

Format:
- surowe probki ADC,
- little-endian,
- jedna probka = uint16_t,
- wartosci 0 do 4095 zapisane w 16 bitach.

Powod:
- format jest prosty do zrzutu,
- latwy do otwarcia w Pythonie, MATLABie, Octave albo Audacity po konwersji,
- nie traci informacji o rzeczywistym poziomie offsetu DC i clippingu.

Uwagi:
- ten plik zapisujemy tylko w trybie diagnostycznym,
- jedna sesja dumpa powinna miec ograniczony czas, np. kilka sekund.

### 3. rds_events.csv

Format CSV, jedna linia na zdarzenie lub probe diagnostyczna wyzszego poziomu.

Proponowane kolumny:
- tick_ms
- event
- pi_hex
- ps
- pty
- block_ok
- block_err
- sync_state
- pilot_detected
- rds57_detected

Przykladowe zdarzenia:
- decoder_start
- pilot_lock
- rds_lock
- ps_update
- sync_lost
- decoder_stop

Cel:
- szybko zobaczyc, czy dekoder w ogole lapie pilot, 57 kHz i poprawne bloki,
- nie trzeba analizowac surowego RAW przy kazdym problemie.

## Wymagania PCB

Na PCB nalezy przewidziec:
- polaczenie MPX z TEA5767 do sekcji RDS
- wejscie na PA4 oznaczone jako RDS_MPX_ADC
- footprint pod prosty tor offsetu DC
- footprint pod MCP6001 i rezystory ustawiajace wzmocnienie
- mozliwosc obejscia aktywnego wzmacniacza na czas pierwszych testow

## Finalna decyzja projektowa na teraz

Na obecnym etapie przyjmujemy:
- fizyczne wyprowadzenie MPX do pin 4 / PA4 / ADC1_IN9
- w planie PCB opisac tylko to polaczenie i rezerwacje pinu
- szczegoly analog front-end i firmware dekodera RDS prowadzic w tym osobnym planie
- domyslny sample rate runtime: 228 kS/s
- domyslny bufor DMA: 2048 probek z obrobka blokow po 1024 probki
- docelowy budzet RAM modulu RDS: okolo 12 KB
- surowy dump ADC tylko w trybie diagnostycznym, nie stale w runtime