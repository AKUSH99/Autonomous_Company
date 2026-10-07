"""Betrieb mit vielen Nutzenden auf einem gemeinsamen API-Schlüssel.

- Taktbremse: höchstens n Aufrufe pro Minute über ALLE Prozesse (Chat-App und Update-Job teilen den Schlüssel). Das
  Fenster liegt in einer SQLite-Datei, damit sich die Prozesse abstimmen. Gezählt wird jede HTTP-Anfrage an die
  Plattform (Chat, Embeddings und Wiederholungen), siehe konfig.http_client.
- Notbremse: Lehnt die Plattform trotzdem ab (HTTP 429), pausieren alle Prozesse so lange, wie sie verlangt.
- Besucher: wer die Seite offen hat (Lebenszeichen alle paar Sekunden) und wie viele Fragen heute gestellt wurden.
- Warteschlange: höchstens MAX_GLEICHZEITIG Fragen werden zugleich bearbeitet, die übrigen warten der Reihe nach.
  So bekommt die erste Person schnell eine Antwort, statt dass alle gleichzeitig ausgebremst werden.
"""
from __future__ import annotations

import datetime as dt
import itertools
import sqlite3
import threading
import time
from contextlib import closing
from pathlib import Path

MAX_GLEICHZEITIG = 2
AKTIV_SEKUNDEN = 45  # so lange gilt eine offene Seite nach ihrem letzten Lebenszeichen als aktiv


