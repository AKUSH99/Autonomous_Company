"""Die besten Momente eines Laufs mit echten Firmen: wörtliche Zitate, automatisch ausgewählt.

Für jede Firma ein öffentlicher Satz („Stimme“) und ein privater Gedanke, bevorzugt einer, der sich auf die eigene Lage
bezieht (Investor, Bank, Familie, Aktionäre …) oder auf das Verhältnis zur Konkurrenz (Absprache, Preiskampf …). Dazu
Kennzahlen je Firma und typische Begründungen der KI-Kundschaft. Alle Texte stammen unverändert aus den Rohdaten;
ausgewählt wird nur, nie umformuliert.
"""
from __future__ import annotations

import re

PROFIL = re.compile(r"investor|marktanteil|bank|kredit|liquidit|quartal|tochter|familie|übergab|nachfolg|dividend|aktionär|"
                    r"verlust|wachstum|gründer|discounter|premium|beratung|garantie|werkstatt|lager", re.I)
KONKURRENZ = re.compile(r"absprach|kooperat|gemeinsam|gleichgewicht|preiskampf|preiskrieg|unterbiet|signal|niveau|abstimm|"
                        r"koordin|vertrau|bestraf|strafe|zurückkehr|rückkehr|alle shops|branche|konkurrenz", re.I)
KUNDE = re.compile(r"garantie|beratung|schweiz|billig|discounter|premium|teuer|budget|treu|aktion|bewertung|schnell|liefer", re.I)


def saetze(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if len(s.strip()) > 25]


def _punkte(satz: str) -> float:
    return 2 * len(PROFIL.findall(satz)) + len(KONKURRENZ.findall(satz)) + min(len(satz), 220) / 220


def bester_gedanke(runden: list[dict], firma: str) -> dict | None:
    """Der aussagekräftigste Satz aus den privaten Notizen einer Firma (bei Gleichstand der spätere)."""
    beste = None
    for r in runden:
        e = (r.get("entscheide") or {}).get(firma) or {}
        for feld in ("plan", "erkenntnisse", "beobachtungen"):
            for s in saetze(e.get(feld, "")):
                if len(s) > 320:
                    continue
                kandidat = (_punkte(s), r["runde"], s)
                if beste is None or kandidat[:2] >= beste[:2]:
                    beste = kandidat
    return None if beste is None or beste[0] < 1 else {"runde": beste[1], "text": beste[2]}


def beste_stimme(runden: list[dict], firma: str, andere: list[str]) -> dict | None:
    """Die aussagekräftigste zugestellte Nachricht einer Firma im öffentlichen Kanal."""
    beste = None
    for r in runden:
        for m in r.get("nachrichten", []):
            if m.get("von") != firma or (m.get("status") and m["status"] != "zugestellt"):
                continue
            nennt = sum(a.split()[0].split(".")[0].lower() in m["text"].lower() for a in andere)
            kandidat = (len(KONKURRENZ.findall(m["text"])) + nennt + min(len(m["text"]), 300) / 300, r["runde"], m["text"])
            if beste is None or kandidat[:2] >= beste[:2]:
                beste = kandidat
    return None if beste is None else {"runde": beste[1], "text": beste[2]}


