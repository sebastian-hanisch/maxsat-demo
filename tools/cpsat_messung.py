"""Messskript des eingefrorenen Maßstabs: schreibt `mxs_cpsat.json` (OR-Tools CP-SAT auf denselben Instanzen wie `mxs_messungen.json`).

Aufruf (aus dem Repo-Ordner, mit dem Test-venv; braucht OR-Tools, nur hier und in den Tests, nie in der App):
    python tools/cpsat_messung.py [--zelle rampen|40|u] [--out datei.json]      # ohne Angaben: alle Zellen nach mxs_cpsat.json
    python tools/cpsat_messung.py --zusammen teil_*.json                          # Teilergebnisse (je --zelle --out) zusammenfassen

Je Instanz ein Arbeiter und 15 Sekunden Zeitlimit; festgehalten werden das bewiesene Optimum (oder None), die Konflikte des Lösers und der Status. Die Konflikte
eines Laufs, der das Zeitlimit erreicht, sind eine untere Schranke. Die Zahlen sind vorgerechnet, nicht live: die App rechnet nie mit OR-Tools. Die Optima dienen
außerdem als Referenz für die Antworten der vier Verfahren (Tests und Messdatei).
"""

import argparse
import json
import sys
from pathlib import Path

from ortools import __version__ as ORTOOLS_VERSION
from ortools.sat.python import cp_model

HIER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))

import mxs_constants as C  # noqa: E402
import mxs_scenario as S  # noqa: E402
from messungen import alle_zellen, instanz  # noqa: E402

DATUM = "2026-11-11"


def cpsat(inst: S.MaxSat, zeitlimit: float = C.CPSAT_ZEITLIMIT) -> dict:
    """Minimierung der Gewichtssumme der verletzten weichen Klauseln (jede weiche Klausel mit einer Verletzungsvariablen)."""
    m = cp_model.CpModel()
    x = [None] + [m.NewBoolVar(f"x{i}") for i in range(1, inst.n + 1)]

    def lit(l):
        return x[l] if l > 0 else x[-l].Not()

    for c in inst.hart:
        m.AddBoolOr([lit(l) for l in c])
    vs = []
    for c in inst.weich:
        v = m.NewBoolVar("v")
        m.AddBoolOr([lit(l) for l in c] + [v])
        vs.append(v)
    m.Minimize(sum(w * v for w, v in zip(inst.gewichte, vs)))
    s = cp_model.CpSolver()
    s.parameters.num_workers = 1
    s.parameters.max_time_in_seconds = zeitlimit
    r = s.Solve(m)
    ok = r == cp_model.OPTIMAL
    return {"optimum": int(round(s.ObjectiveValue())) if ok else None, "konflikte": int(s.NumConflicts()), "status": "ok" if ok else "Abbruch"}


def messe_zelle(art: str, n: int, gewichtet: bool) -> dict:
    out = {}
    for seed in C.SEEDS:
        out[str(seed)] = cpsat(instanz(art, n, seed, gewichtet))
        print(f"  {art} n={n} {'g' if gewichtet else 'u'} Seed {seed}: {out[str(seed)]}", flush=True)
    return {"instanzen": out}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--zelle")
    p.add_argument("--out")
    p.add_argument("--zusammen", nargs="*")
    a = p.parse_args()
    if a.zusammen:
        zellen = {}
        for f in a.zusammen:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
            zellen[d["schluessel"].strip()] = d["zelle"]
        ordnung = {C.zellenschluessel(*z): i for i, z in enumerate(alle_zellen())}
        daten = {"version": 1, "ortools": ORTOOLS_VERSION, "arbeiter": 1, "zeitlimit_s": C.CPSAT_ZEITLIMIT, "datum": DATUM, "messskript": "tools/cpsat_messung.py",
                 "zellen": {k: zellen[k] for k in sorted(zellen, key=lambda k: ordnung[k])}}
        (HIER / C.CPSAT_DATEI).write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
        print("geschrieben:", C.CPSAT_DATEI, len(zellen), "Zellen")
        return
    ziele = [a.zelle] if a.zelle else [C.zellenschluessel(*z) for z in alle_zellen()]
    for schluessel in ziele:
        schluessel = schluessel.strip()
        art, n, g = schluessel.split("|")
        z = messe_zelle(art, int(n), g == "g")
        out = Path(a.out) if a.out else HIER / f"teil_cpsat_{art}_{n}_{g}.json"
        out.write_text(json.dumps({"schluessel": schluessel, "zelle": z}, ensure_ascii=False), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
