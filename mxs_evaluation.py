"""Messreihen, Kennzahlen und Verdikte. Jedes Verdikt ist eine reine Funktion (Art, Text); jede Zahl im Text stammt aus den übergebenen Kennzahlen.

Zählung: ein Lauf, der das Budget erreicht (Status „Abbruch“), zählt mit dem Gesamtbudget und ist nur eine untere Schranke. Kerngröße = Zahl der Literale im Kern;
je Instanz der Median über ihre Kerne, je Zelle der Median über die Instanzen (Mediane der Mediane). Instanzen ohne Kern (lineare Suche) bleiben außen vor.
"""

import functools
import json
import statistics
from pathlib import Path
from typing import NamedTuple

import mxs_algorithm as A
import mxs_constants as C
import mxs_scenario as S

HIER = Path(__file__).resolve().parent


# ------------------------------------------------------------------------------------------------------------------------------ Formatierung

def zahl(x, stellen: int = 0) -> str:
    """Deutsche Zahlenschreibweise: Tausenderpunkt, Dezimalkomma. Ganzzahlige Werte ohne Nachkommastellen, sonst eine bzw. zwei Stellen."""
    if x is None:
        return "–"
    if stellen == 0 and float(x) != int(x):
        stellen = 1 if abs(x * 2 - round(x * 2)) < 1e-9 else 2
    text = f"{x:,.{stellen}f}"
    return text.replace(",", "§").replace(".", ",").replace("§", ".")


def faktor(x: float) -> str:
    """Verhältnis: ab 10 ganzzahlig, darunter eine Nachkommastelle."""
    return zahl(round(x), 0) if x >= 10 else zahl(round(x, 1), 1)


def median(werte):
    return statistics.median(werte) if werte else None


# ------------------------------------------------------------------------------------------------------------------------------ Dateien

@functools.lru_cache(maxsize=None)
def lade_messungen() -> dict:
    pfad = HIER / C.MESSUNGEN_DATEI
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {}


@functools.lru_cache(maxsize=None)
def lade_cpsat() -> dict:
    pfad = HIER / C.CPSAT_DATEI
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {}


def zelle(art: str, n: int, gewichtet: bool):
    """Die vorgerechnete Zelle oder None."""
    return lade_messungen().get("zellen", {}).get(C.zellenschluessel(art, n, gewichtet))


def cpsat_zelle(art: str, n: int, gewichtet: bool):
    return lade_cpsat().get("zellen", {}).get(C.zellenschluessel(art, n, gewichtet))



# ------------------------------------------------------------------------------------------------------------------------------ Kennzahlen

class Kennzahlen(NamedTuple):
    laeufe: int
    median: float | None         # Konflikte (Abbruch zählt mit dem Gesamtbudget)
    minimum: int | None
    maximum: int | None
    aufrufe: float | None        # SAT-Aufrufe, Median
    kern: float | None           # Kerngröße (Mediane der Mediane), None ohne Kerne
    klauseln: float | None       # dem Löser übergebene Klauseln, Median
    abbrueche: int
    falsche: int                 # beendete Läufe, deren Optimum vom Referenzoptimum abweicht
    ohne_referenz: int           # beendete Läufe ohne Referenzoptimum (nicht geprüft)


def gezaehlt(lauf: dict, budget: int) -> int:
    return budget if lauf["status"] == "Abbruch" else lauf["konflikte"]


def referenzoptima(z: dict, cps: dict | None = None) -> dict:
    """Seed -> Referenzoptimum: das von CP-SAT (eingefroren, wenn bewiesen), sonst der gemeinsame Wert aller beendeten Läufe der Zelle, sonst fehlt der Seed."""
    ref = {}
    for inst in z["instanzen"]:
        seed = inst["seed"]
        eintrag = (cps or {}).get("instanzen", {}).get(str(seed))
        if eintrag and eintrag["status"] == "ok":
            ref[seed] = eintrag["optimum"]
            continue
        fertig = {l["optimum"] for l in inst["laeufe"].values() if l["status"] == "ok"}
        if len(fertig) == 1:
            ref[seed] = next(iter(fertig))
    return ref


