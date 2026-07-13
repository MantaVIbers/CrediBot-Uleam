"""Mensajes predefinidos del bot para cada estado de la conversación."""

HANDOFF_HINT = "Si prefieres ayuda humana, escribe 'asesor' en cualquier momento."


def with_handoff_hint(message: str) -> str:
    """Agrega la salida a asesor sin duplicarla."""
    if not message or "asesor" in message.lower():
        return message
    return f"{message}\n\n{HANDOFF_HINT}"


def welcome_message() -> str:
    """Mensaje de bienvenida con el menú principal."""
    return (
        "Hola, soy CrediBot. ¿Qué deseas hacer?\n"
        "1. Precalificar crédito\n"
        "2. Información general\n"
        "3. Hablar con asesor"
    )


def ask_name_message() -> str:
    """Solicita el nombre completo al usuario."""
    return "Perfecto. Indícame tu nombre completo."


def ask_cedula_message() -> str:
    """Solicita la cédula tras el consentimiento."""
    return (
        "Perfecto. Indícame tu número de cédula (10 dígitos) "
        "para consultar tu perfil crediticio."
    )


def ask_consent_message() -> str:
    """Solicita consentimiento para consultar el buró crediticio (RF-08)."""
    return (
        "Antes de continuar necesito tu autorización para consultar tu "
        "historial crediticio (datos simulados con fines académicos). "
        "¿Autorizas la consulta?\n"
        "1. Sí, autorizo\n"
        "2. No autorizo"
    )


def consent_declined_message() -> str:
    """Mensaje cuando el usuario no autoriza la consulta del buró."""
    return (
        "Entendido. Sin tu autorización no podemos consultar tu historial "
        "ni continuar con la precalificación. Puedes volver a escribirnos "
        "cuando desees retomarla."
    )


def invalid_cedula_message(reason: str | None = None) -> str:
    """Mensaje de error para cédula inválida, con el motivo si está disponible."""
    detail = f" {reason}" if reason else ""
    return f"La cédula ingresada no es válida.{detail} Inténtalo de nuevo."


def cedula_not_found_message() -> str:
    """Cédula válida en formato pero inexistente en el buró simulado."""
    return (
        "No encontramos un perfil crediticio asociado a esa cédula en nuestra "
        "base de datos de prueba. Verifica el número o escribe 'asesor'."
    )


def identity_verified_message(name: str, categoria: str, score: int | None = None) -> str:
    """Confirma identidad/elegibilidad y avanza a la precalificación."""
    score_line = f" (score {score})" if score is not None else ""
    return (
        f"Gracias, {name}. Verificamos tu identidad y tu perfil crediticio "
        f"está en categoría {categoria}{score_line}. "
        "Podemos continuar con la precalificación."
    )


def not_eligible_message(name: str | None, motivo: str | None, categoria: str | None = None) -> str:
    """Explica por qué no puede continuar la precalificación automática."""
    motivos = {
        "lista_negra": "Tu perfil figura con restricciones que impiden continuar.",
        "mora_activa": "Registras mora activa que impide la precalificación automática.",
        "score_alto_riesgo": "Tu score se encuentra en la categoría de alto riesgo.",
        "sin_perfil": "No encontramos historial crediticio asociado a tu cédula.",
    }
    saludo = f"{name}, " if name else ""
    detalle = motivos.get(str(motivo), "Por ahora no cumples las condiciones básicas.")
    cat = f" Categoría: {categoria}." if categoria else ""
    return (
        f"{saludo}no podemos continuar con la precalificación automática. "
        f"{detalle}{cat}\n"
        "Puedes escribir 'asesor' para hablar con una persona."
    )


def ask_amount_message(name: str | None = None) -> str:
    """Solicita el monto del crédito, opcionalmente saludando por el nombre."""
    if name:
        return f"Gracias, {name}. ¿Qué monto deseas solicitar?"
    return "¿Qué monto deseas solicitar?"


def ask_purpose_message() -> str:
    """Solicita el destino o producto de interés del crédito."""
    return "¿Para qué necesitas el crédito? Por ejemplo: estudios, negocio, consumo o emergencia."


def invalid_purpose_message() -> str:
    """Mensaje de error para destino de crédito inválido."""
    return "Indica brevemente el destino del crédito, por ejemplo: estudios o negocio."


def ask_term_message() -> str:
    """Solicita el plazo en meses."""
    return "¿En cuántos meses deseas pagar el crédito?"


def ask_income_message() -> str:
    """Solicita el ingreso mensual aproximado."""
    return "¿Cuál es tu ingreso mensual aproximado?"


