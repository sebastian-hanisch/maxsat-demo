"""MaxSAT - die Kerngröße geht mit den Unterschieden einher - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Statt „Ist die Formel erfüllbar?“ fragt MaxSAT: „Wie viele weiche Klauseln müssen fallen?“ Ein Kernverfahren sucht Kerne (kleine Mengen weicher Klauseln, die zusammen
nicht erfüllbar sind); jeder Kern hebt die untere Schranke. Die Demo zeigt das von Hand, vergleicht lineare Suche, Fu-Malik und OLL in Konflikten (nie in Sekunden),
zeigt, was Gewichte kosten, und die Kernminimierung als Negativbefund. Die großen Messreihen und der CP-SAT-Maßstab sind vorgerechnet (nicht live).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import mxs_algorithm as A
import mxs_constants as C
import mxs_evaluation as E
import mxs_live as L
import mxs_scenario as S
import mxs_visualization as V
from mxs_layout import dunkles_design, kopf_css
from mxs_presets import (
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="MaxSAT – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _hand(gewichte, kern_wahl):
    inst = S.handbeispiel(list(gewichte))
    fm = A.laufe(inst, "fu_malik", kern_wahl=kern_wahl) if all(g == 1 for g in gewichte) else None
    return {"inst": inst, "aufzaehlung": A.aufzaehlung(inst), "kerne": A.alle_minimalen_kerne(inst), "fm": fm, "oll": A.laufe(inst, "oll", kern_wahl=kern_wahl)}


@st.cache_data(show_spinner=False)
def _instanz(art, n, seed, hi):
    return S.erzeuge(art, n, seed, hi)


def _sec(n):
    return f"{n:,}".replace(",", ".")


# --- Kopf, Einleitung ----------------------------------------------------------------------------------------------------------------------

st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧮 MaxSAT – die Kerngröße geht mit den Unterschieden einher")
st.markdown(
    """
Bisher fragte der Löser: „Ist die Formel **erfüllbar**?“ MaxSAT fragt: „**Wie viele weiche Klauseln müssen fallen?**“ Harte Klauseln müssen gelten, weiche dürfen verletzt werden,
jede verletzte kostet ihr Gewicht. Ein **Kernverfahren** ruft den Löser unter Annahmen („diese weichen Klauseln gelten“) und bekommt bei „unerfüllbar“ einen **Kern**: eine kleine
Menge weicher Klauseln, die zusammen nicht erfüllbar sind. Mindestens eine davon fällt, die **untere Schranke** steigt. Beobachtet wird: Bei kleinen **Kernen** liegen die Verfahren weit auseinander, bei großen nicht; ob die **Kerngröße** die Ursache ist, ist nicht getrennt untersucht
(Aufwand in **Konflikten** und SAT-Aufrufen, nie in Sekunden). Die Instanzen sind Aufträge mit Unverträglichkeiten: Kontrollpunkte, Rampen und eine überbestimmte Formel.

Weiter unten: vier Experimente (**Kerne von Hand**, **Verfahren im Vergleich**, **Gewichte**, **Kernminimierung**), **🚧 Wo die Annahmen enden** und der Expander
**📐 Mathematische Formulierung**. Messreihen und der CP-SAT-Vergleich sind als „vorgerechnet, nicht live“ gekennzeichnet.
"""
)

with st.expander("So funktioniert ein Kernverfahren", expanded=True):
    st.markdown(
        """
