"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Button, fährt jeden Regler an seine Grenzen
und prüft, dass kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere st.plotly_chart-Aufrufe ohne eindeutiges key= können zufällig
identischen Inhalt rendern und kollidieren) und `StreamlitAPIException` bei Reglern mit berechneten Grenzen (min == max).

Die Live-Knöpfe rechnen in der Voreinstellung (Kontrollpunkte n = 20) in unter einer Sekunde; die schweren Zellen (Formel n = 40) rechnet kein Test live."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import mxs_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "▶"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    start = _fresh_app()
    labels = [b.label for b in start.button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label or start.button[index].disabled:      # gesperrte Knöpfe kann kein Nutzer drücken (live3_go bei ungewichteter Instanz)
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("familie", C.FAMILIEN)
def test_jede_familie_mit_jeder_groesse_und_jeder_gewichtsspanne_laedt_ohne_fehler(familie):
    at = _fresh_app()
    at.sidebar.selectbox(key="familie").set_value(familie).run(timeout=TIMEOUT)
    assert not at.exception
    paare = [(n, hi) for n in C.N_OPTIONEN for hi in (1, 10)] + [(C.N_OPTIONEN[0], 5), (C.N_OPTIONEN[-1], 5)]
    for n, hi in paare:
        at.sidebar.select_slider(key="n").set_value(n)
        at.sidebar.select_slider(key="gewicht_hi").set_value(hi)
        at.run(timeout=TIMEOUT)
        assert not at.exception, (familie, n, hi, [str(e) for e in at.exception])


def test_live_knopf_rechnet_die_voreinstellung_und_zeigt_optimum_und_tabelle():
    at = _fresh_app()
    at.button(key="live_go").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    texte = " ".join(e.value for e in list(at.success) + list(at.warning) + list(at.error))
    assert "OLL: Optimum" in texte and "Lineare Suche von oben: Optimum" in texte and "Fu–Malik (einfach): Optimum" in texte
    assert not at.error


def test_live_knopf_ist_bei_zu_grossen_instanzen_gesperrt():
    at = _fresh_app()
    at.sidebar.selectbox(key="familie").set_value("Formel").run(timeout=TIMEOUT)
    at.sidebar.select_slider(key="n").set_value(60).run(timeout=TIMEOUT)
    assert at.button(key="live_go").disabled and at.button(key="live_serie_go").disabled and at.button(key="live4_go").disabled


def test_ohne_vorgerechnete_zelle_steht_ein_hinweis_statt_eines_fehlers():
    at = _fresh_app()
    at.sidebar.select_slider(key="n").set_value(60).run(timeout=TIMEOUT)          # Kontrollpunkte n = 60: keine Messreihe
    assert any("keine Messreihe vorgerechnet" in i.value for i in at.info)


def test_alle_vier_experimente_und_die_grenzen_stehen_auf_der_seite():
    at = _fresh_app()
    ueberschriften = " ".join(m.value for m in at.markdown if m.value.startswith("## "))
    for t in ("Experiment 1", "Experiment 2", "Experiment 3", "Experiment 4"):
        assert t in ueberschriften
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any(e.label == "📐 Mathematische Formulierung" for e in at.expander)


def test_gewichtete_live_knoepfe_stratifizierung_und_minimierung_rechnen():
    at = _fresh_app()
    at.sidebar.select_slider(key="gewicht_hi").set_value(10).run(timeout=TIMEOUT)
    at.button(key="live3_go").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("OLL + Stratifizierung: Optimum" in e.value for e in list(at.success) + list(at.warning))
    at.button(key="live4_go").click().run(timeout=TIMEOUT)
    assert not at.exception and any("OLL + Stratifizierung + Kernminimierung: Optimum" in e.value for e in list(at.success) + list(at.warning))
    at.button(key="live_serie_go").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
