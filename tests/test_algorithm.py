"""Die Verfahren gegen die Handrechnung des Handbeispiels (Sollwerte aus `sat-cp-planung/handbeispiele/hb_15.py`, dort mit reinem Python und Aufzählung gerechnet)
und Einheiten: Zähler, Klauselzahlen, Instanzerzeuger (DEMO-PLAYBOOK §1b)."""

import pytest

import mxs_algorithm as A
import mxs_scenario as S


# --- Handbeispiel ------------------------------------------------------------------------------------------------------------------------

def test_optimum_und_optimale_belegungen_durch_aufzaehlung(hand):
    opt, arg = A.aufzaehlung(hand)
    assert opt == 3 and arg == [(0, 0, 0), (0, 0, 1), (0, 1, 0), (1, 0, 0)]


def test_die_sechs_minimalen_kerne(hand):
    """S1 = x1, …, S6 = ¬x3: {S1,S2}, {S1,S3}, {S2,S3} (zwei wahr geht nicht), {S1,S4}, {S2,S5}, {S3,S6} (x und ¬x)."""
    assert A.alle_minimalen_kerne(hand) == [[0, 1], [0, 2], [0, 3], [1, 2], [1, 4], [2, 5]]


def test_fu_malik_folge_am_handbeispiel(hand):
    r = A.laufe(hand, "fu_malik", kern_wahl="klein")
    assert [k.mitglieder for k in r.kerne] == [["S1", "S2"], ["S3", "S6"], ["S1'", "S2'", "S4", "S5"]]
    assert r.kerngroessen == [2, 2, 4] and [k.untere for k in r.kerne] == [1, 2, 3]
    assert r.optimum == 3 and r.kosten_modell == 3 and r.status == "ok"


def test_oll_folge_am_handbeispiel(hand):
    r = A.laufe(hand, "oll", kern_wahl="klein")
    assert [k.mitglieder for k in r.kerne] == [["S1", "S2"], ["S3", "S6"], ["S4", "S5", "Z0≥2"]]
    assert r.kerngroessen == [2, 2, 3] and [k.untere for k in r.kerne] == [1, 2, 3]
    assert r.optimum == 3 and r.kosten_modell == 3
    assert r.kerne[0].neu == "Z0≥2"


def test_gewichtetes_handbeispiel_optimum_und_oll_mit_gewichtsabzug(hand_gewichtet):
    opt, arg = A.aufzaehlung(hand_gewichtet)
    assert opt == 4 and arg == [(0, 0, 0), (0, 0, 1), (0, 1, 0)]
    r = A.laufe(hand_gewichtet, "oll", kern_wahl="klein")
    assert [k.mitglieder for k in r.kerne] == [["S1", "S2"], ["S1", "S3"], ["S4", "S5", "Z0≥2"], ["S4", "S6", "Z1≥2"]]
    assert [k.untere for k in r.kerne] == [1, 2, 3, 4] and [k.gewicht for k in r.kerne] == [1, 1, 1, 1]
    assert r.optimum == 4 and r.kosten_modell == 4


def test_gewichtssumme_des_unaeren_zaehlers_am_handbeispiel(hand_gewichtet):
    """Gewichte 2, 1, 1, 3, 1, 1: der unäre Zähler hat 9 Eingänge statt 6 (Handrechnung: 9 = 2 + 1 + 1 + 3 + 1 + 1)."""
    assert sum(hand_gewichtet.gewichte) == 9 and len(hand_gewichtet.weich) == 6
    assert A.lineare_suche(hand_gewichtet, "unten").optimum == 4


def test_fu_malik_verlangt_ungewichtete_instanz(hand_gewichtet):
    with pytest.raises(ValueError):
        A.fu_malik(hand_gewichtet)


def test_der_gefundene_kern_des_loesers_ist_unerfuellbar(hand):
    """Kern des Lösers statt kleinster Kern: die ersten Kerne bestehen aus weichen Klauseln und müssen mit den harten unerfüllbar sein (Aufzählung der Kerne aus der Handrechnung)."""
    minimal = [{f"S{i + 1}" for i in k} for k in A.alle_minimalen_kerne(hand)]
    for v in ("fu_malik", "oll"):
        r = A.laufe(hand, v, kern_wahl="loeser")
        erster = set(r.kerne[0].mitglieder)
        assert any(m <= erster for m in minimal), v           # enthält einen minimalen Kern
        assert r.optimum == 3