1. **Annahmen.** Jede weiche Klausel bekommt ein Annahmeliteral („diese Klausel gilt“). Der Löser sucht eine Belegung, die alle harten Klauseln und alle Annahmen erfüllt.
2. **Kern.** Gibt es keine, nennt der Löser eine Teilmenge der Annahmen, die schon genügt, um den Widerspruch zu erklären: den Kern. Die untere Schranke steigt um das kleinste Gewicht im Kern.
3. **Fu–Malik (einfache Fassung).** Jede Annahme im Kern bekommt eine neue Relaxationsvariable, von denen höchstens eine wahr sein darf (paarweise). Danach wird wieder gefragt.
4. **OLL (einfache Fassung).** Statt paarweise zu begrenzen, zählt ein Zähler (Totalizer) die verletzten Kernmitglieder; neue Annahme: „höchstens eine verletzt“. Kommt ein Zählerausgang später selbst in einen Kern, rückt der nächste nach.
5. **Lineare Suche** (zum Vergleich) kennt keine Kerne: ein Zähler über alle Relaxationsvariablen, die Schranke wandert von oben nach unten oder von unten nach oben, je Schritt ein SAT-Aufruf.
6. **Gewichte, Stratifizierung, Kernminimierung.** Bei Gewichten zieht OLL das kleinste Gewicht im Kern ab; die lineare Suche braucht einen Zähler mit so vielen Eingängen wie die Gewichtssumme.
   Stratifizierung nimmt zuerst die schweren Annahmen; Kernminimierung versucht, den Kern zu verkleinern. Alle Verfahren sind einfache Fassungen nach Gedächtnis, nicht gegen die Literatur geprüft.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz (Experimente 2 bis 4)**")
    familie = st.selectbox("Familie", C.FAMILIEN, key="familie", help="Kontrollpunkte: Kerne aus zwei Literalen. Rampen: große Kerne. Formel: sehr große Kerne.")
    st.caption(C.FAMILIE_BESCHREIBUNG[familie])
    n = int(st.select_slider("Größe n (Aufträge bzw. Variablen)", C.N_OPTIONEN, key="n",
                             help="Live gerechnet werden Kontrollpunkte bis n = 50, Rampen bis n = 60, die Formel bis n = 40; darüber steht nur die vorgerechnete Messreihe (soweit vorhanden)."))
    hi = int(st.select_slider("Gewichte 1 bis …", C.GEWICHT_OPTIONEN, key="gewicht_hi", format_func=lambda g: "ungewichtet" if g == 1 else f"1 bis {g}",
                              help="Gleichverteilte ganze Gewichte je weiche Klausel; ungewichtet zählt jede verletzte Klausel 1. Die vorgerechneten gewichteten Messreihen gelten für 1 bis 10."))
    st.number_input("Zufalls-Seed", 0, C.SEED_MAX, step=1, key="seed",
                    help="Bestimmt die Instanz (SplitMix64, auf jeder Plattform gleich). Die vorgerechneten Messreihen nutzen die Zufalls-Seeds 100 bis 109.")
    st.button("🎲 Neuer Zufalls-Seed", on_click=randomize_seed, width="stretch")
    st.markdown("**Löser**")
    budget = int(st.select_slider("Konfliktbudget je Verfahren", C.BUDGET_OPTIONEN, key="budget", format_func=E.zahl,
                                  help="Höchstens so viele Konflikte je Verfahren und Instanz (je SAT-Aufruf höchstens 10.000). Ein Lauf am Budget gibt keine Antwort, nur eine untere Schranke, "
                                       "und zählt mit dem Budget. Die vorgerechneten Messreihen stehen auf 30.000."))

seed = int(st.session_state["seed"])
art = C.FAMILIE_ART[familie]
inst = _instanz(art, n, seed, hi)
live_max = C.LIVE_N_MAX[art]
zu_gross = n > live_max

# --- Experiment 1: Kerne von Hand -------------------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Experiment 1: Kerne von Hand")
st.caption("Drei Variablen x1, x2, x3; hart: höchstens eine ist wahr. Weich (Gewicht 1): S1 = x1, S2 = x2, S3 = x3, S4 = ¬x1, S5 = ¬x2, S6 = ¬x3. "
           "Wie viele weiche Klauseln müssen mindestens fallen, und welche Kerne findet das Verfahren auf dem Weg?")
c1, c2, c3 = st.columns([1, 1, 2])
gew_label = c1.radio("Gewichte der weichen Klauseln", C.E1_GEWICHT_OPTIONEN, key="e1_gewichte", help="Mit Gewichten zeigt OLL den Gewichtsabzug: eine Annahme behält ihr Restgewicht. Fu–Malik gibt es hier nur ungewichtet.")
kern_wahl_label = c2.radio("Welcher Kern", C.E1_KERN_OPTIONEN, key="e1_kern",
                           help="Kleinster Kern: unter allen unerfüllbaren Teilmengen die kleinste, bei Gleichstand die erste (Aufzählung, nur für diese kleine Instanz). Kern des Lösers: die Annahmen, die der Löser im Schlusskonflikt nennt.")
schritt = int(c3.slider("Kerne anzeigen (bis Kern Nr.)", *C.E1_SCHRITT, key="e1_schritt", help="0: noch kein Kern; 6 zeigt alle gefundenen Kerne."))
gewichte = C.E1_GEWICHTE if gew_label != C.E1_GEWICHT_OPTIONEN[0] else (1,) * 6
kern_wahl = "klein" if kern_wahl_label == C.E1_KERN_OPTIONEN[0] else "loeser"
h = _hand(gewichte, kern_wahl)
hi_inst = h["inst"]
opt_h, arg_h = h["aufzaehlung"]

