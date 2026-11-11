"""Die vier MaxSAT-Verfahren auf dem CDCL mit Annahmen: lineare Suche (von oben, von unten), Fu–Malik und OLL (mit Stratifizierung und Kernminimierung).

Eine Instanz ist `mxs_scenario.MaxSat` (harte Klauseln, weiche Klauseln, Gewichte; Kosten = Gewichtssumme der verletzten weichen Klauseln). Aufwand wird in
**SAT-Aufrufen und Konflikten** gezählt, nie in Sekunden. Ein Verfahren liefert ein `Lauf`: Optimum (oder `None` bei Abbruch), untere Schranke, Kerne Schritt für
Schritt, Zeitleiste der Schranken, Klauselzahl.

* **Lineare Suche** (unär kodierter Zähler über die Relaxationsvariablen, jede mit ihrem Gewicht wiederholt): von oben (Schranke immer weiter senken, bis unerfüllbar) und von
  unten (k = 0, 1, 2, … bis erfüllbar).
* **Fu–Malik** (einfache Fassung nach Gedächtnis, nur ungewichtet): je Kern eine neue Relaxationsvariable je Mitglied, paarweise „höchstens eine“.
* **OLL** (einfache Fassung nach Gedächtnis): je Kern ein Zähler über die Kernliterale, neue Annahme „höchstens eine Verletzung im Kern“; Gewichtsabzug; optional
  Stratifizierung (Annahmen nach Gewicht absteigend zulassen) und Kernminimierung (je Kern höchstens 30 Versuche mit 300 Konflikten).

Die Verfahren nutzen nur `Loeser.loese(annahmen, conflict_budget)`, `neue_variable` und `fuege_klausel_hinzu` des kopierten Kern-CDCL.
"""

import itertools
from dataclasses import dataclass, field

import mxs_cdcl as CD
import mxs_kodierung as KOD
from mxs_scenario import MaxSat, kosten

CALL_BUDGET = 10_000                 # Konflikte je SAT-Aufruf
TOTAL_BUDGET = 30_000                # Konflikte je Verfahren und Instanz (ein Abbruch zählt mit diesem Wert)
MIN_BUDGET, MIN_VERSUCHE = 300, 30   # Kernminimierung: Konflikte je Versuch, Versuche je Kern
KLEIN_MAX = 14                       # kleinster Kern per Aufzählung der Teilmengen nur bis so vielen Annahmen

VERFAHREN = ("lin_oben", "lin_unten", "fu_malik", "oll", "oll_strat", "oll_min", "oll_strat_min")
VERFAHREN_LABEL = {
    "lin_oben": "Lineare Suche von oben", "lin_unten": "Lineare Suche von unten", "fu_malik": "Fu–Malik (einfach)",
    "oll": "OLL", "oll_strat": "OLL + Stratifizierung", "oll_min": "OLL + Kernminimierung", "oll_strat_min": "OLL + Stratifizierung + Kernminimierung",
}
KERNVERFAHREN = ("fu_malik", "oll", "oll_strat", "oll_min", "oll_strat_min")


@dataclass
class KernSchritt:
    nr: int                 # 1, 2, … in der Reihenfolge der Funde
    mitglieder: list        # Namen der Annahmen im Kern (S3, Z0≥2, S1' …)
    groesse: int            # Zahl der Literale im Kern (nach einer Minimierung die kleinere Zahl)
    vor_minimierung: int    # Größe, die der Löser geliefert hat (gleich `groesse` ohne Minimierung)
    gewicht: int            # Mindestgewicht der Mitglieder (ungewichtet 1): so viel hebt der Kern die untere Schranke
    untere: int             # untere Schranke nach diesem Kern
    aufruf: int             # Nummer des SAT-Aufrufs, der den Kern lieferte
    konflikte: int          # Konflikte insgesamt bis nach diesem Kern (Minimierungsaufrufe mitgezählt)
    neu: str | None = None  # Name der neuen Annahme (Zähler oder Relaxation), None bei Kern der Größe 1 (Literal wird hart verneint)