def kennzahlen(z: dict, verfahren: str, referenz: dict | None = None, budget: int = C.BUDGET_REFERENZ) -> Kennzahlen:
    laeufe = [(i["seed"], i["laeufe"][verfahren]) for i in z["instanzen"] if verfahren in i["laeufe"]]
    werte = [gezaehlt(l, budget) for _, l in laeufe]
    kerne = [median(l["kerne"]) for _, l in laeufe if l["kerne"]]
    falsch = sum(1 for s, l in laeufe if l["status"] == "ok" and referenz and s in referenz and l["optimum"] != referenz[s])
    ohne = sum(1 for s, l in laeufe if l["status"] == "ok" and not (referenz and s in referenz))
    return Kennzahlen(len(laeufe), median(werte), min(werte) if werte else None, max(werte) if werte else None, median([l["aufrufe"] for _, l in laeufe]),
                      median(kerne), median([l["klauseln"] for _, l in laeufe]), sum(1 for _, l in laeufe if l["status"] == "Abbruch"), falsch, ohne)


def alle_kennzahlen(z: dict, referenz: dict | None = None, budget: int = C.BUDGET_REFERENZ) -> dict:
    """Verfahren -> Kennzahlen für jedes Verfahren, das in der Zelle gemessen wurde."""
    vorhanden = {v for i in z["instanzen"] for v in i["laeufe"]}
    return {v: kennzahlen(z, v, referenz, budget) for v in C.VERFAHREN if v in vorhanden}


def cpsat_kennzahlen(cps: dict | None):
    """(Median der Konflikte, Abbrüche, Instanzen) aus dem eingefrorenen Band; Abbruch zählt mit den Konflikten bis zum Zeitlimit."""
    if not cps:
        return None
    werte = [e["konflikte"] for e in cps["instanzen"].values()]
    return median(werte), sum(1 for e in cps["instanzen"].values() if e["status"] != "ok"), len(werte)


def vergleich_je_instanz(z: dict, a: str, b: str, budget: int = C.BUDGET_REFERENZ):
    """(Instanzen, in denen `b` weniger Konflikte braucht als `a`, gleich viele, mehr). Abbrüche zählen mit dem Gesamtbudget."""
    weniger = gleich = mehr = 0
    for i in z["instanzen"]:
        if a in i["laeufe"] and b in i["laeufe"]:
            x, y = gezaehlt(i["laeufe"][a], budget), gezaehlt(i["laeufe"][b], budget)
            weniger += y < x
            gleich += y == x
            mehr += y > x
    return weniger, gleich, mehr


def instanzen_gemessen(z: dict, verfahren: str) -> int:
    return sum(1 for i in z["instanzen"] if verfahren in i["laeufe"])


# ------------------------------------------------------------------------------------------------------------------------------ Verdikte

def _abbrueche_text(kz: dict, verfahren) -> str:
    teile = [f"{C.VERFAHREN_LABEL[v]} {kz[v].abbrueche}" for v in verfahren if v in kz]
    n = next(iter(kz.values())).laeufe
    return f"Abbrüche am Budget (von {n} Instanzen): " + ", ".join(teile) + "."


