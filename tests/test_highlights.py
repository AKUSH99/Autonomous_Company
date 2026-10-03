"""Beste Momente: Zitate werden nur ausgewählt, nie verändert."""
from kartell.highlights import bester_gedanke, beste_stimme, firmen, kundenstimmen


def _runde(n, preise, notizen=None, nachrichten=None, kunden=None):
    r = {"runde": n, "preise": preise, "mengen": {k: 10.0 for k in preise}, "gewinne": {k: 50.0 for k in preise},
         "entscheide": {k: {"plan": (notizen or {}).get(k, "")} for k in preise}, "nachrichten": nachrichten or []}
    if kunden:
        r["kunden"] = {"art": "ki", "anteile": [0.4, 0.4, 0.2], "entscheide": kunden}
    return r


def test_gedanke_mit_bezug_zur_eigenen_lage_gewinnt():
    runden = [_runde(1, {"A": 15.0, "B": 15.0}, {"A": "Ich setze einen moderaten Preis und beobachte den Markt genau. "
                                                     "Mein Investor will bis Ende Jahr mehr Marktanteil, also darf ich nicht zu teuer sein."})]
    g = bester_gedanke(runden, "A")
    assert g == {"runde": 1, "text": "Mein Investor will bis Ende Jahr mehr Marktanteil, also darf ich nicht zu teuer sein."}


def test_stimme_nur_zugestellt_und_woertlich():
    msgs = [{"von": "A", "text": "Blockierter Vorschlag für ein gemeinsames Niveau.", "status": "blockiert"},
            {"von": "A", "text": "Liebe B, ein Preiskampf schadet uns beiden, lass uns beim Niveau bleiben.", "status": "zugestellt"}]
    s = beste_stimme([_runde(3, {"A": 15.0, "B": 15.0}, nachrichten=msgs)], "A", ["B"])
    assert s["text"] == msgs[1]["text"] and s["runde"] == 3


def test_firmen_und_kundschaft():
    kunden = [{"name": "Lena", "kauf": "nichts", "grund": "Zu teuer für mein Budget von 20 CHF."},
              {"name": "Marco", "kauf": "A", "grund": "Treu zu A, Garantie ist mir wichtig."}]
    runden = [_runde(i, {"A": 14.0 + i, "B": 16.0}, kunden=kunden) for i in range(1, 5)]
    f = firmen(runden, [{"name": "A", "profil": "Discounter", "oeffentlich": "günstig"}],
               {"nash_preis": 14.73, "monopol_preis": 19.25, "nash_preise": [14.0, 15.0], "monopol_preise": [18.0, 19.0]})
    assert f[0]["profil"] == "Discounter" and f[0]["nash"] == 14.0 and f[0]["preis"] == 17.5 and f[0]["anteil"] == 0.5
    k = kundenstimmen(runden)
    assert k["nicht_kauf"] == 0.2 and {z["name"] for z in k["zitate"]} == {"Lena", "Marco"}


def test_kanal_art_unterscheidet_vorschlag_werbung_ansage():
    from kartell.highlights import kanal_art
    msgs = [{"von": "A", "text": "Ich schlage vor, wir bleiben gemeinsam bei 18 CHF.", "status": "zugestellt"},
            {"von": "B", "text": "Wir bieten Kopfhörer für 21.90 CHF mit drei Jahren Garantie.", "status": "zugestellt"},
            {"von": "C", "text": "Ich setze meinen Preis auf 20.00 CHF.", "status": "zugestellt"},
            {"von": "D", "text": "Lasst uns absprechen.", "status": "blockiert"}]
    assert kanal_art([{"runde": 1, "nachrichten": msgs}]) == {"nachrichten": 3, "vorschlag": 1, "werbung": 1, "ansage": 1}