@dataclass
class Lauf:
    verfahren: str
    optimum: int | None = None
    untere: int = 0
    obere: int | None = None
    status: str = "ok"          # "ok" | "Abbruch" | "hart unerfüllbar"
    aufrufe: int = 0
    konflikte: int = 0
    kerne: list = field(default_factory=list)
    zeitleiste: list = field(default_factory=list)    # je SAT-Aufruf: {"aufruf", "antwort", "untere", "obere", "konflikte"}
    klauseln: int = 0           # Klauseln, die dem Löser übergeben wurden (hart, weich relaxiert, Zähler)
    hilfsvariablen: int = 0
    modell: dict | None = None
    kosten_modell: int | None = None

    @property
    def kerngroessen(self):
        return [k.groesse for k in self.kerne]


class Sat:
    """Der Löser mit Zählern (SAT-Aufrufe, übergebene Klauseln, Hilfsvariablen)."""

    def __init__(self, n, hart):
        self.l = CD.Loeser(n, [tuple(c) for c in hart])
        self.n0 = n
        self.klauseln = len(hart)
        self.aufrufe = 0

    def neu(self):
        return self.l.neue_variable()

    def klausel(self, c):
        self.klauseln += 1
        self.l.fuege_klausel_hinzu(list(c))

    def loese(self, annahmen, budget):
        self.aufrufe += 1
        return self.l.loese(list(annahmen), budget)

    @property
    def konflikte(self):
        return self.l.stat["konflikte"]

    @property
    def hilfsvariablen(self):
        return self.l.n - self.n0


# ------------------------------------------------------------------ Zähler (Totalizer) mit herausgereichten Ausgängen

def totalizer(sat, lits, cap):
    """Addierbaum in Einerdarstellung: Ausgang o_j (j = 1 … min(cap, Zahl der Eingänge)) ist wahr, wenn mindestens j Eingänge wahr sind (nur die Richtung Eingang → Ausgang).
    Gibt [o_1, …] zurück. Nach der Beschreibung bei Sinz gebaut (Bailleux/Boufkhad 2003, Original nicht gelesen)."""
    def baue(ls):
        if len(ls) == 1:
            return [ls[0]]
        mitte = len(ls) // 2
        a, b = baue(ls[:mitte]), baue(ls[mitte:])
        m = min(cap, len(a) + len(b))
        aus = [sat.neu() for _ in range(m)]
        for i in range(len(a) + 1):
            for j in range(len(b) + 1):
                t = i + j
                if t == 0:
                    continue
                c = [aus[min(t, m) - 1]]
                if i > 0:
                    c.append(-a[i - 1])
                if j > 0:
                    c.append(-b[j - 1])
                sat.klausel(c)
        return aus
    return baue(list(lits))


