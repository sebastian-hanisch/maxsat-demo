"""Gemeinsame Fixtures: das Handbeispiel, an dem jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mxs_scenario as S  # noqa: E402


@pytest.fixture
def hand():
    """Drei Variablen, höchstens eine wahr, sechs weiche Klauseln x1, x2, x3, ¬x1, ¬x2, ¬x3 (Gewicht 1). Handrechnung: Optimum 3."""
    return S.handbeispiel()


@pytest.fixture
def hand_gewichtet():
    """Dasselbe mit den Gewichten 2, 1, 1, 3, 1, 1. Handrechnung: Optimum 4."""
    return S.handbeispiel([2, 1, 1, 3, 1, 1])
