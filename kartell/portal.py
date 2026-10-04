"""Preisvergleichsportal (wie Toppreise.ch): eine Rangliste aller Angebote, günstigstes zuerst.

In echten Online-Märkten sehen sich Shops nicht in einem gemeinsamen Chat, sondern über Vergleichsportale. Dort sieht
die Kundschaft Preis, Bewertung und Lieferzeit jedes Shops – und jeder Shop sieht die Preise der Konkurrenz. Statt
Chat-Nachrichten gibt es öffentliche Mitteilungen auf der eigenen Angebotsseite («Aktion: Gratis-Versand»), die
Kundschaft UND Konkurrenz lesen. Eine Absprache ginge dann nur über solche öffentlichen Signale – der Fall, mit dem
sich Wettbewerbsbehörden bei Preisalgorithmen tatsächlich beschäftigen.
"""
from __future__ import annotations


def eintraege(preise: dict[str, float], profile: dict, mitteilungen: dict[str, str] | None = None) -> list[dict]:
    """Angebote sortiert nach Preis. `profile`: Name → FirmenProfil (Bewertung, Lieferzeit, öffentliche Beschreibung)."""
    mitteilungen = mitteilungen or {}
    liste = []
    for name, preis in sorted(preise.items(), key=lambda kv: (kv[1], kv[0])):
        p = profile.get(name)
        liste.append({"shop": name, "preis": round(float(preis), 2),
                      "bewertung": getattr(p, "bewertung", None), "bewertungen": getattr(p, "bewertungen", None),
                      "lieferzeit": getattr(p, "lieferzeit", "") or "", "info": getattr(p, "oeffentlich", "") or "",
                      "mitteilung": mitteilungen.get(name, "")})
    return liste


def als_text(liste: list[dict], titel: str, mit_info: bool = False) -> str:
    zeilen = [titel]
    for rang, e in enumerate(liste, 1):
        teile = [f"{rang}. {e['shop']}: {e['preis']:.2f} CHF"]
        if e["bewertung"] is not None:
            teile.append(f"★ {e['bewertung']:.1f}" + (f" ({e['bewertungen']} Bewertungen)" if e["bewertungen"] else ""))
        if e["lieferzeit"]:
            teile.append(f"Lieferung {e['lieferzeit']}")
        if mit_info and e["info"]:
            teile.append(e["info"])
        if e["mitteilung"]:
            teile.append(f"Mitteilung: „{e['mitteilung']}“")
        zeilen.append(" · ".join(teile))
    return "\n".join(zeilen)


def letzte_mitteilungen(nachrichten: list[dict]) -> dict[str, str]:
    """Neueste öffentliche Mitteilung je Shop (spätere überschreiben frühere)."""
    aktuell: dict[str, str] = {}
    for m in nachrichten:
        aktuell[m["von"]] = m["text"]
    return aktuell