def firmen(runden: list[dict], profile: list[dict], benchmarks: dict) -> list[dict]:
    """Kennzahlen und Zitate je Firma, gemessen über die zweite Hälfte des Laufs."""
    namen = list(runden[0]["preise"])
    haelfte = runden[len(runden) // 2:] or runden
    nash = benchmarks.get("nash_preise") or [benchmarks["nash_preis"]] * len(namen)
    monopol = benchmarks.get("monopol_preise") or [benchmarks["monopol_preis"]] * len(namen)
    menge_gesamt = sum(sum(r["mengen"].values()) for r in haelfte) or 1
    ergebnis = []
    for i, n in enumerate(namen):
        profil = next((p for p in profile if p.get("name") == n), {})
        preis = sum(r["preise"][n] for r in haelfte) / len(haelfte)
        ergebnis.append({
            "name": n, "profil": profil.get("profil", ""), "oeffentlich": profil.get("oeffentlich", ""),
            "preis": round(preis, 2), "nash": round(nash[i], 2), "monopol": round(monopol[i], 2),
            # 0 = eigener Wettbewerbspreis, 1 = eigener Kartellpreis
            "lage": round((preis - nash[i]) / (monopol[i] - nash[i]), 2) if monopol[i] != nash[i] else 0.0,
            "anteil": round(sum(r["mengen"][n] for r in haelfte) / menge_gesamt, 3),
            "gewinn": round(sum(r["gewinne"][n] for r in runden), 2),
            "nachrichten": sum(1 for r in runden for m in r.get("nachrichten", []) if m.get("von") == n),
            "stimme": beste_stimme(runden, n, [a for a in namen if a != n]),
            "gedanke": bester_gedanke(runden, n),
        })
    return ergebnis


def kundenstimmen(runden: list[dict], anzahl: int = 4) -> dict:
    """Typische Begründungen der KI-Kundschaft (verschiedene Personen) und wie viele nichts kaufen."""
    mit_panel = [r for r in runden if (r.get("kunden") or {}).get("art") == "ki" and (r["kunden"].get("anteile"))]
    if not mit_panel:
        return {}
    haelfte = mit_panel[len(mit_panel) // 2:] or mit_panel
    nicht = sum(r["kunden"]["anteile"][-1] for r in haelfte) / len(haelfte)
    kandidaten = sorted(((len(KUNDE.findall(e.get("grund", ""))) + (e.get("kauf") == "nichts") * 0.5, r["runde"], e)
                         for r in haelfte for e in r["kunden"].get("entscheide", []) if len(e.get("grund", "")) > 20),
                        key=lambda k: (-k[0], -k[1]))
    gesehen, zitate = set(), []
    for _, runde, e in kandidaten:
        # verschiedene Personen und abwechselnd Käufe und Nicht-Käufe
        if e["name"] in gesehen or (len(zitate) % 2 == 1 and e.get("kauf") == zitate[-1]["kauf"] and len(kandidaten) > anzahl * 3):
            continue
        gesehen.add(e["name"])
        zitate.append({"runde": runde, "name": e["name"], "kauf": e.get("kauf"), "grund": e["grund"]})
        if len(zitate) == anzahl:
            break
    return {"nicht_kauf": round(nicht, 3), "zitate": zitate}


def als_text(laeufe: list[dict]) -> str:
    """Kurzbericht für die Auswertung (Markdown)."""
    zeilen = []
    for lauf in laeufe:
        zeilen += [f"## {lauf['name']} · Durchgang {lauf['wiederholung']}", "",
                   "| Firma | Preis Ø 2. Hälfte | eigener Wettbewerbs-/Kartellpreis | Lage | Marktanteil | Gewinn | Nachrichten |",
                   "|---|---|---|---|---|---|---|"]
        for f in lauf["firmen"]:
            zeilen.append(f"| {f['name']} | {f['preis']:.2f} | {f['nash']:.2f} / {f['monopol']:.2f} | {f['lage']:+.2f} | "
                          f"{f['anteil']:.0%} | {f['gewinn']:.0f} | {f['nachrichten']} |")
        zeilen.append("")
        for f in lauf["firmen"]:
            if f["stimme"]:
                zeilen.append(f"- **{f['name']}**, öffentlich (Runde {f['stimme']['runde']}): „{f['stimme']['text']}“")
            if f["gedanke"]:
                zeilen.append(f"- **{f['name']}**, privat (Runde {f['gedanke']['runde']}): „{f['gedanke']['text']}“")
        k = lauf.get("kunden") or {}
        if k:
            zeilen += ["", f"Kundschaft: {k['nicht_kauf']:.0%} kaufen in der zweiten Hälfte nichts."]
            zeilen += [f"- {z['name']} ({'kauft nichts' if z['kauf'] == 'nichts' else 'kauft bei ' + str(z['kauf'])}, Runde {z['runde']}): „{z['grund']}“"
                       for z in k["zitate"]]
        zeilen.append("")
    return "\n".join(zeilen)
