"""
LLM insight service for AI betting recommendations.
Supports OpenAI (GPT-4o-mini) and Google Gemini.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from services.ai_recommendation_service import get_ai_recommendation_service


def _build_payload(base: Dict[str, Any]) -> Dict[str, Any]:
    recommendations = base.get("recommendations") or []
    top_pick = base.get("top_pick")
    next_game = base.get("next_game") or {}
    team = base.get("team")

    return {
        "team": team,
        "next_game": {
            "home_team": next_game.get("home_team"),
            "away_team": next_game.get("away_team"),
            "commence_time": next_game.get("commence_time"),
        },
        "top_pick": top_pick,
        "recommendations": recommendations[:4],
        "risk_flags": base.get("risk_flags") or [],
    }


def _system_prompt() -> str:
    return (
        "Jesteś analitykiem zakładów NBA. Zwróć krótki, ostrożny insight "
        "bez gwarancji wygranej. Opieraj się wyłącznie na podanych danych. "
        "Odpowiedz w JSON z polami: summary (string), bullets (array string), warnings (array string)."
    )


def _user_prompt(payload: Dict[str, Any]) -> str:
    return (
        "Dane wejściowe (JSON):\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Wymagania:\n"
        "- summary: 2-3 zdania po polsku, bez przesady, bez obietnic\n"
        "- bullets: 3-5 krótkich punktów (fakty z danych)\n"
        "- warnings: jeśli brak danych/ryzyka, dodaj ostrzeżenia\n"
    )


def _safe_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        return {
            "summary": text.strip()[:600] if text else "",
            "bullets": [],
            "warnings": ["NON_JSON_RESPONSE"],
        }


async def _call_openai(model: str, api_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": _user_prompt(payload)},
        ],
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    return _safe_json(content)


async def _call_gemini(model: str, api_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": _system_prompt() + "\n\n" + _user_prompt(payload)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
    text = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [{}])[0].get("text", "")
    return _safe_json(text)


async def generate_llm_insight(team_abbrev: str, provider: str = "auto") -> Dict[str, Any]:
    base = await get_ai_recommendation_service().get_team_recommendation(team_abbrev)
    payload = _build_payload(base)

    if not base.get("next_game"):
        return {
            "provider": "none",
            "available": False,
            "model": None,
            "summary": None,
            "bullets": [],
            "warnings": ["NO_NEXT_GAME"],
            "generated_at": datetime.utcnow().isoformat(),
        }

    openai_key = os.getenv("OPENAI_API_KEY", "")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    chosen = provider.lower().strip()
    if chosen == "auto":
        if openai_key:
            chosen = "openai"
        elif gemini_key:
            chosen = "gemini"
        else:
            chosen = "none"

    if chosen == "openai" and not openai_key:
        return {
            "provider": "openai",
            "available": False,
            "model": openai_model,
            "summary": None,
            "bullets": [],
            "warnings": ["OPENAI_API_KEY_MISSING"],
            "generated_at": datetime.utcnow().isoformat(),
        }

    if chosen == "gemini" and not gemini_key:
        return {
            "provider": "gemini",
            "available": False,
            "model": gemini_model,
            "summary": None,
            "bullets": [],
            "warnings": ["GEMINI_API_KEY_MISSING"],
            "generated_at": datetime.utcnow().isoformat(),
        }

    if chosen == "openai":
        insight = await _call_openai(openai_model, openai_key, payload)
        return {
            "provider": "openai",
            "available": True,
            "model": openai_model,
            "summary": insight.get("summary"),
            "bullets": insight.get("bullets") or [],
            "warnings": insight.get("warnings") or [],
            "generated_at": datetime.utcnow().isoformat(),
        }

    if chosen == "gemini":
        insight = await _call_gemini(gemini_model, gemini_key, payload)
        return {
            "provider": "gemini",
            "available": True,
            "model": gemini_model,
            "summary": insight.get("summary"),
            "bullets": insight.get("bullets") or [],
            "warnings": insight.get("warnings") or [],
            "generated_at": datetime.utcnow().isoformat(),
        }

    return {
        "provider": "none",
        "available": False,
        "model": None,
        "summary": None,
        "bullets": [],
        "warnings": ["NO_PROVIDER_AVAILABLE"],
        "generated_at": datetime.utcnow().isoformat(),
    }