def verdict_verfahren(kz: dict, familie: str = "") -> tuple:
    """Vergleich OLL gegen die lineare Suche in einer Zelle (Experiment 2). `kz`: Verfahren -> Kennzahlen mit mindestens `oll`, `lin_oben`, `lin_unten`.
    Das Medianverhältnis (bestes lineares Verfahren zu OLL) entscheidet: ab SCHWELLE_GROESSENORDNUNG „um Größenordnungen“, ab SCHWELLE_GLEICHAUF „weniger“,
    darunter „ungefähr gleichauf“, umgekehrt „mehr“."""
    o = kz["oll"]
    lineare = [v for v in ("lin_unten", "lin_oben") if v in kz]
    if o.median is None or not lineare:
        return "info", "Für diese Einstellung liegt kein Vergleich von OLL und linearer Suche vor."
    beste = min(lineare, key=lambda v: kz[v].median)
    best = kz[beste].median
    nenner = max(o.median, C.UNTERE_GRENZE_KONFLIKTE)
    verhaeltnis = best / nenner
    kern = f"Bei Kernen aus {zahl(o.kern)} Literalen (Median)" if o.kern is not None else "Ohne Kerne"
    kopf = f"{kern}, Konflikte im Median: OLL {zahl(o.median)}"
    for v in ("lin_unten", "lin_oben", "fu_malik"):
        if v in kz:
            kopf += f", {C.VERFAHREN_LABEL[v].replace('Lineare Suche', 'lineare Suche')} {zahl(kz[v].median)}"
    kopf += ". "
    if verhaeltnis >= C.SCHWELLE_GROESSENORDNUNG:
        urteil, art = f"Das Kernverfahren braucht höchstens ein Zehntel der Konflikte der besten linearen Suche ({C.VERFAHREN_LABEL[beste]}): ein Abstand von mehr als einer Größenordnung. ", "success"
    elif verhaeltnis > C.SCHWELLE_GLEICHAUF:
        urteil, art = f"OLL braucht weniger als die beste lineare Suche ({C.VERFAHREN_LABEL[beste]}: das {faktor(verhaeltnis)}-Fache), der Abstand ist aber kleiner als eine Größenordnung. ", "info"
    elif verhaeltnis >= 1 / C.SCHWELLE_GLEICHAUF:
        urteil, art = f"OLL und die beste lineare Suche ({C.VERFAHREN_LABEL[beste]}) liegen im Median höchstens um den Faktor {zahl(C.SCHWELLE_GLEICHAUF, 2)} auseinander: ungefähr gleichauf. ", "info"
    else:
        urteil, art = f"Die lineare Suche ({C.VERFAHREN_LABEL[beste]}) braucht im Median weniger als OLL (OLL das {faktor(1 / verhaeltnis)}-Fache). ", "warning"
    return art, kopf + urteil + _abbrueche_text(kz, [v for v in C.HAUPT_VERFAHREN if v in kz])


def verdict_gewichte(kz: dict, klauseln_ungewichtet: float | None, gewichtssumme: float | None, unaer_obergrenze: float | None = None) -> tuple:
    """Gewichtete Zelle (Experiment 3): Kosten der unären Kodierung der linearen Suche (soweit gemessen) gegen OLL.
    `klauseln_ungewichtet`: Median der Klauseln der linearen Suche derselben Zelle ohne Gewichte (oder None); `gewichtssumme` und `unaer_obergrenze`: Median über die
    Instanzen der Gewichtssumme und der gerechneten Klauselzahl des unären Zählers (für Zellen ohne gemessene lineare Suche)."""
    o = kz["oll"]
    text = f"OLL: {o.abbrueche} von {o.laeufe} Instanzen am Budget abgebrochen, Konflikte im Median {zahl(o.median)}. "
    lin = [v for v in ("lin_unten", "lin_oben") if v in kz]
    if lin:
        k = kz[lin[0]]
        text += (f"Die lineare Suche (unär kodiert) braucht im Median {zahl(k.klauseln)} Klauseln"
                 + (f" statt {zahl(klauseln_ungewichtet)} ohne Gewichte (das {faktor(k.klauseln / klauseln_ungewichtet)}-Fache)" if klauseln_ungewichtet else "")
                 + f"; Konflikte im Median {zahl(kz['lin_oben'].median) if 'lin_oben' in kz else '–'} (von oben) und {zahl(kz['lin_unten'].median) if 'lin_unten' in kz else '–'} (von unten). ")
    elif gewichtssumme and unaer_obergrenze:
        text += (f"Die lineare Suche wurde hier nicht gemessen: bei der Gewichtssumme {zahl(gewichtssumme)} (Median) hätte ihr unärer Zähler so viele Eingänge "
                 f"und bis zu {zahl(unaer_obergrenze)} Klauseln (Obergrenze, gerechnet, Median über die Instanzen). ")
    if "oll_strat" in kz:
        s = kz["oll_strat"]
        text += f"Mit Stratifizierung: Konflikte im Median {zahl(s.median)} statt {zahl(o.median)}, SAT-Aufrufe im Median {zahl(s.aufrufe)} statt {zahl(o.aufrufe)}."
    return ("success" if o.abbrueche == 0 else "warning"), text


