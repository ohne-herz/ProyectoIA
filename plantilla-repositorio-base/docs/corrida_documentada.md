# Corrida documentada del servicio RAG (Gate 2)

| Corrida | Modo | Fecha | Propósito |
|---|---|---|---|
| **A** | **REAL** (Gemini: `gemini-3.1-flash-lite` + `gemini-embedding-001`) | 2026-11-24 02:13 UTC | Evidencia de punta a punta con modelo real (Bloque 28) |
| B1-B3 | Simulado (`--simulado`) | 2026-11-24 | Evidencia reproducible sin clave: índice, escalamiento, despliegue de prompt y rechazo de ajuste |

Otras corridas reales del Bloque 28: `src/registros_latencia_costo.jsonl` (5 consultas, saneadas sin texto crudo).

---

## A. Corrida REAL con Gemini: descuento no aplicado (CAS-1060)

**Comando:** `python src/servicio_rag.py --pregunta "¿Que le respondo al cliente del caso CAS-1060?"`

**Escenario:** el cliente reclama un descuento promocional no aplicado. Precio cobrado 59.990, precio con descuento 47.990 (diferencia 12.000) y monto reclamado 10.000. Por POL-15, el ajuste no puede superar lo reclamado, así que corresponde 10.000; por POL-20, requiere aprobación de supervisor.

```text
[indice] indice_creado en indice_gate2/ {'previos': 0, 'nuevos': 6, 'modificados': 0, 'eliminados': 0}
{"ts": "2026-11-24T02:13:24.929+00:00", "evento": "consulta_recibida", "trace_id": "trace-7000f14a", "pregunta_len": 46, "pregunta_huella": "d84e5f36ff1a", "modo": "real"}
{"ts": "2026-11-24T02:13:24.931+00:00", "evento": "indice_creado", "trace_id": "trace-7000f14a"}
{"ts": "2026-11-24T02:13:24.933+00:00", "evento": "crm_consultado", "trace_id": "trace-7000f14a", "caso_id": "CAS-1060", "n_aprobaciones": 1}
{"ts": "2026-11-24T02:13:25.990+00:00", "evento": "documentos_recuperados", "trace_id": "trace-7000f14a", "n": 3, "ids": "POL-15,POL-20,POL-12"}
{"ts": "2026-11-24T02:13:32.683+00:00", "evento": "consumo_llm", "trace_id": "trace-7000f14a", "input_tokens": 606, "output_tokens": 180, "costo_usd": 0.0004215, "prompt_huella": "b9b8ec0cb6f2", "simulado": false}
{"ts": "2026-11-24T02:13:32.685+00:00", "evento": "respuesta_generada", "trace_id": "trace-7000f14a", "respuesta_len": 826, "respuesta_huella": "589b351631a0", "n_fuentes": 3}
--- respuesta completa del servicio ---
{
  "trace_id": "trace-7000f14a",
  "respuesta": "1) Estado del caso: En revisión, con ajuste de 10.000 pendiente de aprobación.\n\n2) Le informo que su reclamo por el descuento no aplicado en el caso CAS-1060 se encuentra actualmente en proceso de revisión. La solicitud de ajuste por 10.000 ya ha sido ingresada al sistema y se encuentra pendiente de la aprobación final por parte de un supervisor [1, 2]. Le pido por favor aguardar, ya que no puedo confirmar la aplicación del ajuste hasta obtener dicha validación [2].\n\n3) Acción del ejecutivo: Verificar que la solicitud de ajuste por 10.000 se encuentre correctamente ingresada en la herramienta, informando al cliente que esta debe ser aprobada por un supervisor según la política POL-15 y POL-20 [1, 2].\n\nFuentes: [1] politicas_atencion.md (POL-15); [2] politicas_atencion.md (POL-20); [3] politicas_atencion.md (POL-12)",
  "fuentes": [
    {"n": 1, "fuente": "politicas_atencion.md", "politica": "POL-15", "citada_por_modelo": false},
    {"n": 2, "fuente": "politicas_atencion.md", "politica": "POL-20", "citada_por_modelo": true},
    {"n": 3, "fuente": "politicas_atencion.md", "politica": "POL-12", "citada_por_modelo": false}
  ],
  "prompt_huella": "b9b8ec0cb6f2",
  "aprobaciones_pendientes": [
    {"tipo": "ajuste_economico", "politica": "POL-20", "caso_id": "CAS-1060", "monto": 10000,
     "detalle": "POL-15: diferencia 12000, tope monto reclamado 10000"}
  ],
  "tiempos_ms": {"crm_ms": 0.96, "recuperacion_ms": 1056.22, "armado_prompt_ms": 0.14, "generacion_ms": 6692.62},
  "auditoria": ["... los mismos 6 eventos de arriba, omitidos por brevedad ..."]
}
--- punto de supervision humana: ajuste_economico (POL-20) ---
[hitl] caso CAS-1060: ajuste_economico por 10000 (POL-15: diferencia 12000, tope monto reclamado 10000) -> requiere aprobacion de supervisor (POL-20)
[hitl] PAUSADO, pendiente de aprobacion: {"motivo": "aprobar ajuste_economico segun POL-20 antes de comunicarlo al cliente", "caso_id": "CAS-1060", "monto": 10000, "trace_id": "trace-7000f14a"}
[hitl] (modo demo) decision del supervisor simulada: aprobar
[hitl] caso CAS-1060: ajuste aprobado: el ejecutivo puede confirmarlo; el abono sigue POL-07
estado final: {'tipo': 'ajuste_economico', 'politica': 'POL-20', 'caso_id': 'CAS-1060', 'trace_id': 'trace-7000f14a', 'detalle': 'POL-15: diferencia 12000, tope monto reclamado 10000', 'monto': 10000, 'aprobado': True, 'resultado': 'ajuste aprobado: el ejecutivo puede confirmarlo; el abono sigue POL-07'}
Proceso terminado sin errores.
```

