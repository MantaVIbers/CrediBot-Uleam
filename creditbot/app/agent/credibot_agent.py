"""Agente Agno para entender texto libre sin controlar el negocio."""
import logging

from app.agent.conversation_memory import recent_conversation_memory
from app.agent.prompts import CREDIBOT_SYSTEM_PROMPT
from app.agent.state_manager import expected_input_for_state
from app.core.config import settings
from app.tools.credit_tools import tools_for_agent

logger = logging.getLogger(__name__)


def _configured() -> bool:
    return bool(settings.openai_enable_ai and settings.openai_api_key)


def render_free_text_retry(
    *,
    base_reply: str,
    state: str,
    user_message: str,
    conversation_id: str,
    user_id: str,
) -> str:
    """Genera una respuesta empática y conserva el dato pendiente.

    Agno se importa de forma diferida para que el webhook siga disponible si
    una instalación aún no incorpora la dependencia.
    """
    expected = expected_input_for_state(state)
    if not _configured() or not expected:
        return base_reply

    try:
        from agno.agent import Agent
        from agno.models.openai.responses import OpenAIResponses

        agent = Agent(
            name="CrediBot",
            model=OpenAIResponses(id=settings.openai_model),
            instructions=CREDIBOT_SYSTEM_PROMPT,
            tools=tools_for_agent(safe_only=True),
            markdown=False,
        )
        prompt = (
            f"Estado controlado: {state}\n"
            f"Dato pendiente: {expected}\n"
            f"Historial reciente:\n{recent_conversation_memory(conversation_id)}\n\n"
            f"Mensaje nuevo del cliente: {user_message}\n\n"
            f"Respuesta base segura: {base_reply}\n\n"
            "Reconoce brevemente el contexto y pide de nuevo solo el dato pendiente. "
            "No ejecutes herramientas que registren datos o deriven el caso."
        )
        result = agent.run(prompt, user_id=user_id, session_id=conversation_id)
        rendered = str(getattr(result, "content", "") or "").strip()
        return rendered or base_reply
    except Exception as exc:  # pragma: no cover - defensa del webhook
        logger.warning("Agno no pudo redactar el reintento contextual: %s", exc)
        return base_reply