def verdict_minimierung(paare: list) -> tuple:
    """`paare`: Liste von (Zellenname, Kennzahlen ohne Minimierung, Kennzahlen mit Minimierung). Zählt die Zellen mit kleineren Kernen und mit mehr Gesamtkonflikten."""
    n = len(paare)
    kleiner = sum(1 for _, a, b in paare if a.kern is not None and b.kern is not None and b.kern < a.kern)
    mehr = sum(1 for _, a, b in paare if b.median > a.median)
    weniger = sum(1 for _, a, b in paare if b.median < a.median)
    text = (f"Mit Kernminimierung werden die Kerne (Median der Mediane) in {kleiner} von {n} Zellen kleiner; die Gesamtkonflikte (Minimierungsaufrufe mitgezählt, Median) "
            f"steigen in {mehr} von {n} Zellen und sinken in {weniger}.")
    return ("warning" if mehr > n / 2 else "info"), text


def kerngroessen_text(lauf: A.Lauf) -> str:
    return ", ".join(str(g) for g in lauf.kerngroessen) if lauf.kerne else "keine"


def verdict_kerne_von_hand(fm: A.Lauf | None, oll: A.Lauf) -> tuple:
    """Experiment 1: Kerngrößen der beiden Kernverfahren am Handbeispiel."""
    if fm is None:
        return "info", f"OLL (mit Gewichtsabzug): Kerne aus {kerngroessen_text(oll)} Literalen, untere Schranke am Ende {oll.untere}, Optimum {oll.optimum}. Fu–Malik gibt es hier nur ungewichtet."
    teil = f"Fu–Malik: Kerne aus {kerngroessen_text(fm)} Literalen, OLL: Kerne aus {kerngroessen_text(oll)}; beide enden bei der unteren Schranke {oll.untere} = Optimum {oll.optimum}. "
    if fm.kerngroessen == oll.kerngroessen:
        return "info", teil + "Die Kerngrößen sind gleich."
    groesser = max(fm.kerngroessen)
    return "success", teil + f"Der größte Kern hat bei Fu–Malik {groesser} Literale, bei OLL {max(oll.kerngroessen)}: OLL baut den Zähler über die Kernliterale statt paarweise „höchstens eins“."


def verdict_live(laeufe: dict, budget: int) -> tuple:
    """Live gerechnete Instanz: je Verfahren Optimum, Konflikte und Status."""
    fertig = {v: l for v, l in laeufe.items() if l.status == "ok"}
    optima = {l.optimum for l in fertig.values()}
    teile = []
    for v, l in laeufe.items():
        teile.append(f"{C.VERFAHREN_LABEL[v]}: " + (f"Optimum {l.optimum}, {zahl(l.konflikte)} Konflikte" if l.status == "ok" else f"Abbruch bei {zahl(budget)} Konflikten, untere Schranke {l.untere}"))
    if len(optima) > 1:
        return "error", "Die Verfahren widersprechen sich im Optimum: " + "; ".join(teile)
    return "success" if fertig else "warning", "; ".join(teile) + "."


def live_messung(inst, verfahren, budget: int, fortschritt=None) -> dict:
    """Die gewählten Verfahren auf einer Instanz (Gesamtbudget `budget`, je SAT-Aufruf höchstens `CALL_BUDGET_MAX`)."""
    out = {}
    for v in verfahren:
        out[v] = A.laufe(inst, v, call_budget=min(C.CALL_BUDGET_MAX, budget), total_budget=budget, kern_wahl="loeser")
        if fortschritt:
            fortschritt(v)
    return out


def live_serie(art: str, n: int, hi: int, verfahren, budget: int, seeds=C.SEEDS) -> dict:
    """Zehn feste Instanzen live, in der Form einer vorgerechneten Zelle (für dieselben Tabellen)."""
    z = {"art": art, "n": n, "gewichtet": hi > 1, "instanzen": []}
    for s in seeds:
        inst = S.erzeuge(art, n, s, hi)
        z["instanzen"].append({"seed": s, "weich": len(inst.weich), "gewichtssumme": sum(inst.gewichte), "laeufe": {
            v: {"optimum": l.optimum, "status": l.status, "aufrufe": l.aufrufe, "konflikte": l.konflikte, "untere": l.untere, "kerne": l.kerngroessen,
                "kerne_vor": [k.vor_minimierung for k in l.kerne], "klauseln": l.klauseln, "hilfsvariablen": l.hilfsvariablen, "kosten_modell": l.kosten_modell}
            for v, l in live_messung(inst, verfahren, budget).items()}})
    return z


# ------------------------------------------------------------------------------------------------------------------------------ Texte für Experiment 1