st.dataframe(pd.DataFrame([{"Klausel": f"S{i + 1}", "Inhalt": E.klausel_text(c), "Gewicht": str(g)} for i, (c, g) in enumerate(zip(hi_inst.weich, hi_inst.gewichte))]
                          + [{"Klausel": "hart", "Inhalt": "höchstens eine der Variablen x1, x2, x3 ist wahr: " + ", ".join(f"({E.klausel_text(c)})" for c in hi_inst.hart), "Gewicht": "–"}]),
             hide_index=True, width="stretch")
kerne_namen = ["{" + ", ".join(f"S{i + 1}" for i in k) + "}" for k in h["kerne"]]
st.markdown(f"**Optimum {opt_h}** (Aufzählung aller 8 Belegungen) bei {len(arg_h)} optimalen Belegungen ({', '.join(''.join(str(b) for b in a) for a in arg_h)} für x1 x2 x3). "
            f"**Minimale Kerne** (mit den harten Klauseln unerfüllbar, jede echte Teilmenge erfüllbar), {len(kerne_namen)} Stück: {', '.join(kerne_namen)}.")

kd = st.columns(2) if h["fm"] is not None else [st.container()]
verfahren_hand = ([("Fu–Malik", h["fm"])] if h["fm"] is not None else []) + [("OLL", h["oll"])]
for spalte, (name, lauf) in zip(kd, verfahren_hand):
    with spalte:
        st.markdown(f"**{name}**")
        gezeigt = lauf.kerne[:schritt]
        if not gezeigt:
            st.info("Noch kein Kern gezeigt: die untere Schranke ist 0.")
        else:
            st.dataframe(pd.DataFrame([{"Kern": k.nr, "Mitglieder": "{" + ", ".join(k.mitglieder) + "}", "Literale": k.groesse, "Mindestgewicht": k.gewicht, "untere Schranke": k.untere}
                                       for k in gezeigt]), hide_index=True, width="stretch")
            st.plotly_chart(V.build_kernmatrix(gezeigt, f"{name}: Kerne"), width="stretch", key=f"matrix_{name}")
            st.caption(E.kern_satz(gezeigt[-1]))
            erkl = [t for t in (E.zaehler_erklaerung(m) for k in gezeigt for m in k.mitglieder) if t]
            if erkl:
                st.caption(" ".join(dict.fromkeys(erkl)))
kind, text = E.verdict_kerne_von_hand(h["fm"], h["oll"])
getattr(st, kind)(text)
if gew_label != C.E1_GEWICHT_OPTIONEN[0]:
    st.caption(f"Die unäre Kodierung der linearen Suche bräuchte hier {sum(gewichte)} Eingänge (die Gewichtssumme) statt {len(gewichte)}.")

st.markdown("---")

# --- Experiment 2: Verfahren im Vergleich ----------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Experiment 2: Verfahren im Vergleich")
st.markdown(f"**Instanz der Seitenleiste:** {S.beschreibung(inst)}"
            + ("" if hi == 1 else f"; Gewichte 1 bis {hi} (Gewichtssumme {sum(inst.gewichte)})") + f". Die Instanz hat {len(inst.hart)} harte und {len(inst.weich)} weiche Klauseln.")
gew_reihe = hi == 10
z = E.zelle(art, n, gew_reihe) if hi in (1, 10) else None
cps = E.cpsat_zelle(art, n, gew_reihe)
if not E.lade_messungen().get("zellen"):
    st.warning("Die vorgerechneten Messreihen (mxs_messungen.json) fehlen; nur die Live-Läufe stehen zur Verfügung.")
elif z is None:
    st.info("Für diese Einstellung ist keine Messreihe vorgerechnet (vorgerechnet sind ungewichtet Kontrollpunkte n = 20, 30, 50, Rampen n = 40, 60, 90 und die Formel n = 40; "
            "gewichtet 1 bis 10 Kontrollpunkte n = 20, 30, 50, Rampen n = 40, 60 und die Formel n = 40). Live rechnen können Sie darunter.")
