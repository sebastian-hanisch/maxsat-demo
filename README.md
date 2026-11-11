# MaxSAT – die Kerngröße geht mit den Unterschieden einher – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-maxsat-demo.streamlit.app/)**

Demo der Linie **SAT und Constraint Programming** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Sie wechselt von der Frage „Ist die Formel erfüllbar?“ zur Frage „**Wie viele weiche Klauseln müssen fallen?**“ (MaxSAT) und nutzt dafür die Bausteine des SAT-Arms der Linie: den CDCL-Löser mit Annahmen, der bei „unerfüllbar“ einen **Kern** nennt (eine Teilmenge der Annahmen, die den Widerspruch erklärt), und den Zähler aus der Kardinalitäts-Kodierung. Die Demo zeigt an einem Beispiel mit sechs weichen Klauseln von Hand, wie Kerne die untere Schranke heben, und vergleicht **lineare Suche, Fu–Malik und OLL** in Konflikten (nie in Sekunden) auf Aufträgen mit Unverträglichkeiten: Kontrollpunkte (Vertex Cover), Rampen (3-Färbung mit möglichst wenigen Konflikten) und einer überbestimmten Zufallsformel.

## Warum dieses Problem

Ein MaxSAT-Löser sucht Kerne. Beobachtet wird: Bei Kernen aus zwei Literalen (Kontrollpunkte n = 50) liegen die Konflikte im Median bei 1 für OLL und bei 1.839,5 (von oben) bzw. 2.629,5 (von unten) für die lineare Suche (zehn Instanzen), die verglichenen Verfahren liegen weit auseinander. Bei großen Kernen (Rampen, Formeln, Kerne aus 25 bis 73 Literalen) sind alle Verfahren teuer: OLL hat bei Rampen n = 40 und 60 im Median das 1,4- bzw. 1,3-Fache weniger Konflikte als die beste lineare Suche (je Instanz in 5 bzw. 9 von 10 Fällen weniger), bei Rampen n = 90 und bei der Formel liegen OLL und lineare Suche innerhalb des Faktors 1,25 gleichauf. Ob die Kerngröße die Ursache dieser Unterschiede ist, ist nicht getrennt untersucht: die Familien unterscheiden sich auch in Struktur und Klauselzahl. **Gewichte** kosten die lineare Suche (ein Zähler mit so vielen Eingängen wie die Gewichtssumme); das kerngeführte OLL kommt mit 110 bzw. 158,5 Klauseln aus, seine Konflikte steigen durch Gewichte bei Kontrollpunkten nicht, bei der Formel auf das 2-Fache; die **Kernminimierung** macht die Kerne kleiner, aber die Gesamtkosten meist größer. Alle Zahlen stehen unten im Abschnitt „Befunde“.

## Modell

