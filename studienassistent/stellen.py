"""Gefundene Stellen für die Anzeige aufbereiten: Werkzeug-Ausgaben in einzelne Stellen zerlegen, doppelte entfernen,
in der Antwort zitierte zuerst, Suchbegriffe hervorheben. Ohne Streamlit, damit es testbar bleibt."""
from __future__ import annotations

import re
from dataclasses import dataclass

_KOPF = re.compile(r"^\[(\d+)\] (?P<modul>.+?) · (?P<datei>.+?)(?:, S\. (?P<seite>\d+))?$")
_FRIST = re.compile(r"^- (?P<datum>.+?)(?: (?P<zeit>\d{1,2}[:.]\d{2}(?:\s*[-–]\s*\d{1,2}[:.]\d{2})?))? · "
                    r"(?P<modul>[^:]+): (?P<titel>.+?)(?: \(Beleg: .*\))?$")
_MARKDOWN = re.compile(r"([\\`*_{}\[\]<>#|$~])")
_FUELLWOERTER = {"aber", "alle", "auch", "bitte", "dann", "darf", "dass", "dein", "deine", "denn", "diese", "dieser",
                 "dieses", "eine", "einem", "einen", "einer", "gibt", "haben", "hast", "habe", "ist", "kann", "muss",
                 "noch", "oder", "sind", "soll", "sollen", "über", "und", "viele", "wann", "warum", "was", "welche",
                 "welcher", "welches", "werden", "wie", "wird", "wieviel", "wo", "zum", "zur", "beinhalten", "genau"}


@dataclass
class Stelle:
    modul: str
    datei: str
    seite: int | None
    text: str
    zitiert: bool = False

    @property
    def ort(self) -> str:
        return self.datei + (f", S. {self.seite}" if self.seite else "")


@dataclass
class Frist:
    datum: str
    zeit: str
    modul: str
    titel: str


def zerlegen(quellen: list[str], antwort: str = "") -> tuple[list[Stelle], list[Frist]]:
    """Werkzeug-Ausgaben → (Stellen, Fristen). Stellen ohne Doppel, die in der Antwort zitierten zuerst."""
    stellen: dict[tuple, Stelle] = {}
    fristen: dict[tuple, Frist] = {}
    for ausgabe in quellen:
        treffer: list[tuple[re.Match, list[str]]] = []  # Kopfzeile + Textzeilen; Treffertexte enthalten selbst Leerzeilen
        for zeile in ausgabe.splitlines():
            if m := _KOPF.match(zeile.strip()):
                treffer.append((m, []))
            elif treffer:
                treffer[-1][1].append(zeile)
            elif f := _FRIST.match(zeile.strip()):
                fristen.setdefault((f["datum"], f["titel"]), Frist(f["datum"], f["zeit"] or "", f["modul"].strip(), f["titel"]))
        for m, zeilen in treffer:
            seite = int(m["seite"]) if m["seite"] else None
            text = _ohne_wortrest(" ".join(" ".join(zeilen).split()))
            stellen.setdefault((m["datei"], seite, text[:80]), Stelle(m["modul"], m["datei"], seite, text))
    for s in stellen.values():
        s.zitiert = _zitiert(s, antwort)
    return sorted(stellen.values(), key=lambda s: not s.zitiert), sorted(fristen.values(), key=lambda f: (f.datum, f.zeit))


def _ohne_wortrest(text: str) -> str:
    """Abschnitte überlappen und beginnen oft mitten im Wort («uellen Beitrag»): den Wortrest durch «…» ersetzen."""
    if text[:1].islower():
        rest = text.split(" ", 1)
        return "… " + rest[1] if len(rest) == 2 else text
    return text


def _zitiert(stelle: Stelle, antwort: str) -> bool:
    """In der Antwort zitiert = Dateiname kommt vor und, falls die Antwort Seiten nennt, auch diese Seite."""
    antwort = antwort.lower()
    if stelle.datei.lower() not in antwort:
        return False
    nach_datei = antwort.split(stelle.datei.lower(), 1)[1][:40]
    seiten = re.findall(r"s\.\s*(\d+)", nach_datei.split(";")[0].split(")")[0])
    return not seiten or stelle.seite is None or str(stelle.seite) in seiten


def suchbegriffe(frage: str) -> list[str]:
    woerter = re.findall(r"\w{4,}", frage.lower())
    return sorted({w for w in woerter if w not in _FUELLWOERTER}, key=len, reverse=True)


def als_markdown(text: str, begriffe: list[str], laenge: int = 450) -> str:
    """Text für st.markdown: Markdown-Zeichen entschärft, Suchbegriffe fett, lange Stellen gekürzt."""
    if len(text) > laenge:
        text = text[:laenge].rsplit(" ", 1)[0] + " …"
    text = _MARKDOWN.sub(r"\\\1", text)
    if begriffe:
        muster = re.compile("(" + "|".join(re.escape(b) for b in begriffe) + r")\w*", re.IGNORECASE)
        text = muster.sub(lambda m: f"**{m.group(0)}**", text)
    return text


BADGE_FARBEN = ["blue", "orange", "violet", "red", "gray", "primary"]  # grün ist für «zitiert» reserviert


def farbe(modul: str) -> str:
    return BADGE_FARBEN[sum(map(ord, modul)) % len(BADGE_FARBEN)]
