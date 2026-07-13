"""Reglas de negocio puras del dominio crediticio.

Este paquete no depende de FastAPI, Supabase ni de la IA: contiene la lógica
determinista de precalificación (validación de cédula, categorización de score,
elegibilidad, cálculo de cuota y monto máximo). Las tools y el agente GPT
invocan estas funciones; el LLM nunca decide scores ni montos por su cuenta.
"""