- **Partielles MaxSAT.** Harte Klauseln müssen gelten, jede weiche Klausel hat ein ganzzahliges Gewicht ≥ 1; Kosten = Summe der Gewichte der verletzten weichen Klauseln, gesucht ist das Minimum (Datenklasse `MaxSat` in `mxs_scenario.py`).
- **Instanzfamilien** (alle Zufall über den ganzzahligen SplitMix64, auf jeder Plattform dieselbe Instanz): **Kontrollpunkte** (Zufallsgraph mit mittlerem Grad 3; hart: jede Kante hat an einem Ende einen Kontrollpunkt, weich: „Auftrag i hat keinen Kontrollpunkt“); **Rampen** (Zufallsgraph mit mittlerem Grad 5, drei Rampen; hart: jeder Auftrag genau eine Rampe, weich: „Kante j ist farbverträglich“); **Formel** (Zufalls-3-SAT mit sechs Klauseln je Variable, alle Klauseln weich). **Gewichte** gleichverteilt 1 bis 10 (Zufalls-Seed 31 · Seed + 7).
- **Kern und untere Schranke.** Der Löser wird unter Annahmen („diese weichen Klauseln gelten“) gefragt; bei „unerfüllbar“ liefert er einen Kern. Mindestens eine Annahme des Kerns wird verletzt, die untere Schranke steigt um das kleinste Gewicht im Kern. Endet das Verfahren, ist die untere Schranke gleich den Kosten des gefundenen Modells.
- **Vier Verfahren** (Datei `mxs_algorithm.py`; alle Fu–Malik, OLL, Stratifizierung und Kernminimierung sind **einfache Fassungen nach Gedächtnis, nicht gegen die Literatur geprüft**): **lineare Suche von oben** (Schranke auf die Kosten immer weiter senken, bis unerfüllbar) und **von unten** (k = 0, 1, 2, … bis erfüllbar), beide mit einem unär kodierten Zähler (jede Relaxationsvariable so oft als Eingang, wie ihr Gewicht sagt); **Fu–Malik** (nur ungewichtet: je Kern eine neue Relaxationsvariable je Mitglied, paarweise höchstens eine); **OLL** (je Kern ein Zähler über die Kernliterale, neue Annahme „höchstens eine Verletzung im Kern“, Gewichtsabzug); dazu **Stratifizierung** (Annahmen nach Gewicht absteigend schichtweise zulassen) und **Kernminimierung** (je Kern höchstens 30 Versuche, ein Literal wegzulassen und mit 300 Konflikten erneut zu prüfen; die Konflikte und SAT-Aufrufe der Minimierung zählen mit).
- **Löser.** CDCL der Linie (Kern-Kopie `mxs_cdcl.py`): 1-UIP, Aktivität (VSIDS-Variante), Phasenspeicher, Luby-Neustarts (Einheit 32), ohne Löschen. Aufwand in **Konflikten** und **SAT-Aufrufen**, nie in Sekunden. Budget: 10.000 Konflikte je SAT-Aufruf und 30.000 je Verfahren und Instanz; ein Lauf am Budget gibt keine Antwort, nur eine untere Schranke, und zählt mit dem Gesamtbudget.
- **Messreihen.** Zehn feste Instanzen je Zelle (Zufalls-Seeds 100 bis 109), alle Verfahren der Zelle. Kennzahlen: Konflikte (Median, Minimum, Maximum), SAT-Aufrufe, **Kerngröße** (Zahl der Literale im Kern; je Instanz der Median, über die Zehn der Median), dem Löser übergebene Klauseln, Abbrüche, falsche Antworten (Abweichung vom Referenzoptimum).
- **CP-SAT als Maßstab** (OR-Tools, ein Arbeiter, 15 Sekunden): nur als **vorgerechnete Datei** `mxs_cpsat.json` (Messskript `tools/cpsat_messung.py`), nie in der App; die Optima daraus sind zugleich die Referenz für die Antworten der Verfahren.
- Mathematik und Symboltabelle: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| CDCL mit Annahmen und Kernen | `mxs_cdcl.py` | **wörtliche Kopie** des Kern-Moduls `cdcl.py` der Linie (Kern-Version 832b2c10dfdea62d); nur der Import ist auf `mxs_rng` umgestellt (`tests/test_kern_kopien.py`) |
| SplitMix64 | `mxs_rng.py` | Kopie von `rng.py` (5d5d8f45d0e1eddf); Regressionstest auf veröffentlichte Referenzwerte |
| Instanzerzeuger (hier: `zufallskanten`, `rand3`) | `mxs_instanzen.py` | Kopie von `instanzen.py` (6795de796b66fff8) |
| Hilfsvariablen, „höchstens eins“ | `mxs_kodierung.py` | Kopie von `kodierung.py` (208571302afd04b4); Fu–Malik nutzt `hoechstens_eins` |
| Zähler mit herausgereichten Ausgängen, vier Verfahren, Kernwahl, Aufzählung | `mxs_algorithm.py` | eigene Einheiten: `totalizer`, `totalizer_klauselzahl`, `lineare_suche`, `fu_malik`, `oll`, `aufzaehlung`, `alle_minimalen_kerne` |
| Instanzerzeuger der drei Familien, Handbeispiel, Kosten | `mxs_scenario.py` | `kontrollpunkte`, `rampen`, `formel`, `mit_gewichten`, `erzeuge` |
| Kennzahlen, Verdikte, Tabellen | `mxs_evaluation.py` | Verdikte sind reine Funktionen; jede Zahl im Text stammt aus den Kennzahlen |
| Vorgerechnete Messreihen | `mxs_messungen.json` | geschrieben von `tools/messungen.py` (dieselben Funktionen wie die Live-Läufe) |
| Eingefrorener CP-SAT-Maßstab | `mxs_cpsat.json` | geschrieben von `tools/cpsat_messung.py` (OR-Tools); in der App nie benutzt |

