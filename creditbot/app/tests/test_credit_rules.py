"""Pruebas de las reglas de precalificación crediticia (escala Ecuador 1–999)."""
from app.core.constants import (
    CREDIT_RESULT_NOT_QUALIFIED,
    CREDIT_RESULT_OBSERVED,
    CREDIT_RESULT_PREAPPROVED,
    SCORE_ACCEPTABLE,
    SCORE_EXCELLENT,
    SCORE_HIGH_RISK,
    SCORE_REGULAR,
)
from app.domain import credit_rules


def test_categorizar_score_excelente():
    assert credit_rules.categorizar_score(999) == SCORE_EXCELLENT
    assert credit_rules.categorizar_score(750) == SCORE_EXCELLENT


def test_categorizar_score_aceptable():
    assert credit_rules.categorizar_score(749) == SCORE_ACCEPTABLE
    assert credit_rules.categorizar_score(550) == SCORE_ACCEPTABLE


def test_categorizar_score_regular():
    assert credit_rules.categorizar_score(549) == SCORE_REGULAR
    assert credit_rules.categorizar_score(349) == SCORE_REGULAR


def test_categorizar_score_alto_riesgo():
    assert credit_rules.categorizar_score(348) == SCORE_HIGH_RISK
    assert credit_rules.categorizar_score(1) == SCORE_HIGH_RISK


def test_elegibilidad_alto_riesgo_no_elegible():
    resultado = credit_rules.verificar_elegibilidad(280)
    assert resultado["elegible"] is False
    assert resultado["motivo"] == "score_alto_riesgo"


def test_elegibilidad_mora_activa_no_elegible():
    resultado = credit_rules.verificar_elegibilidad(
        800, has_delinquency=True, delinquency_days=45
    )
    assert resultado["elegible"] is False
    assert resultado["motivo"] == "mora_activa"


def test_elegibilidad_lista_negra_no_elegible():
    resultado = credit_rules.verificar_elegibilidad(800, lista_negra=True)
    assert resultado["elegible"] is False
    assert resultado["motivo"] == "lista_negra"


def test_elegibilidad_sin_historial_es_regular():
    resultado = credit_rules.verificar_elegibilidad(900, sin_historial=True)
    assert resultado["elegible"] is True
    assert resultado["categoria"] == SCORE_REGULAR


def test_elegibilidad_score_valido():
    resultado = credit_rules.verificar_elegibilidad(720)
    assert resultado["elegible"] is True
    assert resultado["categoria"] == SCORE_ACCEPTABLE
    assert resultado["motivo"] is None


def test_tasa_anual_por_categoria():
    assert credit_rules.tasa_anual(SCORE_EXCELLENT) == 0.145
    assert credit_rules.tasa_anual(SCORE_ACCEPTABLE) == 0.160
    assert credit_rules.tasa_anual(SCORE_REGULAR) == 0.165
    assert credit_rules.tasa_anual(SCORE_HIGH_RISK) == 0.0


def test_capacidad_pago():
    assert credit_rules.calcular_capacidad_pago(1200) == 420.0


def test_capacidad_pago_con_cuotas_actuales():
    assert credit_rules.calcular_capacidad_pago(1200, 100) == 320.0


def test_capacidad_pago_nunca_negativa():
    assert credit_rules.calcular_capacidad_pago(500, 1000) == 0.0


def test_cuota_sin_interes_reparte_igual():
    assert credit_rules.calcular_cuota(1200, 0.0, 12) == 100.0


def test_cuota_francesa_aproximada():
    # $3.000 a 24 meses con TEA 16% ≈ $146,88/mes (sección 14.5 del documento).
    cuota = credit_rules.calcular_cuota(3000, 0.16, 24)
    assert 145.5 < cuota < 148.0


def test_cuota_monto_cero():
    assert credit_rules.calcular_cuota(0, 0.16, 24) == 0.0


def test_monto_maximo_excelente_limitado_por_categoria():
    calculo = credit_rules.calcular_monto_maximo(SCORE_EXCELLENT, 1200, 24)
    # Techo por categoría: 6 x 1200 = 7200; la capacidad soporta más, así que manda el techo.
    assert calculo["techo_categoria"] == 7200.0
    assert calculo["monto_maximo"] == 7200.0
    assert calculo["cuota_estimada"] <= calculo["capacidad_pago"]


def test_precalificar_excelente_preaprobado():
    resultado = credit_rules.precalificar(820, 1200, 24)
    assert resultado["elegible"] is True
    assert resultado["categoria"] == SCORE_EXCELLENT
    assert resultado["result"] == CREDIT_RESULT_PREAPPROVED
    assert resultado["monto_maximo"] > 0


def test_precalificar_aceptable_preaprobado():
    resultado = credit_rules.precalificar(650, 1200, 24)
    assert resultado["categoria"] == SCORE_ACCEPTABLE
    assert resultado["result"] == CREDIT_RESULT_PREAPPROVED


def test_precalificar_regular_observado():
    resultado = credit_rules.precalificar(420, 1200, 24)
    assert resultado["elegible"] is True
    assert resultado["categoria"] == SCORE_REGULAR
    assert resultado["result"] == CREDIT_RESULT_OBSERVED


def test_precalificar_alto_riesgo_no_cumple():
    resultado = credit_rules.precalificar(280, 1200, 24)
    assert resultado["elegible"] is False
    assert resultado["result"] == CREDIT_RESULT_NOT_QUALIFIED
    assert resultado["monto_maximo"] == 0.0


def test_precalificar_mora_no_elegible():
    resultado = credit_rules.precalificar(
        800, 1200, 24, has_delinquency=True, delinquency_days=60
    )
    assert resultado["elegible"] is False
    assert resultado["motivo"] == "mora_activa"


def test_precalificar_monto_solicitado_acotado_al_maximo():
    resultado = credit_rules.precalificar(820, 1200, 24, monto_solicitado=999999)
    assert resultado["monto_evaluado"] == resultado["monto_maximo"]
