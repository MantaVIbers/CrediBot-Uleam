#!/usr/bin/env python3
"""Pruebas conversacionales end-to-end simulando cliente + bot."""
from __future__ import annotations

import json
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Configurar la ruta del proyecto para importaciones
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.repositories.conversation_repository import get_or_create_active_conversation  # noqa: E402
from app.repositories.supabase_client import get_supabase_client  # noqa: E402
from app.repositories.user_repository import get_or_create_user  # noqa: E402
from app.services.conversation_service import process_message  # noqa: E402

# Prefijo telefónico base para generar números de prueba únicos
PHONE_BASE = 593991000000


@dataclass
class Step:
    user: str
    bot: str = ""
    note: str = ""


@dataclass
class Scenario:
    id: str
    title: str
    category: str
    phone: str
    steps: list[Step] = field(default_factory=list)
    expected: list[str] = field(default_factory=list)
    passed: bool = False
    error: str | None = None
    final_state: str | None = None


def _phone(n: int) -> str:
    return str(PHONE_BASE + n)


def _run_steps(phone: str, messages: list[str | tuple[str, str]]) -> list[Step]:
    steps: list[Step] = []
    for item in messages:
        if isinstance(item, tuple):
            user, note = item
        else:
            user, note = item, ""
        bot = process_message(phone, user)
        steps.append(Step(user=user, bot=bot, note=note))
        time.sleep(0.15)
    return steps


def _final_state(phone: str) -> str:
    user = get_or_create_user(phone)
    conv = get_or_create_active_conversation(user["id"])
    return conv.get("current_state", "?")


def _check_all(text: str, needles: list[str]) -> bool:
    lower = text.lower()
    return all(n.lower() in lower for n in needles)


def _build_scenarios() -> list[Scenario]:
    return [
        Scenario(
            id="S01",
            title="Precalificación exitosa con lenguaje natural",
            category="Flujo feliz",
            phone=_phone(1),
            expected=["preaprobado", "maría", "cuota"],
        ),
        Scenario(
            id="S02",
            title="Perfil excelente — score alto",
            category="Flujo feliz",
            phone=_phone(2),
            expected=["preaprobado", "820"],
        ),
        Scenario(
            id="S03",
            title="Menú en lenguaje natural",
            category="Entrada humana",
            phone=_phone(3),
            expected=["nombre completo"],
        ),
        Scenario(
            id="S04",
            title="Cédula inválida (typo humano)",
            category="Errores de validación",
            phone=_phone(4),
            expected=["no es válida"],
        ),
        Scenario(
            id="S05",
            title="Rechazo de consentimiento",
            category="Consentimiento",
            phone=_phone(5),
            expected=["autorización", "retomarla"],
        ),
        Scenario(
            id="S06",
            title="Reinicio desde consentimiento",
            category="Navegación",
            phone=_phone(6),
            expected=["credibot", "precalificar"],
        ),
        Scenario(
            id="S07",
            title="Perfil alto riesgo con mora",
            category="Reglas de negocio",
            phone=_phone(7),
            expected=["no cumple"],
        ),
        Scenario(
            id="S08",
            title="Lista negra",
            category="Reglas de negocio",
            phone=_phone(8),
            expected=["no cumple", "restricciones"],
        ),
        Scenario(
            id="S09",
            title="Perfil regular — resultado observado",
            category="Reglas de negocio",
            phone=_phone(9),
            expected=["observado"],
        ),
        Scenario(
            id="S10",
            title="Opción 3 — derivación a asesor",
            category="Menú",
            phone=_phone(10),
            expected=["asesor humano"],
        ),
        Scenario(
            id="S11",
            title="Palabra clave asesor en medio del flujo",
            category="Handoff",
            phone=_phone(11),
            expected=["asesor humano"],
        ),
        Scenario(
            id="S12",
            title="Monto inválido (texto sin número)",
            category="Errores de validación",
            phone=_phone(12),
            expected=["mayor a 0"],
        ),
        Scenario(
            id="S13",
            title="Plazo fuera de rango",
            category="Errores de validación",
            phone=_phone(13),
            expected=["entre 3 y 36"],
        ),
        Scenario(
            id="S14",
            title="Nombre inválido (una sola palabra)",
            category="Errores de validación",
            phone=_phone(14),
            expected=["al menos 2 palabras"],
        ),
        Scenario(
            id="S15",
            title="Confirmación negativa en resumen",
            category="Navegación",
            phone=_phone(15),
            expected=["nombre completo"],
        ),
        Scenario(
            id="S16",
            title="Modo IA — pregunta sobre score",
            category="IA / RAG",
            phone=_phone(16),
            expected=["score", "750"],
        ),
        Scenario(
            id="S17",
            title="Modo IA — validar cédula en chat",
            category="IA / Tools",
            phone=_phone(17),
            expected=["0912345675", "válid"],
        ),
        Scenario(
            id="S18",
            title="Tres errores de menú → handoff",
            category="Errores repetidos",
            phone=_phone(18),
            expected=["asesor humano"],
        ),
        Scenario(
            id="S19",
            title="Mora activa con score alto (excelente descalificado)",
            category="Reglas de negocio",
            phone=_phone(19),
            expected=["no cumple", "mora"],
        ),
        Scenario(
            id="S20",
            title="Consentimiento en lenguaje natural",
            category="Entrada humana",
            phone=_phone(20),
            expected=["monto"],
        ),
    ]


