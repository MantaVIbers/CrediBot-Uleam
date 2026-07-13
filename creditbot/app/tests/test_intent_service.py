"""Pruebas de detección de intención."""
from app.services import intent_service
from app.services import message_service


# Verifica detección de intención de crédito en lenguaje natural
def test_menu_detecta_credito_en_lenguaje_natural():
    assert intent_service.menu_option_from_text("Quiero solicitar un crédito") == "1"
    assert intent_service.menu_option_from_text("necesito un prestamo") == "1"


# Verifica detección de intención de información y asesoría
def test_menu_detecta_info_y_asesor():
    assert intent_service.menu_option_from_text("quiero información de requisitos") == "2"
    assert intent_service.menu_option_from_text("hablar con una persona") == "3"


# Verifica detección de confirmación (sí/no) en lenguaje natural
def test_confirmacion_detecta_si_y_no():
    assert intent_service.confirmation_from_text("sí autorizo") == "1"
    assert intent_service.confirmation_from_text("confirmo") == "1"
    assert intent_service.confirmation_from_text("no, quiero corregir") == "2"


# Verifica que preguntas sobre políticas se detecten correctamente
def test_detecta_pregunta_de_politicas():
    assert intent_service.is_policy_question("qué requisitos necesito?") is True
    assert intent_service.is_policy_question("documentos para credito") is True
    assert intent_service.is_policy_question("hola") is False


# Verifica que respuestas numéricas no se confundan con preguntas de políticas
def test_no_confunde_respuesta_numerica_con_politica():
    """Respuestas de plazo/monto no deben activar RAG por contener 'plazos'."""
    assert intent_service.looks_like_numeric_answer("12") is True
    assert intent_service.looks_like_numeric_answer("en 12 plazos") is True
    assert intent_service.is_policy_question("en 12 plazos") is False
    assert intent_service.is_policy_question("cuáles son los plazos?") is True


# Verifica que "hablar con una persona" no se confunda con solicitud de crédito
def test_menu_no_deriva_por_persona_natural():
    assert intent_service.menu_option_from_text("credito para persona natural") == "1"
    assert intent_service.menu_option_from_text("hablar con una persona") == "3"


# Verifica que la pista de asesor no se duplique al aplicarse múltiples veces
def test_handoff_hint_no_se_duplica():
    message = message_service.with_handoff_hint("Indica tu ingreso mensual")
    assert "asesor" in message.lower()
    assert message_service.with_handoff_hint(message) == message