> Salida copiada de la consola. Se compactó el formato de `fuentes` y se omitió `auditoria`, que repite los 6 eventos JSON del inicio; los valores no se modificaron.

### A.1 Verificación contra la rúbrica

| Criterio | Evidencia en la corrida | Resultado |
|---|---|---|
| Pipeline de punta a punta (no compensable) | Sin `Traceback`; termina con `Proceso terminado sin errores.` | ✅ |
| Índice persistido con embeddings reales | `indice_creado en indice_gate2/` con 6 políticas; en la próxima corrida debe decir `indice_reutilizado` | ✅ |
| Cita de fuente (no compensable) | La respuesta cita `[1, 2]` y `[2]`; el campo `fuentes` lista POL-15, POL-20 y POL-12 | ✅ |
| Logs sin contenido crudo (no compensable) | Los eventos solo tienen largos (`pregunta_len`, `respuesta_len`), huellas, `caso_id` y códigos de política. No aparecen ni la pregunta, ni el texto de las políticas, ni el nombre del cliente | ✅ |
| Supervisión humana (no compensable) | El grafo se pausa (`PAUSADO, pendiente de aprobacion`) y continúa con la decisión. En esta corrida la decisión fue la del modo demo; el rechazo interactivo está en B3 | ✅ |
| Un `trace_id` por consulta | `trace-7000f14a` en los 6 eventos, en la respuesta y en la solicitud de aprobación | ✅ |
| Regla de negocio respetada | Monto de 10.000 (tope del monto reclamado), no 12.000 | ✅ |
| POL-20: no confirmar un ajuste pendiente | La respuesta dice "no puedo confirmar la aplicación del ajuste hasta obtener dicha validación" | ✅ |
| Trazabilidad del prompt | `prompt_huella: b9b8ec0cb6f2` (versión v1 activa) | ✅ |

### A.2 Costo y latencia (Bloque 28)

| Métrica | Valor | Lectura |
|---|---|---|
| Tokens de entrada / salida | 606 / 180 | El contexto (3 políticas + CRM) multiplica la entrada frente a la pregunta sola |
| Costo por consulta | USD 0,0004215 | 606 × 0,25/1M + 180 × 1,50/1M (verificado) |
| Proyección 10.000 consultas/mes | ≈ USD 4,2 | En línea con los ≈ USD 3 de `decision-arquitectura.md`, más alto por el contexto RAG |
| Recuperación (embedding de la consulta + búsqueda) | 1.056 ms | Incluye una llamada a la API de embeddings |
| Generación | 6.693 ms | 86 % del tiempo total |
| CRM + armado del prompt | ~1 ms | Despreciable |
| **Total** | **≈ 7,75 s** | Dentro del rango medido en el Gate 1 (5-13 s). Sigue siendo alto para atención en línea (riesgo R-10); la mitigación candidata es streaming |

