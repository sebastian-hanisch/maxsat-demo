"""Claims: jede Zahl der README-Tabelle „Befunde“ (DEMO-PLAYBOOK §4, §11a).

Drei Quellen: (1) die vorgerechneten Messreihen `mxs_messungen.json` (Budget 30.000 Konflikte je Verfahren und Instanz, 10 feste Instanzen je Zelle; die erwarteten Werte
stehen unten als Tabellen, damit eine stille Änderung der Datei auffällt), (2) der eingefrorene CP-SAT-Maßstab `mxs_cpsat.json`, (3) Neumessung billiger Zellen gegen die Datei
(die Instanzen kommen aus SplitMix64 und sind auf jeder Plattform dieselben). Nicht hier stehen die Verfahren-Handwerte (test_algorithm.py) und die Orakel (test_oracle_maxsat.py).
Alle Zahlen sind Mediane über zehn Instanzen (Konflikte, Abbruch zählt mit 30.000); Zeiten kommen nirgends vor."""

import pytest

import mxs_algorithm as A
import mxs_constants as C
import mxs_evaluation as E
import mxs_scenario as S

# Zelle -> (OLL, lineare Suche von oben, von unten, Fu–Malik, OLL + Kernminimierung); Konflikte im Median. @@ungewichtet@@
U = {
    "kontrollpunkte|20|u": (1.5, 39.5, 55, 3.5, 1),
    "kontrollpunkte|30|u": (1, 121, 211.5, 4, 0.5),
    "kontrollpunkte|50|u": (1, 1839.5, 2629.5, 25.5, 3.5),
    "rampen|40|u": (254, 443, 365, 284.5, 520),
    "rampen|60|u": (380.5, 809.5, 504.5, 980, 1093.5),
    "rampen|90|u": (16504.5, 18264.5, 17856, 30000, 20742.5),
    "formel|40|u": (2797, 17179.5, 2386, 18551.5, 5548),
}
# Zelle -> Abbrüche (OLL, von oben, von unten, Fu–Malik, OLL + Kernminimierung)
U_ABBRUECHE = {
    "kontrollpunkte|20|u": (0, 0, 0, 0, 0), "kontrollpunkte|30|u": (0, 0, 0, 0, 0), "kontrollpunkte|50|u": (0, 0, 0, 0, 0),
    "rampen|40|u": (0, 0, 0, 1, 0), "rampen|60|u": (0, 0, 0, 2, 0), "rampen|90|u": (5, 5, 5, 6, 5), "formel|40|u": (0, 3, 0, 5, 0),
}
# Zelle -> (OLL, OLL + Stratifizierung, OLL + Stratifizierung + Kernminimierung), Konflikte im Median; Gewichte 1 bis 10
G = {
    "kontrollpunkte|20|g": (0, 0, 0.5), "kontrollpunkte|30|g": (0, 1, 1), "kontrollpunkte|50|g": (0.5, 1, 1.5),
    "rampen|40|g": (192.5, 116, 347), "rampen|60|g": (508.5, 353.5, 1465), "formel|40|g": (5522.5, 1286.5, 2660.5),
}
# Zelle -> CP-SAT (Konflikte im Median, Abbrüche am Zeitlimit von 15 Sekunden)
CPS = {
    "kontrollpunkte|20|u": (0, 0), "kontrollpunkte|30|u": (2.5, 0), "kontrollpunkte|50|u": (20.5, 0), "rampen|40|u": (1653.5, 0), "rampen|60|u": (2653, 0),
    "rampen|90|u": (193899, 5), "formel|40|u": (33529.5, 0),
    "kontrollpunkte|20|g": (1.5, 0), "kontrollpunkte|30|g": (3.5, 0), "kontrollpunkte|50|g": (168, 0), "rampen|40|g": (365.5, 0), "rampen|60|g": (1165, 0), "formel|40|g": (6001.5, 0),
}
# Zelle -> (Optimum Minimum, Median, Maximum) über die zehn Instanzen (Referenzoptimum)
OPT = {
    "kontrollpunkte|20|u": (8, 9.5, 11), "kontrollpunkte|30|u": (12, 14, 16), "kontrollpunkte|50|u": (23, 24, 26), "rampen|40|u": (0, 2.5, 4), "rampen|60|u": (1, 2, 3),
    "rampen|90|u": (2, 2, 3), "formel|40|u": (2, 3, 5), "kontrollpunkte|20|g": (35, 50, 66), "kontrollpunkte|30|g": (51, 66.5, 89), "kontrollpunkte|50|g": (111, 116.5, 154),
    "rampen|40|g": (0, 6, 9), "rampen|60|g": (2, 5, 7), "formel|40|g": (4, 10, 16),
}


