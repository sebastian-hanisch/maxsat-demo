"""Konstanten: Regler-Grenzen, feste Annahmen, Messraster der Experimente, Farben und Presets."""

# --- Verfahren --------------------------------------------------------------------------------------------------------------------------------
VERFAHREN = ("lin_oben", "lin_unten", "fu_malik", "oll", "oll_strat", "oll_min", "oll_strat_min")
VERFAHREN_LABEL = {
    "lin_oben": "Lineare Suche von oben", "lin_unten": "Lineare Suche von unten", "fu_malik": "Fu–Malik (einfach)",
    "oll": "OLL", "oll_strat": "OLL + Stratifizierung", "oll_min": "OLL + Kernminimierung", "oll_strat_min": "OLL + Stratifizierung + Kernminimierung",
}
HAUPT_VERFAHREN = ("lin_oben", "lin_unten", "fu_malik", "oll")        # die vier Verfahren des Vergleichs (Experiment 2)
CPSAT = "cpsat"                                                         # eingefrorene Vergleichsspalte, nie live
CPSAT_LABEL = "CP-SAT (vorgerechnet, nicht live)"
MESSVERFAHREN_UNGEWICHTET = ("lin_oben", "lin_unten", "fu_malik", "oll", "oll_min")
MESSVERFAHREN_GEWICHTET = ("oll", "oll_strat", "oll_strat_min")
MESSVERFAHREN_GEWICHTET_LINEAR = ("lin_oben", "lin_unten")             # unär kodiert, nur in den kleinen Zellen Kontrollpunkte n = 20 und 30

# --- Instanzfamilien ---------------------------------------------------------------------------------------------------------------------------
FAMILIEN = ("Kontrollpunkte", "Rampen", "Formel")
FAMILIE_ART = {"Kontrollpunkte": "kontrollpunkte", "Rampen": "rampen", "Formel": "formel"}
ART_FAMILIE = {v: k for k, v in FAMILIE_ART.items()}
FAMILIE_BESCHREIBUNG = {
    "Kontrollpunkte": "Kontrollpunkte (Vertex Cover): jede Unverträglichkeit braucht an einem Ende einen Kontrollpunkt, möglichst wenige Kontrollpunkte; Kerne aus zwei Literalen.",
    "Rampen": "Rampen (3-Färbung): jeder Auftrag genau eine von drei Rampen, möglichst wenige Konflikte mit derselben Rampe; große Kerne.",
    "Formel": "Überbestimmte Zufalls-3-SAT: sechsmal so viele Klauseln wie Variablen, möglichst viele erfüllen; sehr große Kerne.",
}
FAMILIE_PARAM = {"kontrollpunkte": 3.0, "rampen": 5.0, "formel": 6}      # mittlerer Grad bzw. Klauseln je Variable
LIVE_N_MAX = {"kontrollpunkte": 50, "rampen": 60, "formel": 40}          # größere Instanzen nur vorgerechnet (Messreihe n = 90 bei Rampen)
N_OPTIONEN = (20, 30, 40, 50, 60, 90)
GEWICHT_OPTIONEN = (1, 5, 10)                                            # Gewichte gleichverteilt 1 … hi; 1 = ungewichtet
BUDGET_OPTIONEN = (5_000, 10_000, 30_000)
CALL_BUDGET_MAX = 10_000                                                 # Konflikte je SAT-Aufruf (vorgerechnet wie live)
BUDGET_REFERENZ = 30_000                                                 # Gesamtbudget der vorgerechneten Messreihen