### A.3 Hallazgos de la revisión manual y correcciones

Revisé la respuesta a mano, porque la métrica automática no mide si el contenido es correcto (ver `docs/limites_metrica.md`).

| # | Hallazgo | Causa | Corrección | Prueba |
|---|---|---|---|---|
| H-1 | El modelo afirmó que la solicitud de ajuste "**ya ha sido ingresada al sistema**", y en el paso 3 pidió "verificar que se encuentre ingresada". Es falso: el CRM tiene `ajustes_generados: 0`, y por POL-15 es el ejecutivo quien debe generar la solicitud | El bloque CRM decía `estado_ajuste: PENDIENTE de aprobacion`, y el modelo interpretó "pendiente" como "solicitud ya creada". Es una ambigüedad del dato, no de la política | El CRM ahora dice explícitamente `solicitud_de_ajuste: NO ingresada aun, el ejecutivo debe generarla con la herramienta de solicitud de ajuste \| aprobacion: quedara PENDIENTE de supervisor (POL-20)`. Mismo cambio en el ejemplo del prompt `Asistente_Ejecutivo` del banco | `test_crm_no_sugiere_solicitud_ya_ingresada` |
| H-2 | POL-15 quedó con `citada_por_modelo: false` aunque el modelo la citó | Gemini agrupa citas como `[1, 2]` y la expresión regular solo reconocía `[1]` | Nueva función `extraer_citas()`, que reconoce citas simples y agrupadas | `test_citas_agrupadas_se_reconocen` |
| H-3 | Se recuperó POL-12 (escalamiento), que no aplica a este caso | Con k=3 siempre llegan 3 políticas; la tercera es la menos parecida | Sin cambio: el modelo no la usó. Es el costo aceptado de priorizar exhaustividad (ver `docs/evaluacion_recuperacion.md`) | — |

**Lección (riesgo R-01):** las políticas estaban bien, y el error vino de cómo se redactó el dato estructurado que recibe el modelo. Los campos de estado deben describir hechos ("no ingresada") y no estados ambiguos ("pendiente").

> **Pendiente:** volver a ejecutar esta corrida real con las correcciones y confirmar que el paso 3 indica "generar la solicitud con la herramienta" y que POL-15 aparece con `citada_por_modelo: true`.

---

## B. Corridas simuladas (reproducibles sin clave)

> Embeddings léxicos y modelo deterministas, sin llamar a la API. Los tokens son aproximados (largo/4) y el costo usa las tarifas de `gemini-3.1-flash-lite`.

### B1. Primera corrida: el índice se crea

```
[indice] indice_creado en indice_gate2_simulado/ {'previos': 0, 'nuevos': 6, 'modificados': 0, 'eliminados': 0}
```

### B2. Reembolso vencido (CAS-1043): índice reutilizado, escalamiento POL-12 y despliegue de prompt

Comando: `python src/servicio_rag.py --simulado --proponer-prompt`

