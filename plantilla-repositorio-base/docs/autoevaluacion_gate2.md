# Autoevaluación Gate 2

Estimación propia según la función de la primera lección de la unidad, actualizada tras la corrida real con Gemini (`docs/corrida_documentada.md`, corrida A). **Ajustar con criterio propio.**

```python
pesos = {"pipeline_funcional": 0.25, "recuperacion_citacion": 0.15, "costo_latencia": 0.10,
         "personalizacion": 0.15, "observabilidad": 0.15, "seguridad_gobernanza": 0.20}

mi_puntaje = {
    "pipeline_funcional": 90,      # corrida real de punta a punta sin errores (trace-7000f14a) + modo simulado
    "recuperacion_citacion": 80,   # citas garantizadas; métricas sobre el corpus propio, pero simuladas
    "costo_latencia": 90,          # corrida real: USD 0,00042 y 7,75 s por etapa; 5 corridas reales previas (B28)
    "personalizacion": 85,         # matriz propia con sensibilidad; queda pendiente revisar 20 respuestas
    "observabilidad": 90,          # trace_id único, eventos por etapa, guardia contra contenido crudo
    "seguridad_gobernanza": 85,    # filtro sobre Document, HITL de escalamiento/ajuste/prompt, matriz con 21 riesgos (3 CRITICO, 9 ALTO)
}

no_compensables = {
    "pipeline_corre_de_punta_a_punta": True,   # tests/test_gate2.py::test_pipeline_corre_de_punta_a_punta
    "respuestas_citan_fuente": True,           # test_respuestas_citan_fuente
    "logs_sin_contenido_crudo": True,          # test_logs_sin_contenido_crudo
    "supervision_humana_funciona": True,       # test_supervision_humana_funciona
}
# promedio ponderado = 86,75 · no compensables OK: True
```

## Brechas conocidas (honestas)

| Brecha | Impacto | Plan |
|---|---|---|
| Métricas B27 corridas con embeddings simulados | Recuperación léxica, no semántica | `python src/evaluar_corpus.py` con clave y actualizar la tabla |
| Corrida real con hallazgos H-1 y H-2 ya corregidos en el código | Falta confirmar la corrección con Gemini real | Re-ejecutar la corrida A y anexarla |
| Latencia real de ≈ 7,75 s (86 % en generación) | Alta para un cliente en línea (R-10) | Streaming en Gate 3 |
| Checkpointer en memoria | Una aprobación pendiente se pierde si el proceso se reinicia | Checkpointer persistente en Gate 3 (FastAPI) |
| Filtro de inyección por patrones | No cubre paráfrasis | Aceptado para el alcance; documentado en R-02 |
| Banco de prompts reescrito sin re-evaluar | `registro_resultados.json` quedó sin resultados vigentes | `python -m src.consistencia` con clave |
| Monto de devolución POL-16 = monto reclamado | Supuesto: la política solo define el tope | Validar la regla; documentado en R-07 |
