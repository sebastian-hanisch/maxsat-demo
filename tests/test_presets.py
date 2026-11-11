"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Voreinstellungen; Permalink; jedes Preset durchläuft die Instanzerzeugung (DEMO-PLAYBOOK §11a Punkt 7)."""

import mxs_constants as C
import mxs_presets as P
import mxs_scenario as S


def test_jedes_preset_hat_hilfetext_und_nur_bekannte_schluessel():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) <= set(P.SETTING_SPECS), name
        assert C.PRESET_HELP[name]


def test_presetwerte_liegen_in_den_reglergrenzen_und_optionen():
    for name, preset in C.PRESETS.items():
        for key, wert in preset.items():
            spec = P.SETTING_SPECS[key]
            assert wert in spec.options if spec.options else spec.lo <= wert <= spec.hi, (name, key)


def test_standard_preset_ist_das_erste_und_gleich_den_voreinstellungen():
    erstes = C.PRESETS[next(iter(C.PRESETS))]
    assert all(erstes.get(key, spec.default) == spec.default for key, spec in P.SETTING_SPECS.items())
    for name, preset in list(C.PRESETS.items())[1:]:
        assert any(preset.get(key, spec.default) != spec.default for key, spec in P.SETTING_SPECS.items()), f"{name} entspricht den Voreinstellungen"


def test_setting_specs_und_preset_keys_decken_sich():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_die_vier_presets_des_plans():
    assert list(C.PRESETS) == ["Handbeispiel", "Vertex Cover n = 30", "Färbung n = 40 Grad 5,0", "Zufall n = 40 m/n 6"]
    assert (C.PRESETS["Vertex Cover n = 30"], C.PRESETS["Färbung n = 40 Grad 5,0"], C.PRESETS["Zufall n = 40 m/n 6"]) == (
        {"familie": "Kontrollpunkte", "n": 30}, {"familie": "Rampen", "n": 40}, {"familie": "Formel", "n": 40})


def test_beschriebene_parameter_stimmen_mit_den_instanzen_der_presets():
    """Hilfetexte nennen Grad 5,0 und m/n 6: die Instanzen der Presets haben genau das."""
    assert C.FAMILIE_PARAM == {"kontrollpunkte": 3.0, "rampen": 5.0, "formel": 6}
    r = S.erzeuge("rampen", 40, 100)
    assert len(r.meta["kanten"]) == 100 and 2 * len(r.meta["kanten"]) / 40 == 5.0
    f = S.erzeuge("formel", 40, 100)
    assert len(f.weich) / 40 == 6


def test_jedes_preset_erzeugt_eine_instanz_innerhalb_der_live_grenzen():
    for name, preset in C.PRESETS.items():
        art = C.FAMILIE_ART[preset.get("familie", P.SETTING_SPECS["familie"].default)]
        n = preset.get("n", P.SETTING_SPECS["n"].default)
        assert n <= C.LIVE_N_MAX[art], name
        assert S.erzeuge(art, n, C.DEFAULT_SEED).n >= n


def test_permalink_rastet_auf_erlaubte_werte_ein():
    spec = P.SETTING_SPECS
    assert P.einrasten(spec["n"], "47") == 50 and P.einrasten(spec["n"], "x") is None and P.einrasten(spec["n"], "1000") == 90
    assert P.einrasten(spec["familie"], "Rampen") == "Rampen" and P.einrasten(spec["familie"], "irgendwas") is None
    assert P.einrasten(spec["gewicht_hi"], "7") == 5 and P.einrasten(spec["budget"], "20000") == 10000
    assert P.einrasten(spec["seed"], "-1") == 0 and P.einrasten(spec["seed"], "9999999") == C.SEED_MAX
    assert P.einrasten(spec["e1_schritt"], "99") == 6 and P.einrasten(spec["e1_kern"], "Kern des Lösers") == "Kern des Lösers"
