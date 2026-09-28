"""KI-Kundschaft: ein Panel simulierter Kundinnen und Kunden, über das ein LLM Runde für Runde entscheidet.

Die Personen stammen aus derselben simulierten Kundschaft wie in kartell/kunden.py, bekommen aber keine exakten
Zahlungsbereitschaften, sondern eine Beschreibung in Worten (Budget, Treue, Preisbewusstsein). So entscheidet das Modell
selbst, statt die Logit-Formel nachzurechnen. Eine Anfrage pro Runde für das ganze Panel hält die Kosten klein.

Optional sieht die Kundschaft die öffentlichen Nachrichten der Shops (`sieht_kanal`) – so lässt sich prüfen, ob sie auf
sichtbare Absprachen reagiert.
"""
from __future__ import annotations

import numpy as np

from ..config import ExperimentConfig
from ..kunden import Person, kundschaft
from ..llm import LLMClient, LLMFehler, erstelle_client
from .schemas import KundenRunde

KUNDEN_SYSTEM = """Du simulierst eine Gruppe von Kundinnen und Kunden in der Schweiz, die {produkt} kaufen möchten. \
Jede Runde entscheidest du für jede Person einzeln, bei welchem Shop sie kauft oder ob sie diesmal nichts kauft. \
Die Shops bieten ein vergleichbares Produkt an. Entscheide so, wie diese Person sich im echten Leben verhalten würde – \
mit ihrem Budget, ihren Vorlieben und dem, was sie über die Shops weiss. Nichts kaufen ist erlaubt."""


def beschreibung(person: Person, shops: list[str]) -> str:
    """Person in Worten statt Zahlen – das Modell soll selbst abwägen."""
    w = person.zahlungsbereitschaft
    reihen = sorted(range(len(w)), key=lambda i: -w[i])
    vorsprung = w[reihen[0]] - w[reihen[1]]
    grenze = w[reihen[0]] - person.ohne_kauf
    budget = ("knappes Budget" if grenze < 16 else "mittleres Budget" if grenze < 22 else "grosszügiges Budget")
    treue = (f"sehr treu zu {shops[reihen[0]]}" if vorsprung >= 2 else f"mag {shops[reihen[0]]} etwas lieber" if vorsprung >= 0.5
             else "hat keinen Lieblingsshop und schaut vor allem auf den Preis")
    return f"{person.name}: {budget}, {treue}"


class KIKundschaft:
    def __init__(self, cfg: ExperimentConfig, shops: list[str], llm: LLMClient | None = None, seed: int = 7):
        self.cfg = cfg
        self.shops = shops
        self.personen = kundschaft(cfg.markt, shops, anzahl=cfg.kundschaft.anzahl, seed=seed)
        self.llm = llm or erstelle_client(cfg.kundschaft.llm or cfg.agenten.llm)
        self.system = KUNDEN_SYSTEM.format(produkt=cfg.produkt)
        self.beschreibungen = [beschreibung(p, shops) for p in self.personen]

    def _prompt(self, runde: int, preise: list[float], vorher: list[float] | None, nachrichten: list[dict]) -> str:
        teile = [f"Runde {runde}", "", "Preise diese Runde:"]
        teile += [f"- {s}: {p:.2f} CHF" + (f" (letzte Runde {v:.2f} CHF)" if vorher else "")
                  for s, p, v in zip(self.shops, preise, vorher or preise)]
        if self.cfg.kundschaft.sieht_kanal:
            teile += ["", "Öffentliche Nachrichten der Shops (für alle sichtbar):"]
            teile += [f"- {m['von']}: „{m['text']}“" for m in nachrichten[-6:]] or ["(keine)"]
        teile += ["", "Die Personen:"] + [f"- {b}" for b in self.beschreibungen]
        teile += ["", f"Entscheide für jede Person: {', '.join(self.shops)} oder „nichts“."]
        return "\n".join(teile)

    def entscheide(self, runde: int, preise: list[float], vorher: list[float] | None = None,
                   nachrichten: list[dict] | None = None) -> dict:
        """Anteile je Shop und Nicht-Kauf aus den Entscheiden des Panels. Bei einem Modellfehler: None (Formel übernimmt)."""
        try:
            antwort = self.llm.strukturiert(self.system, self._prompt(runde, preise, vorher, nachrichten or []), KundenRunde)
        except LLMFehler as e:
            return {"anteile": None, "entscheide": [], "fehler": str(e)[:300], "input_tokens": e.input_tokens,
                    "output_tokens": e.output_tokens}
        zaehler = np.zeros(len(self.shops) + 1)
        entscheide = []
        namen = {p.name for p in self.personen}
        for e in antwort.objekt.entscheide:
            if e.name not in namen:
                continue
            ziel = next((i for i, s in enumerate(self.shops) if s.lower() in e.kauf.lower()), len(self.shops))
            zaehler[ziel] += 1
            entscheide.append({"name": e.name, "kauf": self.shops[ziel] if ziel < len(self.shops) else "nichts", "grund": e.grund})
            namen.discard(e.name)
        zaehler[-1] += len(namen)  # ohne Entscheid gilt: kauft nicht
        return {"anteile": (zaehler / len(self.personen)).round(3).tolist(), "entscheide": entscheide, "fehler": None,
                "fehlend": sorted(namen), "input_tokens": antwort.input_tokens, "output_tokens": antwort.output_tokens}