@pytest.fixture(scope="module")
def M():
    return E.lade_messungen()["zellen"]


@pytest.fixture(scope="module")
def P():
    return E.lade_cpsat()["zellen"]


def _kz(M, P, key):
    return E.alle_kennzahlen(M[key], E.referenzoptima(M[key], P[key]))


# --- Aufbau der Dateien --------------------------------------------------------------------------------------------------------------------

def test_messdatei_hat_alle_13_zellen_mit_je_zehn_instanzen_und_den_festen_seeds(M, P):
    assert set(M) == set(U) | set(G) == set(P)
    assert E.lade_messungen()["seeds"] == list(range(100, 110)) and E.lade_messungen()["budget_gesamt"] == 30_000
    for z in M.values():
        assert [i["seed"] for i in z["instanzen"]] == list(range(100, 110))


# --- Antworten ------------------------------------------------------------------------------------------------------------------------------

def test_claim_keine_falsche_antwort_in_532_beendeten_laeufen(M, P):
    """Von 570 Läufen (13 Zellen × 10 Instanzen × 3 bis 5 Verfahren) erreichen 38 das Budget; die übrigen 532 liefern das Referenzoptimum (CP-SAT; bewiesen bei 125 von 130
    Instanzen, die 5 übrigen sind Rampen n = 90, bei denen auch kein Verfahren beendet hat) und ein Endmodell, dessen Kosten gleich der unteren Schranke sind."""
    gesamt = beendet = 0
    for k, z in M.items():
        ref = E.referenzoptima(z, P[k])
        assert len(ref) == (5 if k == "rampen|90|u" else 10), k           # Rampen n = 90: 5 Instanzen ohne Beweis von CP-SAT und ohne beendeten Lauf
        for i in z["instanzen"]:
            for v, l in i["laeufe"].items():
                gesamt += 1
                if l["status"] == "ok":
                    beendet += 1
                    assert l["optimum"] == ref[i["seed"]] and l["untere"] == l["optimum"] and l["kosten_modell"] == l["optimum"], (k, i["seed"], v)
                else:
                    assert l["status"] == "Abbruch" and l["optimum"] is None and l["untere"] <= ref.get(i["seed"], l["untere"])
    assert (gesamt, beendet) == (570, 532)
    assert sum(E.alle_kennzahlen(z, E.referenzoptima(z, P[k]))[v].falsche for k, z in M.items() for v in E.alle_kennzahlen(z)) == 0


def test_claim_cpsat_beweist_125_von_130_instanzen_und_die_optima_der_zellen(M, P):
    assert sum(1 for k in P for e in P[k]["instanzen"].values() if e["status"] == "ok") == 125
    assert E.lade_cpsat()["zeitlimit_s"] == 15 and E.lade_cpsat()["arbeiter"] == 1
    for k, (lo, med, hi) in OPT.items():
        ref = sorted(E.referenzoptima(M[k], P[k]).values())
        assert (ref[0], E.median(ref), ref[-1]) == (lo, med, hi), k


# --- Kerngröße entscheidet -------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("key", list(U))
def test_claim_ungewichtete_zellen_konflikte_im_median_und_abbrueche(M, P, key):
    kz = _kz(M, P, key)
    assert tuple(kz[v].median for v in ("oll", "lin_oben", "lin_unten", "fu_malik", "oll_min")) == U[key]
    assert tuple(kz[v].abbrueche for v in ("oll", "lin_oben", "lin_unten", "fu_malik", "oll_min")) == U_ABBRUECHE[key]


def test_claim_kontrollpunkte_kerne_aus_zwei_literalen_und_ein_bis_zwei_konflikte(M, P):
    """Kontrollpunkte n = 20, 30, 50: die Kerne haben im Median 2 Literale, OLL braucht im Median höchstens 1,5 Konflikte (höchstens 9 in einer Instanz),
    die beste lineare Suche mindestens 39,5 Konflikte; OLL braucht höchstens ein Zehntel (Medianverhältnis 26 bis 1.840)."""
    for n in (20, 30, 50):
        key = f"kontrollpunkte|{n}|u"
        kz = _kz(M, P, key)
        assert kz["oll"].kern == 2 and kz["fu_malik"].kern == 2 and kz["oll"].maximum <= 9
        best = min(kz["lin_oben"].median, kz["lin_unten"].median)
        assert best >= 39.5 and best / max(kz["oll"].median, 1) >= C.SCHWELLE_GROESSENORDNUNG
        assert E.verdict_verfahren(kz)[0] == "success"
    assert [round(min(U[f"kontrollpunkte|{n}|u"][1:3]) / max(U[f"kontrollpunkte|{n}|u"][0], 1)) for n in (20, 30, 50)] == [26, 121, 1840]


