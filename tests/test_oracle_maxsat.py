"""Orakel-Test maxsat-demo / maxsat: das Optimum jeder Instanz gegen zwei unabhängige Rechenwege (ORACLE-PLAYBOOK §5, DEMO-PLAYBOOK §12).

1. **Aufzählung aller Belegungen** (eigene Schleife in diesem Test, nichts aus `mxs_algorithm`): kleine Instanzen mit n ≤ 12 Variablen, ungewichtet und gewichtet.
2. **OR-Tools CP-SAT** (nur im Test-venv, nie in der App): 40 Instanzen (Kontrollpunkte, Rampen, Formeln; je ungewichtet und gewichtet), alle Verfahren.
Dazu die angezeigten Kennzahlen: Kosten des Endmodells gleich der unteren Schranke gleich dem Optimum, jede Zeitleiste der unteren Schranke monoton, jeder Kern aus
weichen Klauseln unabhängig als unerfüllbar bestätigt, Eigenschaften (Gewichte × c, Reihenfolge der weichen Klauseln, OLL-Schranke gleich Fu–Malik-Schranke).
Der große Lauf (1.056 Läufe, 0 Abweichungen) stand im Scratch-Ordner, nicht im Repo."""

import itertools

import pytest

import mxs_algorithm as A
import mxs_scenario as S

ALLE_UNGEWICHTET = ("lin_oben", "lin_unten", "fu_malik", "oll", "oll_strat", "oll_min", "oll_strat_min")
ALLE_GEWICHTET = tuple(v for v in ALLE_UNGEWICHTET if v != "fu_malik")


def _erfuellt(c, bits):
    return any(bits[abs(l) - 1] == (l > 0) for l in c)


def _aufzaehlung(inst):
    """Eigener Orakelweg: Optimum durch Aufzählung aller 2^n Belegungen (None: harte Klauseln unerfüllbar)."""
    beste = None
    for bits in itertools.product((False, True), repeat=inst.n):
        if all(_erfuellt(c, bits) for c in inst.hart):
            k = sum(w for c, w in zip(inst.weich, inst.gewichte) if not _erfuellt(c, bits))
            beste = k if beste is None else min(beste, k)
    return beste


def _cpsat(inst):
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")
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
    assert s.Solve(m) == cp_model.OPTIMAL
    return int(round(s.ObjectiveValue()))


def _kleine_instanzen():
    out = []
    for seed in range(100, 104):
        out += [S.kontrollpunkte(12, 3.0, seed), S.formel(10, 6, seed), S.formel(9, 8, seed)]
    return out


def _alle_instanzen():
    """40 Instanzen: 3 Familien × 4 Zufalls-Seeds × ungewichtet/gewichtet (1 bis 10) plus 3 Familien × 4 Seeds mit Gewichten 1 bis 3."""
    out = []
    for seed in range(100, 104):
        basis = [S.kontrollpunkte(16, 3.0, seed), S.rampen(10, 4.0, seed), S.formel(12, 6, seed)]
        out += basis + [S.mit_gewichten(b, seed) for b in basis]
    out += [S.mit_gewichten(S.kontrollpunkte(16, 3.0, s), s, 1, 3) for s in range(100, 104)]
    out += [S.mit_gewichten(S.kontrollpunkte(16, 3.0, s), s, 1, 3) for s in range(100, 104)]
    out += [S.mit_gewichten(S.formel(12, 6, s), s, 1, 3) for s in range(100, 104)]
    out += [S.mit_gewichten(S.rampen(10, 4.0, s), s, 1, 3) for s in range(100, 104)]
    return out


def test_aufzaehlung_des_orakels_am_handbeispiel(hand, hand_gewichtet):
    assert _aufzaehlung(hand) == 3 and _aufzaehlung(hand_gewichtet) == 4       # Handrechnung


def test_optimum_gegen_aufzaehlung_alle_verfahren_ungewichtet_und_gewichtet():
    for inst in _kleine_instanzen() + [S.mit_gewichten(i, 7) for i in _kleine_instanzen()]:
        ref = _aufzaehlung(inst)
        gewichtet = any(g != 1 for g in inst.gewichte)
        for v in (ALLE_GEWICHTET if gewichtet else ALLE_UNGEWICHTET):
            r = A.laufe(inst, v)
            assert r.status == "ok" and r.optimum == ref, (inst.meta, v)