else:
    ref = E.referenzoptima(z, cps)
    kz = E.alle_kennzahlen(z, ref)
    st.caption(f"Vorgerechnet, nicht live (Messskripte tools/messungen.py und tools/cpsat_messung.py, Dateien mxs_messungen.json und mxs_cpsat.json): zehn feste Instanzen "
               f"(Zufalls-Seeds 100 bis 109), Budget {_sec(C.BUDGET_REFERENZ)} Konflikte je Verfahren und Instanz, je SAT-Aufruf {_sec(C.CALL_BUDGET_MAX)}; Python-CDCL mit Aktivität, "
               "Phasenspeicher und Luby-Neustarts. CP-SAT: ein Arbeiter, 15 Sekunden Zeitlimit, Konflikte der Löser-Statistik.")
    if "oll" in kz and "lin_oben" in kz:
        kind, text = E.verdict_verfahren(kz)
        getattr(st, kind)(text)
    roh = {v: E.konflikte_je_instanz(z, v, cps) for v in list(kz) + ([C.CPSAT] if cps else [])}
    st.plotly_chart(V.build_streifen(roh, C.BUDGET_REFERENZ, f"Konflikte je Instanz: {familie}, n = {n}" + (", Gewichte 1 bis 10" if gew_reihe else "")), width="stretch", key="streifen_ref")
    st.dataframe(pd.DataFrame(E.tabellenzeilen(z, cps)), hide_index=True, width="stretch")
    st.caption("Ein Lauf am Budget zählt mit dem Budget und ist nur eine untere Schranke. Kerngröße: Literale im Kern, Mediane der Mediane. "
               "falsche Antworten: beendete Läufe, deren Optimum vom Referenzoptimum (CP-SAT, soweit bewiesen, sonst der gemeinsame Wert der beendeten Läufe) abweicht.")

with st.expander("🔁 Live rechnen (eine Instanz oder zehn)", expanded=False):
    gewaehlt = st.multiselect("Verfahren", [v for v in C.VERFAHREN if not (v == "fu_malik" and hi > 1)], default=[v for v in C.HAUPT_VERFAHREN if not (v == "fu_malik" and hi > 1)],
                              format_func=lambda v: C.VERFAHREN_LABEL[v], key="e2_verfahren", help="Fu–Malik gibt es hier nur ungewichtet.")
    if zu_gross:
        st.info(f"Live gerechnet wird in dieser Familie nur bis n = {live_max}; bei n = {n} bleibt die vorgerechnete Messreihe (soweit vorhanden).")
    if art == "formel":
        st.caption("Die Formel ist die schwerste Familie: je nach Verfahren dauert ein Lauf deutlich länger als bei den Kontrollpunkten.")
    signatur = (art, n, seed, hi, tuple(gewaehlt), budget)
    b1, b2 = st.columns(2)
    if b1.button("Diese Instanz live lösen", key="live_go", disabled=zu_gross or not gewaehlt,
                 help="Die gewählten Verfahren auf der Instanz der Seitenleiste; ein Fortschrittsbalken zählt die fertigen Verfahren, ein zweiter Klick mit denselben Einstellungen antwortet aus dem Zwischenspeicher."):
        st.session_state["live_e2"] = {"sig": signatur, "laeufe": L.instanz(art, n, seed, hi, tuple(gewaehlt), budget)}
    g = st.session_state.get("live_e2")
    if g and g["sig"] == signatur:
        laeufe = g["laeufe"]
        kind, text = E.verdict_live(laeufe, budget)
        getattr(st, kind)(text)
        st.dataframe(pd.DataFrame([{"Verfahren": C.VERFAHREN_LABEL[v], "Optimum": str(l.optimum) if l.status == "ok" else "–", "Status": l.status, "Konflikte": l.konflikte,
                                    "SAT-Aufrufe": l.aufrufe, "Kerne": len(l.kerne), "Kerngrößen (erste 8)": ", ".join(str(x) for x in l.kerngroessen[:8]) or "–",
                                    "Klauseln": l.klauseln, "untere Schranke": l.untere} for v, l in laeufe.items()]), hide_index=True, width="stretch")
        st.plotly_chart(V.build_zeitleiste(laeufe, "Schranken nach jedem SAT-Aufruf"), width="stretch", key="zeitleiste_live")
    elif g:
        st.caption("Die Einstellungen haben sich geändert: erneut starten.")
    signatur_serie = (art, n, hi, tuple(gewaehlt), budget)
    if b2.button("Messreihe live starten (10 Instanzen)", key="live_serie_go", disabled=zu_gross or not gewaehlt,
                 help="Zehn feste Instanzen (Zufalls-Seeds 100 bis 109) mit den gewählten Verfahren; ein Fortschrittsbalken zählt die fertigen Läufe, ein zweiter Klick mit denselben Einstellungen antwortet aus dem Zwischenspeicher."):
        st.session_state["live_serie"] = {"sig": signatur_serie, "zelle": L.serie(art, n, hi, tuple(gewaehlt), budget)}
    gs = st.session_state.get("live_serie")
    if gs and gs["sig"] == signatur_serie:
        zl = gs["zelle"]
        kzl = E.alle_kennzahlen(zl, None, budget)
        if "oll" in kzl and "lin_oben" in kzl and "lin_unten" in kzl:
            kind, text = E.verdict_verfahren(kzl)
            getattr(st, kind)(text)
        st.dataframe(pd.DataFrame(E.tabellenzeilen(zl, None, budget)), hide_index=True, width="stretch")
        st.caption(f"Live gemessen, nicht vorgerechnet: Budget {_sec(budget)} Konflikte; ohne Referenzoptimum werden die Antworten nicht geprüft.")
    elif gs:
        st.caption("Die Einstellungen haben sich geändert: Messreihe erneut starten.")

