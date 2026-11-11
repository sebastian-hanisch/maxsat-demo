"""Szenario: partielle MaxSAT-Instanzen (harte und weiche Klauseln, Gewichte) aus festen Zufalls-Seeds.

Drei Familien, alle über den ganzzahligen SplitMix64 (`mxs_rng`, nie Python-`random`):

* **Kontrollpunkte (Vertex Cover):** Konfliktgraph aus Aufträgen mit Unverträglichkeiten; hart: jede Kante hat an mindestens einem Ende einen Kontrollpunkt;
  weich: „Auftrag i bekommt keinen Kontrollpunkt“ (Kosten = Zahl der Kontrollpunkte). Kerne haben zwei Literale.
* **Rampen (3-Färbung mit möglichst wenigen verletzten Kanten):** hart: jeder Auftrag genau eine Rampe; weich: „Kante j ist farbverträglich“
  (Kosten = Zahl der Kanten mit zwei Aufträgen auf derselben Rampe). Kerne sind groß (zusammenhängende Teilgraphen).
* **Überbestimmte Formel (Zufalls-3-SAT):** keine harte Klausel, jede Klausel weich (Kosten = Zahl der verletzten Klauseln).

Eine Instanz ist `MaxSat(n, hart, weich, gewichte, meta)`; Kosten = Summe der Gewichte der verletzten weichen Klauseln. Das Handbeispiel (drei Variablen,
sechs weiche Klauseln) ist von Hand nachrechenbar.
"""

from typing import NamedTuple

import mxs_instanzen as I
from mxs_rng import SplitMix64


class MaxSat(NamedTuple):
    n: int
    hart: list
    weich: list
    gewichte: list
    meta: dict


GEWICHT_MIN, GEWICHT_MAX = 1, 10


def handbeispiel(gewichte=None) -> MaxSat:
    """Variablen x1, x2, x3; hart: höchstens eine wahr; weich: S1 = x1, S2 = x2, S3 = x3, S4 = ¬x1, S5 = ¬x2, S6 = ¬x3."""
    hart = [(-1, -2), (-1, -3), (-2, -3)]
    weich = [(1,), (2,), (3,), (-1,), (-2,), (-3,)]
    g = list(gewichte) if gewichte is not None else [1] * 6
    return MaxSat(3, hart, weich, g, {"art": "handbeispiel", "name": "Handbeispiel"})


def kontrollpunkte(n: int, grad: float, seed: int) -> MaxSat:
    """Vertex-Cover-Minimierung auf einem Zufallsgraphen mit n Knoten und mittlerem Grad `grad`. Variable i + 1 = „Auftrag i kontrolliert“."""
    kanten = I.zufallskanten(n, int(round(n * grad / 2)), seed)
    return MaxSat(n, [(a + 1, b + 1) for a, b in kanten], [(-(i + 1),) for i in range(n)], [1] * n,
                  {"art": "kontrollpunkte", "n_knoten": n, "grad": grad, "seed": seed, "kanten": kanten})


def rampen(n: int, grad: float, seed: int, k: int = 3) -> MaxSat:
    """k-Färbung mit möglichst wenigen verletzten Kanten. Variable i·k + c + 1 = „Auftrag i auf Rampe c“; danach je Kante eine Variable „farbverträglich“."""
    kanten = I.zufallskanten(n, int(round(n * grad / 2)), seed)

    def x(i, c):
        return i * k + c + 1

    hart = []
    for i in range(n):
        hart.append(tuple(x(i, c) for c in range(k)))
        for c in range(k):
            for d in range(c + 1, k):
                hart.append((-x(i, c), -x(i, d)))
    weich = []
    nv = n * k
    for a, b in kanten:
        nv += 1
        for c in range(k):
            hart.append((-nv, -x(a, c), -x(b, c)))
        weich.append((nv,))
    return MaxSat(nv, hart, weich, [1] * len(weich), {"art": "rampen", "n_knoten": n, "grad": grad, "seed": seed, "k": k, "kanten": kanten})


def formel(n: int, verhaeltnis: int, seed: int) -> MaxSat:
    """Überbestimmte Zufalls-3-SAT: m = n·verhaeltnis Klauseln, alle weich, keine hart."""
    inst = I.rand3(n, n * verhaeltnis, seed)
    return MaxSat(n, [], list(inst.klauseln), [1] * len(inst.klauseln), {"art": "formel", "n_knoten": n, "verhaeltnis": verhaeltnis, "seed": seed})


def mit_gewichten(inst: MaxSat, seed: int, lo: int = GEWICHT_MIN, hi: int = GEWICHT_MAX) -> MaxSat:
    """Gleichverteilte ganze Gewichte lo..hi je weiche Klausel (Zufalls-Seed 31·seed + 7, SplitMix64)."""
    rng = SplitMix64(31 * seed + 7)
    return inst._replace(gewichte=[lo + rng.below(hi - lo + 1) for _ in inst.weich], meta=dict(inst.meta, gewichtet=True, gewicht_hi=hi))


def erzeuge(art: str, n: int, seed: int, gewicht_hi: int = 1) -> MaxSat:
    """Die Instanz der App und der Messreihen: Familie `art` ("kontrollpunkte", "rampen", "formel") mit ihrem festen Parameter (Grad 3 bzw. 5, sechs Klauseln je Variable),
    Größe n, Zufalls-Seed; `gewicht_hi` > 1 gibt gleichverteilte Gewichte 1 … gewicht_hi, 1 lässt alle Gewichte 1."""
    if art == "kontrollpunkte":
        basis = kontrollpunkte(n, 3.0, seed)
    elif art == "rampen":
        basis = rampen(n, 5.0, seed)
    elif art == "formel":
        basis = formel(n, 6, seed)
    else:
        raise ValueError(f"unbekannte Familie: {art}")
    return mit_gewichten(basis, seed, 1, gewicht_hi) if gewicht_hi > 1 else basis


def ohne_gewichte(inst: MaxSat) -> MaxSat:
    return inst._replace(gewichte=[1] * len(inst.weich))


def kosten(inst: MaxSat, modell: dict) -> int:
    """Summe der Gewichte der verletzten weichen Klauseln unter `modell` (Variable -> bool). Unabhängig vom Löser."""
    return sum(w for c, w in zip(inst.weich, inst.gewichte) if not any((modell[abs(l)] if l > 0 else not modell[abs(l)]) for l in c))


def hart_erfuellt(inst: MaxSat, modell: dict) -> bool:
    return I.pruefe_modell(inst.hart, modell)


def beschreibung(inst: MaxSat) -> str:
    m = inst.meta
    art = m.get("art")
    if art == "handbeispiel":
        return "Handbeispiel: drei Variablen, höchstens eine wahr, sechs weiche Klauseln"
    if art == "kontrollpunkte":
        return f"Kontrollpunkte: {m['n_knoten']} Aufträge, {len(m['kanten'])} Unverträglichkeiten (mittlerer Grad {str(m['grad']).replace('.', ',')}), Zufalls-Seed {m['seed']}"
    if art == "rampen":
        return f"Rampen: {m['n_knoten']} Aufträge auf {m['k']} Rampen, {len(m['kanten'])} Konflikte (mittlerer Grad {str(m['grad']).replace('.', ',')}), Zufalls-Seed {m['seed']}"
    return f"Überbestimmte Formel: {m['n_knoten']} Variablen, {len(inst.weich)} Klauseln (Verhältnis {m['verhaeltnis']}), Zufalls-Seed {m['seed']}"
