"""Verifica la integridad del seed de perfiles crediticios (seed_credit_profiles.sql).

Estos datos se cargan en Supabase y deben cumplir dos invariantes:
1. Toda cédula ficticia debe ser válida según el algoritmo módulo 10 (tool `validar_cedula`).
2. La categoría declarada debe coincidir con la que calcula `categorizar_score`.

Si alguien edita el seed y rompe una cédula o una categoría, esta prueba lo detecta.
"""
from app.domain.cedula_validator import is_valid_cedula
from app.domain.credit_rules import categorizar_score

# Espejo de los perfiles definidos en supabase/seed_credit_profiles.sql
# (cedula, score, categoria_declarada). Mantener sincronizado con el .sql.
SEED_PROFILES = [
    ("0911111110", 820, "excelente"),
    ("0922222229", 900, "excelente"),
    ("0101010106", 780, "excelente"),
    ("1305050500", 760, "excelente"),
    ("0909090904", 850, "excelente"),
    ("0303030308", 750, "excelente"),
    ("0912345675", 720, "aceptable"),
    ("0933333338", 650, "aceptable"),
    ("1710034560", 600, "aceptable"),
    ("1313131318", 700, "aceptable"),
    ("1340040045", 580, "aceptable"),
    ("0102030400", 620, "aceptable"),
    ("0505050500", 550, "aceptable"),
    ("0944444447", 420, "regular"),
    ("1712345675", 500, "regular"),
    ("1707070700", 350, "regular"),
    ("0818181810", 470, "regular"),
    ("0955555552", 280, "alto_riesgo"),
    ("1320020025", 200, "alto_riesgo"),
    ("1800180018", 320, "alto_riesgo"),
    ("0919191916", 800, "excelente"),
]


def test_all_seed_cedulas_are_valid():
    """Todas las cédulas del seed deben pasar el validador módulo 10."""
    invalid = [cedula for cedula, _, _ in SEED_PROFILES if not is_valid_cedula(cedula)]
    assert invalid == [], f"Cédulas inválidas en el seed: {invalid}"


def test_seed_cedulas_are_unique():
    """No debe haber cédulas duplicadas en el seed."""
    cedulas = [cedula for cedula, _, _ in SEED_PROFILES]
    assert len(cedulas) == len(set(cedulas))


def test_seed_categories_match_score():
    """La categoría declarada debe coincidir con la calculada por el score."""
    mismatches = [
        (cedula, categoria, categorizar_score(score))
        for cedula, score, categoria in SEED_PROFILES
        if categorizar_score(score) != categoria
    ]
    assert mismatches == [], f"Categorías inconsistentes: {mismatches}"


def test_seed_covers_all_categories():
    """El seed debe cubrir las 4 categorías para la demo."""
    categorias = {categoria for _, _, categoria in SEED_PROFILES}
    assert categorias == {"excelente", "aceptable", "regular", "alto_riesgo"}
