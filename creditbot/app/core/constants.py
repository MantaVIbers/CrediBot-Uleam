"""Constantes del flujo conversacional y resultados de crédito."""

# Estados del flujo de la conversación con el usuario
START = "START"
MENU = "MENU"
ASK_NAME = "ASK_NAME"
ASK_AMOUNT = "ASK_AMOUNT"
ASK_TERM = "ASK_TERM"
ASK_INCOME = "ASK_INCOME"
CONFIRM_DATA = "CONFIRM_DATA"
EVALUATE_REQUEST = "EVALUATE_REQUEST"
SHOW_RESULT = "SHOW_RESULT"
HANDOFF_REQUESTED = "HANDOFF_REQUESTED"
FINISHED = "FINISHED"

# Resultados posibles de la evaluación crediticia
CREDIT_RESULT_PREAPPROVED = "preaprobado"
CREDIT_RESULT_OBSERVED = "observado"
CREDIT_RESULT_NOT_QUALIFIED = "no_cumple"
