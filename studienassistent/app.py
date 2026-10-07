"""Chat-Oberfläche (Streamlit):  python -m studienassistent app"""
from __future__ import annotations

import time
import uuid

import streamlit as st

from studienassistent.__main__ import lade_alles
from studienassistent.agent import fragen_live
from studienassistent.betrieb import Warteschlange
from studienassistent.konfig import betrieb
from studienassistent.stellen import als_markdown, farbe, suchbegriffe, zerlegen

MODELL = "glm-flash"  # GLM-5.3 Flash; die Antwort entsteht immer mit maximalem Reasoning

st.set_page_config(page_title="FHNW Studienassistent", page_icon="🎓")
st.title("FHNW Studienassistent")


@st.cache_resource(show_spinner="Unterlagen werden geladen …")
def agent(modell: str):
    return lade_alles(modell, denken=True)


@st.cache_resource
def schlange() -> Warteschlange:
    return Warteschlange()  # eine für alle Sitzungen der App


graph, suche, _ = agent(MODELL)
st.session_state.setdefault("besucher", str(uuid.uuid4()))  # zählt offene Seiten, bleibt bei «Neues Gespräch»
st.caption("Fragen zu Prüfungen, Abgaben, Fristen und Inhalten im BAI-Herbstsemester 2026 – jede Antwort mit Quelle.")
st.markdown("**Eingerichtet für diese Module:** " + " ".join(f":{farbe(m)}-badge[{m}]" for m in suche.module()))


@st.fragment(run_every=10)
def auslastung() -> None:
    """Lebenszeichen senden und die Lage anzeigen; aktualisiert sich alle 10 Sekunden von selbst."""
    b = betrieb()
    b.lebenszeichen(st.session_state["besucher"])
    lage, (in_arbeit, wartend) = b.lage(), schlange().zustand()
    st.markdown("**Gerade los**")
    st.markdown(f"👥 {lage['aktiv']} {'Person' if lage['aktiv'] == 1 else 'Personen'} online  \n"
                f"💬 {in_arbeit} {'Frage' if in_arbeit == 1 else 'Fragen'} in Arbeit"
                + (f", {wartend} in der Warteschlange" if wartend else ""))
    st.progress(min(lage["aufrufe_minute"] / lage["limit"], 1.0),
                text=f"🔑 API-Schlüssel: {lage['aufrufe_minute']} von {lage['limit']} Aufrufen pro Minute")
    schnitt = f", Ø {lage['schnitt_sekunden']:.0f} s pro Antwort" if lage["schnitt_sekunden"] else ""
    zahl = lambda n, eins, mehr: f"{n} {eins if n == 1 else mehr}"
    st.caption(f"Heute: {zahl(lage['fragen_heute'], 'Frage', 'Fragen')} von "
               f"{zahl(lage['fragende_heute'], 'Person', 'Personen')}{schnitt}; "
               f"{zahl(lage['besucher_heute'], 'Besuch', 'Besuche')}")


with st.sidebar:
    st.caption("Modell: GLM-5.3 Flash (Swiss AI Research Platform)  \n🧠 Reasoning: immer maximal")
    if st.button("Neues Gespräch"):
        st.session_state.pop("thread", None)
        st.session_state.pop("verlauf", None)
    st.markdown("**Beispiele**\n- Was ist diese Woche fällig?\n- Wie wird die Gruppenarbeit in GenAI bewertet?\n"
                "- Wie viele Folien darf das Pitch Deck in Entrepreneurship haben?\n- Wann ist die Marketing-Präsentation?")
    st.divider()
    auslastung()


def zeige_stellen(quellen: list[str], antwort: str, frage: str) -> None:
    """Gefundene Stellen als Karten: Modul, Datei und Seite, «zitiert», Suchbegriffe fett; Fristen als Liste."""
    stellen, fristen = zerlegen(quellen, antwort)
    if not stellen and not fristen:
        return
    zitiert = sum(s.zitiert for s in stellen)
    teile = [f"{len(stellen)} Stellen" if stellen else "", f"{len(fristen)} Termine" if fristen else ""]
    titel = "📄 Gefundene Stellen · " + " · ".join(x for x in teile if x) + (f" · {zitiert} zitiert" if zitiert else "")
    begriffe = suchbegriffe(frage)
    with st.expander(titel):
        if fristen:
            st.markdown("**📅 Termine**")
            st.markdown("\n".join(f"- **{f.datum}**{' ' + f.zeit if f.zeit else ''} · :{farbe(f.modul)}-badge[{f.modul}] "
                                   f"{als_markdown(f.titel, [])}" for f in fristen))
        for s in stellen:
            with st.container(border=True):
                kopf = f":{farbe(s.modul)}-badge[{s.modul}] **{als_markdown(s.datei, [])}**"
                kopf += f" · S. {s.seite}" if s.seite else ""
                kopf += " :green-badge[:material/check: in der Antwort zitiert]" if s.zitiert else ""
                st.markdown(kopf)
                st.markdown(f"<small>{als_markdown(s.text, begriffe)}</small>", unsafe_allow_html=True)


st.session_state.setdefault("thread", str(uuid.uuid4()))
st.session_state.setdefault("verlauf", [])

for eintrag in st.session_state["verlauf"]:
    with st.chat_message(eintrag["rolle"]):
        st.markdown(eintrag["text"])
        if eintrag.get("quellen"):
            zeige_stellen(eintrag["quellen"], eintrag["text"], eintrag.get("frage", ""))

if frage := st.chat_input("Deine Frage zum Studium …"):
    st.session_state["verlauf"].append({"rolle": "user", "text": frage})
    with st.chat_message("user"):
        st.markdown(frage)
    with st.chat_message("assistant"):
        status, feld, text = st.empty(), st.empty(), ""
        hinweise = {"unterlagen_durchsuchen": "🔎 Durchsuche die Unterlagen …", "fristen_anzeigen": "📅 Schaue in die Fristen …",
                    "module_auflisten": "📚 Liste die Module …"}
        nummer, start = schlange().anstellen(), time.time()
        try:  # finally gibt den Platz auch frei, wenn jemand die Seite schliesst oder neu lädt
            while (stelle := schlange().position(nummer)) > 0:
                status.caption(f"⏳ Gerade fragen viele gleichzeitig. Du bist Nr. {stelle} in der Warteschlange …")
                time.sleep(1)
            status.caption("Denke nach …")
            for art, inhalt in fragen_live(graph, frage, st.session_state["thread"]):
                if art == "werkzeug":  # Zwischentext vor einer Suche verwerfen, nur die Endantwort bleibt stehen
                    status.caption(hinweise.get(inhalt, "Arbeite …"))
                    text = ""
                    feld.empty()
                elif art == "denken":  # Entwurf verwerfen: Jetzt schreibt das Modell mit Reasoning die Antwort
                    status.caption("🧠 Denke über die Antwort nach …")
                    text = ""
                    feld.empty()
                elif art == "text":
                    status.empty()
                    text += inhalt
                    feld.markdown(text + " ▌")
                else:
                    r = inhalt
        finally:
            schlange().fertig(nummer)
        betrieb().frage_erledigt(st.session_state["besucher"], start)
        status.empty()
        feld.markdown(r["antwort"])
        zeige_stellen(r["quellen"], r["antwort"], frage)
    st.session_state["verlauf"].append({"rolle": "assistant", "text": r["antwort"], "quellen": r["quellen"], "frage": frage})