Der **Totalizer** (Addierbaum in Einerdarstellung) ist nach der Beschreibung bei Sinz gebaut, das Original (Bailleux und Boufkhad, CP 2003) ist nicht gelesen. Er gibt anders als die Kern-Kodierung alle Ausgänge heraus, weil OLL und die lineare Suche einzelne Ausgänge als Annahme brauchen; seine Klauselzahl steht als Formel (je Knoten (p_a + 1)(p_b + 1) − 1) und wird im Test gegen den Aufbau geprüft.

Experimente in der App: **Kerne von Hand** (Handbeispiel mit sechs weichen Klauseln: Optimum durch Aufzählung, alle minimalen Kerne, Fu–Malik und OLL nebeneinander mit Kerngröße und unterer Schranke je Schritt, Klausel-Matrix mit den Kernen, wahlweise mit den Gewichten 2, 1, 1, 3, 1, 1), **Verfahren im Vergleich** (vorgerechnete Zelle mit Streifendiagramm, Tabelle, Verdikt und CP-SAT-Spalte; dazu live eine Instanz oder zehn), **Was kosten Gewichte** (Klauselzahl des unären Zählers gerechnet, OLL mit und ohne Stratifizierung), **Kernminimierung als Negativbefund** (über alle Zellen, live auf einer Instanz). Die großen Messreihen und CP-SAT sind **vorgerechnet, nicht live**.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen dieser Tabelle stehen in `tests/test_claims.py` (Messungen: `mxs_messungen.json`, Skript `tools/messungen.py`; CP-SAT: `mxs_cpsat.json`, Skript `tools/cpsat_messung.py`). **13 Zellen** (7 ungewichtet, 6 gewichtet 1 bis 10), **10 feste Instanzen** je Zelle (Zufalls-Seeds 100 bis 109), 570 Läufe der Verfahren; Budget 10.000 Konflikte je SAT-Aufruf und 30.000 je Verfahren und Instanz. Konflikte als **Median über die zehn Instanzen**, ein Lauf am Budget zählt mit 30.000 und ist nur eine untere Schranke. **Von den 570 Läufen erreichen 38 das Budget; die übrigen 532 liefern das Referenzoptimum** (OR-Tools CP-SAT, bewiesen bei 125 von 130 Instanzen; die 5 übrigen sind Rampen n = 90, bei denen auch kein Verfahren beendet hat) mit Kosten des Endmodells gleich unterer Schranke gleich Optimum: **0 falsche Antworten**. Die Instanzen sind eine Familie je Zelle mit festem Parameter; die Aussagen gelten für diese Instanzen und die einfachen Fassungen der Verfahren, nicht für andere Familien oder Löser.

