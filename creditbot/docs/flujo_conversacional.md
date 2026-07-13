# Flujo conversacional de CrediBot

## Estados

| Estado | Descripción |
|---|---|
| `START` | Inicio de conversación |
| `MENU` | Menú principal |
| `ASK_NAME` | Solicita nombre |
| `ASK_CEDULA` | Solicita cédula |
| `CONSENT` | Solicita autorización para consultar perfil |
| `ASK_PURPOSE` | Solicita destino o producto del crédito |
| `ASK_AMOUNT` | Solicita monto |
| `ASK_TERM` | Solicita plazo |
| `ASK_INCOME` | Solicita ingreso |
| `CONFIRM_DATA` | Confirma resumen |
| `SHOW_RESULT` | Muestra resultado |
| `HANDOFF_REQUESTED` | Derivado a asesor |
| `FINISHED` | Conversación cerrada |

## Flujo esperado

```text
Usuario: Hola
Bot: Hola, soy CrediBot. ¿Qué deseas hacer?
     1. Precalificar crédito
     2. Información general
     3. Hablar con asesor

Usuario: 1
Bot: Perfecto. Indícame tu nombre completo.

Usuario: Carlos Ortiz
Bot: Gracias. Ahora indícame tu número de cédula (10 dígitos) para consultar tu perfil crediticio.

Usuario: 0912345675
Bot: Para precalificarte necesito tu autorización para consultar tu historial crediticio.
     1. Sí, autorizo
     2. No autorizo

Usuario: Sí autorizo
Bot: ¿Para qué necesitas el crédito? Por ejemplo: estudios, negocio, consumo o emergencia.

Usuario: estudios
Bot: ¿Qué monto deseas solicitar?

Usuario: 500
Bot: ¿En cuántos meses deseas pagar el crédito?

Usuario: 12
Bot: ¿Cuál es tu ingreso mensual aproximado?

Usuario: 700
Bot: Resumen:
     Nombre: Carlos Ortiz
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
     Cuota estimada: $41.67
     Un asesor puede continuar con la validación final.
```

## Regla de negocio v2

```text
perfil = consulta por cédula en credit_profiles
capacidad_pago = ingreso_neto * 0.35 - cuotas_actuales
monto_maximo = menor entre techo por score y monto por capacidad de pago
cuota_estimada = amortización francesa con TEA por categoría
```

| Condición | Resultado |
|---|---|
| Score excelente/aceptable y cuota dentro de capacidad | `preaprobado` |
| Score regular o caso revisable | `observado` |
| Alto riesgo, mora activa mayor a 30 días o lista negra | `no_cumple` |

## Intención natural e IA

El menú acepta números y frases como `quiero un crédito`, `necesito información`
o `hablar con una persona`. La IA de OpenAI redacta la respuesta final cuando está
configurada, pero las reglas de negocio y los estados los controla el backend.
El modelo recibe solo contexto seguro: estado actual, paso pendiente y fragmentos
RAG recuperados.

## RAG de políticas

Las preguntas sobre requisitos, documentos, tasas, plazos o condiciones se
responden con información recuperada desde `docs/policies/credito_mvp.md`.
Si el usuario hace una pregunta informativa mientras está entregando datos, el
bot responde y conserva el estado actual para no perder el flujo.

## Derivación a asesor

Se crea un caso en `handoff_cases` cuando:

- El usuario elige la opción 3 del menú
- Escribe palabras como `asesor`, `humano`, `persona` o `agente`
- El resultado queda como `observado`
- Falla 3 veces con datos inválidos

Cada caso incluye un resumen para el asesor y un transcript con los últimos mensajes
guardados. El historial completo se mantiene en `messages` para seguimiento posterior.

## Cómo probar el flujo

### Opción 1: simulador local

Usa `POST /simulate/message` cambiando el campo `message` en cada paso.

### Opción 2: Twilio WhatsApp Sandbox

1. Configura el webhook en Twilio Console.
2. Une tu número al Sandbox.
3. Escribe desde WhatsApp al número de prueba de Twilio.

Guía: [`twilio_setup.md`](twilio_setup.md)
