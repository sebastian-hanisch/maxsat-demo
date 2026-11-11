"""Permalink (Begrenzen/Einrasten), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).

Die Regler der Seitenleiste (Zufalls-Seed, Familie, Größe, Gewichte, Budget) und die Regler von Experiment 1 im Hauptbereich (Gewichte des Handbeispiels, Kernwahl,
Schritt) stehen alle in SETTING_SPECS: ein Preset legt Werte für alle fest, und das aktive Preset ist hervorgehoben, solange jeder dieser Regler dem Preset entspricht.
"""

import random
from dataclasses import dataclass

import streamlit as st

import mxs_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple = ()


SETTING_SPECS = {
    "seed": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "familie": SettingSpec("fam", str, "Kontrollpunkte", options=C.FAMILIEN),
    "n": SettingSpec("n", int, 20, options=C.N_OPTIONEN),
    "gewicht_hi": SettingSpec("gw", int, 1, options=C.GEWICHT_OPTIONEN),
    "budget": SettingSpec("budget", int, C.BUDGET_REFERENZ, options=C.BUDGET_OPTIONEN),
    "e1_gewichte": SettingSpec("e1g", str, C.E1_GEWICHT_OPTIONEN[0], options=C.E1_GEWICHT_OPTIONEN),
    "e1_kern": SettingSpec("e1k", str, C.E1_KERN_OPTIONEN[0], options=C.E1_KERN_OPTIONEN),
    "e1_schritt": SettingSpec("e1s", int, C.DEFAULT_E1_SCHRITT, *C.E1_SCHRITT),
}
PRESET_KEYS = {key: key for key in SETTING_SPECS}      # Schlüssel im Preset = Schlüssel des Reglers


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def einrasten(spec: SettingSpec, roh):
    """Wert aus der Adresszeile auf einen erlaubten Wert bringen (Zahlen: begrenzen bzw. auf die nächste Option, Text: nur erlaubte Werte), sonst None."""
    try:
        wert = spec.caster(roh)
    except (ValueError, TypeError):
        return None
    if spec.options:
        if spec.caster in (int, float):
            return min(spec.options, key=lambda o: abs(o - wert))
        return wert if wert in spec.options else None
    return max(spec.lo, min(spec.hi, wert))


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf erlaubte Werte begrenzt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            wert = einrasten(spec, qp[spec.url_param])
            if wert is not None:
                st.session_state[state_key] = wert
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    preset = C.PRESETS[name]
    for key, spec in SETTING_SPECS.items():
        st.session_state[key] = preset.get(key, spec.default)


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None (zustandslos)."""
    for name, preset in C.PRESETS.items():
        if all(st.session_state.get(key, spec.default) == preset.get(key, spec.default) for key, spec in SETTING_SPECS.items()):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
                  type="primary" if aktiv == name else "secondary")


def randomize_seed():
    st.session_state["seed"] = random.randint(0, C.SEED_MAX)