| Frage | Befund |
|---|---|
| **Kerne aus zwei Literalen** (Kontrollpunkte n = 20, 30, 50, ungewichtet) | Die Kerne haben im Median 2 Literale. Konflikte im Median: **OLL 1,5 / 1 / 1** (höchstens 9 in einer Instanz), Fu–Malik 3,5 / 4 / 25,5, lineare Suche von oben 39,5 / 121 / 1.839,5, von unten 55 / 211,5 / 2.629,5; CP-SAT 0 / 2,5 / 20,5. Die beste lineare Suche braucht das 26-, 121- und 1.840-Fache von OLL (Medianverhältnis der besten linearen Suche zu OLL). Optimum im Median 9,5 / 14 / 24 (`test_claim_kontrollpunkte_kerne_aus_zwei_literalen_und_ein_bis_zwei_konflikte`). |
| **Große Kerne** (Rampen n = 40, 60, 90 und Formel n = 40, ungewichtet) | Kerne im Median aus **25 / 61 / 73 / 70 Literalen**. Konflikte im Median OLL 254 / 380,5 / 16.504,5 / 2.797, lineare Suche von unten 365 / 504,5 / 17.856 / 2.386, von oben 443 / 809,5 / 18.264,5 / 17.179,5. OLL hat bei Rampen n = 40 und 60 im Median das 1,4- bzw. 1,3-Fache weniger als die beste lineare Suche (unten), je Instanz bei Rampen n = 40 in 5 von 10, bei n = 60 in 9 von 10 Fällen weniger; bei Rampen n = 90 und der Formel liegen beide innerhalb des Faktors 1,25 („ungefähr gleichauf“), bei Rampen n = 90 ist OLL je Instanz in 4 von 10, bei der Formel in 6 von 10 Fällen billiger als die beste lineare Suche; der Median der linearen Suche von unten liegt bei der Formel etwas niedriger als der von OLL (2.386 gegen 2.797). Es gibt in diesen Zellen **keinen Abstand von einer Größenordnung** (`test_claim_grosse_kerne_rampen_und_formel_oll_ungefaehr_gleichauf_mit_der_linearen_suche`). |
| **Abbrüche am Budget** (je 10 Instanzen) | OLL bricht nie öfter ab als die lineare Suche von oben oder Fu–Malik: Rampen n = 90 OLL 5, lineare Suche von oben 5, von unten 5, Fu–Malik 6; Formel n = 40 OLL **0**, von oben 3, von unten 0, Fu–Malik 5; Rampen n = 40 / 60 Fu–Malik 1 / 2, sonst 0. In allen 7 ungewichteten Zellen zusammen: OLL 5, Fu–Malik 14 (`test_claim_oll_bricht_nicht_oefter_ab_als_die_lineare_suche_und_bei_formeln_seltener`). |
| **OLL gegen Fu–Malik** | OLL braucht im Median in **allen 7** ungewichteten Zellen weniger Konflikte; je Instanz in 52 von 70 weniger, in 13 gleich viele, in 5 mehr. Die Kerne sind bei Rampen und Formel kleiner (25 gegen 47, 61 gegen 77,25, 73 gegen 119,5 und 70 gegen 158,5 Literale), bei den Kontrollpunkten gleich (2 Literale) (`test_claim_oll_gegen_fu_malik`). |
| **Gewichte 1 bis 10: lineare Suche** (Kontrollpunkte n = 20 und 30) | Der unär kodierte Zähler braucht im Median **6.542 bzw. 13.317,5 Klauseln** statt 328 bzw. 658 ohne Gewichte (das 19,9- bzw. 20,2-Fache); OLL kommt mit 110 und 158,5 Klauseln aus. Konflikte im Median gewichtet: lineare Suche von oben 106,5 / 230, von unten 255 / 756, **OLL 0 / 0** (`test_claim_unaerer_zaehler_kostet_das_zwanzigfache_an_klauseln`). |
| **Gewichte: OLL** | OLL löst alle gewichteten Zellen bis auf **eine Instanz der Formel** (1 von 10 am Budget) ohne Abbruch; Konflikte im Median: Kontrollpunkte n = 20 / 30 / 50: 0 / 0 / 0,5, Rampen n = 40 / 60: 192,5 / 508,5, Formel: 5.522,5 (ungewichtet 2.797, das 2-Fache) (`test_claim_gewichtet_oll_bricht_nur_bei_der_formel_einmal_ab_und_die_stratifizierung_nie`). |
| **Stratifizierung** | Konflikte im Median OLL → OLL + Stratifizierung: Rampen n = 40 192,5 → **116**, n = 60 508,5 → **353,5**, Formel 5.522,5 → **1.286,5** (kein Abbruch mehr); bei Kontrollpunkten keine Verbesserung (0 → 0, 0 → 1, 0,5 → 1). **Median allein täuscht:** je Instanz hat die Stratifizierung bei Rampen n = 40 in 8 von 10, bei n = 60 nur in 3 von 10, bei der Formel in 9 von 10 weniger Konflikte. Sie braucht mehr SAT-Aufrufe (Rampen 7 → 13 und 6 → 14, Formel 11 → 15) (`test_claim_stratifizierung_senkt_den_median_bei_rampen_und_formel_nicht_bei_kontrollpunkten`). |
| **Kernminimierung** (Negativbefund) | Über alle 13 Zellen (ungewichtet OLL gegen OLL + Minimierung, gewichtet jeweils mit Stratifizierung): die Kerne werden in **7 Zellen kleiner** (Rampen n = 40: 25 → 16, n = 60: 61 → 34,75, Formel: 70 → 60, gewichtet Rampen n = 40: 47 → 26,5), in den übrigen sind sie gleich (Kontrollpunkte: 2); die **Gesamtkonflikte** (Minimierungsaufrufe mitgezählt) sind im Median in **10 Zellen größer**, in 2 kleiner (Kontrollpunkte n = 20 und 30 ungewichtet: 1,5 → 1 und 1 → 0,5), in 1 gleich. Bei Rampen n = 40 steigen die SAT-Aufrufe von 3,5 auf 66,5 (`test_claim_kernminimierung_kerne_kleiner_konflikte_meist_groesser`, `test_claim_kerngroessen_mit_und_ohne_minimierung`, `test_claim_minimierungsaufrufe_zaehlen_mit`). |
| **CP-SAT** (vorgerechnet; Konflikte der Löser-Statistik, mit denen des Python-CDCL nicht gleichwertig) | Kontrollpunkte ungewichtet 0 / 2,5 / 20,5, gewichtet 1,5 / 3,5 / 168 Konflikte im Median. Rampen n = 40 / 60 / 90 und Formel n = 40: 1.653,5 / 2.653 / 193.899 / 33.529,5, das 6,5- / 7,0- / 11,7- / 12,0-Fache der OLL-Konflikte; bei Rampen n = 90 5 von 10 Instanzen ohne Beweis nach 15 Sekunden. Gewichtet liegt CP-SAT bei Rampen und Formel über OLL + Stratifizierung (365,5 / 1.165 / 6.001,5 gegen 116 / 353,5 / 1.286,5) (`test_claim_cpsat_baender`, `test_claim_cpsat_auf_kontrollpunkten_wenige_konflikte_auf_rampen_und_formeln_ein_vielfaches_von_oll`). |
| **Handbeispiel** (drei Variablen, höchstens eine wahr, sechs weiche Klauseln) | Optimum 3 bei 4 optimalen Belegungen; sechs minimale Kerne {S1,S2}, {S1,S3}, {S1,S4}, {S2,S3}, {S2,S5}, {S3,S6}. Fu–Malik findet Kerne aus 2, 2 und **4** Literalen, OLL aus 2, 2 und **3** (untere Schranke 1, 2, 3). Gewichte 2, 1, 1, 3, 1, 1: Optimum 4 bei 3 Belegungen, OLL findet vier Kerne, der unäre Zähler hätte 9 statt 6 Eingänge (`tests/test_algorithm.py`, von Hand nachgerechnet; kleinster Kern, bei Gleichstand der lexikographisch erste). |

