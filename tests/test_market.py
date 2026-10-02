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


def test_unterschiedliche_kosten_je_shop():
    import numpy as np
    from kartell.market import LogitMarkt, MarktParameter
    markt = LogitMarkt(MarktParameter(firmen=3, kosten_je_firma=(0.85, 1.0, 1.1)))
    pn, pm = np.array(markt.nash_preise()), np.array(markt.monopol_preise())
    c, am = markt.kostenvektor, markt.p.alpha * markt.p.mu
    # Nash: Bedingung erster Ordnung je Shop; Monopol: gleicher Aufschlag für alle
    assert np.allclose(pn - c, am / (1 - markt.anteile(pn)), atol=1e-6)
    assert np.allclose(pm - c, (pm - c)[0]) and np.isclose((pm - c)[0], am / (1 - markt.anteile(pm).sum()), atol=1e-6)
    assert pn[0] < pn[1] < pn[2] and (pm > pn).all()  # der günstigste Anbieter verlangt am wenigsten
    # Kein Shop kann sich im Nash-Gleichgewicht einseitig verbessern
    for i in range(3):
        for d in (-0.05, 0.05):
            p = pn.copy(); p[i] += d
            assert markt.gewinne(p)[i] <= markt.gewinne(pn)[i] + 1e-9
    b = markt.benchmarks()
    assert b.nash_preise and np.isclose(b.nash_preis, pn.mean()) and b.monopol_gewinn > b.nash_gewinn


def test_gleiche_kosten_wie_bisher():
    from kartell.market import LogitMarkt, MarktParameter
    alt = LogitMarkt(MarktParameter(firmen=2)).benchmarks()
    neu = LogitMarkt(MarktParameter(firmen=2, kosten_je_firma=(1.0, 1.0))).benchmarks()
    assert round(alt.nash_preis, 2) == 14.73 and round(alt.monopol_preis, 2) == 19.25
    assert abs(alt.nash_preis - neu.nash_preis) < 1e-9 and alt.nash_preise is None