def test_claim_grosse_kerne_rampen_und_formel_oll_ungefaehr_gleichauf_mit_der_linearen_suche(M, P):
    """Rampen n = 40 und 60 (Kerne aus 25 und 61 Literalen): OLL hat das 1,4- bzw. 1,3-Fache weniger Konflikte als die beste lineare Suche (unten), Rampen n = 90 und Formel n = 40
    (Kerne aus 73 und 70 Literalen) liegen innerhalb des Faktors 1,25; Formel: die lineare Suche von unten braucht 2.386 gegen 2.797 bei OLL, also weniger als OLL."""
    erwartet = {"rampen|40|u": ("info", 25, 1.4), "rampen|60|u": ("info", 61, 1.3), "rampen|90|u": ("info", 73, 1.1), "formel|40|u": ("info", 70, 0.9)}
    for key, (art, kern, verhaeltnis) in erwartet.items():
        kz = _kz(M, P, key)
        assert E.verdict_verfahren(kz)[0] == art and kz["oll"].kern == kern
        assert round(min(kz["lin_oben"].median, kz["lin_unten"].median) / kz["oll"].median, 1) == verhaeltnis
    assert "ungefähr gleichauf" in E.verdict_verfahren(_kz(M, P, "rampen|90|u"))[1] and "ungefähr gleichauf" in E.verdict_verfahren(_kz(M, P, "formel|40|u"))[1]
    assert "ungefähr gleichauf" not in E.verdict_verfahren(_kz(M, P, "rampen|40|u"))[1]


def test_claim_oll_bricht_nicht_oefter_ab_als_die_lineare_suche_und_bei_formeln_seltener(M, P):
    """Abbrüche je Zelle (von 10): OLL nie mehr als die lineare Suche von oben; Formel n = 40: OLL 0, von oben 3, von unten 0, Fu–Malik 5."""
    for key in U:
        o, oben, unten, fm, mn = U_ABBRUECHE[key]
        assert o <= oben and o <= fm, key
    assert U_ABBRUECHE["formel|40|u"][:4] == (0, 3, 0, 5)
    assert sum(U_ABBRUECHE[k][0] for k in U) == 5 and sum(U_ABBRUECHE[k][3] for k in U) == 14


def test_claim_oll_gegen_fu_malik(M, P):
    """Medianvergleich: OLL braucht in allen 7 Zellen weniger Konflikte als Fu–Malik; je Instanz in 52 von 70 weniger, in 13 gleich viele, in 5 mehr; die Kerne von OLL sind in 4 der 7 Zellen
    kleiner (Rampen und Formel: 25 gegen 47, 61 gegen 77,25, 73 gegen 119,5, 70 gegen 158,5 Literale), in den 3 Kontrollpunkt-Zellen gleich (2)."""
    weniger = gleich = mehr = 0
    for key in U:
        assert U[key][0] < U[key][3], key
        w, g, m = E.vergleich_je_instanz(M[key], "fu_malik", "oll")
        weniger, gleich, mehr = weniger + w, gleich + g, mehr + m
    assert (weniger, gleich, mehr) == (52, 13, 5)
    kerne = {k: (_kz(M, P, k)["oll"].kern, _kz(M, P, k)["fu_malik"].kern) for k in U}
    assert [k for k, (o, f) in kerne.items() if o < f] == ["rampen|40|u", "rampen|60|u", "rampen|90|u", "formel|40|u"]
    assert [k for k, (o, f) in kerne.items() if o == f] == ["kontrollpunkte|20|u", "kontrollpunkte|30|u", "kontrollpunkte|50|u"]
    assert kerne["rampen|40|u"] == (25, 47) and kerne["rampen|60|u"] == (61, 77.25) and kerne["rampen|90|u"] == (73, 119.5) and kerne["formel|40|u"] == (70, 158.5)


# --- Gewichte --------------------------------------------------------------------------------------------------------------------------

