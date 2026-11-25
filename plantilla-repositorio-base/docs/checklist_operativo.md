# Checklist operativo: servicio RAG para ejecutivos de Customer Service (Gate 2)

Cada verificación usa algo que ya existe en el proyecto. No requiere dependencias nuevas. Los comandos se ejecutan desde la raíz del proyecto, con el entorno virtual activo.

## 1. Antes de la primera corrida (o al cambiar de equipo)

| # | Verificación | Comando / dónde mirar | Criterio de aceptación |
|---|---|---|---|
| 1.1 | Entorno, librerías y clave | `python verificar_entorno.py` | "Entorno listo para la corrida final". La clave aparece como "definida" y nunca se muestra |
| 1.2 | La clave no se sube al repositorio | `git status` | `.env` **no** aparece (está en `.gitignore`) |
| 1.3 | Criterios no compensables | `pytest tests/test_gate2.py -v` | Todos los tests pasan |
| 1.4 | Modelo y tarifas | `.env` (`GEMINI_MODEL`, `TARIFA_*`) o los valores por defecto | Coinciden con `docs/decision-arquitectura.md`: `gemini-3.1-flash-lite`, USD 0,25 / 1,50 por 1M tokens |

## 2. Índice y base de conocimiento

| # | Verificación | Comando / dónde mirar | Criterio de aceptación |
|---|---|---|---|
| 2.1 | El índice existe y no se reconstruye | Línea `[indice]` al correr `python src/servicio_rag.py` | La primera vez `indice_creado`; después `indice_reutilizado` con `'nuevos': 0` |
| 2.2 | Cambio de una política | Editar `src/corpus/politicas_atencion.md` y volver a correr | Solo cambia `'modificados'`; no se duplican chunks |
| 2.3 | Cambio de modelo de embeddings | — | Borrar `indice_gate2/` y reindexar: un índice no admite embeddings de otra dimensión |
| 2.4 | Calidad de recuperación tras cambiar políticas | `python src/evaluar_corpus.py` | Exhaustividad con k=3 ≥ 0,9; si baja, revisar los casos fallidos en `docs/evaluacion_recuperacion.md` |

## 3. Durante la operación (costo, latencia y señales de riesgo)

Resumen de las consultas registradas:

```
python src/resumen_operativo.py            # reales y simuladas
python src/resumen_operativo.py --reales   # solo consultas con Gemini
```

| Indicador | Fuente | Umbral de alerta | Valor de referencia medido | Acción si se supera |
|---|---|---|---|---|
| Latencia p95 por consulta | `logs/consumo_llm.jsonl` → `tiempo_total_ms` | > 10.000 ms | 7.750 ms (corrida real A) | Revisar si el cuello es `generacion_ms` (modelo) o `recuperacion_ms` (embeddings). Mitigación candidata: streaming (R-10) |
| Costo por consulta | `costo_usd` | > USD 0,001 | USD 0,00042 | Revisar `tokens.input_tokens`: un k mayor o políticas más largas inflan la entrada |
| Respuestas sin citas del modelo | evento `respuesta_sin_citas_del_modelo` | > 10 % de las consultas | 0 | Revisar el prompt activo (`prompt_huella`) y comparar con la versión anterior (R-01) |
| Documentos descartados por inyección | evento `documentos_descartados` | Cualquier ocurrencia | 0 | Revisar qué política se modificó y quién la cambió (R-02) |
| Consultas bloqueadas | evento `consulta_bloqueada` | Revisión semanal | — | Confirmar si fue un ataque o un falso positivo del filtro (R-03) |
| Errores 429 / 503 del modelo | Consola del servicio | Repetidos en la misma hora | — | Esperar y reintentar; si persisten, revisar la cuota del proyecto en Gemini (R-10) |

`resumen_operativo.py` termina con código 1 si se supera un umbral, así que también sirve en un pipeline de CI.

## 4. Aprobaciones humanas

| # | Situación | Qué se espera | Riesgo |
|---|---|---|---|
| 4.1 | Caso con plazo vencido (POL-12) | Pausa `[hitl] PAUSADO` antes de comunicar el escalamiento | R-05 |
| 4.2 | Ajuste económico (POL-15/16) | Pausa con el monto calculado; si el supervisor rechaza, "NO confirmar al cliente" | R-07 |
| 4.3 | Nueva versión de prompt | `python src/servicio_rag.py --interactivo --proponer-prompt`: diff, aprobación y nueva `prompt_huella` en las consultas siguientes | R-06 |
| 4.4 | Aprobación pendiente al reiniciar el proceso | Hoy se pierde (`InMemorySaver`) | R-11, residual hasta el Gate 3 |

## 5. Antes de entregar o desplegar

| # | Verificación | Comando | Criterio |
|---|---|---|---|
| 5.1 | Suite completa | `pytest` | Todo pasa (`test_orquestacion` requiere la clave en `.env`) |
| 5.2 | Matriz de riesgos vigente | `python src/matriz_riesgos.py` | "OK": todo ALTO/CRÍTICO tiene un punto de supervisión |
| 5.3 | Logs sin contenido crudo | Buscar en `logs/` un nombre de cliente o una frase de la pregunta | 0 coincidencias |
| 5.4 | Evidencia actualizada | `docs/corrida_documentada.md` | Incluye al menos una corrida real con `"simulado": false` |
| 5.5 | Secretos | `git status` y revisar el contenido de cualquier zip | Ni `.env` ni claves en archivos compartidos (R-13) |

## Responsables (propuesta para un piloto)

| Rol | Responsabilidad |
|---|---|
| Ejecutivo | Usar las fuentes antes de responder; no confirmar ajustes pendientes |
| Supervisor | Aprobar o rechazar escalamientos y ajustes |
| Responsable técnico | Secciones 1, 2, 3 y 5; aprobar cambios de prompt |
