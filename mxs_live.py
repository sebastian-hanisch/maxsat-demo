"""Live-Knöpfe: Zwischenspeicher und Fortschrittsanzeige.

Jede lange Aktion (eine Instanz mit mehreren Verfahren, eine Messreihe über zehn Instanzen) besteht aus Einheiten (ein Verfahren auf einer Instanz). Jede Einheit ist eine
reine Funktion ihrer Parameter (die Instanzen sind deterministisch, SplitMix64) und liegt einzeln im Zwischenspeicher (`st.cache_data`, kleine `max_entries`); die Anzeige zählt
die fertigen Einheiten (`mit_fortschritt`). Ein zweiter Klick mit denselben Einstellungen antwortet aus dem Speicher, und die Läufe einer Instanz, die eine Messreihe
schon gerechnet hat, rechnet die Einzelinstanz nicht noch einmal. Die Ergebnisse sind bitgleich zu den ungespeicherten Funktionen (`tests/test_live.py`).
Rechnung, Zahlen und Aussagen ändern sich nicht."""

import streamlit as st

import mxs_constants as C
import mxs_evaluation as E


@st.cache_data(show_spinner=False, max_entries=80)
def lauf(art, n, seed, hi, verfahren, budget):
    return E.live_lauf(art, n, seed, hi, verfahren, budget)


def mit_fortschritt(titel: str, schritte: list, rechne) -> list:
    """Führt die Schritte nacheinander aus und zeigt, wie viele fertig sind. `schritte`: Liste aus (Beschriftung, Argumente); `rechne(*Argumente)` liefert das Ergebnis
    (aus dem Zwischenspeicher oder frisch gerechnet). Rückgabe: die Ergebnisse in der Reihenfolge der Schritte."""
    n = len(schritte)
    ergebnisse = []
    with st.status(titel, expanded=True) as status:
        balken = st.progress(0.0, text=f"0 von {n} fertig")
        for i, (beschriftung, args) in enumerate(schritte):
            balken.progress(i / n, text=f"{beschriftung} (Schritt {i + 1} von {n})")
            ergebnisse.append(rechne(*args))
        balken.progress(1.0, text=f"{n} von {n} fertig")
        status.update(label=f"{titel}: fertig", state="complete", expanded=False)
    return ergebnisse


def instanz(art, n, seed, hi, verfahren, budget) -> dict:
    """Die gewählten Verfahren auf einer Instanz, mit Fortschrittsanzeige (je Verfahren ein Schritt). Wie `E.live_messung`, mit Zwischenspeicher."""
    verfahren = tuple(verfahren)
    schritte = [(C.VERFAHREN_LABEL[v], (art, n, seed, hi, v, budget)) for v in verfahren]
    return dict(zip(verfahren, mit_fortschritt("Die Instanz wird gelöst", schritte, lauf)))


def serie(art, n, hi, verfahren, budget) -> dict:
    """Die Messreihe über die zehn festen Instanzen, mit Fortschrittsanzeige (je Instanz und Verfahren ein Schritt). Wie `E.live_serie`, mit Zwischenspeicher."""
    verfahren = tuple(verfahren)
    schritte = [(f"Instanz {i + 1} von {len(C.SEEDS)}, {C.VERFAHREN_LABEL[v]}", (art, n, s, hi, v, budget)) for i, s in enumerate(C.SEEDS) for v in verfahren]
    ergebnisse = mit_fortschritt("Die Messreihe läuft", schritte, lauf)
    je_schritt = {(s, v): l for (s, v), l in zip(((s, v) for s in C.SEEDS for v in verfahren), ergebnisse)}
    return E.live_serie_aufbauen(art, n, hi, verfahren, budget, lambda a, n_, s, h, v, b: je_schritt[(s, v)])


def instanz_aus_speicher(art, n, seed, hi, verfahren, budget) -> dict:
    """Wie `instanz`, ohne Anzeige (aus dem Zwischenspeicher; rechnet nur, was dort fehlt)."""
    return {v: lauf(art, n, seed, hi, v, budget) for v in verfahren}


def serie_aus_speicher(art, n, hi, verfahren, budget) -> dict:
    """Wie `serie`, ohne Anzeige."""
    return E.live_serie_aufbauen(art, n, hi, tuple(verfahren), budget, lauf)