# --- Zähler -----------------------------------------------------------------------------------------------------------------------------

def test_zaehler_handrechnung_drei_eingaenge():
    """Totalizer über 3 Eingänge: Teilung 1 | 2. Rechter Knoten (2 Blätter): (1+1)(1+1)−1 = 3 Klauseln, 2 Ausgänge; Wurzel (1 und 2 Ausgänge): (1+1)(2+1)−1 = 5 Klauseln."""
    s = A.Sat(3, [])
    o = A.totalizer(s, [1, 2, 3], 3)
    assert len(o) == 3 and s.klauseln == 3 + 5 and s.hilfsvariablen == 2 + 3
    assert A.totalizer_klauselzahl(3, 3) == 8


@pytest.mark.parametrize("m,cap", [(1, 1), (2, 2), (5, 5), (9, 9), (12, 3), (20, 7), (30, 30)])
def test_klauselzahl_ohne_bauen_gleicht_dem_gebauten_zaehler(m, cap):
    s = A.Sat(m, [])
    A.totalizer(s, list(range(1, m + 1)), cap)
    assert s.klauseln == A.totalizer_klauselzahl(m, cap)


def test_zaehler_zaehlt_richtig():
    """Alle 2^6 Belegungen der Eingänge: unter ¬o_j ist die Formel genau dann erfüllbar, wenn weniger als j Eingänge wahr sind."""
    import itertools
    for bits in itertools.product((False, True), repeat=6):
        for j in range(1, 7):
            s = A.Sat(6, [])
            o = A.totalizer(s, list(range(1, 7)), 6)
            annahmen = [(i + 1) if b else -(i + 1) for i, b in enumerate(bits)] + [-o[j - 1]]
            assert (s.l.loese(annahmen, None).antwort is True) == (sum(bits) < j), (bits, j)


def test_unaere_klauselzahl_waechst_mit_der_gewichtssumme():
    assert A.unaere_klauselzahl([1] * 6) == A.totalizer_klauselzahl(6, 6)
    assert A.unaere_klauselzahl([2, 1, 1, 3, 1, 1]) == A.totalizer_klauselzahl(9, 9) > A.unaere_klauselzahl([1] * 6)


# --- Instanzerzeuger ---------------------------------------------------------------------------------------------------------------------

def test_instanzerzeuger_sind_deterministisch_und_haben_die_erwartete_groesse():
    k = S.kontrollpunkte(30, 3.0, 100)
    assert k == S.kontrollpunkte(30, 3.0, 100) and k != S.kontrollpunkte(30, 3.0, 101)
    assert len(k.hart) == 45 and len(k.weich) == 30 and k.n == 30            # 30 · 3 / 2 Kanten
    r = S.rampen(10, 4.0, 100)
    assert len(r.weich) == 20 and r.n == 30 + 20                              # 10 Aufträge × 3 Rampen + 20 Kantenvariablen
    assert len(r.hart) == 10 * (1 + 3) + 20 * 3
    f = S.formel(40, 6, 100)
    assert len(f.weich) == 240 and f.hart == [] and f.n == 40


def test_gewichte_sind_gleichverteilt_in_der_spanne_und_ein_zufalls_seed_bestimmt_sie():
    a = S.erzeuge("kontrollpunkte", 30, 100, 10)
    assert a.gewichte == S.erzeuge("kontrollpunkte", 30, 100, 10).gewichte and min(a.gewichte) >= 1 and max(a.gewichte) <= 10
    assert S.erzeuge("kontrollpunkte", 30, 100, 1).gewichte == [1] * 30
    assert S.erzeuge("kontrollpunkte", 30, 100, 5).gewichte != a.gewichte and max(S.erzeuge("kontrollpunkte", 30, 100, 5).gewichte) <= 5
    with pytest.raises(ValueError):
        S.erzeuge("unbekannt", 30, 100)


def test_kosten_und_hartpruefung_unabhaengig_vom_loeser(hand):
    modell = {1: False, 2: False, 3: True}
    assert S.hart_erfuellt(hand, modell) and S.kosten(hand, modell) == 3
    assert not S.hart_erfuellt(hand, {1: True, 2: True, 3: False})
