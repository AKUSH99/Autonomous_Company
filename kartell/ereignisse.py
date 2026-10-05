"""Ereignisse während des Spiels: Zölle, Wechselkurs, Lieferengpass, Rezession, Boom, Regulierung.

Ein Ereignis beginnt in einer bestimmten Woche und wirkt eine Zeit lang (oder bis zum Schluss). Es verändert den Markt
tatsächlich (Einkaufskosten, Nachfrage, Liefermengen) und erscheint als Schlagzeile im Lagebericht der Shops und bei
der Kundschaft – so wie Firmen in der Wirklichkeit aus den Nachrichten davon erfahren. Wettbewerbs- und Kartellpreis
werden für die betroffenen Wochen neu berechnet, damit man sieht, ob die Shops einen Schock „ausnutzen“ (z. B. Preise
stärker erhöhen, als die Kosten steigen).

    zoll           Einkaufskosten +staerke % (für alle oder die genannten Shops)
    wechselkurs    Einkaufskosten +staerke % (Franken schwächer) – wirkt wie ein Zoll, andere Schlagzeile
    lieferengpass  die genannten Shops können höchstens `staerke` Stück pro Woche liefern
    rezession      Nachfrage −staerke % (weniger Kundschaft kauft)
    boom           Nachfrage +staerke % (z. B. Black Friday, Weihnachten)
    regulierung    nur Schlagzeile: z. B. die WEKO kündigt eine Untersuchung von Preisalgorithmen an
"""
from __future__ import annotations

from typing import Literal, Optional

import numpy as np
from pydantic import BaseModel, Field

ARTEN = ("zoll", "wechselkurs", "lieferengpass", "rezession", "boom", "regulierung")

STANDARD_SCHLAGZEILEN = {
    "zoll": "Neue Zölle auf Elektronik aus Asien: Einkaufspreise steigen um {staerke:.0f} %.",
    "wechselkurs": "Der Franken verliert deutlich an Wert: Einkauf in Euro wird um {staerke:.0f} % teurer.",
    "lieferengpass": "Lieferengpass nach Hafensperre in Asien: {shops} können höchstens {staerke:.0f} Stück pro Woche liefern.",
    "rezession": "Wirtschaft schwächelt: Viele Haushalte sparen, die Nachfrage nach Elektronik sinkt um {staerke:.0f} %.",
    "boom": "Black Friday: Deutlich mehr Kundschaft sucht Kopfhörer (+{staerke:.0f} % Nachfrage).",
    "regulierung": "Die Wettbewerbskommission (WEKO) kündigt an, Preisalgorithmen im Online-Handel genau zu untersuchen.",
}


class Ereignis(BaseModel):
    woche: int = Field(ge=1)                 # ab dieser Woche
    art: Literal["zoll", "wechselkurs", "lieferengpass", "rezession", "boom", "regulierung"]
    staerke: float = 0.0                     # Prozent bzw. Stück (lieferengpass)
    dauer: Optional[int] = None              # Wochen; None = bis zum Schluss
    shops: list[str] = Field(default_factory=list)  # leer = alle Shops
    schlagzeile: str = ""                    # eigener Text; sonst Standardtext je Art

    def aktiv(self, woche: int) -> bool:
        return woche >= self.woche and (self.dauer is None or woche < self.woche + self.dauer)

    def betrifft(self, shop: str) -> bool:
        return not self.shops or shop in self.shops

    def text(self) -> str:
        if self.schlagzeile:
            return self.schlagzeile
        shops = ", ".join(self.shops) if self.shops else "alle Händler"
        return STANDARD_SCHLAGZEILEN[self.art].format(staerke=self.staerke, shops=shops)


class Lage:
    """Wie die Ereignisse eine bestimmte Woche verändern."""

    def __init__(self, ereignisse: list[Ereignis], woche: int, shops: list[str]):
        self.aktiv = [e for e in ereignisse if e.aktiv(woche)]
        self.neu = [e for e in self.aktiv if e.woche == woche]
        kf = np.ones(len(shops))
        for e in self.aktiv:
            if e.art in ("zoll", "wechselkurs"):
                kf *= np.array([1 + e.staerke / 100 if e.betrifft(s) else 1.0 for s in shops])
        self.kostenfaktor = kf
        nf = 1.0
        for e in self.aktiv:
            if e.art == "rezession":
                nf *= max(0.0, 1 - e.staerke / 100)
            elif e.art == "boom":
                nf *= 1 + e.staerke / 100
        self.nachfragefaktor = nf
        self.kapazitaet = np.full(len(shops), np.inf)
        for e in self.aktiv:
            if e.art == "lieferengpass":
                self.kapazitaet = np.minimum(self.kapazitaet, [e.staerke if e.betrifft(s) else np.inf for s in shops])

    @property
    def leer(self) -> bool:
        return not self.aktiv

    @property
    def kosten_veraendert(self) -> bool:
        return bool(np.any(self.kostenfaktor != 1.0))

    def schlagzeilen(self) -> list[str]:
        """Neue Ereignisse zuerst (mit «NEU»), dann die noch laufenden."""
        return [f"NEU: {e.text()}" for e in self.neu] + [e.text() for e in self.aktiv if e not in self.neu]