st.markdown("---")

# --- Experiment 3: Gewichte ---------------------------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Experiment 3: Was kosten Gewichte?")
st.markdown("Die lineare Suche braucht einen Zähler, der Gewichte als Wiederholung kodiert (**unär**): eine Relaxationsvariable mit Gewicht 7 geht siebenmal in den Zähler. "
            "OLL zieht stattdessen das kleinste Gewicht im Kern ab und baut Zähler nur über Kerne. Die Klauselzahl des unären Zählers wird hier gerechnet, ohne ihn zu lösen.")
zeilen = []
balken = {}
for spanne in C.GEWICHT_OPTIONEN:
    ii = _instanz(art, n, seed, spanne)
    summe = sum(ii.gewichte)
    kl = A.totalizer_klauselzahl(summe, summe)
    zeilen.append({"Gewichte": "ungewichtet" if spanne == 1 else f"1 bis {spanne}", "weiche Klauseln": len(ii.weich), "Gewichtssumme (Eingänge des unären Zählers)": summe,
                   "Klauseln des unären Zählers (Obergrenze)": kl})
    balken[f"unär, Gewichte {'aus' if spanne == 1 else f'1 bis {spanne}'}"] = max(kl, 1)
st.caption(f"Instanz der Seitenleiste ({S.beschreibung(inst)}). Obergrenze: der Zähler der Messreihen ist auf die Kosten der ersten gefundenen Lösung gedeckelt und deshalb etwas kleiner.")
st.dataframe(pd.DataFrame(zeilen), hide_index=True, width="stretch",
             column_config={k: st.column_config.NumberColumn(format="localized") for k in ("weiche Klauseln", "Gewichtssumme (Eingänge des unären Zählers)", "Klauseln des unären Zählers (Obergrenze)")})
zg = E.zelle(art, n, True)
zu = E.zelle(art, n, False)
cpsg = E.cpsat_zelle(art, n, True)
if zg:
    refg = E.referenzoptima(zg, cpsg)
    kzg = E.alle_kennzahlen(zg, refg)
    if "oll" in kzg:
        balken["OLL (gewichtet 1 bis 10, Median, vorgerechnet)"] = max(int(kzg["oll"].klauseln), 1)
    st.plotly_chart(V.build_klauseln(balken, "Klauseln: unärer Zähler gegen OLL"), width="stretch", key="chart_klauseln")
    klu = None
    if zu and "lin_unten" in E.alle_kennzahlen(zu):
        klu = E.alle_kennzahlen(zu)["lin_unten"].klauseln
    sw = E.median([i["gewichtssumme"] for i in zg["instanzen"]])
    ob = E.median([A.totalizer_klauselzahl(i["gewichtssumme"], i["gewichtssumme"]) for i in zg["instanzen"]])
    kind, text = E.verdict_gewichte(kzg, klu, sw, ob)
    getattr(st, kind)(text)
    st.caption(f"Vorgerechnet, nicht live: {familie}, n = {n}, Gewichte 1 bis 10, zehn Instanzen, Budget {_sec(C.BUDGET_REFERENZ)} Konflikte.")
    st.dataframe(pd.DataFrame(E.tabellenzeilen(zg, cpsg)), hide_index=True, width="stretch")
else:
    st.plotly_chart(V.build_klauseln(balken, "Klauseln des unären Zählers (Obergrenze)"), width="stretch", key="chart_klauseln")
    st.info("Für diese Einstellung ist keine gewichtete Messreihe vorgerechnet (gewichtet 1 bis 10: Kontrollpunkte n = 20, 30, 50, Rampen n = 40, 60, Formel n = 40).")

