"""Randfälle der Verfahren (DEMO-PLAYBOOK §12): kein Kern, harte Klauseln unerfüllbar, eine weiche Klausel, Kern aus einem Literal, Gewicht 0, Gleichstand, Budget."""

import pytest

import mxs_algorithm as A
from mxs_scenario import MaxSat, formel, kontrollpunkte


def _inst(n, hart, weich, gewichte=None):
    return MaxSat(n, [tuple(c) for c in hart], [tuple(c) for c in weich], list(gewichte) if gewichte else [1] * len(weich), {"art": "test"})


ALLE = ("lin_oben", "lin_unten", "fu_malik", "oll", "oll_strat", "oll_min", "oll_strat_min")


@pytest.mark.parametrize("v", ALLE)
def test_keine_weiche_klausel_verletzt_optimum_null_ohne_kern(v):
    r = A.laufe(_inst(2, [(1, 2)], [(1,), (2,)]), v)
    assert r.optimum == 0 and r.kerne == [] and r.status == "ok" and r.kosten_modell == 0


@pytest.mark.parametrize("v", ALLE)
def test_harte_klauseln_unerfuellbar_ist_der_leere_kern(v):
    r = A.laufe(_inst(1, [(1,), (-1,)], [(1,)]), v)
    assert r.optimum is None and r.status == "hart unerfüllbar" and r.kerne == []


@pytest.mark.parametrize("v", ALLE)
def test_eine_einzige_weiche_klausel_die_nicht_gelten_kann(v):
    """hart (¬x1), weich (x1): Kern aus einem Literal, Kosten 1."""
    r = A.laufe(_inst(1, [(-1,)], [(1,)]), v)
    assert r.optimum == 1 and r.kosten_modell == 1


def test_kern_aus_einem_literal_wird_hart_verneint_und_hat_groesse_eins():
    r = A.laufe(_inst(2, [(-1,)], [(1,), (2,)]), "oll")
    assert r.kerngroessen == [1] and r.kerne[0].mitglieder == ["S1"] and r.kerne[0].neu is None and r.optimum == 1


def test_mehrere_kerne_aus_einem_literal_nacheinander():
    """Harte Einheiten ¬x1, ¬x2, ¬x3, weich x1, x2, x3: drei Kerne aus je einem Literal, Optimum 3, das Endmodell kostet 3."""
    inst = _inst(3, [(-1,), (-2,), (-3,)], [(1,), (2,), (3,)])
    for v in ("oll", "oll_min"):
        r = A.laufe(inst, v)
        assert r.optimum == 3 and r.kosten_modell == 3 and r.kerngroessen == [1, 1, 1], v


def test_gewicht_null_zaehlt_nie():
    inst = _inst(1, [(-1,)], [(1,)], [0])
    r = A.laufe(inst, "oll")
    assert r.optimum == 0 and r.kerne == []


def test_gleichstand_zwischen_kernen_nimmt_den_lexikographisch_ersten(hand):
    """Im Handbeispiel sind {S1,S2} und {S1,S3} gleich klein: bei kleinstem Kern gewinnt der lexikographisch erste."""
    assert A.laufe(hand, "oll", kern_wahl="klein").kerne[0].mitglieder == ["S1", "S2"]


def test_budget_gibt_abbruch_und_eine_untere_schranke_nie_eine_falsche_antwort():
    inst = kontrollpunkte(50, 3.0, 100)
    r = A.laufe(inst, "lin_oben", call_budget=5, total_budget=5)
    assert r.status == "Abbruch" and r.optimum is None
    opt = A.laufe(inst, "oll").optimum
    assert (r.obere is None or r.obere >= opt) and r.untere <= opt


def test_die_untere_schranke_wird_vom_budget_nicht_ueber_das_optimum_gehoben():
    inst = formel(30, 6, 100)
    ref = A.laufe(inst, "oll").optimum
    r = A.laufe(inst, "oll", call_budget=50, total_budget=50)
    assert r.status == "Abbruch" and r.untere <= ref


def test_ein_unbekanntes_verfahren_ist_ein_fehler(hand):
    with pytest.raises(ValueError):
        A.laufe(hand, "unbekannt")


def test_aufzaehlung_nur_bis_n_14():
    with pytest.raises(ValueError):
        A.aufzaehlung(kontrollpunkte(20, 3.0, 100))
