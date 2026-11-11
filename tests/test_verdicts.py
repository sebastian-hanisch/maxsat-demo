"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Kennzahlen, nicht Seeds. Schwellen (vor dem Bau festgelegt): `SCHWELLE_GLEICHAUF` = 1,25 (Medianverhältnis, bis zu dem
zwei Verfahren als ungefähr gleichauf gelten) und `SCHWELLE_GROESSENORDNUNG` = 10 (ab dem Zehnfachen „um Größenordnungen“)."""

import mxs_algorithm as A
import mxs_constants as C
import mxs_evaluation as E


def _kz(median, abbrueche=0, kern=None, klauseln=100, aufrufe=5, laeufe=10):
    return E.Kennzahlen(laeufe, median, 0, 99, aufrufe, kern, klauseln, abbrueche, 0, 0)


def _zelle(oll, oben, unten, fm=None, kern=2):
    kz = {"oll": _kz(oll, kern=kern), "lin_oben": _kz(oben), "lin_unten": _kz(unten)}
    if fm is not None:
        kz["fu_malik"] = _kz(fm)
    return kz


def test_schwellen_stehen_vor_dem_bau_fest():
    assert C.SCHWELLE_GLEICHAUF == 1.25 and C.SCHWELLE_GROESSENORDNUNG == 10


def test_verfahren_um_groessenordnungen_nennt_kern_und_alle_zahlen():
    art, text = E.verdict_verfahren(_zelle(4, 2325, 3170, fm=17))
    assert art == "success"
    assert "Bei Kernen aus 2 Literalen (Median)" in text and "Konflikte im Median: OLL 4" in text
    assert "lineare Suche von unten 3.170" in text and "lineare Suche von oben 2.325" in text and "Fu–Malik (einfach) 17" in text
    assert "Lineare Suche von oben" in text and "mehr als einer Größenordnung" in text


def test_groessenordnung_ist_inklusive_beim_zehnfachen():
    assert E.verdict_verfahren(_zelle(10, 100, 120))[0] == "success"          # genau das Zehnfache
    art, text = E.verdict_verfahren(_zelle(10, 99, 120))                      # 9,9
    assert art == "info" and "das 9,9-Fache" in text


def test_ohne_konflikt_zaehlt_der_median_null_als_eins():
    art, text = E.verdict_verfahren(_zelle(0, 50, 60))
    assert art == "success" and "Konflikte im Median: OLL 0" in text


def test_gleichauf_innerhalb_des_faktors_1_25_in_beide_richtungen():
    for oll, oben, unten in ((100, 125, 300), (125, 100, 300), (100, 300, 80)):
        art, text = E.verdict_verfahren(_zelle(oll, oben, unten))
        assert art == "info" and "ungefähr gleichauf" in text and "1,25" in text, (oll, oben, unten)


def test_lineare_suche_besser_ist_eine_warnung_mit_faktor():
    art, text = E.verdict_verfahren(_zelle(200, 100, 160))                    # beste lineare Suche 100: OLL das Doppelte
    assert art == "warning" and "das 2,0-Fache" in text
    assert "Lineare Suche von oben" in text


def test_oll_etwas_besser_ist_info_mit_faktor_aber_unter_einer_groessenordnung():
    art, text = E.verdict_verfahren(_zelle(100, 300, 500))
    assert art == "info" and "das 3,0-Fache" in text and "Größenordnung" in text


def test_abbrueche_aller_verfahren_stehen_im_text():
    kz = _zelle(100, 300, 500, fm=700)
    kz = {v: k._replace(abbrueche=i) for i, (v, k) in enumerate(kz.items())}
    text = E.verdict_verfahren(kz)[1]
    assert "von 10 Instanzen" in text and "OLL 0" in text and "Lineare Suche von oben 1" in text and "Lineare Suche von unten 2" in text and "Fu–Malik (einfach) 3" in text


def test_verfahren_ohne_oll_median_meldet_keinen_vergleich():
    art, text = E.verdict_verfahren({"oll": _kz(None), "lin_oben": _kz(5)})
    assert art == "info" and "kein Vergleich" in text


def test_gewichte_mit_linearer_suche_nennt_klauselfaktor_und_konflikte():
    kz = {"oll": _kz(0), "lin_oben": _kz(456, klauseln=14502), "lin_unten": _kz(921, klauseln=14502), "oll_strat": _kz(1, aufrufe=9)}
    art, text = E.verdict_gewichte(kz, 658, 162)
    assert art == "success" and "OLL: 0 von 10 Instanzen am Budget abgebrochen" in text
    assert "14.502 Klauseln statt 658 ohne Gewichte (das 22-Fache)" in text and "Konflikte im Median 456 (von oben) und 921 (von unten)" in text
    assert "Mit Stratifizierung: Konflikte im Median 1 statt 0, SAT-Aufrufe im Median 9 statt 5" in text


def test_gewichte_ohne_lineare_suche_nennt_die_gerechnete_obergrenze_des_zaehlers():
    kz = {"oll": _kz(7472, abbrueche=2)}
    art, text = E.verdict_gewichte(kz, None, 1292, 123456)
    assert art == "warning" and "OLL: 2 von 10 Instanzen am Budget abgebrochen" in text and "Gewichtssumme 1.292 (Median)" in text and "bis zu 123.456 Klauseln" in text
    assert "nicht gemessen" in text


def test_minimierung_zaehlt_kleinere_kerne_und_mehr_konflikte():
    paare = [("a", _kz(10, kern=50), _kz(30, kern=30)), ("b", _kz(10, kern=8), _kz(20, kern=8)), ("c", _kz(100, kern=5), _kz(90, kern=2))]
    art, text = E.verdict_minimierung(paare)
    assert art == "warning" and "in 2 von 3 Zellen kleiner" in text and "steigen in 2 von 3 Zellen und sinken in 1" in text


def test_minimierung_ist_info_wenn_die_konflikte_nicht_ueberwiegend_steigen():
    paare = [("a", _kz(10, kern=5), _kz(10, kern=5)), ("b", _kz(10, kern=5), _kz(5, kern=4))]
    art, text = E.verdict_minimierung(paare)
    assert art == "info" and "in 1 von 2 Zellen kleiner" in text and "steigen in 0 von 2 Zellen und sinken in 1" in text


def test_kerne_von_hand_nennt_kerngroessen_beider_verfahren(hand):
    fm, oll = A.laufe(hand, "fu_malik", kern_wahl="klein"), A.laufe(hand, "oll", kern_wahl="klein")
    art, text = E.verdict_kerne_von_hand(fm, oll)
    assert art == "success" and "Fu–Malik: Kerne aus 2, 2, 4 Literalen" in text and "OLL: Kerne aus 2, 2, 3" in text and "unteren Schranke 3 = Optimum 3" in text
    assert "bei Fu–Malik 4 Literale, bei OLL 3" in text


def test_kerne_von_hand_gewichtet_hat_keinen_fu_malik(hand_gewichtet):
    art, text = E.verdict_kerne_von_hand(None, A.laufe(hand_gewichtet, "oll", kern_wahl="klein"))
    assert art == "info" and "Kerne aus 2, 2, 3, 3 Literalen" in text and "Optimum 4" in text and "nur ungewichtet" in text


def test_kerne_von_hand_gleiche_groessen_sind_info(hand):
    oll = A.laufe(hand, "oll", kern_wahl="klein")
    art, text = E.verdict_kerne_von_hand(oll, oll)
    assert art == "info" and "gleich" in text


def test_live_verdikt_meldet_widerspruch_als_fehler_und_abbruch_als_warnung(hand):
    a, b = A.laufe(hand, "oll"), A.laufe(hand, "lin_unten")
    assert E.verdict_live({"oll": a, "lin_unten": b}, 30000)[0] == "success"
    b.optimum = 4
    assert E.verdict_live({"oll": a, "lin_unten": b}, 30000)[0] == "error"
    c = A.laufe(hand, "oll", call_budget=0, total_budget=0)
    art, text = E.verdict_live({"oll": c}, 30000)
    assert art == "warning" and "Abbruch bei 30.000 Konflikten, untere Schranke 0" in text


def test_zahlenformat_deutsch():
    assert E.zahl(1234567) == "1.234.567" and E.zahl(2.5) == "2,5" and E.zahl(None) == "–" and E.zahl(0) == "0"
    assert E.faktor(22.4) == "22" and E.faktor(9.94) == "9,9"
