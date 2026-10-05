"""Chat-Oberfläche (Streamlit):  python -m studienassistent app"""
from __future__ import annotations

import uuid

import streamlit as st

from studienassistent.__main__ import lade_alles
from studienassistent.agent import fragen_live

st.set_page_config(page_title="FHNW Studienassistent", page_icon="🎓")
st.title("FHNW Studienassistent")
st.caption("Fragen zu Modulen, Prüfungen, Abgaben und Fristen im BAI-Herbstsemester 2026 – jede Antwort mit Quelle.")

with st.sidebar:
    modell = st.selectbox("Modell", ["deepseek", "apertus", "glm"], help="Sprachmodelle der Swiss AI Research Platform")
    denken = st.toggle("Reasoning", value=False, help="Das Modell denkt vor der Antwort nach – genauer, aber langsamer.")
    if st.button("Neues Gespräch"):
        st.session_state.pop("thread", None)
        st.session_state.pop("verlauf", None)
    st.markdown("**Beispiele**\n- Was ist diese Woche fällig?\n- Wie wird die Gruppenarbeit in GenAI bewertet?\n"
                "- Wie viele Folien darf das Pitch Deck in Entrepreneurship haben?\n- Wann ist die Marketing-Präsentation?")


@st.cache_resource(show_spinner="Unterlagen werden geladen …")
def agent(modell: str, denken: bool):
    return lade_alles(modell, denken)


graph, suche, _ = agent(modell, denken)
st.session_state.setdefault("thread", str(uuid.uuid4()))
st.session_state.setdefault("verlauf", [])

for eintrag in st.session_state["verlauf"]:
    with st.chat_message(eintrag["rolle"]):
        st.markdown(eintrag["text"])
        if eintrag.get("quellen"):
            with st.expander("Gefundene Stellen"):
                for q in eintrag["quellen"]:
                    st.text(q[:2500])

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
            elif art == "text":
                status.empty()
                text += inhalt
                feld.markdown(text + " ▌")
            else:
                r = inhalt
        status.empty()
        feld.markdown(r["antwort"])
        if r["quellen"]:
            with st.expander("Gefundene Stellen"):
                for q in r["quellen"]:
                    st.text(q[:2500])
    st.session_state["verlauf"].append({"rolle": "assistant", "text": r["antwort"], "quellen": r["quellen"]})
