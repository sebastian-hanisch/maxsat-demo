"""Die kopierten Kern-Module (`mxs_rng`, `mxs_instanzen`, `mxs_kodierung`, `mxs_cdcl`): wörtliche Kopie, Regressionswerte, Einheiten mit Handrechnung.

Der Hash-Test (Kern-Version im Modulkopf gegen den Text der Kopie mit rückübersetzten Importen) läuft immer; der Vergleich mit dem Kern selbst nur, solange der Ordner
`sat-cp-planung/kern` neben dem Repo liegt. Die Regressionswerte stehen unabhängig davon im Test."""

import hashlib
import itertools
import re
from math import comb
from pathlib import Path

import pytest

import mxs_instanzen as I
import mxs_kodierung as K
from mxs_cdcl import Loeser, luby, solve
from mxs_rng import SplitMix64

ROOT = Path(__file__).resolve().parent.parent
KERN = ROOT.parent / "sat-cp-planung" / "kern"
MODULE = ("rng", "instanzen", "kodierung", "cdcl")
VERSION = {"rng": "5d5d8f45d0e1eddf", "instanzen": "6795de796b66fff8", "kodierung": "208571302afd04b4", "cdcl": "832b2c10dfdea62d"}
ERLAUBTE_IMPORTE = {"heapq", "itertools", "dataclasses", "typing", "math", "mxs_rng"}


def _lies(pfad: Path) -> str:
    return pfad.read_bytes().decode("utf-8").replace("\r\n", "\n")


def _kern_text(modul: str) -> tuple[str, str]:
    """(Kern-Version aus dem Kopf, Text der Kopie im Zustand des Kerns)."""
    text = _lies(ROOT / f"mxs_{modul}.py")
    kopf, zweite, rest = text.split("\n", 2)
    version = re.search(r"Kern-Version ([0-9a-f]{16})", kopf).group(1)
    assert "mxs_" in zweite
    return version, re.sub(r"^from mxs_rng import", "from rng import", rest, flags=re.M)


@pytest.mark.parametrize("modul", MODULE)
def test_kopie_gleicht_der_kern_version(modul):
    version, text = _kern_text(modul)
    assert version == VERSION[modul]
    assert hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] == version


@pytest.mark.parametrize("modul", MODULE)
def test_kopie_gleicht_dem_kern_bis_auf_kopf_und_importe(modul):
    quelle = KERN / f"{modul}.py"
    if not quelle.exists():
        pytest.skip("kern/ liegt nicht neben dem Repo")
    assert _kern_text(modul)[1] == _lies(quelle)


def test_kern_version_stimmt_mit_hashes_txt():
    hashes = KERN / "HASHES.txt"
    if not hashes.exists():
        pytest.skip("kern/ liegt nicht neben dem Repo")
    eintraege = {z.split()[1]: z.split()[0] for z in hashes.read_text(encoding="utf-8").splitlines() if z.strip()}
    for modul, version in VERSION.items():
        assert eintraege[f"{modul}.py"] == version


def test_kopien_importieren_nichts_aus_dem_kern_oder_anderen_demos():
    for modul in MODULE:
        for zeile in _lies(ROOT / f"mxs_{modul}.py").splitlines():
            if zeile.startswith(("import ", "from ")):
                assert zeile.split()[1] in ERLAUBTE_IMPORTE, (modul, zeile)


# --- SplitMix64 und Instanzen -------------------------------------------------------------------------------------------------------------

def test_splitmix_bekannte_werte():
    g = SplitMix64(0)
    assert [g.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]
    h = SplitMix64(12345)
    assert [h.next() for _ in range(3)] == [2454886589211414944, 3778200017661327597, 2205171434679333405]


def test_zufallskanten_deterministisch_und_ohne_doppelte():
    a, b = I.zufallskanten(30, 45, 100), I.zufallskanten(30, 45, 100)
    assert a == b and len(set(a)) == 45 and all(x < y for x, y in a) and a == sorted(a)
    assert I.zufallskanten(30, 45, 101) != a
    with pytest.raises(ValueError):
        I.zufallskanten(3, 4, 0)


# --- Kodierung des Kerns (Handwerte) -----------------------------------------------------------------------------------------------------

def test_kern_kodierungen_handbeispiel_zahlen():
    for verfahren, (kl, hv) in {"binomial": (4, 0), "sinz": (13, 6), "totalizer": (15, 7)}.items():
        pool = K.Hilfsvariablen(4)
        assert len(K.hoechstens([1, 2, 3, 4], 2, pool, verfahren)) == kl and pool.n - 4 == hv
    assert K.hoechstens_eins([1, 2, 3]) == [(-1, -2), (-1, -3), (-2, -3)]
    assert K.klauselzahl_binomial(25, 5) == comb(25, 6)


# --- CDCL: Einheiten und Kerne unter Annahmen ----------------------------------------------------------------------------------------------

def test_luby_folge():
    assert [luby(i) for i in range(1, 16)] == [1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8]


def test_solve_kleine_antworten():
    assert solve(2, [(1,), (-1,)]).antwort is False
    assert solve(2, [(1, 2), (-1,)]).modell == {1: False, 2: True}


def test_kern_unter_annahmen_handrechnung():
    """Hart: (¬1 ∨ ¬2). Annahmen 1, 2, 3: unerfüllbar, der Kern ist {1, 2} (die Annahme 3 gehört nicht dazu)."""
    r = Loeser(3, [(-1, -2)]).loese([1, 3, 2])
    assert r.antwort is False and set(r.kern) == {1, 2}
    assert Loeser(3, [(-1, -2)]).loese([1, 3]).antwort is True


def test_kern_ist_unabhaengig_unerfuellbar_und_eine_teilmenge_der_annahmen():
    """100 kleine Formeln mit festen Zufalls-Seeds: unter den Annahmen unerfüllbar genau dann, wenn Aufzählung es bestätigt; der Kern genügt schon (Aufzählung)."""
    def erfuellbar(n, klauseln, annahmen):
        for bits in itertools.product((False, True), repeat=n):
            if all(bits[abs(a) - 1] == (a > 0) for a in annahmen) and all(any(bits[abs(l) - 1] == (l > 0) for l in c) for c in klauseln):
                return True
        return False

    for seed in range(100):
        inst = I.rand3(7, 9 + seed % 6, seed)
        rng = SplitMix64(1000 + seed)
        annahmen = [(v + 1) if rng.coin() else -(v + 1) for v in range(7) if rng.below(3)]
        r = Loeser(7, list(inst.klauseln)).loese(annahmen)
        assert (r.antwort is True) == erfuellbar(7, inst.klauseln, annahmen), seed
        if r.antwort is False:
            assert set(r.kern) <= set(annahmen), seed
            assert not erfuellbar(7, inst.klauseln, r.kern), seed


def test_inkrementell_klauseln_und_variablen_hinzufuegen():
    s = Loeser(2, [(1, 2)])
    assert s.loese().antwort is True
    v = s.neue_variable()
    assert v == 3
    s.fuege_klausel_hinzu((-1,))
    s.fuege_klausel_hinzu((-2, 3))
    r = s.loese([-3])
    assert r.antwort is False and set(r.kern) <= {-3}
    assert s.loese([3]).antwort is True