Die Zählung je Instanz steht neben jedem Verhältnis der Mediane, weil der Median allein täuscht (Stratifizierung bei Rampen n = 60). Die App zeigt je eine Zelle samt Streifendiagramm der zehn Instanzen.

## Ehrliche Grenzen

- **Drei Familien mit je einem Parameter, ein Löser.** Kontrollpunkte (Grad 3), Rampen (Grad 5), Formeln (sechs Klauseln je Variable), je Zelle zehn Instanzen, ein Python-CDCL (Aktivität, Phasenspeicher, Luby-Neustarts, ohne Löschen). Rangfolgen können bei anderen Familien, Gewichtsverteilungen (hier nur gleichverteilt 1 bis 10), Parametern oder Lösern anders ausfallen. **Dass die Kerngröße die Ursache der Unterschiede ist, ist nicht getrennt untersucht:** die drei Familien unterscheiden sich außer in der Kerngröße (2 bis 158,5 Literale, Median je Zelle, Fu–Malik eingeschlossen) auch in Struktur und Klauselzahl, und Optimum und Familie gehen miteinander einher (Optimum im Median bei Kontrollpunkten 9,5 / 14 / 24, bei Rampen n = 40 2,5, bei der Formel 3); gemessen ist, dass die Verfahren bei kleinen Kernen weit auseinanderliegen und bei großen nicht.
- **Die Verfahren sind einfache Fassungen nach Gedächtnis.** Fu–Malik, OLL, Stratifizierung und Kernminimierung sind nicht gegen die Literatur geprüft; es fehlen Hardening, Core-Exhaustion, Diversitätsregel und gewichtete Kodierungen (Generalized Totalizer). Die Kernminimierung ist ein einfacher Ablauf (300 Konflikte, 30 Versuche je Kern); andere Budgets können anders ausgehen. Aussagen über moderne MaxSAT-Löser machen diese Messungen nicht.
- **Kerne sind die Annahmen des Schlusskonflikts, nicht notwendig klein.** Die „Kerngröße“ der Tabellen ist die Größe des vom Löser gelieferten Kerns (bei Minimierung des verkleinerten); die Zahlen sind Mediane der Mediane. Am Handbeispiel gibt es den kleinsten Kern per Aufzählung der Teilmengen (nur bis 14 Annahmen).
- **Gewichtete lineare Suche nur in zwei kleinen Zellen** (Kontrollpunkte n = 20 und 30, unäre Kodierung); in den anderen Zellen ist nur die gerechnete Klauselzahl des Zählers genannt (Obergrenze), keine Messung.
- **Konflikte sind keine Laufzeit.** Die Zeit je Konflikt hängt von der Formelgröße ab (große Zähler, viele Hilfsvariablen); sie ist nicht gemessen. Die Konflikte von CP-SAT stammen aus dessen Statistik und sind mit denen des Python-CDCL nicht gleichwertig; CP-SAT lief mit einem Arbeiter und 15 Sekunden Zeitlimit.
- **Rampen n = 90 sind zu schwer für Python:** 5 von 10 Instanzen erreichen bei OLL und bei der linearen Suche das Budget, bei 5 Instanzen ist das Optimum unbekannt. Die Zelle steht nur als vorgerechnete Messreihe; live rechnet die App Kontrollpunkte bis n = 50, Rampen bis n = 60 und die Formel bis n = 40. **Nicht vertretbar** und nicht gemessen: Rampen ab Grad 6, Formeln mit acht Klauseln je Variable oder n ≥ 60, gewichtete lineare Suche ab n = 30 in den anderen Familien.
- **Mediane mit Abbrüchen sind nach oben vom Budget begrenzt** (Rampen n = 90, Formel gewichtet bei OLL mit einem Abbruch, Fu–Malik); die Mediane dieser Zellen sind untere Schranken.

