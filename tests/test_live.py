"""Live-Knöpfe: Zwischenspeicher und Fortschrittsanzeige (mxs_live.py). Der Zwischenspeicher ändert keine Zahl: gespeichert gleich ungespeichert (bitgleich),
ein anderer Parameter kommt nie aus dem Speicher, ein zweiter Aufruf mit denselben Parametern rechnet nicht noch einmal."""

import mxs_algorithm as A
import mxs_constants as C
import mxs_evaluation as E
import mxs_live as L
import mxs_scenario as S
from streamlit.testing.v1 import AppTest

ART, N, HI, BUDGET = "kontrollpunkte", 20, 1, 5000
VERF = ("lin_oben", "oll")


def _zaehler(monkeypatch):
    aufrufe = []
    echt = A.laufe

    def zaehlend(inst, verfahren, **kwargs):
        aufrufe.append(verfahren)
        return echt(inst, verfahren, **kwargs)

    monkeypatch.setattr(A, "laufe", zaehlend)
    return aufrufe


def test_lauf_gespeichert_gleich_ungespeichert_und_gleich_live_messung():
    L.lauf.clear()
    ref = E.live_messung(S.erzeuge(ART, N, 100, HI), VERF, BUDGET)
    for v in VERF:
        roh = E.live_lauf(ART, N, 100, HI, v, BUDGET)
        assert roh == ref[v]
        assert L.lauf(ART, N, 100, HI, v, BUDGET) == roh
        assert L.lauf(ART, N, 100, HI, v, BUDGET) == roh


def test_lauf_zweiter_aufruf_rechnet_nicht_anderer_parameter_schon(monkeypatch):
    L.lauf.clear()
    aufrufe = _zaehler(monkeypatch)
    L.lauf(ART, N, 100, HI, "oll", BUDGET)
    L.lauf(ART, N, 100, HI, "oll", BUDGET)
    assert len(aufrufe) == 1
    a = L.lauf(ART, N, 101, HI, "oll", BUDGET)            # anderer Zufalls-Seed
    b = L.lauf(ART, N, 100, HI, "lin_oben", BUDGET)       # anderes Verfahren
    c = L.lauf(ART, N + 5, 100, HI, "oll", BUDGET)        # andere Größe
    d = L.lauf(ART, N, 100, 10, "oll", BUDGET)            # andere Gewichte
    assert len(aufrufe) == 5
    assert a == E.live_lauf(ART, N, 101, HI, "oll", BUDGET) and b == E.live_lauf(ART, N, 100, HI, "lin_oben", BUDGET)
    assert c == E.live_lauf(ART, N + 5, 100, HI, "oll", BUDGET) and d == E.live_lauf(ART, N, 100, 10, "oll", BUDGET)


def _alte_serie(art, n, hi, verfahren, budget, seeds):
    """Die Messreihe so, wie sie vor dem Zwischenspeicher gerechnet wurde (unabhängige Abschrift der früheren Fassung)."""
    z = {"art": art, "n": n, "gewichtet": hi > 1, "instanzen": []}
    for s in seeds:
        inst = S.erzeuge(art, n, s, hi)
        z["instanzen"].append({"seed": s, "weich": len(inst.weich), "gewichtssumme": sum(inst.gewichte), "laeufe": {
            v: {"optimum": l.optimum, "status": l.status, "aufrufe": l.aufrufe, "konflikte": l.konflikte, "untere": l.untere, "kerne": l.kerngroessen,
                "kerne_vor": [k.vor_minimierung for k in l.kerne], "klauseln": l.klauseln, "hilfsvariablen": l.hilfsvariablen, "kosten_modell": l.kosten_modell}
            for v, l in E.live_messung(inst, verfahren, budget).items()}})
    return z


def test_serie_aus_einheiten_bitgleich_zur_alten_serie():
    L.lauf.clear()
    seeds = C.SEEDS[:3]
    alt = _alte_serie(ART, N, HI, VERF, BUDGET, seeds)
    assert E.live_serie(ART, N, HI, VERF, BUDGET, seeds) == alt
    assert E.live_serie_aufbauen(ART, N, HI, VERF, BUDGET, L.lauf, seeds) == alt
    assert E.live_serie_aufbauen(ART, N, HI, VERF, BUDGET, L.lauf, seeds) == alt      # zweiter Durchlauf aus dem Speicher


def test_fortschrittsanzeige_liefert_ergebnisse_in_reihenfolge_und_ohne_fehler():
    def skript():
        import streamlit as st
        import mxs_live as L

        erg = L.mit_fortschritt("Probe", [("eins", (1,)), ("zwei", (2,)), ("drei", (3,))], lambda x: x * 10)
        st.write(f"ergebnis {erg}")

    at = AppTest.from_function(skript)
    at.run(timeout=60)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("ergebnis [10, 20, 30]" in m.value for m in at.markdown)