def literal_text(l: int) -> str:
    return f"x{l}" if l > 0 else f"¬x{-l}"


def klausel_text(c) -> str:
    return " ∨ ".join(literal_text(l) for l in c)


def kern_satz(schritt: A.KernSchritt) -> str:
    """Ein Satz zu einem Kern: wer gehört dazu, was folgt für die untere Schranke."""
    mitglieder = "{" + ", ".join(schritt.mitglieder) + "}"
    satz = (f"Kern {schritt.nr} {mitglieder}: zusammen mit den harten Klauseln nicht erfüllbar, mindestens eine dieser Annahmen wird verletzt; "
            f"die untere Schranke steigt um {schritt.gewicht} auf {schritt.untere}.")
    if schritt.neu:
        satz += f" Neue Annahme: {schritt.neu}."
    return satz


def zaehler_erklaerung(name: str) -> str | None:
    """„Z0≥2“ -> Erklärung der Annahme (nur für Zähler-Namen), sonst None."""
    if not name.startswith("Z") or "≥" not in name:
        return None
    nr, k = name[1:].split("≥")
    return f"{name}: weniger als {k} der Mitglieder von Kern {int(nr) + 1} sind verletzt."


# ------------------------------------------------------------------------------------------------------------------------------ Tabellen

def tabellenzeilen(z: dict, cps: dict | None = None, budget: int = C.BUDGET_REFERENZ, verfahren=None) -> list:
    """Zeilen der Vergleichstabelle einer Zelle (vorgerechnet oder live): je Verfahren Kennzahlen, am Ende die eingefrorene CP-SAT-Zeile (falls vorhanden)."""
    ref = referenzoptima(z, cps)
    kz = alle_kennzahlen(z, ref, budget)
    zeilen = []
    for v, k in kz.items():
        if verfahren is not None and v not in verfahren:
            continue
        zeilen.append({"Verfahren": C.VERFAHREN_LABEL[v], "Konflikte (Median)": zahl(k.median), "Minimum": zahl(k.minimum), "Maximum": zahl(k.maximum),
                       "SAT-Aufrufe (Median)": zahl(k.aufrufe), "Kerngröße (Median)": zahl(k.kern) if k.kern is not None else "–", "Klauseln (Median)": zahl(k.klauseln),
                       "Abbrüche am Budget": str(k.abbrueche), "falsche Antworten": str(k.falsche)})
    c = cpsat_kennzahlen(cps)
    if c:
        zeilen.append({"Verfahren": C.CPSAT_LABEL, "Konflikte (Median)": zahl(c[0]), "Minimum": "–", "Maximum": "–", "SAT-Aufrufe (Median)": "–", "Kerngröße (Median)": "–",
                       "Klauseln (Median)": "–", "Abbrüche am Budget": str(c[1]), "falsche Antworten": "–"})
    return zeilen


def konflikte_je_instanz(z: dict, verfahren: str, cps: dict | None = None, budget: int = C.BUDGET_REFERENZ) -> list:
    """Konflikte je Instanz (Abbruch zählt mit dem Gesamtbudget); `verfahren` = "cpsat" nimmt die eingefrorenen Konflikte von CP-SAT."""
    if verfahren == C.CPSAT:
        return [e["konflikte"] for e in cps["instanzen"].values()] if cps else []
    return [gezaehlt(i["laeufe"][verfahren], budget) for i in z["instanzen"] if verfahren in i["laeufe"]]


def minimierungspaare() -> list:
    """(Zellenname, Kennzahlen ohne Minimierung, Kennzahlen mit Minimierung) über alle vorgerechneten Zellen: ungewichtet OLL gegen OLL + Kernminimierung,
    gewichtet OLL + Stratifizierung gegen OLL + Stratifizierung + Kernminimierung."""
    paare = []
    for gew, zellen, (a, b) in ((False, C.ZELLEN_UNGEWICHTET, ("oll", "oll_min")), (True, C.ZELLEN_GEWICHTET, ("oll_strat", "oll_strat_min"))):
        for art, n in zellen:
            z = zelle(art, n, gew)
            if z:
                paare.append((f"{C.ART_FAMILIE[art]} n = {n}" + (" (gewichtet)" if gew else ""), kennzahlen(z, a), kennzahlen(z, b)))
    return paare