```
[indice] indice_reutilizado en indice_gate2_simulado/ {'previos': 6, 'nuevos': 0, 'modificados': 0, 'eliminados': 0}
{"ts": "2026-11-24T02:15:22.095+00:00", "evento": "consulta_recibida", "trace_id": "trace-350b9c69", "pregunta_len": 67, "pregunta_huella": "1db5c6703745", "modo": "simulado"}
{"ts": "2026-11-24T02:15:22.095+00:00", "evento": "indice_reutilizado", "trace_id": "trace-350b9c69"}
{"ts": "2026-11-24T02:15:22.095+00:00", "evento": "crm_consultado", "trace_id": "trace-350b9c69", "caso_id": "CAS-1043", "n_aprobaciones": 1}
{"ts": "2026-11-24T02:15:22.098+00:00", "evento": "documentos_recuperados", "trace_id": "trace-350b9c69", "n": 3, "ids": "POL-07,POL-12,POL-16"}
{"ts": "2026-11-24T02:15:22.099+00:00", "evento": "consumo_llm", "trace_id": "trace-350b9c69", "input_tokens": 495, "output_tokens": 145, "costo_usd": 0.00034125, "prompt_huella": "b9b8ec0cb6f2", "simulado": true}
{"ts": "2026-11-24T02:15:22.099+00:00", "evento": "respuesta_generada", "trace_id": "trace-350b9c69", "respuesta_len": 698, "respuesta_huella": "9686d9a5d11a", "n_fuentes": 3}
--- respuesta completa del servicio ---
{
  "trace_id": "trace-350b9c69",
  "respuesta": "1) Estado del caso: caso_id: CAS-1043 | tipo: Reembolso | estado: Aprobado | dias_habiles_desde_aprobacion: 13 | monto_reclamado: 34990 | ajustes_generados: 0 | politica_aplicable: POL-07 | plazo_dias: 10 | dias_transcurridos: 13 | plazo_restante_dias: 0 | requiere_escalamiento: True | ajuste: no procede (POL-07: ya aprobado: se abona segun POL-07)\n2) Que le respondo al cliente: Un reembolso aprobado se abona en un plazo máximo de 10 días hábiles desde su aprobación [1].\n3) Accion del ejecutivo: aplicar POL-07 [1]; escalar a Supervision y ofrecer nueva fecha en 48 horas [2].\n\nFuentes: [1] politicas_atencion.md (POL-07); [2] politicas_atencion.md (POL-12); [3] politicas_atencion.md (POL-16)",
  "fuentes": [
    {
      "n": 1,
      "fuente": "politicas_atencion.md",
      "politica": "POL-07",
      "citada_por_modelo": true
    },
    {
      "n": 2,
      "fuente": "politicas_atencion.md",
      "politica": "POL-12",
      "citada_por_modelo": true
    },
    {
      "n": 3,
      "fuente": "politicas_atencion.md",
      "politica": "POL-16",
      "citada_por_modelo": false
    }
  ],
  "prompt_huella": "b9b8ec0cb6f2",
  "aprobaciones_pendientes": [
    {
      "tipo": "escalamiento",
      "politica": "POL-12",
      "caso_id": "CAS-1043",
      "detalle": "13 dias vs plazo 10"
    }
  ],
  "tiempos_ms": {
    "crm_ms": 0.12,
    "recuperacion_ms": 2.81,
    "armado_prompt_ms": 0.07,
    "generacion_ms": 0.36
  },
  "auditoria": [
    {
      "ts": "2026-11-24T02:15:22.095+00:00",
      "evento": "consulta_recibida",
      "trace_id": "trace-350b9c69",
      "pregunta_len": 67,
      "pregunta_huella": "1db5c6703745",
      "modo": "simulado"
    },
    {
      "ts": "2026-11-24T02:15:22.095+00:00",
      "evento": "indice_reutilizado",
      "trace_id": "trace-350b9c69"
    },
    {
      "ts": "2026-11-24T02:15:22.095+00:00",
      "evento": "crm_consultado",
      "trace_id": "trace-350b9c69",
      "caso_id": "CAS-1043",
      "n_aprobaciones": 1
    },
    {
      "ts": "2026-11-24T02:15:22.098+00:00",
      "evento": "documentos_recuperados",
      "trace_id": "trace-350b9c69",
      "n": 3,
      "ids": "POL-07,POL-12,POL-16"
    },
    {
      "ts": "2026-11-24T02:15:22.099+00:00",
      "evento": "consumo_llm",
      "trace_id": "trace-350b9c69",
      "input_tokens": 495,
      "output_tokens": 145,
      "costo_usd": 0.00034125,
      "prompt_huella": "b9b8ec0cb6f2",
      "simulado": true
    },
    {
      "ts": "2026-11-24T02:15:22.099+00:00",
      "evento": "respuesta_generada",
      "trace_id": "trace-350b9c69",
      "respuesta_len": 698,
      "respuesta_huella": "9686d9a5d11a",
      "n_fuentes": 3
    }
  ]
}
--- punto de supervision humana: escalamiento (POL-12) ---
[hitl] caso CAS-1043: escalamiento (13 dias vs plazo 10) -> requiere aprobacion de supervisor (POL-12)
[hitl] PAUSADO, pendiente de aprobacion: {"motivo": "aprobar escalamiento segun POL-12 antes de comunicarlo al cliente", "caso_id": "CAS-1043", "monto": null, "trace_id": "trace-350b9c69"}
[hitl] (modo demo) decision del supervisor simulada: aprobar
[hitl] caso CAS-1043: escalado a Supervision: ofrecer nueva fecha de contacto dentro de 48 horas
estado final: {'tipo': 'escalamiento', 'politica': 'POL-12', 'caso_id': 'CAS-1043', 'trace_id': 'trace-350b9c69', 'detalle': '13 dias vs plazo 10', 'aprobado': True, 'resultado': 'escalado a Supervision: ofrecer nueva fecha de contacto dentro de 48 horas'}
--- punto de supervision humana: despliegue de prompt ---
[hitl] propuesta de prompt b9b8ec0cb6f2 -> 53b072dabe9b
    --- version_activa
    +++ version_propuesta
    @@ -132,3 +132,19 @@
     citando
     la
     politica.
    +En
    +reembolsos
    +aprobados,
    +informa
    +siempre
    +la
    +fecha
    +de
    +aprobacion
    +y
    +el
    +plazo
    +restante
    +de
    +abono
    +(POL-07).
[hitl] PAUSADO, pendiente de aprobacion: {"motivo": "aprobar nueva version de prompt en produccion", "huella_propuesta": "53b072dabe9b"}
[hitl] (modo demo) decision del supervisor simulada: aprobar
[hitl] version 53b072dabe9b activada
Proceso terminado sin errores.
```