with st.expander("🔁 Live: OLL mit und ohne Stratifizierung auf der Instanz der Seitenleiste"):
    if hi == 1:
        st.info("Die Instanz der Seitenleiste ist ungewichtet: Stratifizierung hätte nur eine Schicht und ändert nichts. Wählen Sie in der Seitenleiste Gewichte.")
    if zu_gross:
        st.info(f"Live gerechnet wird in dieser Familie nur bis n = {live_max}.")
    sig3 = (art, n, seed, hi, budget)
    if st.button("OLL und OLL + Stratifizierung live starten", key="live3_go", disabled=zu_gross or hi == 1):
        st.session_state["live_e3"] = {"sig": sig3, "laeufe": L.instanz(art, n, seed, hi, ("oll", "oll_strat"), budget)}
    g3 = st.session_state.get("live_e3")
    if g3 and g3["sig"] == sig3:
        kind, text = E.verdict_live(g3["laeufe"], budget)
        getattr(st, kind)(text)
        st.dataframe(pd.DataFrame([{"Verfahren": C.VERFAHREN_LABEL[v], "Konflikte": l.konflikte, "SAT-Aufrufe": l.aufrufe, "Kerne": len(l.kerne), "Status": l.status}
                                   for v, l in g3["laeufe"].items()]), hide_index=True, width="stretch")
    elif g3:
        st.caption("Die Einstellungen haben sich geändert: erneut starten.")

st.markdown("---")

# --- Experiment 4: Kernminimierung ----------------------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Experiment 4: Kernminimierung als Negativbefund")
st.markdown("Ein kleinerer Kern verspricht stärkere Schranken. Die einfache Minimierung (je Literal weglassen und mit 300 Konflikten erneut prüfen, höchstens 30 Versuche je Kern) "
            "macht die Kerne kleiner, aber jeder Versuch ist ein SAT-Aufruf, und seine Konflikte zählen mit. Über alle vorgerechneten Zellen:")
paare = E.minimierungspaare()
if paare:
    kind, text = E.verdict_minimierung(paare)
    getattr(st, kind)(text)
    st.plotly_chart(V.build_minimierung([(n_, a.median, b.median) for n_, a, b in paare], "Gesamtkonflikte je Zelle, ohne und mit Kernminimierung"), width="stretch", key="chart_min")
    st.dataframe(pd.DataFrame([{"Zelle": n_, "Kerngröße ohne": E.zahl(a.kern), "Kerngröße mit": E.zahl(b.kern), "Konflikte ohne (Median)": E.zahl(a.median), "Konflikte mit (Median)": E.zahl(b.median),
                                "Abbrüche ohne": a.abbrueche, "Abbrüche mit": b.abbrueche} for n_, a, b in paare]), hide_index=True, width="stretch")
    st.caption("Ungewichtet: OLL gegen OLL + Kernminimierung; gewichtet (1 bis 10): OLL + Stratifizierung gegen OLL + Stratifizierung + Kernminimierung. Vorgerechnet, nicht live.")
else:
    st.warning("Die vorgerechneten Messreihen (mxs_messungen.json) fehlen.")
