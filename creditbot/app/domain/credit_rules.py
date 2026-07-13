"""Reglas de negocio de precalificación crediticia (escala Ecuador 1–999).

Implementa la sección 14 del documento de arquitectura v2. Es lógica determinista
y pura: no depende de la base de datos ni del LLM. Las tools del agente invocan
estas funciones para que el modelo nunca invente scores, cuotas ni montos.
"""
from app.core.constants import (
    CREDIT_RESULT_NOT_QUALIFIED,
    CREDIT_RESULT_OBSERVED,
    CREDIT_RESULT_PREAPPROVED,
    SCORE_ACCEPTABLE,
    SCORE_EXCELLENT,
    SCORE_HIGH_RISK,
    SCORE_REGULAR,
)

# Tasa efectiva anual (TEA) ficticia por categoría, por debajo del tope legal BCE.
TASA_POR_CATEGORIA: dict[str, float] = {
    SCORE_EXCELLENT: 0.145,
    SCORE_ACCEPTABLE: 0.160,
    SCORE_REGULAR: 0.165,
}

# Techo de monto como múltiplo del ingreso mensual, según categoría de score.
MULTIPLICADOR_MONTO: dict[str, float] = {
    SCORE_EXCELLENT: 6.0,
    SCORE_ACCEPTABLE: 4.0,
    SCORE_REGULAR: 1.5,
    SCORE_HIGH_RISK: 0.0,
}

# Proporción del ingreso neto que se considera capacidad de pago.
CAPACITY_RATIO = 0.35
# Umbral de días de mora que descalifica automáticamente.
MAX_DELINQUENCY_DAYS = 30
# Holgura permitida de la cuota sobre la capacidad para quedar "observado".
OBSERVED_TOLERANCE = 1.15


def categorizar_score(score: int) -> str:
    """Clasifica el score crediticio (1–999) en una categoría de riesgo."""
    if score >= 750:
        return SCORE_EXCELLENT
    if score >= 550:
        return SCORE_ACCEPTABLE
    if score >= 349:
        return SCORE_REGULAR
    return SCORE_HIGH_RISK


def verificar_elegibilidad(
    score: int,
    *,
    has_delinquency: bool = False,
    delinquency_days: int = 0,
    lista_negra: bool = False,
    sin_historial: bool = False,
) -> dict[str, object]:
    """Determina si el solicitante puede continuar la precalificación.

    Retorna un dict con `elegible` (bool), `categoria` (str) y `motivo` (str|None).
    Un solicitante sin historial se trata como categoría 'regular' (monto conservador).
    """
    categoria = SCORE_REGULAR if sin_historial else categorizar_score(score)

    if lista_negra:
        return {"elegible": False, "categoria": categoria, "motivo": "lista_negra"}

    if has_delinquency and delinquency_days > MAX_DELINQUENCY_DAYS:
        return {"elegible": False, "categoria": categoria, "motivo": "mora_activa"}

    if categoria == SCORE_HIGH_RISK:
        return {"elegible": False, "categoria": categoria, "motivo": "score_alto_riesgo"}

    return {"elegible": True, "categoria": categoria, "motivo": None}


def tasa_anual(categoria: str) -> float:
    """Retorna la TEA correspondiente a la categoría (0 si no es elegible)."""
    return TASA_POR_CATEGORIA.get(categoria, 0.0)


def calcular_capacidad_pago(ingreso_neto: float, cuotas_actuales: float = 0.0) -> float:
    """Capacidad de pago mensual = 35% del ingreso neto menos cuotas vigentes."""
    return round(max(ingreso_neto * CAPACITY_RATIO - cuotas_actuales, 0.0), 2)


def calcular_cuota(monto: float, tea: float, plazo_meses: int) -> float:
    """Calcula la cuota mensual con el sistema de amortización francés.

    cuota = monto * [ r (1+r)^n ] / [ (1+r)^n - 1 ], con r = tea / 12.
    Si la tasa es 0, se reparte el monto en cuotas iguales.
    """
    if plazo_meses <= 0:
        raise ValueError("El plazo debe ser mayor a 0 meses.")
    if monto <= 0:
        return 0.0

    # Calcular tasa mensual a partir de la TEA
    r = tea / 12
    if r == 0:
        return round(monto / plazo_meses, 2)

    # Aplicar fórmula de amortización francesa
    factor = (1 + r) ** plazo_meses
    cuota = monto * (r * factor) / (factor - 1)
    return round(cuota, 2)