### B3. Descuento no aplicado (CAS-1060): el supervisor RECHAZA el ajuste

Comando: `python src/servicio_rag.py --simulado --interactivo --pregunta "¿Que le respondo al cliente del caso CAS-1060?"` (respuesta del supervisor: `n`)

```
{"ts": "2026-11-24T02:15:23.394+00:00", "evento": "consulta_recibida", "trace_id": "trace-26928f22", "pregunta_len": 46, "pregunta_huella": "d84e5f36ff1a", "modo": "simulado"}
{"ts": "2026-11-24T02:15:23.394+00:00", "evento": "indice_reutilizado", "trace_id": "trace-26928f22"}
{"ts": "2026-11-24T02:15:23.394+00:00", "evento": "crm_consultado", "trace_id": "trace-26928f22", "caso_id": "CAS-1060", "n_aprobaciones": 1}
{"ts": "2026-11-24T02:15:23.398+00:00", "evento": "documentos_recuperados", "trace_id": "trace-26928f22", "n": 3, "ids": "POL-20,POL-15,POL-21"}
{"ts": "2026-11-24T02:15:23.399+00:00", "evento": "consumo_llm", "trace_id": "trace-26928f22", "input_tokens": 639, "output_tokens": 216, "costo_usd": 0.00048375, "prompt_huella": "53b072dabe9b", "simulado": true}
{"ts": "2026-11-24T02:15:23.399+00:00", "evento": "respuesta_generada", "trace_id": "trace-26928f22", "respuesta_len": 981, "respuesta_huella": "5738eb9a81b7", "n_fuentes": 3}
  "respuesta": "1) Estado del caso: caso_id: CAS-1060 | tipo: Descuento no aplicado | estado: En revision | precio_cobrado: 59990 | precio_con_descuento: 47990 | monto_reclamado: 10000 | ajustes_generados: 0 | requiere_escalamiento: False | politica_aplicable: POL-15 | ajuste_calculado: 10000 (POL-15, diferencia 12000, tope monto reclamado 10000) | solicitud_de_ajuste: NO ingresada aun, el ejecutivo debe generarla con la herramienta de solicitud de ajuste | aprobacion: quedara PENDIENTE de supervisor (POL-20), no confirmar el ajuste al cliente\n2) Que le respondo al cliente: Si el cliente reclama un descuento promocional que no se aplicó en su compra, el ejecutivo verifica que exista un caso abierto o en revisión de tipo \"Descuento no aplicado\" [2].\n3) Accion del ejecutivo: aplicar POL-15 [2]; solicitar aprobacion del supervisor y no confirmar el ajuste al cliente [1].\n\nFuentes: [1] politicas_atencion.md (POL-20); [2] politicas_atencion.md (POL-15); [3] politicas_atencion.md (POL-21)",
[hitl] caso CAS-1060: ajuste_economico por 10000 (POL-15: diferencia 12000, tope monto reclamado 10000) -> requiere aprobacion de supervisor (POL-20)
[hitl] PAUSADO, pendiente de aprobacion: {"motivo": "aprobar ajuste_economico segun POL-20 antes de comunicarlo al cliente", "caso_id": "CAS-1060", "monto": 10000, "trace_id": "trace-26928f22"}
[hitl] ¿Aprobar? (s/n): [hitl] caso CAS-1060: ajuste rechazado: el ejecutivo NO confirma el ajuste al cliente
estado final: {'tipo': 'ajuste_economico', 'politica': 'POL-20', 'caso_id': 'CAS-1060', 'trace_id': 'trace-26928f22', 'detalle': 'POL-15: diferencia 12000, tope monto reclamado 10000', 'monto': 10000, 'aprobado': False, 'resultado': 'ajuste rechazado: el ejecutivo NO confirma el ajuste al cliente'}
```

