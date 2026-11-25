# Evaluación de recuperación sobre el corpus propio (Bloque 27)

Fecha: 2026-11-24 · Modo: **real** · Corpus: `src/corpus/politicas_atencion.md` (6 políticas, 1 chunk por política) · Casos: 10 (9 con respuesta, 1 sin respuesta en el corpus)

## Promedios (solo casos con respuesta)

| k | Precisión | Exhaustividad | F1 |
|---|---|---|---|
| 1 | 1.0 | 0.944 | 0.963 |
| 3 | 0.333 | 0.944 | 0.489 |

## Detalle con k=3

| Pregunta | Recuperados | Precisión | Exhaustividad |
|---|---|---|---|
| ¿En cuántos días hábiles se abona un reembolso aprobado? | POL-07, POL-16, POL-20 | 0.33 | 1.0 |
| El reembolso aprobado lleva más días que el plazo, ¿qué hago? | POL-07, POL-16, POL-20 | 0.33 | 0.5 |
| ¿Cuándo debo escalar un caso a Supervisión? | POL-12, POL-20, POL-21 | 0.33 | 1.0 |
| Me cobraron el precio normal de un producto que estaba en oferta | POL-15, POL-20, POL-16 | 0.33 | 1.0 |
| ¿Cómo se calcula el ajuste por un descuento promocional no aplicado? | POL-15, POL-20, POL-16 | 0.33 | 1.0 |
| Devolví el producto y quiero que me devuelvan el dinero | POL-16, POL-07, POL-20 | 0.33 | 1.0 |
| ¿Puedo confirmarle al cliente el ajuste antes de que lo apruebe el supervisor? | POL-20, POL-15, POL-12 | 0.33 | 1.0 |
| ¿Se puede generar un segundo ajuste económico en el mismo caso? | POL-20, POL-21, POL-15 | 0.33 | 1.0 |
| El cliente insiste en un ajuste sobre un caso que ya está cerrado | POL-21, POL-20, POL-15 | 0.33 | 1.0 |
| ¿Qué horario tiene la sucursal de Concepción? | POL-07, POL-12, POL-21 | 0.0 | None |

## Lectura

- Con k=3 la precisión queda acotada por diseño: la mayoría de las preguntas tiene 1 política relevante, así que el máximo posible es 0,33. La métrica que importa para el ejecutivo es la **exhaustividad** (que la política correcta llegue al contexto).
- El caso sin respuesta (horario de sucursal) igual recupera 3 políticas: el retriever siempre devuelve k documentos. La protección es el prompt ("si falta un dato, dilo") y no comprometer información fuera del contexto.
- Los casos con exhaustividad menor a 1 se ven en el detalle. En el servicio, la búsqueda se enriquece con el tipo de caso y la política que entrega el CRM (por ejemplo, POL-12 cuando el plazo está vencido), lo que compensa parte de estas pérdidas; esta evaluación mide el retriever sin ese refuerzo.
- Decisión: mantener k=3 en el servicio, porque prioriza exhaustividad y el costo de tokens extra es bajo (ver `logs/consumo_llm.jsonl`).