def _execute(scenario: Scenario) -> Scenario:
    try:
        if scenario.id == "S01":
            scenario.steps = _run_steps(scenario.phone, [
                ("Hola", "inicio"),
                ("1", "menú precalificar"),
                ("María González", "nombre"),
                ("0912345675", "cédula válida seed"),
                ("sí, autorizo", "consentimiento natural"),
                ("cinco mil", "monto IA"),
                ("un año", "plazo IA"),
                ("mil doscientos", "ingreso IA"),
                ("1", "confirmar"),
            ])
        elif scenario.id == "S02":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Carlos Ortiz Vera", "0911111110", "1",
                "8000", "24", "2500", "1",
            ])
        elif scenario.id == "S03":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "quiero precalificar crédito",
            ])
        elif scenario.id == "S04":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Pedro Salas", "1234567890",
            ])
        elif scenario.id == "S05":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Ana Test", "0912345675", "2",
            ])
        elif scenario.id == "S06":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Luis Test", "0912345675", "Comenzar de nuevo",
            ])
        elif scenario.id == "S07":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Elena Bravo", "0955555552", "1",
                "3000", "12", "1500", "1",
            ])
        elif scenario.id == "S08":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Marcos Zambrano", "1320020025", "1",
                "2000", "12", "1200", "1",
            ])
        elif scenario.id == "S09":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Jorge Cedeño", "0944444447", "1",
                "1500", "12", "900", "1",
            ])
        elif scenario.id == "S10":
            scenario.steps = _run_steps(scenario.phone, ["Hola", "3"])
        elif scenario.id == "S11":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Cliente Handoff", "0912345675", "asesor",
            ])
        elif scenario.id == "S12":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Monto Malo", "0912345675", "1", "nada de plata",
            ])
        elif scenario.id == "S13":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Plazo Malo", "0912345675", "1", "5000", "99 meses",
            ])
        elif scenario.id == "S14":
            scenario.steps = _run_steps(scenario.phone, ["Hola", "1", "Pedro"])
        elif scenario.id == "S15":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Laura Pérez", "0912345675", "1",
                "4000", "12", "1100", "2",
            ])
        elif scenario.id == "S16":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "2", "¿Qué es score excelente?",
            ])
        elif scenario.id == "S17":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "2", "¿La cédula 0912345675 es válida?",
            ])
        elif scenario.id == "S18":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "xyz", "abc", "???",
            ])
        elif scenario.id == "S19":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Tomás Freire", "0919191916", "1",
                "5000", "12", "2000", "1",
            ])
        elif scenario.id == "S20":
            scenario.steps = _run_steps(scenario.phone, [
                "Hola", "1", "Diego Ramírez", "1712345675", "sip autorizo",
            ])

        combined = "\n".join(s.bot for s in scenario.steps)
        scenario.passed = _check_all(combined, scenario.expected)
        scenario.final_state = _final_state(scenario.phone)
    except Exception as exc:  # noqa: BLE001
        scenario.error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        scenario.passed = False
    return scenario


def _audit_sample() -> list[dict]:
    try:
        rows = (
            get_supabase_client()
            .table("tool_audit_logs")
            .select("tool_name, success, latency_ms, created_at")
            .order("created_at", desc=True)
            .limit(8)
            .execute()
        )
        return rows.data or []
    except Exception:  # noqa: BLE001
        return []


def main() -> None:
    started = datetime.now(timezone.utc)
    # Ejecutar todos los escenarios de prueba
    scenarios = [_execute(s) for s in _build_scenarios()]
    audit = _audit_sample()
    passed = sum(1 for s in scenarios if s.passed)
    failed = [s for s in scenarios if not s.passed]

    report = {
        "generated_at": started.isoformat(),
        "environment": "local + Supabase real",
        "total": len(scenarios),
        "passed": passed,
        "failed": len(failed),
        "pass_rate_pct": round(100 * passed / len(scenarios), 1),
        "audit_sample": audit,
        "scenarios": [
            {
                "id": s.id,
                "title": s.title,
                "category": s.category,
                "phone": s.phone,
                "passed": s.passed,
                "expected": s.expected,
                "final_state": s.final_state,
                "error": s.error,
                "transcript": [{"user": st.user, "bot": st.bot, "note": st.note} for st in s.steps],
            }
            for s in scenarios
        ],
    }

    # Guardar reporte en archivo JSON y imprimir resumen
    out = ROOT.parent / "reporte_chat_results.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": passed, "total": len(scenarios), "failed_ids": [s.id for s in failed]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