## Befunde und Korrekturen gegenüber dem Plan

- **Neue Instanzen, neue Zahlen.** Der Plan nennt Zahlen der Vormessung mit Python-`random`; diese Demo misst mit SplitMix64 neu, die Plan-Zahlen gelten als überholt. Die Richtungen stimmen in den Kernaussagen, nicht überall in der Größe.
- **Kontrollpunkte.** Plan: OLL 0 bis 4 Konflikte, lineare Suche 155 bis 3.170 (n = 30, 50). Hier: OLL im Median 1 (in einer Instanz bis 9) Konflikte; lineare Suche 121 bis 2.629,5 im Median.
- **Große Kerne.** Plan: „OLL holt die lineare Suche ein und bricht seltener ab“, bei der Formel OLL 4.481 gegen 5.443 (von unten). Hier: bei Rampen n = 40 und 60 hat OLL das 1,4- bzw. 1,3-Fache weniger, bei der Formel liegt der Median der linearen Suche von unten etwas niedriger als der von OLL (2.386 gegen 2.797, innerhalb des Faktors 1,25, je Instanz ist OLL in 6 von 10 Fällen billiger als die beste lineare Suche), die Richtung des Plans ist dort nicht bestätigt; „bricht seltener ab“ gilt für die Formel (0 gegen 3 bei der linearen Suche von oben und 5 bei Fu–Malik), nicht bei Rampen n = 90 (gleich viele).
- **Rampen n = 90.** Plan (Z2): „mit einem erwarteten Abbruch“ (Vormessung: ein Abbruch von 10 bei OLL). Hier **5 von 10** bei OLL und bei der linearen Suche; die Zelle ist eine vorgerechnete Messreihe geblieben, nicht live.
- **OLL gegen Fu–Malik.** Plan: bei Optimum 1 bis 5 Median 1.372 gegen 5.496 Konflikte und 0 gegen 18 Abbrüche von 42. Hier in allen 7 Zellen weniger Konflikte und 5 gegen 14 Abbrüche; die Gruppierung nach Optimum aus dem Plan (1 bis 5, 6 bis 15, über 15) ist nicht wiederholt.
- **Gewichte.** Plan: 6.674 und 14.502 Klauseln bei n = 20 und 30. Hier 6.542 und 13.317,5 im Median (andere Instanzen, gleiche Größenordnung, Faktor etwa 20 gegenüber ungewichtet). Plan: Zufall n = 40 gewichtet 7.472 → 2.272 mit Stratifizierung, Färbung n = 60 304 → 182; hier 5.522,5 → 1.286,5 und 508,5 → 353,5: die Richtung stimmt, bei Rampen n = 60 aber nur in 3 von 10 Instanzen.
- **CP-SAT.** Plan: „bis zu zwei Größenordnungen schlechter“ auf Färbung und Zufallsformeln. Hier **höchstens das 12-Fache** der OLL-Konflikte (eine Größenordnung) bei 15 Sekunden Zeitlimit; die Demo sagt nichts über die Arbeitsweise von CP-SAT; Kontrollpunkte 0 bis 20,5 Konflikte (Plan: 4 bis 50).
- **Kernminimierung.** Plan: Kerne kleiner, Gesamtkonflikte meist größer (Negativbefund). Hier bestätigt: in 10 von 13 Zellen größer.
- **Zählung der SAT-Aufrufe.** In den Läufen mit Kernminimierung zählen die Aufrufe der Minimierung mit (anders als in der Vormessung); die Konflikte zählten dort schon mit.
- **Kleine Korrektur an OLL gegenüber der Vormessung.** Ein Kern aus einem Literal, das selbst ein Zählerausgang ist, zieht hier den nächsten Ausgang nach (die Vormessungsfassung ließ das aus); die Reihenfolge neuer Annahmen folgt dem Handbeispiel (neuer Zähler vor dem Nachzug). Die Orakel-Tests (Optimum aller Varianten gegen CP-SAT und Aufzählung) bestätigen die Antworten; die Wirkung auf die Zahlen ist nicht einzeln gemessen.
- **Variablenzahl des Handbeispiels.** Das Handbeispiel des Plans nennt 11 Variablen bei Fu–Malik (ohne Selektoren gezählt); die Demo nutzt Einheitsklauseln direkt als Annahme und Selektoren nur für relaxierte Klauseln, ihre Hilfsvariablen sind anders gezählt, deshalb ist diese Zahl nicht übernommen. Kerngrößen und untere Schranken stimmen mit dem Plan überein.
- **Nicht übernommen.** Rampen mit Grad 6,0 und 6,5, Formeln mit n = 60 und 80 oder acht Klauseln je Variable sind nicht Teil der Messreihe (der Plan nennt sie nur als Hinweis); die vier unvollständigen Zellen der Vormessung entfallen damit.