class Betrieb:
    def __init__(self, pfad: Path, pro_minute: int):
        self.pfad, self.pro_minute = Path(pfad), pro_minute
        self.gewartet = 0.0  # Sekunden, die dieser Prozess insgesamt auf die Bremse gewartet hat (für die Evaluation)
        self.pfad.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._verbindung()) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS aufrufe (zeit REAL NOT NULL, art TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS aufrufe_zeit ON aufrufe (zeit);
                CREATE TABLE IF NOT EXISTS besuche (besucher TEXT PRIMARY KEY, erstmals REAL, zuletzt REAL);
                CREATE TABLE IF NOT EXISTS fragen (besucher TEXT, start REAL, sekunden REAL);
                CREATE TABLE IF NOT EXISTS ablehnungen (zeit REAL, pause REAL);
                CREATE TABLE IF NOT EXISTS bewertungen (antwort TEXT PRIMARY KEY, zeit REAL, gut INTEGER);
            """)

    def _verbindung(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.pfad, timeout=30, isolation_level=None)
        db.execute("PRAGMA journal_mode=WAL")
        return db

    # ---------- Taktbremse ----------

    def warten(self, art: str = "chat") -> float:
        """Sekunden bis zur nächsten freien Anfrage; 0 = sofort, die Anfrage ist dann gebucht."""
        with closing(self._verbindung()) as db:
            db.execute("BEGIN IMMEDIATE")  # sperrt die Datei für andere Prozesse bis zum Ende
            try:
                jetzt = time.time()
                bis = db.execute("SELECT MAX(zeit + pause) FROM ablehnungen").fetchone()[0] or 0
                if bis > jetzt:  # Notbremse: die Plattform hat eine Pause verlangt
                    return bis - jetzt
                zeiten = [z for (z,) in db.execute("SELECT zeit FROM aufrufe WHERE zeit > ? ORDER BY zeit", (jetzt - 60,))]
                if len(zeiten) < self.pro_minute:
                    db.execute("INSERT INTO aufrufe VALUES (?, ?)", (jetzt, art))
                    db.execute("DELETE FROM aufrufe WHERE zeit < ?", (jetzt - 8 * 86400,))  # eine Woche Verlauf reicht
                    return 0.0
                return zeiten[-self.pro_minute] + 60 - jetzt + 0.05
            finally:
                db.execute("COMMIT")

    def abgelehnt(self, pause: float) -> None:
        """Die Plattform hat mit HTTP 429 abgelehnt: alle Prozesse warten `pause` Sekunden."""
        with closing(self._verbindung()) as db, db:
            db.execute("INSERT INTO ablehnungen VALUES (?, ?)", (time.time(), pause))

    def bremsen(self, art: str = "chat") -> None:
        while (w := self.warten(art)) > 0:
            self.schlafen(min(w, 5))

    def schlafen(self, sekunden: float) -> None:
        time.sleep(sekunden)
        self.gewartet += sekunden

    # ---------- Besucher und Statistik ----------

    def lebenszeichen(self, besucher: str) -> None:
        jetzt = time.time()
        with closing(self._verbindung()) as db, db:
            db.execute("INSERT INTO besuche VALUES (?, ?, ?) ON CONFLICT(besucher) DO UPDATE SET zuletzt = excluded.zuletzt",
                       (besucher, jetzt, jetzt))

    def frage_erledigt(self, besucher: str, start: float) -> None:
        with closing(self._verbindung()) as db, db:
            db.execute("INSERT INTO fragen VALUES (?, ?, ?)", (besucher, start, time.time() - start))

    def bewerten(self, antwort_id: str, gut: bool | None) -> None:
        """👍/👎 zu einer Antwort (None = zurückgenommen). Gespeichert wird nur die Bewertung, nicht der Text."""
        with closing(self._verbindung()) as db, db:
            if gut is None:
                db.execute("DELETE FROM bewertungen WHERE antwort = ?", (antwort_id,))
            else:
                db.execute("INSERT OR REPLACE INTO bewertungen VALUES (?, ?, ?)", (antwort_id, time.time(), int(gut)))

    def lage(self) -> dict:
        jetzt = time.time()
        heute = dt.datetime.combine(dt.date.today(), dt.time()).timestamp()
        with closing(self._verbindung()) as db:
            aktiv = db.execute("SELECT COUNT(*) FROM besuche WHERE zuletzt > ?", (jetzt - AKTIV_SEKUNDEN,)).fetchone()[0]
            minute = db.execute("SELECT COUNT(*) FROM aufrufe WHERE zeit > ?", (jetzt - 60,)).fetchone()[0]
            fragen, personen, schnitt = db.execute(
                "SELECT COUNT(*), COUNT(DISTINCT besucher), AVG(sekunden) FROM fragen WHERE start > ?", (heute,)).fetchone()
            besucher_heute = db.execute("SELECT COUNT(*) FROM besuche WHERE zuletzt > ?", (heute,)).fetchone()[0]
            gut, schlecht = db.execute("SELECT COALESCE(SUM(gut), 0), COALESCE(SUM(1 - gut), 0) FROM bewertungen").fetchone()
            abgelehnt_heute = db.execute("SELECT COUNT(*) FROM ablehnungen WHERE zeit > ?", (heute,)).fetchone()[0]
            bis = db.execute("SELECT MAX(zeit + pause) FROM ablehnungen").fetchone()[0] or 0
        return {"daumen_hoch": gut, "daumen_runter": schlecht, "abgelehnt_heute": abgelehnt_heute, "pause_noch": max(0.0, bis - jetzt), "aktiv": aktiv, "aufrufe_minute": minute, "limit": self.pro_minute, "fragen_heute": fragen,
                "fragende_heute": personen, "besucher_heute": besucher_heute, "schnitt_sekunden": schnitt}


class Warteschlange:
    """Der Reihe nach: höchstens `plaetze` Fragen gleichzeitig. Nur innerhalb eines Prozesses (die Chat-App)."""

    def __init__(self, plaetze: int = MAX_GLEICHZEITIG):
        self.plaetze, self.sperre = plaetze, threading.Lock()
        self.wartend: list[int] = []
        self.in_arbeit: set[int] = set()
        self._nummern = itertools.count(1)

    def anstellen(self) -> int:
        with self.sperre:
            nummer = next(self._nummern)
            self.wartend.append(nummer)
            return nummer

    def position(self, nummer: int) -> int:
        """0 = darf jetzt loslegen (der Platz ist dann belegt), sonst die Stelle in der Warteschlange (1 = als Nächstes)."""
        with self.sperre:
            if nummer in self.in_arbeit:
                return 0
            stelle = self.wartend.index(nummer)
            if stelle == 0 and len(self.in_arbeit) < self.plaetze:
                self.wartend.pop(0)
                self.in_arbeit.add(nummer)
                return 0
            return stelle + 1

    def fertig(self, nummer: int) -> None:
        """Gibt den Platz frei bzw. verlässt die Schlange (auch wenn jemand die Seite schliesst)."""
        with self.sperre:
            self.in_arbeit.discard(nummer)
            if nummer in self.wartend:
                self.wartend.remove(nummer)

    def zustand(self) -> tuple[int, int]:
        with self.sperre:
            return len(self.in_arbeit), len(self.wartend)
