# Flujo conversacional de CrediBot (v2)

Diagrama Mermaid: [`docs/diagramas/flujo_estados.mmd`](diagramas/flujo_estados.mmd)

## Estados

| Estado | Descripción |
|---|---|
| `START` | Inicio de conversación |
| `MENU` | Menú principal |
| `CONSENT` | Autorización para consultar historial (antes de la cédula) |
| `ASK_CEDULA` | Solicita cédula + verificación de identidad/elegibilidad |
| `ASK_PURPOSE` | Destino del crédito |
| `ASK_AMOUNT` | Monto solicitado |
| `ASK_TERM` | Plazo en meses |
| `ASK_INCOME` | Ingreso mensual |
| `CONFIRM_DATA` | Confirma resumen |
| `SHOW_RESULT` | Muestra resultado de precalificación |
| `NOT_ELIGIBLE` | No puede continuar (score/mora/lista negra) |
| `HANDOFF_REQUESTED` | Derivado a asesor |
| `FINISHED` | Conversación cerrada |

## Flujo esperado (alineado a requisitos v2)

```text
Usuario: Hola
Bot: Hola, soy CrediBot. ¿Qué deseas hacer?
     1. Precalificar crédito
     2. Información general
     3. Hablar con asesor

Usuario: 1
Bot: Antes de continuar necesito tu autorización para consultar tu
     historial crediticio (datos simulados). ¿Autorizas?
     1. Sí, autorizo
     2. No autorizo

Usuario: 1
Bot: Perfecto. Indícame tu número de cédula (10 dígitos).

Usuario: 0912345675
Bot: Gracias, María González López. Verificamos tu identidad y tu perfil
     está en categoría aceptable (score 720). Podemos continuar.
     ¿Para qué necesitas el crédito?

Usuario: estudios
Bot: Gracias, María González López. ¿Qué monto deseas solicitar?

Usuario: 500
Bot: ¿En cuántos meses deseas pagar el crédito?

Usuario: 12
Bot: ¿Cuál es tu ingreso mensual aproximado?

Usuario: 700
Bot: Resumen:
     Nombre: María González López
     Cédula: 09******75
     Destino: estudios
     Monto: $500.00
     Plazo: 12 meses
     Ingreso: $700.00
     ¿Confirmas la información?
     1. Sí
     2. No

Usuario: 1
Bot: Resultado: Preaprobado.
     Categoría de score: aceptable
     Monto máximo / cuota / TEA...
```

## Verificación temprana (VERIFY_IDENTITY)

Tras una cédula válida, el backend (no el LLM):

1. Busca el perfil en `credit_profiles`.
2. Si no existe → pide reintentar.
3. Aplica `verificar_elegibilidad` (score Ecuador, mora, lista negra).
4. Si no elegible → `NOT_ELIGIBLE` con explicación.
5. Si elegible → toma el nombre del perfil y continúa a `ASK_PURPOSE`.

## Regla de negocio

Ver `app/domain/credit_rules.py` (escala Ecuador 1–999, TEA por categoría, cuota francesa).

## Derivación humana

Siempre disponible: menú opción 3, palabra `asesor`, o resultado `observado`.