## Verifikation

- **Handrechnung** (`tests/test_algorithm.py`): Handbeispiel mit Optimum 3 bei vier optimalen Belegungen, den sechs minimalen Kernen, der Fu–Malik-Folge (Kerngrößen 2, 2, 4) und der OLL-Folge (2, 2, 3) sowie der gewichteten Fassung (Optimum 4, Kerne {S1, S2}, {S1, S3}, {S4, S5, Z0≥2}, {S4, S6, Z1≥2}); die Sollwerte stammen aus einer unabhängigen Rechnung mit reinem Python und Aufzählung. Zähler von Hand (drei Eingänge: 3 + 5 Klauseln), Zähler gegen alle 2⁶ Belegungen, Klauselzahl-Formel gegen den Aufbau, Instanzerzeuger.
- **Orakel** (`tests/test_oracle_maxsat.py`): das Optimum aller sieben Verfahrensvarianten gegen **Aufzählung** aller Belegungen (eigene Schleife im Test, 24 kleine Instanzen, ungewichtet und gewichtet) und gegen **OR-Tools CP-SAT** (40 Instanzen aus allen drei Familien, ungewichtet und gewichtet 1 bis 10 bzw. 1 bis 3, kleinster Kern und Kern des Lösers); Kosten des Endmodells gleich unterer Schranke gleich Optimum, harte Klauseln im Endmodell erfüllt; untere Schranke monoton und nie über dem Optimum; jeder Kern aus weichen Klauseln unabhängig als unerfüllbar bestätigt; Gewichte × c ergeben Optimum × c und dieselben Kerne; Vertauschen der weichen Klauseln ändert das Optimum nie; OLL-Schranke gleich Fu–Malik-Schranke am Ende. Der große Lauf im Scratch-Ordner (1.056 Läufe, 0 Abweichungen) steht nicht im Repo.
- **Kopien** (`tests/test_kern_kopien.py`): Kern-Hash (in jeder Umgebung), Vergleich mit dem Kern (neben `sat-cp-planung/kern`), SplitMix64-Referenzwerte, Kerne unter Annahmen gegen Aufzählung auf 100 kleinen Formeln, inkrementelles Hinzufügen von Klauseln und Variablen.
- **Randfälle** (`tests/test_edge_cases.py`): keine weiche Klausel verletzt (Optimum 0, kein Kern), harte Klauseln unerfüllbar (leerer Kern), eine einzelne weiche Klausel, Kerne aus einem Literal, Gewicht 0, Gleichstand zwischen Kernen, Budget erreicht (nie eine falsche Antwort).
- **Zweige** (`tests/test_zweige.py`): jedes Verfahren weicht auf mindestens einer Instanz vom Nachbarverfahren ab (Fu–Malik gegen OLL in Kerngröße, mit und ohne Stratifizierung in SAT-Aufrufen, mit und ohne Minimierung, von oben und von unten); ungewichtet ist die Stratifizierung wirkungslos.
- **Verdikte** als reine Funktionen, jede Schwelle (Verhältnis 1,25 inklusive, Zehnfaches inklusive) und jede Zahl im Text an handgesetzten Kennzahlen (`tests/test_verdicts.py`). **Claims:** jede Zahl der Tabelle „Befunde“ (`tests/test_claims.py`) aus der Messdatei, dazu eine Neumessung billiger Zellen gegen die Datei.
- **Oberfläche:** AppTest-Rauchtest (jeder Button einschließlich der Live-Läufe, jeder Slider am Minimum und Maximum, jede Familie mit jeder Größe und Gewichtsspanne), Schnellstart in der Seitenleiste und Hervorhebung (`tests/test_layout.py`), Footer-Test, Laufzeit-Importe.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: vier Experimente, Grenzen, Mathematik |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt): Streamlit, Pandas, Plotly |
| `requirements-dev.txt` | Laufzeit plus pytest und OR-Tools (nur Gegenprobe in den Tests und in `tools/`) |
| `tools/messungen.py`, `tools/cpsat_messung.py` | Messskripte der vorgerechneten Messreihen und des CP-SAT-Maßstabs |
| `mxs_algorithm.py` | Zähler, lineare Suche, Fu–Malik, OLL, Aufzählung, minimale Kerne |
| `mxs_cdcl.py`, `mxs_instanzen.py`, `mxs_kodierung.py`, `mxs_rng.py` | wörtliche Kopien der Kern-Module (Herkunft und Kern-Version im Kopf) |
| `mxs_constants.py` | Regler-Grenzen, Messraster, Schwellen, Farben, Presets |
| `mxs_evaluation.py` | Kennzahlen, Verdikte, Tabellen, Live-Messung |
| `mxs_layout.py` | Fester Kopf (Stylesheet) |
| `mxs_messungen.json`, `mxs_cpsat.json` | vorgerechnete Messreihen, eingefrorener CP-SAT-Maßstab |
| `mxs_presets.py` | Permalink (Einrasten), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `mxs_scenario.py` | Handbeispiel, Instanzerzeuger, Gewichte, Kosten |
| `mxs_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Randfälle, Zweige, Verdikte, Claims, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

Hardening, Core-Exhaustion und Diversitätsregel bei OLL, Generalized Totalizer und andere gewichtete Kodierungen (die gewichtete lineare Suche nutzt den unären Zähler), Kernminimierung mit Strategie (Budget je Versuch, Auswahl der Literale), Aufzählung des kleinsten Kerns für große Instanzen, Rampen mit Grad 6 oder mehr, Formeln mit acht Klauseln je Variable oder n ≥ 60, andere Gewichtsverteilungen als gleichverteilt 1 bis 10, Zeitmessungen, weitere Löser, CP-SAT in der App (nur der eingefrorene Maßstab), ein Abgleich mit der MaxSAT-Literatur und Industrieinstanzen.


## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v    # 167 Tests
```

