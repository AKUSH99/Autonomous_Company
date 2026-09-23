import numpy as np
import pytest

from kartell.market import LogitMarkt, MarktParameter
from kartell.metrics import kollusionsindex, preisindex


def test_referenzwerte_aus_der_literatur():
    # Calvano et al. (2020): a=2, a0=0, mu=0.25, c=1, zwei Firmen -> Nash ≈ 1.47, Monopol ≈ 1.92
    b = LogitMarkt(MarktParameter(alpha=1)).benchmarks()
    assert b.nash_preis == pytest.approx(1.473, abs=1e-3)
    assert b.monopol_preis == pytest.approx(1.925, abs=1e-3)


def test_preisskala_alpha_skaliert_linear():
    b1 = LogitMarkt(MarktParameter(alpha=1)).benchmarks()
    b10 = LogitMarkt(MarktParameter(alpha=10)).benchmarks()
    assert b10.nash_preis == pytest.approx(10 * b1.nash_preis, rel=1e-9)
    assert b10.monopol_preis == pytest.approx(10 * b1.monopol_preis, rel=1e-9)


@pytest.mark.parametrize("firmen", [2, 3, 4])
def test_nash_preis_ist_gleichgewicht(firmen):
    m = LogitMarkt(MarktParameter(firmen=firmen, alpha=10))
    pn = m.nash_preis()
    basis = m.gewinne([pn] * firmen)[0]
    abweichungen = [m.gewinne([pn + d] + [pn] * (firmen - 1))[0] for d in np.linspace(-3, 3, 301)]
    assert max(abweichungen) <= basis + 1e-6


def test_monopolpreis_maximiert_gemeinsamen_gewinn():
    m = LogitMarkt(MarktParameter(alpha=10))
    pm = m.monopol_preis()
    beste = max(m.gewinne([p, p]).sum() for p in np.linspace(11, 30, 1901))
    assert m.gewinne([pm, pm]).sum() >= beste - 1e-6


def test_anteile_und_indizes():
    m = LogitMarkt(MarktParameter(alpha=10))
    s = m.anteile([15, 18])
    assert 0 < s.sum() < 1 and s[0] > s[1]
    b = m.benchmarks()
    assert kollusionsindex(b.nash_gewinn, b) == pytest.approx(0)
    assert kollusionsindex(b.monopol_gewinn, b) == pytest.approx(1)
    assert preisindex(b.monopol_preis, b) == pytest.approx(1)