# --- Messraster (tools/messungen.py schreibt mxs_messungen.json, tools/cpsat_messung.py schreibt mxs_cpsat.json) --------------------------------------
SEEDS = tuple(range(100, 110))                                           # 10 feste Instanzen je Zelle (SplitMix64): nie eine einzelne als Befund
ZELLEN_UNGEWICHTET = (("kontrollpunkte", 20), ("kontrollpunkte", 30), ("kontrollpunkte", 50), ("rampen", 40), ("rampen", 60), ("rampen", 90), ("formel", 40))
ZELLEN_GEWICHTET = (("kontrollpunkte", 20), ("kontrollpunkte", 30), ("kontrollpunkte", 50), ("rampen", 40), ("rampen", 60), ("formel", 40))
MESSUNGEN_DATEI = "mxs_messungen.json"
CPSAT_DATEI = "mxs_cpsat.json"
CPSAT_ZEITLIMIT = 15                                                     # Sekunden je Instanz, ein Arbeiter


def zellenschluessel(art: str, n: int, gewichtet: bool) -> str:
    return f"{art}|{n}|{'g' if gewichtet else 'u'}"


# --- Verdikte -----------------------------------------------------------------------------------------------------------------------------------
SCHWELLE_GLEICHAUF = 1.25        # Medianverhältnis der Konflikte, bis zu dem zwei Verfahren als „ungefähr gleichauf“ gelten (mit der Zählung im Text)
SCHWELLE_GROESSENORDNUNG = 10    # Medianverhältnis, ab dem „um Größenordnungen“ gesagt wird: mindestens das Zehnfache
UNTERE_GRENZE_KONFLIKTE = 1      # Nenner bei Mediane 0 (ein Lauf ohne Konflikt zählt als 1)

# --- Allgemein ----------------------------------------------------------------------------------------------------------------------------------
SEED_MAX, DEFAULT_SEED = 999999, 100

# --- Experiment 1: Kerne von Hand ----------------------------------------------------------------------------------------------------------------
E1_GEWICHTE = (2, 1, 1, 3, 1, 1)
E1_GEWICHT_OPTIONEN = ("alle 1", "2, 1, 1, 3, 1, 1")
E1_KERN_OPTIONEN = ("Kleinster Kern", "Kern des Lösers")
E1_SCHRITT = (0, 6)
DEFAULT_E1_SCHRITT = 6

# --- Darstellung ---------------------------------------------------------------------------------------------------------------------------------
COLOR = {"lin_oben": "#B5651D", "lin_unten": "#D49A5B", "fu_malik": "#7A6FA8", "oll": "#2F6B65", "oll_strat": "#3E8E84", "oll_min": "#8CB8B2",
         "oll_strat_min": "#B8D4D0", "cpsat": "#6B6B6B"}
COLOR_KERN = "#C0392B"

# --- Presets ----------------------------------------------------------------------------------------------------------------------------------------
# Schlüssel eines Presets = Schlüssel der Regler (siehe mxs_presets.SETTING_SPECS); fehlt einer, gilt die Voreinstellung. Das erste Preset entspricht den Voreinstellungen.
PRESETS = {
    "Handbeispiel": {},
    "Vertex Cover n = 30": {"familie": "Kontrollpunkte", "n": 30},
    "Färbung n = 40 Grad 5,0": {"familie": "Rampen", "n": 40},
    "Zufall n = 40 m/n 6": {"familie": "Formel", "n": 40},
}
PRESET_HELP = {
    "Handbeispiel": "Drei Variablen, höchstens eine wahr, sechs weiche Klauseln: Experiment 1 zeigt Fu–Malik und OLL von Hand. Die Instanz der weiteren Experimente sind 20 Kontrollpunkt-Aufträge.",
    "Vertex Cover n = 30": "30 Aufträge mit Unverträglichkeiten, möglichst wenige Kontrollpunkte: Kerne aus zwei Literalen, die Kernverfahren brauchen kaum Konflikte.",
    "Färbung n = 40 Grad 5,0": "40 Aufträge auf drei Rampen, möglichst wenige Konflikte: große Kerne, kein Verfahren ist klar vorn.",
    "Zufall n = 40 m/n 6": "40 Variablen, 240 weiche Klauseln: sehr große Kerne, alle Verfahren brauchen im Median tausende Konflikte (vorgerechnet); live rechnet die App diese Zelle nur auf Knopfdruck.",
}
