from kartell.agents.pricing import LLMPreisAgent
from kartell.agents.schemas import KanalNachricht, PreisEntscheid
from kartell.config import AgentSpec, ExperimentConfig, LLMSpec, lade_config
from kartell.graph import Simulation
from kartell.llm import LLMAntwort, LLMFehler


def test_demo_ohne_aufsicht_fuehrt_zum_kartell():
    cfg = lade_config("experiments/demo_absprache_ohne_aufsicht.yaml")
    cfg.runden = 6
    verlauf = Simulation(cfg).starte()
    assert len(verlauf) == 6
    b = Simulation(cfg).benchmarks
    assert all(abs(p - b.monopol_preis) < 0.5 for p in verlauf[-1]["preise"].values())


def test_filter_blockiert_absprachen_und_preise_fallen():
    cfg = lade_config("experiments/demo_absprache_mit_filter.yaml")
    cfg.runden = 6
    sim = Simulation(cfg)
    verlauf = sim.starte()
    nachrichten = [n for r in verlauf for n in r["nachrichten"]]
    assert nachrichten and all(n["status"] == "blockiert" for n in nachrichten)
    assert all(abs(p - sim.benchmarks.nash_preis) < 0.5 for p in verlauf[-1]["preise"].values())


class _SkriptLLM:
    """Simuliert ein LLM: antwortet je nach Schema, merkt sich die Prompts."""
    name = "fake"

    def __init__(self, preis=17.0, text="Hallo", fehler_bei=None):
        self.preis, self.text, self.fehler_bei, self.prompts = preis, text, fehler_bei, []

    def strukturiert(self, system, nutzer, schema):
        self.prompts.append(nutzer)
        if self.fehler_bei and self.fehler_bei in nutzer:
            raise LLMFehler("simulierter Ausfall")
        if schema is PreisEntscheid:
            return LLMAntwort(PreisEntscheid(beobachtungen="b", plan="p", erkenntnisse="e", preis=self.preis), 50, 10)
        return LLMAntwort(KanalNachricht(ueberlegung="u", nachricht=self.text), 40, 5)


def _cfg(**kw) -> ExperimentConfig:
    return ExperimentConfig(name="test", runden=3, kommunikation={"aktiv": True}, **kw)


def test_llm_agenten_im_graphen_mit_kanal_und_historie():
    cfg = _cfg()
    llms = [_SkriptLLM(preis=16.0, text="Neue Farben da"), _SkriptLLM(preis=18.0, text="")]
    agenten = [LLMPreisAgent(AgentSpec(name=n, llm=LLMSpec()), cfg, llm, 10.0) for n, llm in zip(["Shop A", "Shop B"], llms)]
    verlauf = Simulation(cfg, agenten=agenten).starte()
    assert [r["preise"] for r in verlauf][-1] == {"Shop A": 16.0, "Shop B": 18.0}
    assert verlauf[0]["tokens"]["input"] > 0
    # Shop B sieht in Runde 3 die Historie und die Nachricht von Shop A
    letzter_prompt = llms[1].prompts[-1]
    assert "Marktverlauf" in letzter_prompt and "Neue Farben da" in letzter_prompt
    # LLM-Agenten sehen nie den Nash- oder Monopolpreis
    assert "14.73" not in letzter_prompt and "19.25" not in letzter_prompt


def test_guardrail_preisgrenze_und_ausfall():
    cfg = _cfg()
    a = LLMPreisAgent(AgentSpec(name="Shop A", llm=LLMSpec()), cfg, _SkriptLLM(preis=999.0), 10.0)
    b = LLMPreisAgent(AgentSpec(name="Shop B", llm=LLMSpec()), cfg, _SkriptLLM(preis=15.0, fehler_bei="Runde 2"), 10.0)
    verlauf = Simulation(cfg, agenten=[a, b]).starte()
    assert verlauf[0]["preise"]["Shop A"] == 50.0 and verlauf[0]["entscheide"]["Shop A"]["korrigiert"]
    assert verlauf[1]["entscheide"]["Shop B"]["fehler"] and verlauf[1]["preise"]["Shop B"] == 15.0


def test_dauerhafter_modellausfall_bricht_lauf_ab():
    import pytest

    from kartell.graph import MAX_AUSFALL_RUNDEN, ModellAusfall
    cfg = _cfg()
    cfg.runden = 10
    agenten = [LLMPreisAgent(AgentSpec(name=n, llm=LLMSpec()), cfg, _SkriptLLM(fehler_bei="Runde"), 10.0)
               for n in ("Shop A", "Shop B")]
    protokoll = []

    class Logger:
        def runde(self, eintrag):
            protokoll.append(eintrag)

    with pytest.raises(ModellAusfall):
        Simulation(cfg, agenten=agenten, logger=Logger()).starte()
    assert len(protokoll) == MAX_AUSFALL_RUNDEN  # die gescheiterten Runden bleiben im Protokoll sichtbar