def invalid_name_message() -> str:
    """Mensaje de error para nombre inválido."""
    return "El nombre debe tener al menos 2 palabras o 5 caracteres. Inténtalo de nuevo."


def invalid_amount_message() -> str:
    """Mensaje de error para monto inválido."""
    return "El monto debe ser un número mayor a 0. Inténtalo de nuevo."


def invalid_term_message() -> str:
    """Mensaje de error para plazo inválido."""
    return "El plazo debe ser un número entre 3 y 36 meses. Inténtalo de nuevo."


def invalid_income_message() -> str:
    """Mensaje de error para ingreso inválido."""
    return "El ingreso debe ser un número mayor a 0. Inténtalo de nuevo."


def invalid_menu_message() -> str:
    """Mensaje de error para opción de menú inválida."""
    return "Selecciona una opción válida: 1, 2 o 3."


def invalid_confirmation_message() -> str:
    """Mensaje de error para confirmación inválida."""
    return "Selecciona una opción válida: 1 (Sí) o 2 (No)."


def general_info_message() -> str:
    """Mensaje informativo con el menú principal."""
    return (
        "CrediBot te ayuda a precalificar una solicitud de crédito de forma rápida "
        "por WhatsApp. Selecciona una opción del menú:\n"
        "1. Precalificar crédito\n"
        "2. Información general\n"
        "3. Hablar con asesor"
    )


def policy_info_message(answer: str, continuation: str | None = None) -> str:
    """Mensaje informativo recuperado desde políticas internas."""
    if continuation:
        return f"{answer}\n\nPara continuar: {continuation}"
    return answer


def confirm_data_message(data: dict) -> str:
    """Muestra resumen de datos para confirmación del usuario."""
    cedula_line = f"Cédula: {data['cedula']}\n" if data.get("cedula") else ""
    return (
        "Resumen:\n"
        f"Nombre: {data['name']}\n"
        f"{cedula_line}"
        f"Destino: {data['purpose']}\n"
        f"Monto: ${data['amount']:.2f}\n"
        f"Plazo: {data['term']} meses\n"
        f"Ingreso: ${data['income']:.2f}\n"
        "¿Confirmas la información?\n"
        "1. Sí\n"
        "2. No"
    )


def _result_details(data: dict) -> str:
    """Bloque común de detalles numéricos de la precalificación v2."""
    tea_pct = float(data.get("tea", 0.0)) * 100
    return (
        f"Categoría de score: {data['categoria']}\n"
        f"Monto máximo precalificado: ${float(data['monto_maximo']):.2f}\n"
        f"Plazo: {int(data['plazo_meses'])} meses\n"
        f"Cuota estimada: ${float(data['cuota_estimada']):.2f}\n"
        f"Tasa referencial (TEA): {tea_pct:.2f}%"
    )


def preapproved_message(data: dict) -> str:
    """Mensaje de resultado preaprobado (v2 con monto máximo, cuota y tasa)."""
    return (
        "Resultado: Preaprobado.\n"
        f"{_result_details(data)}\n"
        "Un asesor puede continuar con la validación final."
    )


def observed_message(data: dict) -> str:
    """Mensaje de resultado observado (requiere revisión de asesor)."""
    return (
        "Resultado: Observado.\n"
        f"{_result_details(data)}\n"
        "Un asesor revisará tu caso y se comunicará contigo."
    )


def not_qualified_message(data: dict) -> str:
    """Mensaje de resultado no cumple condiciones."""
    motivos = {
        "lista_negra": "Tu perfil figura con restricciones que impiden continuar.",
        "mora_activa": "Registras mora activa que impide la precalificación.",
        "score_alto_riesgo": "Tu score se encuentra en la categoría de alto riesgo.",
    }
    motivo_line = motivos.get(str(data.get("motivo")), "")
    detalle = f"{motivo_line}\n" if motivo_line else ""
    return (
        "Resultado: No cumple.\n"
        f"Categoría de score: {data['categoria']}\n"
        f"{detalle}"
        "Por ahora no cumples las condiciones básicas de precalificación."
    )


def handoff_message() -> str:
    """Mensaje de derivación a asesor humano."""
    return (
        "Te derivaremos con un asesor humano. "
        "En breve alguien del equipo se comunicará contigo."
    )


def handoff_waiting_message() -> str:
    """Confirma recepción mientras el cliente espera respuesta del asesor."""
    return (
        "Recibimos tu mensaje. Un asesor humano te responderá pronto por este mismo chat."
    )


def finished_message() -> str:
    """Mensaje de despedida al finalizar la conversación."""
    return "Gracias por usar CrediBot. Si necesitas algo más, escríbenos de nuevo."