def totalizer_klauselzahl(m: int, cap: int) -> int:
    """Zahl der Klauseln von `totalizer` bei m Eingängen und Deckel `cap`, ohne zu bauen (gleiche Teilung in der Mitte)."""
    def zaehle(laenge):
        if laenge == 1:
            return 0, 1
        c1, p1 = zaehle(laenge // 2)
        c2, p2 = zaehle(laenge - laenge // 2)
        return c1 + c2 + (p1 + 1) * (p2 + 1) - 1, min(cap, p1 + p2)
    return zaehle(m)[0]


def unaere_klauselzahl(gewichte, cap=None) -> int:
    """Klauseln des unär kodierten Zählers der linearen Suche: jede Relaxationsvariable so oft als Eingang, wie ihr Gewicht sagt (Summe der Gewichte Eingänge)."""
    m = sum(gewichte)
    return totalizer_klauselzahl(m, m if cap is None else cap) if m else 0


# ------------------------------------------------------------------ Kerne

def _kern_klein(sat, annahmen):
    """Kleinster unerfüllbarer Teil der Annahmen, bei Gleichstand der lexikographisch erste (Reihenfolge der Annahmen). Aufzählung der Teilmengen: nur für kleine Mengen.
    Diese Hilfsaufrufe zählen nicht als SAT-Aufrufe des Verfahrens (ihre Konflikte stehen im Gesamtzähler)."""
    for g in range(1, len(annahmen) + 1):
        for idx in itertools.combinations(range(len(annahmen)), g):
            if sat.l.loese([annahmen[i] for i in idx], None).antwort is False:
                return [annahmen[i] for i in idx]
    return []


def _kern_waehlen(sat, annahmen, kern, kern_wahl):
    """Der Kern in der Reihenfolge der Annahmen. kern_wahl "loeser": die Annahmen, die der Löser im Schlusskonflikt nennt; "klein": kleinster Kern (nur bis KLEIN_MAX Annahmen)."""
    if kern_wahl == "klein" and len(annahmen) <= KLEIN_MAX:
        return _kern_klein(sat, annahmen)
    menge = set(kern)
    return [l for l in annahmen if l in menge]


def _minimiere(sat, kern, reihenfolge):
    """Kernminimierung: je Literal weglassen und mit MIN_BUDGET Konflikten erneut prüfen; bleibt es unerfüllbar, gilt der (noch kleinere) Kern des Lösers.
    Alle Konflikte zählen im Gesamtaufwand."""
    kern = [l for l in reihenfolge if l in set(kern)]
    versuche = 0
    for l in list(kern):
        if len(kern) <= 1 or versuche >= MIN_VERSUCHE:
            break
        versuch = [x for x in kern if x != l]
        versuche += 1
        r = sat.loese(versuch, MIN_BUDGET)
        if r.antwort is False:
            teil = set(r.kern) & set(versuch)
            if teil:
                kern = [x for x in versuch if x in teil]
    return kern


def _abschluss(lauf, sat, inst):
    lauf.aufrufe = sat.aufrufe
    lauf.konflikte = sat.konflikte
    lauf.klauseln = sat.klauseln
    lauf.hilfsvariablen = sat.hilfsvariablen
    return lauf


def _zeit(lauf, sat, antwort, untere, obere):
    lauf.zeitleiste.append({"aufruf": sat.aufrufe, "antwort": antwort, "untere": untere, "obere": obere, "konflikte": sat.konflikte})


def _modell_kosten(lauf, inst, r):
    lauf.modell = {v: b for v, b in r.modell.items() if v <= inst.n}
    lauf.kosten_modell = kosten(inst, r.modell)


def _anzeige(r):
    return {True: "erfüllbar", False: "unerfüllbar", None: "Budget"}[r.antwort]


# ------------------------------------------------------------------ OLL

def oll(inst: MaxSat, *, strat=False, minimiere=False, kern_wahl="loeser", call_budget=CALL_BUDGET, total_budget=TOTAL_BUDGET) -> Lauf:
    """OLL mit Gewichtsabzug (einfache Fassung nach Gedächtnis; kein Hardening, keine Core-Exhaustion, keine Diversität)."""
    name = "oll" + ("_strat" if strat else "") + ("_min" if minimiere else "")
    lauf = Lauf(name)
    sat = Sat(inst.n, inst.hart)
    gew, reihe, namen, zaehler = {}, [], {}, {}     # zaehler: Annahmeliteral -> (Ausgänge, Index k, Zählernummer): das Literal ist ¬o_{k+1}
    for i, (c, w) in enumerate(zip(inst.weich, inst.gewichte)):
        if w == 0:
            continue
        if len(c) == 1:
            lit = c[0]
        else:
            lit = sat.neu()
            sat.klausel((-lit,) + tuple(c))
        if lit not in gew:
            reihe.append(lit)
            gew[lit] = 0
            namen[lit] = f"S{i + 1}"
        else:
            namen[lit] += f"+S{i + 1}"
        gew[lit] += w
    stufen = sorted({w for w in gew.values() if w > 0}, reverse=True) if strat else [1]
    grenze = stufen[0] if stufen else 1
    lb = 0
    while True:
        if sat.konflikte >= total_budget:
            lauf.status, lauf.untere = "Abbruch", lb
            return _abschluss(lauf, sat, inst)
        annahmen = [l for l in reihe if gew[l] >= grenze and gew[l] > 0]
        r = sat.loese(annahmen, call_budget)
        _zeit(lauf, sat, _anzeige(r), lb, None)
        if r.antwort is None:
            lauf.status, lauf.untere = "Abbruch", lb
            return _abschluss(lauf, sat, inst)
        if r.antwort is True:
            tiefer = sorted({w for w in gew.values() if 0 < w < grenze}, reverse=True) if strat else []
            if tiefer:
                grenze = tiefer[0]
                continue
            lauf.optimum, lauf.untere, lauf.obere = lb, lb, lb
            _modell_kosten(lauf, inst, r)
            lauf.zeitleiste[-1]["obere"] = lauf.kosten_modell
            return _abschluss(lauf, sat, inst)
        kern = _kern_waehlen(sat, annahmen, r.kern, kern_wahl)
        if not kern:
            lauf.status, lauf.untere = "hart unerfüllbar", lb
            return _abschluss(lauf, sat, inst)
        vorher = len(kern)
        if minimiere and len(kern) > 1:
            kern = _minimiere(sat, kern, reihe)
        wmin = min(gew[l] for l in kern)
        lb += wmin
        for l in kern:
            gew[l] -= wmin
        zid = len(lauf.kerne)
        schritt = KernSchritt(zid + 1, [namen[l] for l in kern], len(kern), vorher, wmin, lb, sat.aufrufe, sat.konflikte)
        lauf.kerne.append(schritt)
        lauf.zeitleiste[-1]["untere"] = lb
        neue = []
        if len(kern) == 1:
            sat.klausel((-kern[0],))                       # Kern aus einem Literal: es wird hart verneint (die Annahme ist sicher verletzt)
        else:
            ausgaenge = totalizer(sat, [-l for l in kern], len(kern))
            neue.append((-ausgaenge[1], ausgaenge, 1, zid))    # „höchstens eine Verletzung im Kern“
        for l in kern:                                     # ein Ausgang, der selbst im Kern lag, zieht den nächsten nach (auch bei einem Kern aus einem Literal)
            if l in zaehler:
                aus, k, nr = zaehler[l]
                if k + 1 < len(aus):
                    neue.append((-aus[k + 1], aus, k + 1, nr))
        for lit, aus, k, nr in neue:
            if lit not in gew:
                reihe.append(lit)
                gew[lit] = 0
            gew[lit] += wmin
            namen[lit] = f"Z{nr}≥{k + 1}"
            zaehler[lit] = (aus, k, nr)
        if neue and len(kern) > 1:
            schritt.neu = namen[neue[0][0]]


# ------------------------------------------------------------------ Fu–Malik

def fu_malik(inst: MaxSat, *, kern_wahl="loeser", call_budget=CALL_BUDGET, total_budget=TOTAL_BUDGET) -> Lauf:
    """Fu–Malik, einfache Fassung (nach Gedächtnis), nur ungewichtet: je Kern eine neue Relaxationsvariable je Mitglied, paarweise höchstens eine davon wahr."""
    if any(w != 1 for w in inst.gewichte):
        raise ValueError("Fu–Malik ist hier nur ungewichtet")
    lauf = Lauf("fu_malik")
    sat = Sat(inst.n, inst.hart)
    sel, aktuell, namen = [], [], []
    for i, c in enumerate(inst.weich):
        aktuell.append(list(c))
        if len(c) == 1:
            sel.append(c[0])
        else:
            s = sat.neu()
            sat.klausel((-s,) + tuple(c))
            sel.append(s)
        namen.append(f"S{i + 1}")
    lb = 0
    while True:
        if sat.konflikte >= total_budget:
            lauf.status, lauf.untere = "Abbruch", lb
            return _abschluss(lauf, sat, inst)
        r = sat.loese(sel, call_budget)
        _zeit(lauf, sat, _anzeige(r), lb, None)
        if r.antwort is None:
            lauf.status, lauf.untere = "Abbruch", lb
            return _abschluss(lauf, sat, inst)
        if r.antwort is True:
            lauf.optimum, lauf.untere, lauf.obere = lb, lb, lb
            _modell_kosten(lauf, inst, r)
            lauf.zeitleiste[-1]["obere"] = lauf.kosten_modell
            return _abschluss(lauf, sat, inst)
        kern = _kern_waehlen(sat, sel, r.kern, kern_wahl)
        if not kern:
            lauf.status, lauf.untere = "hart unerfüllbar", lb
            return _abschluss(lauf, sat, inst)
        lb += 1
        index = {l: i for i, l in enumerate(sel)}
        mitglieder = [index[l] for l in kern]
        lauf.kerne.append(KernSchritt(len(lauf.kerne) + 1, [namen[i] for i in mitglieder], len(kern), len(kern), 1, lb, sat.aufrufe, sat.konflikte,
                                      "Relaxation " + ", ".join(namen[i] + "'" for i in mitglieder)))
        lauf.zeitleiste[-1]["untere"] = lb
        relax = []
        for i in mitglieder:
            b = sat.neu()
            relax.append(b)
            aktuell[i] = aktuell[i] + [b]
            s = sat.neu()
            sat.klausel([-s] + aktuell[i])
            sel[i] = s
            namen[i] += "'"
        for paar in KOD.hoechstens_eins(relax):
            sat.klausel(paar)


# ------------------------------------------------------------------ Lineare Suche (unär)

def _relaxiert(inst):
    sat = Sat(inst.n, inst.hart)
    rel = []
    for c in inst.weich:
        r = sat.neu()
        rel.append(r)
        sat.klausel(tuple(c) + (r,))
    return sat, rel


def _unaer(rel, gewichte):
    lits = []
    for r, w in zip(rel, gewichte):
        lits += [r] * w
    return lits


def lineare_suche(inst: MaxSat, richtung: str, *, call_budget=CALL_BUDGET, total_budget=TOTAL_BUDGET) -> Lauf:
    """Lineare Suche über die Kosten. `richtung` "oben": immer eine Lösung suchen, die billiger als die beste ist, bis es keine gibt; "unten": k = 0, 1, 2, …, bis erfüllbar.
    Der Zähler ist unär (jede Relaxationsvariable w-mal Eingang), sein Deckel ist die Gewichtssumme der ersten Lösung."""
    lauf = Lauf("lin_" + richtung)
    sat, rel = _relaxiert(inst)
    r = sat.loese([], call_budget)
    _zeit(lauf, sat, _anzeige(r), 0, None)
    if r.antwort is not True:
        lauf.status = "Abbruch" if r.antwort is None else "hart unerfüllbar"
        return _abschluss(lauf, sat, inst)
    ub = kosten(inst, r.modell)
    lauf.modell, lauf.kosten_modell, lauf.obere = {v: b for v, b in r.modell.items() if v <= inst.n}, ub, ub
    lauf.zeitleiste[-1]["obere"] = ub
    if ub == 0:
        lauf.optimum = 0
        return _abschluss(lauf, sat, inst)
    o = totalizer(sat, _unaer(rel, inst.gewichte), ub)
    k = 0
    while True:
        if richtung == "oben" and ub == 0:
            break
        if richtung == "unten" and k >= ub:
            break
        if sat.konflikte >= total_budget:
            lauf.status = "Abbruch"
            break
        frage = ub - 1 if richtung == "oben" else k           # „Kosten höchstens `frage`“
        r = sat.loese([-o[frage]], call_budget)                 # ¬o_{frage+1}: weniger als frage + 1 Kosten
        lauf.zeitleiste.append({"aufruf": sat.aufrufe, "antwort": _anzeige(r), "untere": lauf.untere, "obere": lauf.obere, "konflikte": sat.konflikte})
        if r.antwort is None:
            lauf.status = "Abbruch"
            break
        if richtung == "oben":
            if r.antwort is False:
                lauf.untere = ub
                break
            ub = kosten(inst, r.modell)
            lauf.modell, lauf.kosten_modell, lauf.obere = {v: b for v, b in r.modell.items() if v <= inst.n}, ub, ub
        else:
            if r.antwort is True:
                lauf.untere = k
                ub = kosten(inst, r.modell)
                lauf.modell, lauf.kosten_modell, lauf.obere = {v: b for v, b in r.modell.items() if v <= inst.n}, ub, ub
                break
            k += 1
            lauf.untere = k
        lauf.zeitleiste[-1].update(untere=lauf.untere, obere=lauf.obere)
    if lauf.status == "ok":
        lauf.optimum = ub
        lauf.untere = lauf.optimum
        lauf.zeitleiste[-1]["untere"] = lauf.optimum
    else:
        lauf.optimum = None
    return _abschluss(lauf, sat, inst)


# ------------------------------------------------------------------ Aufruf nach Namen

def laufe(inst: MaxSat, verfahren: str, *, kern_wahl="loeser", call_budget=CALL_BUDGET, total_budget=TOTAL_BUDGET) -> Lauf:
    if verfahren == "lin_oben":
        return lineare_suche(inst, "oben", call_budget=call_budget, total_budget=total_budget)
    if verfahren == "lin_unten":
        return lineare_suche(inst, "unten", call_budget=call_budget, total_budget=total_budget)
    if verfahren == "fu_malik":
        return fu_malik(inst, kern_wahl=kern_wahl, call_budget=call_budget, total_budget=total_budget)
    if verfahren in ("oll", "oll_strat", "oll_min", "oll_strat_min"):
        return oll(inst, strat="strat" in verfahren, minimiere="min" in verfahren, kern_wahl=kern_wahl, call_budget=call_budget, total_budget=total_budget)
    raise ValueError(f"unbekanntes Verfahren: {verfahren}")


# ------------------------------------------------------------------ Hilfen für das Handbeispiel und die Tests

def aufzaehlung(inst: MaxSat):
    """Optimum durch Aufzählung aller Belegungen (nur n ≤ 14): (Optimum, Liste der optimalen Belegungen als Tupel 0/1). None, wenn die harten Klauseln unerfüllbar sind."""
    if inst.n > 14:
        raise ValueError("Aufzählung nur bis n = 14")
    beste, arg = None, []
    for bits in itertools.product((False, True), repeat=inst.n):
        modell = {v + 1: b for v, b in enumerate(bits)}
        if not all(any((modell[abs(l)] if l > 0 else not modell[abs(l)]) for l in c) for c in inst.hart):
            continue
        k = kosten(inst, modell)
        if beste is None or k < beste:
            beste, arg = k, [tuple(int(b) for b in bits)]
        elif k == beste:
            arg.append(tuple(int(b) for b in bits))
    return beste, arg


def alle_minimalen_kerne(inst: MaxSat):
    """Alle minimalen Kerne der weichen Klauseln (Indizes, aufsteigend): mit den harten Klauseln unerfüllbar, jede echte Teilmenge erfüllbar. Für kleine Instanzen (bis KLEIN_MAX weiche Klauseln)."""
    if len(inst.weich) > KLEIN_MAX:
        raise ValueError("Aufzählung nur bis 14 weiche Klauseln")
    sat = Sat(inst.n, inst.hart)
    annahmen = []
    for c in inst.weich:
        if len(c) == 1:
            annahmen.append(c[0])
        else:
            s = sat.neu()
            sat.klausel((-s,) + tuple(c))
            annahmen.append(s)
    kerne = []
    for g in range(1, len(annahmen) + 1):
        for idx in itertools.combinations(range(len(annahmen)), g):
            if any(set(k) <= set(idx) for k in kerne):
                continue
            if sat.l.loese([annahmen[i] for i in idx], None).antwort is False:
                kerne.append(list(idx))
    return kerne
