"""Messskript der vorgerechneten Messreihen: schreibt `mxs_messungen.json` (zehn feste Instanzen je Zelle, alle Verfahren).

Aufruf (aus dem Repo-Ordner, mit dem Test-venv oder dem Laufzeit-venv; ohne OR-Tools):
    python tools/messungen.py --liste                       # alle Zellen
    python tools/messungen.py --zelle rampen|40|u --out teil_rampen_40_u.json
    python tools/messungen.py --zusammen teil_*.json        # fasst die Teilergebnisse zu mxs_messungen.json zusammen

Je Zelle laufen die Verfahren `C.MESSVERFAHREN_*` auf den Instanzen mit den Zufalls-Seeds `C.SEEDS` (SplitMix64, auf jeder Plattform dieselben Instanzen) mit
10.000 Konflikten je SAT-Aufruf und 30.000 Konflikten je Verfahren und Instanz (ein Abbruch zählt mit diesem Wert und ist nur eine untere Schranke).
Gemessen wird in Konflikten und SAT-Aufrufen, nie in Sekunden. Die Instanzen der Messreihe sind dieselben wie die der App bei dem jeweiligen Zufalls-Seed.
"""

import argparse
import json
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))

import mxs_algorithm as A  # noqa: E402
import mxs_constants as C  # noqa: E402
import mxs_scenario as S  # noqa: E402



def instanz(art: str, n: int, seed: int, gewichtet: bool) -> S.MaxSat:
    param = C.FAMILIE_PARAM[art]
    if art == "kontrollpunkte":
        basis = S.kontrollpunkte(n, param, seed)
    elif art == "rampen":
        basis = S.rampen(n, param, seed)
    else:
        basis = S.formel(n, param, seed)
    return S.mit_gewichten(basis, seed) if gewichtet else basis


def verfahren_der_zelle(art: str, n: int, gewichtet: bool) -> tuple:
    if not gewichtet:
        return C.MESSVERFAHREN_UNGEWICHTET
    return (C.MESSVERFAHREN_GEWICHTET_LINEAR + C.MESSVERFAHREN_GEWICHTET) if art == "kontrollpunkte" and n in (20, 30) else C.MESSVERFAHREN_GEWICHTET


def zusammenfassung(lauf: A.Lauf) -> dict:
    return {"optimum": lauf.optimum, "status": lauf.status, "aufrufe": lauf.aufrufe, "konflikte": lauf.konflikte, "untere": lauf.untere,
            "kerne": lauf.kerngroessen, "kerne_vor": [k.vor_minimierung for k in lauf.kerne], "klauseln": lauf.klauseln, "hilfsvariablen": lauf.hilfsvariablen,
            "kosten_modell": lauf.kosten_modell}


def messe_zelle(art: str, n: int, gewichtet: bool, aus=None) -> dict:
    zelle = {"art": art, "n": n, "gewichtet": gewichtet, "param": C.FAMILIE_PARAM[art], "instanzen": []}
    for seed in C.SEEDS:
        inst = instanz(art, n, seed, gewichtet)
        eintrag = {"seed": seed, "weich": len(inst.weich), "gewichtssumme": sum(inst.gewichte), "laeufe": {}}
        for v in verfahren_der_zelle(art, n, gewichtet):
            t0 = time.time()
            lauf = A.laufe(inst, v, call_budget=C.CALL_BUDGET_MAX, total_budget=C.BUDGET_REFERENZ)
            eintrag["laeufe"][v] = zusammenfassung(lauf)
            print(f"  {art} n={n} {'g' if gewichtet else 'u'} Seed {seed} {v}: Optimum {lauf.optimum} {lauf.status}, {lauf.konflikte} Konflikte, {time.time() - t0:.1f} s", flush=True)
        zelle["instanzen"].append(eintrag)
        if aus is not None:
            aus(zelle)
    return zelle


def alle_zellen() -> list:
    return [(a, n, False) for a, n in C.ZELLEN_UNGEWICHTET] + [(a, n, True) for a, n in C.ZELLEN_GEWICHTET]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--liste", action="store_true")
    p.add_argument("--zelle")
    p.add_argument("--out")
    p.add_argument("--zusammen", nargs="*")
    a = p.parse_args()
    if a.liste:
        for art, n, g in alle_zellen():
            print(C.zellenschluessel(art, n, g))
        return
    if a.zelle:
        art, n, g = a.zelle.split("|")
        out = Path(a.out or f"teil_{art}_{n}_{g}.json")

        def schreibe(z):
            out.write_text(json.dumps({"schluessel": a.zelle, "zelle": z}, ensure_ascii=False), encoding="utf-8", newline="\n")
        z = messe_zelle(art, int(n), g == "g", schreibe)
        schreibe(z)
        return
    if a.zusammen:
        zellen = {}
        for f in a.zusammen:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
            assert len(d["zelle"]["instanzen"]) == len(C.SEEDS), (f, "unvollständig")
            zellen[d["schluessel"]] = d["zelle"]
        ordnung = {C.zellenschluessel(*z): i for i, z in enumerate(alle_zellen())}
        zellen = {k: zellen[k] for k in sorted(zellen, key=lambda k: ordnung[k])}
        daten = {"version": 1, "seeds": list(C.SEEDS), "budget_je_aufruf": C.CALL_BUDGET_MAX, "budget_gesamt": C.BUDGET_REFERENZ,
                 "messskript": "tools/messungen.py", "zellen": zellen}
        (HIER / C.MESSUNGEN_DATEI).write_text(json.dumps(daten, ensure_ascii=False, indent=None, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
        print("geschrieben:", C.MESSUNGEN_DATEI, len(zellen), "Zellen")


if __name__ == "__main__":
    main()