def test_claim_unaerer_zaehler_kostet_das_zwanzigfache_an_klauseln(M, P):
    """Kontrollpunkte n = 20 und 30: die lineare Suche braucht gewichtet im Median 6.542 bzw. 13.317,5 Klauseln statt 328 bzw. 658 (das 19,9- bzw. 20,2-Fache)."""
    for n, u, g in ((20, 328, 6542), (30, 658, 13317.5)):
        ku, kg = _kz(M, P, f"kontrollpunkte|{n}|u"), _kz(M, P, f"kontrollpunkte|{n}|g")
        assert (ku["lin_unten"].klauseln, kg["lin_unten"].klauseln) == (u, g) and (kg["lin_oben"].klauseln == g)
        assert round(g / u, 1) == {20: 19.9, 30: 20.2}[n]
        assert kg["oll"].klauseln < 200 and kg["oll"].abbrueche == 0


def test_claim_gewichtet_oll_bricht_nur_bei_der_formel_einmal_ab_und_die_stratifizierung_nie(M, P):
    for key, (oll, strat, smin) in G.items():
        kz = _kz(M, P, key)
        assert (kz["oll"].median, kz["oll_strat"].median, kz["oll_strat_min"].median) == (oll, strat, smin), key
        assert kz["oll_strat"].abbrueche == 0 and kz["oll_strat_min"].abbrueche == 0
        assert kz["oll"].abbrueche == (1 if key == "formel|40|g" else 0)


def test_claim_stratifizierung_senkt_den_median_bei_rampen_und_formel_nicht_bei_kontrollpunkten(M, P):
    """Median der Konflikte OLL → OLL + Stratifizierung: Rampen n = 40 192,5 → 116, n = 60 508,5 → 353,5, Formel 5.522,5 → 1.286,5; Kontrollpunkte unverändert oder 0 → 1.
    Je Instanz weniger Konflikte mit Stratifizierung: Rampen n = 40 in 8 von 10, n = 60 nur in 3 von 10 (Median allein täuscht), Formel in 9 von 10. Mehr SAT-Aufrufe (Rampen 7 → 13, 6 → 14, Formel 11 → 15)."""
    for key in ("rampen|40|g", "rampen|60|g", "formel|40|g"):
        assert G[key][1] < G[key][0]
    for key in ("kontrollpunkte|20|g", "kontrollpunkte|30|g", "kontrollpunkte|50|g"):
        assert G[key][1] >= G[key][0]
    assert [E.vergleich_je_instanz(M[k], "oll", "oll_strat")[0] for k in ("rampen|40|g", "rampen|60|g", "formel|40|g")] == [8, 3, 9]
    assert [(_kz(M, P, k)["oll"].aufrufe, _kz(M, P, k)["oll_strat"].aufrufe) for k in ("rampen|40|g", "rampen|60|g", "formel|40|g")] == [(7, 13), (6, 14), (11, 15)]


# --- Kernminimierung --------------------------------------------------------------------------------------------------------------------

def test_claim_kernminimierung_kerne_kleiner_konflikte_meist_groesser(M, P):
    """13 Zellen (7 ungewichtet: OLL gegen OLL + Minimierung; 6 gewichtet: OLL + Stratifizierung gegen OLL + Stratifizierung + Minimierung): Kerne (Median der Mediane) in 7 Zellen
    kleiner (in den übrigen gleich), Gesamtkonflikte im Median in 10 Zellen größer, in 2 kleiner (Kontrollpunkte n = 20 und 30 ungewichtet), in 1 gleich."""
    paare = E.minimierungspaare()
    assert len(paare) == 13
    assert sum(1 for _, a, b in paare if b.kern < a.kern) == 7 and sum(1 for _, a, b in paare if b.kern > a.kern) == 0
    assert sum(1 for _, a, b in paare if b.median > a.median) == 10 and sum(1 for _, a, b in paare if b.median < a.median) == 2 and sum(1 for _, a, b in paare if b.median == a.median) == 1
    assert [n for n, a, b in paare if b.median < a.median] == ["Kontrollpunkte n = 20", "Kontrollpunkte n = 30"]
    assert E.verdict_minimierung(paare)[0] == "warning"


def test_claim_kerngroessen_mit_und_ohne_minimierung(M, P):
    kern = {n: (a.kern, b.kern) for n, a, b in E.minimierungspaare()}
    assert kern["Rampen n = 40"] == (25, 16) and kern["Rampen n = 60"] == (61, 34.75) and kern["Rampen n = 90"] == (73, 64.5) and kern["Formel n = 40"] == (70, 60)
    assert kern["Rampen n = 40 (gewichtet)"] == (47, 26.5) and kern["Rampen n = 60 (gewichtet)"] == (87.25, 57.25) and kern["Formel n = 40 (gewichtet)"] == (107, 78)


