"""Dashboard für Demo und Analyse:  streamlit run dashboard/app.py

Zeigt Läufe live (die Simulation schreibt jede Runde in runden.jsonl) oder spielt sie für die
Präsentation Runde für Runde ab.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

from kartell.bericht import lade_lauf  # noqa: E402
from kartell.config import anzeigename  # noqa: E402

st.set_page_config(page_title="KI-Kartell", layout="wide")
# zehn gut unterscheidbare Farben, damit auch Versuche mit 10 Shops lesbar bleiben
FARBEN = ["#1C86C9", "#D9730D", "#8E44D8", "#1E9A57", "#C0392B", "#7F7F7F", "#BCBD22", "#17BECF", "#E377C2", "#8C564B"]

with st.sidebar:
    st.header("Läufe")
    runs_ordner = Path(st.text_input("Ordner", str(WURZEL / "runs"), help="wird rekursiv durchsucht, z. B. auch der Branch \"ergebnisse\""))
    laeufe = sorted({m.parent for m in runs_ordner.rglob("meta.json")}, key=lambda o: o.name, reverse=True) if runs_ordner.exists() else []

    with st.expander("Neuen Lauf starten"):
        configs = sorted((WURZEL / "experiments").glob("*.yaml"))
        wahl = st.selectbox("Experiment", configs, format_func=lambda p: p.stem)
        runden = st.number_input("Runden", 1, 300, 20)
        st.caption("Echte LLM-Läufe kosten Geld – vorher `python -m kartell schaetzung` prüfen.")
        if st.button("Starten", type="primary"):
            subprocess.Popen([sys.executable, "-m", "kartell", "lauf", str(wahl), "--ja", "--runden", str(runden),
                              "--wiederholungen", "1", "--ausgabe", str(runs_ordner)], cwd=WURZEL)
            time.sleep(1.5)
            st.rerun()

    if not laeufe:
        st.info("Noch keine Läufe. Starte einen Lauf oder `python -m kartell demo`.")
        st.stop()
    ordner = st.selectbox("Lauf", laeufe, format_func=lambda p: p.name)
    live = st.toggle("Live aktualisieren", value=not (ordner / "ergebnis.json").exists())

lauf = lade_lauf(ordner)
meta, runden_alle, b = lauf["meta"], lauf["runden"], lauf["benchmarks"]
gesamt = meta["config"]["runden"]

st.title(anzeigename(meta["name"], meta["config"].get("titel", "")))
st.caption(f"{meta.get('beschreibung', '')} · Agenten: {', '.join(f'{k} ({v})' for k, v in meta['agenten'].items())} · "
           f"Compliance: {meta['compliance'] or 'aus'}")

if not runden_alle:
    st.info("Warte auf die erste Runde …")
    time.sleep(2)
    st.rerun()

bis = st.slider("Wiedergabe bis Runde", 1, len(runden_alle), len(runden_alle)) if not live else len(runden_alle)
runden = runden_alle[:bis]
shops = list(runden[0]["preise"])

letzte = runden[-min(10, len(runden)):]
mittel_preis = sum(p for r in letzte for p in r["preise"].values()) / (len(letzte) * len(shops))
mittel_gewinn = sum(g for r in letzte for g in r["gewinne"].values()) / (len(letzte) * len(shops))
nachrichten = [n for r in runden for n in r.get("nachrichten", [])]
spalten = st.columns(5)
spalten[0].metric("Runde", f"{runden[-1]['runde']} / {gesamt}")
spalten[1].metric("Ø Preis (letzte 10)", f"{mittel_preis:.2f} CHF")
spalten[2].metric("Preisindex", f"{round((mittel_preis - b.nash_preis) / (b.monopol_preis - b.nash_preis), 2) + 0.0:+.2f}",
                  help="0 = Wettbewerb (Nash), 1 = perfektes Kartell (Monopol)")
spalten[3].metric("Kollusionsindex", f"{round((mittel_gewinn - b.nash_gewinn) / (b.monopol_gewinn - b.nash_gewinn), 2) + 0.0:+.2f}",
                  help="Gewinn relativ zu Wettbewerb (0) und Kartell (1)")
spalten[4].metric("Blockierte Nachrichten", f"{sum(n.get('status') == 'blockiert' for n in nachrichten)} / {len(nachrichten)}")

fig = go.Figure()
fig.add_hrect(y0=b.nash_preis, y1=b.monopol_preis, fillcolor="#2E9C86", opacity=0.07, line_width=0)
fig.add_hline(y=b.nash_preis, line_dash="dash", line_color="#2E9C86", annotation_text=f"Wettbewerb (Nash) {b.nash_preis:.2f}")
fig.add_hline(y=b.monopol_preis, line_dash="dash", line_color="#C0392B", annotation_text=f"Kartell (Monopol) {b.monopol_preis:.2f}")
x = [r["runde"] for r in runden]
for i, shop in enumerate(shops):
    fig.add_trace(go.Scatter(x=x, y=[r["preise"][shop] for r in runden], name=shop, mode="lines+markers",
                             line=dict(width=2, color=FARBEN[i % len(FARBEN)]), marker=dict(size=5)))
for r in runden:
    if r.get("abweichung"):
        fig.add_vline(x=r["runde"], line_dash="dot", line_color="#555",
                      annotation_text=f"Abweichung erzwungen ({r['abweichung']['shop']})")
blockiert_x = [r["runde"] for r in runden if any(n.get("status") == "blockiert" for n in r.get("nachrichten", []))]
if blockiert_x:
    fig.add_trace(go.Scatter(x=blockiert_x, y=[b.grenzkosten * 1.05] * len(blockiert_x), mode="markers", name="Nachricht blockiert",
                             marker=dict(symbol="x", size=9, color="#C0392B")))
fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), xaxis_title="Runde", yaxis_title="Preis (CHF)",
                  legend=dict(orientation="h", y=1.08), hovermode="x unified")
st.plotly_chart(fig, width="stretch")

links, rechts = st.columns([3, 2])
with links:
    st.subheader("Kanal & Compliance")
    if not nachrichten:
        st.caption("Keine Nachrichten (Kanal aus oder Agenten schweigen).")
    for r in reversed(runden[-15:]):
        if r.get("abweichung"):
            st.info(f"Runde {r['runde']}: {r['abweichung']['shop']} wird von der Simulation auf den Wettbewerbspreis gesetzt "
                    "(erzwungene Abweichung). Die Nachrichten der nächsten Runde zeigen die Reaktion.")
        if (r.get("marktbeobachtung") or {}).get("hinweis"):
            st.caption(f"Marktbeobachtung nach Runde {r['runde']}: {r['marktbeobachtung']['hinweis']}")
        for n in r.get("nachrichten", []):
            status = n.get("status", "zugestellt")
            symbol = "🚫" if status == "blockiert" else "✉️"
            st.markdown(f"**Runde {r['runde']} · {n['von']}** {symbol} {status}  \n> {n['text']}")
            c = n.get("compliance")
            if c:
                st.caption(f"Compliance: {c.get('kategorie')} – {c.get('begruendung')} "
                           f"{'· ' + ', '.join(c.get('rechtsgrundlagen') or []) if c.get('rechtsgrundlagen') else ''}")
with rechts:
    st.subheader("Strategienotizen")
    r = runden[-1]
    for shop in shops:
        e = r["entscheide"].get(shop, {})
        with st.expander(f"{shop} · Runde {r['runde']} · {r['preise'][shop]:.2f} CHF", expanded=True):
            st.markdown(f"**Plan:** {e.get('plan') or '–'}")
            st.markdown(f"**Erkenntnisse:** {e.get('erkenntnisse') or '–'}")
            for w in e.get("werkzeug_aufrufe") or []:
                st.caption(f"Werkzeug nachfrage_schaetzen({w.get('argumente')}) → {str(w.get('ergebnis', ''))[:200]}")
            if e.get("erzwungen"):
                st.info(f"Von der Simulation auf den Wettbewerbspreis gesetzt – gewollt waren {e['preis_gewollt']:.2f} CHF.")
            if e.get("fehler"):
                st.error(e["fehler"])
    for a in r.get("aufsicht", []):
        if a.get("bedenklich"):
            st.warning(f"Aufsicht zu {a['agent']}: {a['hinweis']}")

with st.expander("Rohdaten"):
    st.dataframe(pd.DataFrame([{"runde": r["runde"], **{f"preis {s}": r["preise"][s] for s in shops},
                                **{f"gewinn {s}": r["gewinne"][s] for s in shops}} for r in runden]), width="stretch")

if live and not (ordner / "ergebnis.json").exists():
    time.sleep(2)
    st.rerun()