with st.expander("🔁 Live: OLL mit und ohne Kernminimierung auf der Instanz der Seitenleiste"):
    if zu_gross:
        st.info(f"Live gerechnet wird in dieser Familie nur bis n = {live_max}.")
    sig4 = (art, n, seed, hi, budget)
    verf4 = ("oll_strat", "oll_strat_min") if hi > 1 else ("oll", "oll_min")
    if st.button("Mit und ohne Kernminimierung live starten", key="live4_go", disabled=zu_gross):
        st.session_state["live_e4"] = {"sig": sig4, "laeufe": L.instanz(art, n, seed, hi, verf4, budget)}
    g4 = st.session_state.get("live_e4")
    if g4 and g4["sig"] == sig4:
        kind, text = E.verdict_live(g4["laeufe"], budget)
        getattr(st, kind)(text)
        st.dataframe(pd.DataFrame([{"Verfahren": C.VERFAHREN_LABEL[v], "Konflikte (mit Minimierungsaufrufen)": l.konflikte, "SAT-Aufrufe": l.aufrufe, "Kerne": len(l.kerne),
                                    "größter Kern": str(max(l.kerngroessen)) if l.kerne else "–", "größter Kern vor der Minimierung": str(max(k.vor_minimierung for k in l.kerne)) if l.kerne else "–",
                                    "Status": l.status} for v, l in g4["laeufe"].items()]), hide_index=True, width="stretch")
    elif g4:
        st.caption("Die Einstellungen haben sich geändert: erneut starten.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Zusammenhang mit der Kerngröße gilt allgemein** | Gemessen sind **drei** Instanzfamilien mit je einem Parameter (Kontrollpunkte mit mittlerem Grad 3, Rampen mit Grad 5, Formeln mit sechs Klauseln je Variable), zehn Instanzen je Zelle und **ein** Löser (Python-CDCL, Standardbausteine). Die Familien unterscheiden sich auch in Struktur, Klauselzahl und Optimum; ob die Kerngröße die Ursache ist, ist nicht getrennt untersucht. Bei anderen Familien, Gewichtsverteilungen oder Lösern kann sich die Rangfolge ändern. | – |
| **Die Verfahren sind die der Literatur** | OLL, Fu–Malik, Stratifizierung und Kernminimierung sind **einfache Fassungen nach Gedächtnis**, nicht gegen die Literatur geprüft: ohne Hardening, ohne Core-Exhaustion, ohne Diversitätsregel; die Kernminimierung ist ein einfacher Versuchsablauf (300 Konflikte, 30 Versuche). Aussagen über „moderne MaxSAT-Löser“ machen die Messungen nicht. | – |
| **Weniger Konflikte heißt weniger Aufwand** | Die Konfliktzahl sagt nichts über die Zeit je Konflikt, den Speicher oder die Größe der Zähler (Experiment 3). | Kodierungen (Stück „Kardinalität kodieren“ der Linie) |
| **Gewichte sind gleichverteilt 1 bis 10** | Die lineare Suche ist nur in den kleinen Zellen (Kontrollpunkte n = 20 und 30) gewichtet gemessen, mit unärer Kodierung; ein Generalized Totalizer oder andere gewichtete Kodierungen sind nicht gebaut. | Verfahrenswahl (Stück der Linie) |
| **CP-SAT ist ein Maßstab** | CP-SAT ist vorgerechnet (ein Arbeiter, 15 Sekunden, Konflikte der Löser-Statistik) und nicht mit denselben Bausteinen gebaut; es braucht ungewichtet auf Rampen und Formeln das 6,5- bis 12-Fache der Konflikte von OLL, auf den Kontrollpunkten 0 bis 20,5 Konflikte; über die Arbeitsweise von CP-SAT sagt die Demo nichts. Das ist ein Vergleich dieser Instanzen, keine Aussage über CP-SAT allgemein. | `konzepte-lineare-programmierung`, Verfahrenswahl |
| **Alle Zellen sind live rechenbar** | Rampen ab Grad 6, Formeln mit acht Klauseln je Variable oder n ≥ 60 sowie die gewichtete lineare Suche ab n = 30 sind in Python nicht vertretbar und stehen nur als Hinweis in der README. | – |
    """
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben und gesucht.** Gegeben sind Variablen $x_1, \dots, x_n$, harte Klauseln $H$ und weiche Klauseln $C_1, \dots, C_m$ mit ganzzahligen Gewichten $w_i \ge 1$. Gesucht ist eine Belegung $\alpha$, die alle harten Klauseln erfüllt und die Kosten minimiert (partielles MaxSAT):
$$\min_{\alpha \models H}\ \sum_{i=1}^{m} w_i \,[\alpha \not\models C_i]$$

| Symbol | Bedeutung |
|---|---|
| $H$, $C_i$, $w_i$ | harte Klauseln, weiche Klausel $i$, ihr Gewicht |
| $a_i$ | Annahmeliteral: $a_i$ wahr heißt „$C_i$ gilt“ (bei einer Einheitsklausel das Literal selbst, sonst eine Hilfsvariable mit $a_i \to C_i$) |
| $K$ | Kern: Menge von Annahmen mit $H \wedge \bigwedge_{a \in K} a$ unerfüllbar |
| $LB$ | untere Schranke auf die Kosten |
| $o_j$ | Ausgang $j$ eines Zählers: wahr, wenn mindestens $j$ der Eingänge wahr sind |
| $\rho_i$ | Relaxationsvariable der weichen Klausel $i$ (Lineare Suche, Fu–Malik) |

**Kern und untere Schranke.** Ist $K$ ein Kern, dann verletzt jede Belegung mindestens eine Klausel aus $K$. Mit dem kleinsten Gewicht $w_K = \min_{a \in K} w(a)$ gilt nach dem Abzug von $w_K$ bei allen Mitgliedern
$$LB \leftarrow LB + w_K, \qquad w(a) \leftarrow w(a) - w_K \quad (a \in K).$$
Das Verfahren endet, sobald alle Annahmen mit positivem Gewicht gemeinsam erfüllbar sind; dann ist $LB$ gleich den Kosten der gefundenen Belegung und damit das Optimum.

**Lineare Suche.** Jede weiche Klausel wird zu $C_i \vee \rho_i$ relaxiert; ein Zähler über die Eingänge, in denen $\rho_i$ genau $w_i$-mal vorkommt (unär), begrenzt die Kosten:
$$\sum_{i} w_i\,\rho_i \le k \quad\Longleftrightarrow\quad \neg o_{k+1}$$
Von oben wird $k$ auf (Kosten der besten Belegung) $- 1$ gesetzt, bis die Frage unerfüllbar ist; von unten läuft $k = 0, 1, 2, \dots$, bis sie erfüllbar ist. Der Zähler hat so viele Eingänge wie die Gewichtssumme $W = \sum_i w_i$.

**Fu–Malik (ungewichtet).** Für einen Kern $K$ erhält jede weiche Klausel $C_i$ mit $a_i \in K$ eine neue Variable $b_i$ (neue Klausel $C_i \vee b_i$, neues Annahmeliteral); von den $b_i$ darf höchstens eine wahr sein:
$$\bigwedge_{i < j,\ a_i, a_j \in K} (\neg b_i \vee \neg b_j), \qquad LB \leftarrow LB + 1.$$

**OLL.** Für einen Kern $K = \{a_1, \dots, a_r\}$ mit $r \ge 2$ zählt ein Zähler die verletzten Mitglieder, $o_j$ ist wahr, wenn mindestens $j$ der Literale $\neg a_1, \dots, \neg a_r$ wahr sind. Die neue Annahme ist $\neg o_2$ („höchstens eine Verletzung im Kern“) mit dem Gewicht $w_K$; liegt später $\neg o_j$ selbst in einem Kern, kommt $\neg o_{j+1}$ mit dem abgezogenen Gewicht hinzu. Ein Kern aus einem Literal macht dieses Literal hart falsch.
Der Totalizer teilt die $m$ Eingänge in der Mitte; mit $p$ = Zahl der Ausgänge eines Kindes (Blatt: 1) hat ein Knoten mit Kindern $a, b$ genau $(p_a+1)(p_b+1)-1$ Klauseln und $\min(\text{Deckel},\, p_a + p_b)$ Ausgänge:
$$(\neg o^{(a)}_i \vee \neg o^{(b)}_j \vee o^{(v)}_{i+j}) \qquad (i, j \ge 0,\ (i,j) \ne (0,0)).$$

**Stratifizierung und Minimierung.** Stratifizierung lässt zuerst nur Annahmen mit Gewicht $\ge g$ zu, $g$ von der größten Gewichtsstufe absteigend; ein Kern ist auch dann ein Kern der Gesamtformel. Die Kernminimierung entfernt ein Literal aus $K$, wenn der Rest nach höchstens 300 Konflikten noch unerfüllbar ist.

**Handbeispiel.** Bei $H = \{(\neg x_1 \vee \neg x_2), (\neg x_1 \vee \neg x_3), (\neg x_2 \vee \neg x_3)\}$ und den sechs Einheitsklauseln $x_1, x_2, x_3, \neg x_1, \neg x_2, \neg x_3$ sind $\{S_1, S_2\}$ und $\{S_3, S_6\}$ Kerne; die Kosten sind mindestens 3, und $000$ erreicht 3.

**Literatur.** Ein Zähler in Einerdarstellung (Totalizer) nach Bailleux und Boufkhad, CP 2003 (Original nicht gelesen, Umsetzung nach Sekundärbeschreibung); Sinz, CP 2005 (Volltext gelesen) für den sequenziellen Zähler. OLL und Fu–Malik sind hier einfache Fassungen nach Gedächtnis, nicht gegen die Literatur geprüft. Alle Vergleiche sind eigene Messungen dieser Demo.
        """
    )

sync_query_params({key: st.session_state[key] for key in ("seed", "familie", "n", "gewicht_hi", "budget", "e1_gewichte", "e1_kern", "e1_schritt")})

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)