def calcular_monto_por_capacidad(capacidad: float, tea: float, plazo_meses: int) -> float:
    """Invierte la fórmula francesa: mayor monto cuya cuota no supera la capacidad."""
    if capacidad <= 0 or plazo_meses <= 0:
        return 0.0

    r = tea / 12
    if r == 0:
        return round(capacidad * plazo_meses, 2)

    factor = (1 + r) ** plazo_meses
    monto = capacidad * (factor - 1) / (r * factor)
    return round(monto, 2)


def calcular_monto_maximo(
    categoria: str,
    ingreso_neto: float,
    plazo_meses: int,
    cuotas_actuales: float = 0.0,
) -> dict[str, float | str]:
    """Calcula el monto máximo precalificado y su cuota estimada.

    El techo es el menor valor entre el múltiplo permitido por la categoría y el
    monto que la capacidad de pago puede sostener con la TEA correspondiente.
    """
    tea = tasa_anual(categoria)
    capacidad = calcular_capacidad_pago(ingreso_neto, cuotas_actuales)
    # Límite superior según la categoría del score
    techo_categoria = round(MULTIPLICADOR_MONTO.get(categoria, 0.0) * ingreso_neto, 2)
    monto_por_capacidad = calcular_monto_por_capacidad(capacidad, tea, plazo_meses)

    monto_maximo = round(min(techo_categoria, monto_por_capacidad), 2)
    cuota_estimada = calcular_cuota(monto_maximo, tea, plazo_meses)

    return {
        "categoria": categoria,
        "tea": tea,
        "capacidad_pago": capacidad,
        "techo_categoria": techo_categoria,
        "monto_maximo": monto_maximo,
        "cuota_estimada": cuota_estimada,
        "plazo_meses": plazo_meses,
    }


def _clasificar_resultado(categoria: str, cuota: float, capacidad: float) -> str:
    """Aplica la tabla de resultados de la sección 14.6."""
    if categoria == SCORE_HIGH_RISK:
        return CREDIT_RESULT_NOT_QUALIFIED
    if categoria == SCORE_REGULAR:
        return CREDIT_RESULT_OBSERVED
    if cuota <= capacidad and categoria in (SCORE_EXCELLENT, SCORE_ACCEPTABLE):
        return CREDIT_RESULT_PREAPPROVED
    if cuota <= capacidad * OBSERVED_TOLERANCE:
        return CREDIT_RESULT_OBSERVED
    return CREDIT_RESULT_NOT_QUALIFIED


def precalificar(
    score: int,
    ingreso_neto: float,
    plazo_meses: int,
    *,
    cuotas_actuales: float = 0.0,
    has_delinquency: bool = False,
    delinquency_days: int = 0,
    lista_negra: bool = False,
    sin_historial: bool = False,
    monto_solicitado: float | None = None,
) -> dict[str, object]:
    """Ejecuta la precalificación completa y retorna el resultado estructurado.

    Combina elegibilidad + cálculo de monto máximo + clasificación del resultado.
    Si se pasa `monto_solicitado`, la cuota se evalúa sobre ese monto (acotado al
    máximo precalificado); si no, se usa el monto máximo.
    """
    elegibilidad = verificar_elegibilidad(
        score,
        has_delinquency=has_delinquency,
        delinquency_days=delinquency_days,
        lista_negra=lista_negra,
        sin_historial=sin_historial,
    )
    categoria = str(elegibilidad["categoria"])

    if not elegibilidad["elegible"]:
        return {
            "elegible": False,
            "categoria": categoria,
            "motivo": elegibilidad["motivo"],
            "result": CREDIT_RESULT_NOT_QUALIFIED,
            "tea": tasa_anual(categoria),
            "capacidad_pago": calcular_capacidad_pago(ingreso_neto, cuotas_actuales),
            "monto_maximo": 0.0,
            "cuota_estimada": 0.0,
            "plazo_meses": plazo_meses,
        }

    calculo = calcular_monto_maximo(categoria, ingreso_neto, plazo_meses, cuotas_actuales)
    monto_maximo = float(calculo["monto_maximo"])
    tea = float(calculo["tea"])
    capacidad = float(calculo["capacidad_pago"])

    monto_evaluado = monto_maximo
    if monto_solicitado is not None:
        monto_evaluado = round(min(monto_solicitado, monto_maximo), 2)

    cuota = calcular_cuota(monto_evaluado, tea, plazo_meses)
    result = _clasificar_resultado(categoria, cuota, capacidad)

    return {
        "elegible": True,
        "categoria": categoria,
        "motivo": None,
        "result": result,
        "tea": tea,
        "capacidad_pago": capacidad,
        "techo_categoria": float(calculo["techo_categoria"]),
        "monto_maximo": monto_maximo,
        "monto_evaluado": monto_evaluado,
        "cuota_estimada": cuota,
        "plazo_meses": plazo_meses,
    }
