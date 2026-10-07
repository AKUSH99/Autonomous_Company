"""Chat-Oberfläche (Streamlit):  python -m studienassistent app"""
from __future__ import annotations

import uuid

import streamlit as st

from studienassistent.__main__ import lade_alles
from studienassistent.agent import fragen_live
from studienassistent.stellen import als_markdown, farbe, suchbegriffe, zerlegen

MODELL = "glm-flash"  # GLM-5.3 Flash; die Antwort entsteht immer mit maximalem Reasoning

st.set_page_config(page_title="FHNW Studienassistent", page_icon="🎓")
st.title("FHNW Studienassistent")
st.caption("Fragen zu Modulen, Prüfungen, Abgaben und Fristen im BAI-Herbstsemester 2026 – jede Antwort mit Quelle.")

with st.sidebar:
    st.caption("Modell: GLM-5.3 Flash (Swiss AI Research Platform)  \n🧠 Reasoning: immer maximal")
    if st.button("Neues Gespräch"):
        st.session_state.pop("thread", None)
        st.session_state.pop("verlauf", None)
    st.markdown("**Beispiele**\n- Was ist diese Woche fällig?\n- Wie wird die Gruppenarbeit in GenAI bewertet?\n"
                "- Wie viele Folien darf das Pitch Deck in Entrepreneurship haben?\n- Wann ist die Marketing-Präsentation?")


@st.cache_resource(show_spinner="Unterlagen werden geladen …")
def agent(modell: str):
    return lade_alles(modell, denken=True)


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


graph, suche, _ = agent(MODELL)
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
        status.caption("Denke nach …")
        hinweise = {"unterlagen_durchsuchen": "🔎 Durchsuche die Unterlagen …", "fristen_anzeigen": "📅 Schaue in die Fristen …",
                    "module_auflisten": "📚 Liste die Module …"}
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
        status.empty()
        feld.markdown(r["antwort"])
        zeige_stellen(r["quellen"], r["antwort"], frage)
    st.session_state["verlauf"].append({"rolle": "assistant", "text": r["antwort"], "quellen": r["quellen"], "frage": frage})
