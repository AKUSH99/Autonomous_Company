"""Simulierte Kundschaft: entspricht der Logit-Nachfrage und misst, was Kartellpreise die Kunden kosten."""
import numpy as np

from kartell.kunden import kundenschaden, kundschaft
from kartell.market import LogitMarkt, MarktParameter


def _runden(a, b, n=4):
    return [{"preise": {"Shop A": a, "Shop B": b}} for _ in range(n)]


def test_personen_ergeben_die_logit_anteile():
    p = MarktParameter()
    markt = LogitMarkt(p)
    leute = kundschaft(p, ["Shop A", "Shop B"], anzahl=20000, seed=3)
    for preise in ([14.73, 14.73], [19.25, 19.25], [15.0, 18.0]):
        wahl = [x.waehle(preise) for x in leute]
        empirisch = [wahl.count(0) / len(wahl), wahl.count(1) / len(wahl), wahl.count(None) / len(wahl)]
        s = markt.anteile(preise)
        assert np.allclose(empirisch, list(s) + [1 - s.sum()], atol=0.015)


def test_kundenschaden_null_bei_wettbewerb_und_positiv_beim_kartell():
    p = MarktParameter()
    b = LogitMarkt(p).benchmarks()
    assert kundenschaden(_runden(b.nash_preis, b.nash_preis), p)["schaden_pro_kunde"] == 0.0
    kartell = kundenschaden(_runden(b.monopol_preis, b.monopol_preis), p)
    assert kartell["schaden_pro_kunde"] > 3 and 50 < kartell["schaden_prozent"] < 60
    assert kartell["ohne_kauf"] > kartell["ohne_kauf_nash"]
    assert kundenschaden(_runden(13.0, 13.0), p)["schaden_pro_kunde"] < 0  # Preiskampf: Kunden sparen


def test_personen_sind_fest_und_lesbar():
    p = MarktParameter()
    a, b = kundschaft(p, ["Shop A", "Shop B"]), kundschaft(p, ["Shop A", "Shop B"])
    assert [x.zahlungsbereitschaft for x in a] == [x.zahlungsbereitschaft for x in b]  # gleiche Kundschaft in jedem Lauf
    assert a[0].name == "Lena" and "kauft höchstens bis" in a[0].typ(["Shop A", "Shop B"])