def test_claim_minimierungsaufrufe_zaehlen_mit(M, P):
    """Mit Minimierung mehr SAT-Aufrufe (Median): Rampen n = 40: 3,5 → 66,5; Formel: 4 → 94."""
    for key, (a, b) in {"rampen|40|u": (3.5, 66.5), "formel|40|u": (4, 94)}.items():
        kz = _kz(M, P, key)
        assert (kz["oll"].aufrufe, kz["oll_min"].aufrufe) == (a, b)


# --- CP-SAT --------------------------------------------------------------------------------------------------------------------------------

def test_claim_cpsat_baender(M, P):
    for key, (med, abbr) in CPS.items():
        assert E.cpsat_kennzahlen(P[key]) == (med, abbr, 10), key


def test_claim_cpsat_auf_kontrollpunkten_wenige_konflikte_auf_rampen_und_formeln_ein_vielfaches_von_oll(M, P):
    """CP-SAT (Konflikte der Löser-Statistik, nicht gleichwertig zu denen des Python-CDCL): Kontrollpunkte ungewichtet 0 bis 20,5 im Median; Rampen n = 40, 60, 90 und Formel n = 40 das 6,5-, 7,0-,
    11,7- und 12,0-Fache der OLL-Konflikte (Median), bei Rampen n = 90 mit 5 Abbrüchen von 10 am Zeitlimit; gewichtet bei Rampen und Formel über OLL + Stratifizierung."""
    assert max(CPS[f"kontrollpunkte|{n}|u"][0] for n in (20, 30, 50)) == 20.5
    verhaeltnis = {k: round(CPS[k][0] / U[k][0], 1) for k in ("rampen|40|u", "rampen|60|u", "rampen|90|u", "formel|40|u")}
    assert verhaeltnis == {"rampen|40|u": 6.5, "rampen|60|u": 7.0, "rampen|90|u": 11.7, "formel|40|u": 12.0}
    assert CPS["rampen|90|u"][1] == 5
    assert [CPS[k][0] > G[k][1] for k in ("rampen|40|g", "rampen|60|g", "formel|40|g")] == [True, True, True]


# --- Zweige: keine Spalte mit lauter gleichen Werten ----------------------------------------------------------------------------------------

def test_keine_spalte_der_messtabellen_hat_lauter_gleiche_werte(M, P):
    for key, z in M.items():
        for spalte in ("konflikte", "aufrufe", "klauseln"):
            werte = {l[spalte] for i in z["instanzen"] for l in i["laeufe"].values()}
            assert len(werte) > 1, (key, spalte)
    for key in U:
        assert len({U[key][j] for j in range(5)}) > 1


# --- Neumessung billiger Zellen gegen die Datei -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("n,gewichtet", [(20, False), (30, False), (20, True), (30, True)])
def test_neumessung_kontrollpunkte_stimmt_exakt_mit_der_messdatei_ueberein(M, n, gewichtet):
    """Alle Verfahren der Zelle neu gerechnet (ungewichtet alle zehn Instanzen, gewichtet die ersten drei: die unäre Kodierung ist teuer): Optimum, Status, Konflikte, SAT-Aufrufe,
    Kerngrößen und Klauseln gleich der Datei (deterministisch)."""
    z = M[C.zellenschluessel("kontrollpunkte", n, gewichtet)]
    for i in (z["instanzen"][:3] if gewichtet else z["instanzen"]):
        inst = S.erzeuge("kontrollpunkte", n, i["seed"], 10 if gewichtet else 1)
        assert sum(inst.gewichte) == i["gewichtssumme"] and len(inst.weich) == i["weich"]
        for v, alt in i["laeufe"].items():
            r = A.laufe(inst, v, call_budget=C.CALL_BUDGET_MAX, total_budget=C.BUDGET_REFERENZ)
            assert (r.optimum, r.status, r.konflikte, r.aufrufe, r.kerngroessen, r.klauseln) == (alt["optimum"], alt["status"], alt["konflikte"], alt["aufrufe"], alt["kerne"], alt["klauseln"]), (n, gewichtet, i["seed"], v)


def test_neumessung_rampen_40_zwei_instanzen_stimmen_mit_der_messdatei_ueberein(M):
    z = M["rampen|40|u"]
    for i in z["instanzen"][:2]:
        inst = S.erzeuge("rampen", 40, i["seed"], 1)
        for v in ("oll", "lin_unten"):
            r = A.laufe(inst, v, call_budget=C.CALL_BUDGET_MAX, total_budget=C.BUDGET_REFERENZ)
            alt = i["laeufe"][v]
            assert (r.optimum, r.konflikte, r.aufrufe, r.kerngroessen) == (alt["optimum"], alt["konflikte"], alt["aufrufe"], alt["kerne"]), (i["seed"], v)