Die vorgerechneten Messreihen neu schreiben: `python tools/messungen.py --zelle rampen|40|u --out teil.json` je Zelle (Liste mit `--liste`), danach `python tools/messungen.py --zusammen teil_*.json`; den Maßstab entsprechend mit `tools/cpsat_messung.py`. Das dauert wegen des Python-CDCL mehrere Stunden.

## Einordnung und Quellen

- **Keine Literaturquelle zu MaxSAT gelesen.** Fu–Malik und OLL (Andres u. a.; Morgado u. a.) sind nach Gedächtnis und eigener Messung gebaut, nicht gegen die Literatur geprüft; alle Aussagen dieser README sind Messungen der einfachen Fassungen in Python-CDCL, keine Aussagen über moderne MaxSAT-Löser.
- Sinz, Towards an optimal CNF encoding of Boolean cardinality constraints, CP 2005 (Volltext gelesen): sequentieller Zähler. Bailleux und Boufkhad, CP 2003 (Totalizer): **Original nicht gelesen**, nach der Beschreibung bei Sinz gebaut.
- CP-SAT als Maßstab: Perron, Didier und Gay, CP 2023 (nur Abstract gelesen); hier nur als Messung dieser Instanzen verwendet.
- Zähler und Kodierungen im Vergleich: [kardinalitaet-kodieren-demo](https://github.com/sebastian-hanisch/kardinalitaet-kodieren-demo); Konflikte und Kerne im CDCL: [konfliktlernen-demo](https://github.com/sebastian-hanisch/konfliktlernen-demo); derselbe Konfliktgraph mit anderer Frage (Färbung): [graph-coloring-demo](https://github.com/sebastian-hanisch/graph-coloring-demo).

Gebaut mit Streamlit, Pandas und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).
