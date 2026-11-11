"""Zweig-Tests (DEMO-PLAYBOOK §0): jedes Verfahren weicht auf mindestens einer Instanz vom Nachbarverfahren ab, keine Spalte mit lauter gleichen Werten.

Eine Variante, die nie ausgeführt wird (toter Zweig), zeigt sich hier als „immer gleich“."""

import mxs_algorithm as A
import mxs_scenario as S


def test_fu_malik_gegen_oll_kerngroesse_am_handbeispiel(hand):
    fm, oll = A.laufe(hand, "fu_malik", kern_wahl="klein"), A.laufe(hand, "oll", kern_wahl="klein")
    assert fm.kerngroessen == [2, 2, 4] and oll.kerngroessen == [2, 2, 3]


def test_fu_malik_gegen_oll_konflikte_auf_rampen():
    """Auf Rampen (n = 30, Grad 5) braucht Fu–Malik nicht dieselben Konflikte und Klauseln wie OLL: auf mindestens einer der drei Instanzen verschieden."""
    unterschiede = 0
    for seed in (100, 101, 102):
        inst = S.rampen(30, 5.0, seed)
        fm, oll = A.laufe(inst, "fu_malik"), A.laufe(inst, "oll")
        assert fm.optimum == oll.optimum
        unterschiede += (fm.konflikte, fm.klauseln) != (oll.konflikte, oll.klauseln)
    assert unterschiede >= 1


def test_mit_und_ohne_stratifizierung_unterscheiden_sich_in_den_sat_aufrufen():
    unterschiede = [A.laufe(i, "oll").aufrufe != A.laufe(i, "oll_strat").aufrufe for i in (S.erzeuge("rampen", 30, s, 10) for s in (100, 101, 102))]
    assert any(unterschiede)


def test_ungewichtet_ist_stratifizierung_wirkungslos_weil_es_nur_eine_schicht_gibt():
    inst = S.rampen(30, 5.0, 100)
    a, b = A.laufe(inst, "oll"), A.laufe(inst, "oll_strat")
    assert (a.konflikte, a.aufrufe, a.kerngroessen) == (b.konflikte, b.aufrufe, b.kerngroessen)


def test_kernminimierung_verkleinert_kerne_und_zaehlt_mehr_sat_aufrufe():
    inst = S.rampen(30, 5.0, 100)
    a, b = A.laufe(inst, "oll"), A.laufe(inst, "oll_min")
    assert a.optimum == b.optimum
    assert b.aufrufe > a.aufrufe                                                    # die Minimierungsaufrufe zählen mit
    assert sum(k.groesse for k in b.kerne) < sum(k.vor_minimierung for k in b.kerne)  # mindestens ein Kern wurde kleiner
    assert all(k.groesse == k.vor_minimierung for k in a.kerne)


def test_lineare_suche_oben_und_unten_fragen_verschieden_oft():
    inst = S.kontrollpunkte(30, 3.0, 100)
    oben, unten = A.laufe(inst, "lin_oben"), A.laufe(inst, "lin_unten")
    assert oben.optimum == unten.optimum and oben.aufrufe != unten.aufrufe


def test_kernverfahren_gegen_lineare_suche_bei_zwei_literal_kernen():
    """Kontrollpunkte: Kerne aus zwei Literalen, die Kernverfahren brauchen weniger Konflikte als die lineare Suche (Zählung über drei Instanzen)."""
    weniger = 0
    for seed in (100, 101, 102):
        inst = S.kontrollpunkte(40, 3.0, seed)
        assert set(A.laufe(inst, "oll").kerngroessen[:3]) == {2}
        weniger += A.laufe(inst, "oll").konflikte < min(A.laufe(inst, "lin_oben").konflikte, A.laufe(inst, "lin_unten").konflikte)
    assert weniger == 3
