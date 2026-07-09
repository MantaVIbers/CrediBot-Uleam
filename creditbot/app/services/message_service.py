"""Mensajes predefinidos del bot para cada estado de la conversación."""


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


def ask_amount_message(name: str | None = None) -> str:
    """Solicita el monto del crédito, opcionalmente saludando por el nombre."""
    if name:
        return f"Gracias, {name}. ¿Qué monto deseas solicitar?"
    return "¿Qué monto deseas solicitar?"


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


def confirm_data_message(data: dict) -> str:
    """Muestra resumen de datos para confirmación del usuario."""
    return (
        "Resumen:\n"
        f"Nombre: {data['name']}\n"
        f"Monto: ${data['amount']:.2f}\n"
        f"Plazo: {data['term']} meses\n"
        f"Ingreso: ${data['income']:.2f}\n"
        "¿Confirmas la información?\n"
        "1. Sí\n"
        "2. No"
    )


def preapproved_message(data: dict) -> str:
    """Mensaje de resultado preaprobado."""
    return (
        f"Resultado: Preaprobado.\n"
        f"Cuota estimada: ${data['estimated_payment']:.2f}\n"
        "Un asesor puede continuar con la validación final."
    )


def observed_message(data: dict) -> str:
    """Mensaje de resultado observado (requiere revisión de asesor)."""
    return (
        f"Resultado: Observado.\n"
        f"Cuota estimada: ${data['estimated_payment']:.2f}\n"
        f"Capacidad de pago: ${data['payment_capacity']:.2f}\n"
        "Un asesor revisará tu caso y se comunicará contigo."
    )


def not_qualified_message(data: dict) -> str:
    """Mensaje de resultado no cumple condiciones."""
    return (
        f"Resultado: No cumple.\n"
        f"Cuota estimada: ${data['estimated_payment']:.2f}\n"
        f"Capacidad de pago: ${data['payment_capacity']:.2f}\n"
        "Por ahora no cumples las condiciones básicas de precalificación."
    )


def handoff_message() -> str:
    """Mensaje de derivación a asesor humano."""
    return (
        "Te derivaremos con un asesor humano. "
        "En breve alguien del equipo se comunicará contigo."
    )


def finished_message() -> str:
    """Mensaje de despedida al finalizar la conversación."""
    return "Gracias por usar CrediBot. Si necesitas algo más, escríbenos de nuevo."
