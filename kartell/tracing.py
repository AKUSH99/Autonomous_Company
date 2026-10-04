"""Tracing mit LangSmith: jeder Lauf als Baum aus Graph-Knoten, LLM-Aufrufen und Werkzeugen.

Eingeschaltet wird es nur über Umgebungsvariablen – ohne sie ändert sich nichts und es geht nichts nach aussen:

    LANGSMITH_TRACING=true
    LANGSMITH_API_KEY=lsv2_...
    LANGSMITH_PROJECT=ki-kartell        # optional, sonst "default"

LangGraph meldet die Knoten (kommunikation, compliance_filter, preisentscheid, aufsicht, markt) von selbst.
Weil unsere Backends die Anbieter-SDKs direkt aufrufen statt über LangChain, hängen wir die LLM-Aufrufe und
Werkzeuge hier als eigene Läufe ein – mit Prompts, strukturierter Antwort, Tokens und Modellname.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from langsmith import traceable
from langsmith.utils import tracing_is_enabled

if TYPE_CHECKING:
    from .config import LLMSpec
    from .llm.base import LLMClient


def aktiv() -> bool:
    return bool(tracing_is_enabled())


def _eingaben(argumente: dict) -> dict:
    schema = argumente.get("schema")
    werkzeuge = argumente.get("werkzeuge") or []
    return {
        "messages": [{"role": "system", "content": argumente.get("system", "")},
                     {"role": "user", "content": argumente.get("nutzer", "")}],
        "schema": getattr(schema, "__name__", str(schema)),
        "werkzeuge": [w.name for w in werkzeuge],
    }


def _ausgaben(antwort) -> dict:
    objekt = antwort.objekt
    return {
        "output": objekt.model_dump(mode="json") if hasattr(objekt, "model_dump") else objekt,
        "werkzeug_aufrufe": antwort.werkzeug_aufrufe,
        # LangSmith liest Tokens (und daraus Kosten) aus usage_metadata.
        "usage_metadata": {"input_tokens": antwort.input_tokens, "output_tokens": antwort.output_tokens,
                           "total_tokens": antwort.input_tokens + antwort.output_tokens},
    }


def mit_tracing(client: LLMClient, spec: LLMSpec) -> LLMClient:
    """Meldet jeden `strukturiert`-Aufruf des Clients als LLM-Lauf. Ohne LANGSMITH_TRACING ein reiner Durchreicher."""
    provider = "anthropic" if spec.provider == "anthropic" else (spec.base_url or spec.provider)
    client.strukturiert = traceable(
        run_type="llm",
        name=f"llm:{client.name}",
        metadata={"ls_provider": provider, "ls_model_name": spec.model},
        process_inputs=_eingaben,
        process_outputs=_ausgaben,
    )(client.strukturiert)
    return client


def werkzeug_lauf(funktion: Callable[..., tuple[str, bool]]) -> Callable[..., tuple[str, bool]]:
    """Meldet einen Werkzeugaufruf als Tool-Lauf, benannt nach dem Werkzeug."""
    verfolgt = traceable(run_type="tool", process_inputs=lambda a: {"name": a.get("name"), "argumente": a.get("argumente")},
                         process_outputs=lambda r: {"ergebnis": r[0], "fehler": r[1]})(funktion)

    def aufruf(werkzeuge, name, argumente, protokoll):
        if not aktiv():
            return funktion(werkzeuge, name, argumente, protokoll)
        return verfolgt(werkzeuge, name, argumente, protokoll, langsmith_extra={"name": f"werkzeug:{name}"})

    return aufruf


def lauf_config(cfg, seed: int) -> dict:
    """Name, Tags und Metadaten für den obersten Lauf, damit sich Läufe in LangSmith filtern lassen."""
    modelle = sorted({a.llm.model for a in cfg.agenten_liste() if a.llm.provider not in ("scripted", "regeln")})
    return {
        "run_name": f"{cfg.name} · seed {seed}",
        "tags": [cfg.name, f"compliance:{cfg.compliance.modus}", "kanal" if cfg.kommunikation.aktiv else "ohne-kanal"],
        "metadata": {"experiment": cfg.name, "titel": cfg.titel, "seed": seed, "runden": cfg.runden,
                     "firmen": cfg.markt.firmen, "modelle": modelle},
    }