### B4. Registro de consumo (`logs/consumo_llm.jsonl`, corridas simuladas)

```
{"ts": "2026-11-24T02:15:20+00:00", "trace_id": "trace-0a6d4486", "modelo": "simulado", "simulado": true, "k": 3, "prompt_huella": "b9b8ec0cb6f2", "pregunta_huella": "1db5c6703745", "tokens": {"input_tokens": 495, "output_tokens": 145, "total_tokens": 640}, "costo_usd": 0.00034125, "tiempos_ms": {"crm_ms": 0.15, "recuperacion_ms": 2.75, "armado_prompt_ms": 0.34, "generacion_ms": 0.39}, "tiempo_total_ms": 3.63}
{"ts": "2026-11-24T02:15:22+00:00", "trace_id": "trace-350b9c69", "modelo": "simulado", "simulado": true, "k": 3, "prompt_huella": "b9b8ec0cb6f2", "pregunta_huella": "1db5c6703745", "tokens": {"input_tokens": 495, "output_tokens": 145, "total_tokens": 640}, "costo_usd": 0.00034125, "tiempos_ms": {"crm_ms": 0.12, "recuperacion_ms": 2.81, "armado_prompt_ms": 0.07, "generacion_ms": 0.36}, "tiempo_total_ms": 3.36}
{"ts": "2026-11-24T02:15:23+00:00", "trace_id": "trace-26928f22", "modelo": "simulado", "simulado": true, "k": 3, "prompt_huella": "53b072dabe9b", "pregunta_huella": "d84e5f36ff1a", "tokens": {"input_tokens": 639, "output_tokens": 216, "total_tokens": 855}, "costo_usd": 0.00048375, "tiempos_ms": {"crm_ms": 0.12, "recuperacion_ms": 3.53, "armado_prompt_ms": 0.07, "generacion_ms": 0.34}, "tiempo_total_ms": 4.06}
```

---

## Qué demuestra este documento

- El servicio corre de punta a punta con **Gemini real** y en modo simulado, con el mismo código.
- **Mismo `trace_id`** en todos los eventos de una consulta, en su registro de consumo y en la aprobación del supervisor.
- **Sin contenido crudo** en los logs: solo largos, huellas, ids de caso y códigos de política.
- **Reglas de dinero deterministas**: el monto del ajuste lo calcula el código (10.000 con tope) y el modelo no lo recalcula.
- **Supervisión humana real**: el grafo se detiene y respeta tanto la aprobación (A, B2) como el rechazo (B3).
- **Mejora con evidencia**: la revisión manual de la corrida real encontró 2 defectos (H-1, H-2), que se corrigieron y quedaron cubiertos por tests.