def test_optimum_gegen_cpsat_40_instanzen_alle_varianten():
    instanzen = _alle_instanzen()
    assert len(instanzen) == 40
    for inst in instanzen:
        ref = _cpsat(inst)
        gewichtet = any(g != 1 for g in inst.gewichte)
        for v in (ALLE_GEWICHTET if gewichtet else ALLE_UNGEWICHTET):
            for kern_wahl in ("loeser",) + (("klein",) if v.startswith(("oll", "fu")) and len(inst.weich) <= 12 else ()):
                r = A.laufe(inst, v, kern_wahl=kern_wahl)
                assert r.status == "ok" and r.optimum == ref, (inst.meta, v, kern_wahl, r.optimum, ref)
                # angezeigte Kennzahlen: Kosten des Endmodells = untere Schranke = Optimum, harte Klauseln erfüllt
                assert r.kosten_modell == ref and r.untere == ref and r.obere == ref, (inst.meta, v)
                assert S.hart_erfuellt(inst, r.modell) and S.kosten(inst, r.modell) == ref


def test_untere_schranke_monoton_und_nie_ueber_dem_optimum():
    for inst in _alle_instanzen()[:12]:
        ref = _aufzaehlung(inst) if inst.n <= 12 else _cpsat(inst)
        for v in ("lin_oben", "lin_unten", "fu_malik", "oll", "oll_min") if all(g == 1 for g in inst.gewichte) else ("oll", "oll_strat", "lin_unten"):
            r = A.laufe(inst, v)
            untere = [e["untere"] for e in r.zeitleiste]
            assert untere == sorted(untere) and max(untere) <= ref, (inst.meta, v)
            assert [k.untere for k in r.kerne] == sorted(k.untere for k in r.kerne) and (not r.kerne or r.kerne[-1].untere <= ref)


def test_jeder_kern_aus_weichen_klauseln_ist_unabhaengig_unerfuellbar():
    """Kerne, deren Mitglieder nur S<i> sind (keine Zähler, keine Relaxationen): mit den harten Klauseln gibt es keine Belegung (Aufzählung)."""
    for inst in _kleine_instanzen()[:8]:
        for v in ("fu_malik", "oll", "oll_min"):
            for kern in A.laufe(inst, v).kerne:
                if all(m.startswith("S") and m[1:].isdigit() for m in kern.mitglieder):
                    idx = [int(m[1:]) - 1 for m in kern.mitglieder]
                    assert not any(all(_erfuellt(c, bits) for c in inst.hart) and all(_erfuellt(inst.weich[i], bits) for i in idx)
                                   for bits in itertools.product((False, True), repeat=inst.n)), (inst.meta, v, kern.mitglieder)


def test_gewichte_mal_c_ergibt_optimum_mal_c_und_die_gleichen_kerne():
    for seed in range(100, 104):
        a = S.mit_gewichten(S.kontrollpunkte(14, 3.0, seed), seed)
        for c in (2, 7):
            b = a._replace(gewichte=[c * g for g in a.gewichte])
            ra, rb = A.laufe(a, "oll"), A.laufe(b, "oll")
            assert rb.optimum == c * ra.optimum
            assert [k.mitglieder for k in ra.kerne] == [k.mitglieder for k in rb.kerne]


def test_reihenfolge_der_weichen_klauseln_aendert_das_optimum_nie():
    for seed in range(100, 106):
        inst = S.mit_gewichten(S.formel(10, 6, seed), seed)
        ref = _aufzaehlung(inst)
        for ordnung in (list(range(len(inst.weich)))[::-1], list(range(0, len(inst.weich), 2)) + list(range(1, len(inst.weich), 2))):
            neu = inst._replace(weich=[inst.weich[i] for i in ordnung], gewichte=[inst.gewichte[i] for i in ordnung])
            assert A.laufe(neu, "oll").optimum == ref == A.laufe(neu, "oll_strat").optimum


def test_oll_schranke_gleich_fu_malik_schranke_am_ende():
    for inst in _kleine_instanzen():
        assert A.laufe(inst, "oll").untere == A.laufe(inst, "fu_malik").untere == _aufzaehlung(inst)
