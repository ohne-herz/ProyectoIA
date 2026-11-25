# Decisión de arquitectura: elección de modelo

**Nombre:** Alejandro Orrego  
**Fecha comparación:** 2026-10-20  
**Nombre de la miniaplicación:** "Modelo atencion casos"

## Modelo elegido

**gemini-3.1-flash-lite**

Elegí el modelo porque fue el único que completó las 4 ejecuciones sin errores, aplicó correctamente las políticas de atención en todas ellas y tiene un costo por consulta entre 12 y 18 veces menor que los otros candidatos, con una latencia promedio igual o mejor.

## Utilidad de la aplicación

La aplicación sirve para ayudar a ejecutivos de un contact center a responder, mientras el cliente espera en línea, la pregunta "¿qué le respondo a este cliente y en qué estado está su caso?". Para ello cruza una base de conocimiento con procedimientos y políticas de atención (RAG) con el estado de los casos del cliente en un CRM simulado expuesto por API.

Los requisitos que necesito cumplir son:

* **Requisito 1 – Precisión en la aplicación de políticas:** la respuesta debe identificar correctamente el estado del caso, aplicar la política que corresponde y no comprometer plazos ni resultados que las políticas no respaldan.
* **Requisito 2 – Latencia y disponibilidad para atención en línea:** el ejecutivo tiene al cliente esperando, por lo que el modelo debe responder rápido y de forma estable, sin fallas de servicio.
* **Requisito 3 – Costo sostenible a escala:** el costo por consulta debe ser bajo, porque la aplicación se usa en cada interacción de cada ejecutivo.

## Diagrama de arquitectura

[Diagrama de Arquitectura](secuencia%20gemini.drawio)

## Comparación de candidatos

Se compararon los modelos **gemini-3.1-flash-lite**, **gemini-3.8-flash** y **gemini-3.6-flash**, ejecutando 4 veces la misma petición con cada uno. El prompt simula el caso real del proyecto: políticas de reembolso y escalamiento más el estado del cliente en el CRM, con un caso de reembolso que supera el plazo comprometido.

### Resultados de la medición

| Criterio                            | 3.1-flash-lite | 3.8-flash            | 3.6-flash        |
|:------------------------------------|----------------|----------------------|------------------|
| Ejecuciones exitosas                | **4 de 4**     | 1 de 4               | 1 de 4           |
| Latencia promedio                   | **9,35 s**     | 18,19 s        | 9,58 s     |
| Latencia mín – máx                  | 5,65 – 13,25 s | No medible           | No medible       |
| Costo por consulta (USD)            | **$0,000305**  | $0,003704            | $0,005444        |
| Costo relativo                      | **1x**         | ≈ 12x                | ≈ 18x            |
| Proyección 10.000 consultas/mes     | **≈ $3**       | ≈ $37                | ≈ $54            |
| Errores observados                  | Ninguno        | 1 × 503, 2 × timeout | 2 × 429, 1 × 503 |
| Precio 1M tokens (entrada / salida) | $0,25 / $1,50  | $0,75 / $3,75        | $0,75 / $3,75    |


### Cumplimiento de requisitos

| Requisito                      | 3.1-flash-lite                  | 3.8-flash                 | 3.6-flash                 |
|:-------------------------------|---------------------------------|---------------------------|---------------------------|
| R1 – Precisión en políticas    | Cumple (con ajuste de prompt)   | Cumple                    | Cumple                    |
| R2 – Latencia y disponibilidad | Parcial (4 de 4, latencia alta) | No cumple (3 de 4 fallas) | No cumple (3 de 4 fallas) |
| R3 – Costo sostenible          | Cumple (el más bajo)            | Parcial            | No cumple        |

## Justificación

Se definió usar el modelo **gemini-3.1-flash-lite** por las siguientes razones:

1. **Calidad suficiente para el caso de uso:** en las 4 ejecuciones identificó correctamente el incumplimiento de plazo y aplicó el escalamiento según POL-12. Los modelos Flash no mostraron una conclusión distinta ni mejor, solo respuestas algo más completas en la forma.
2. **Único modelo con disponibilidad comprobada:** fue el único que completó las 4 ejecuciones. En un contact center, una herramienta que falla mientras el cliente espera obliga al ejecutivo a volver a la búsqueda manual en varios sistemas.
3. **Costo significativamente menor:** cuesta entre 12 y 18 veces menos por consulta. Los modelos Flash usan más tokens de razonamiento (que se cobran como salida) para llegar a la misma conclusión.
4. **Latencia igual o mejor:** su promedio (9,35 s) es igual o menor que el de los modelos Flash en su única ejecución exitosa.

### Riesgos identificados y mitigaciones

| Riesgo                                                     | Mitigación                                                                                                        |
|:-----------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| Flash-lite promete acciones no respaldadas por la política | Instrucción explícita en el prompt: "No comprometas plazos, resultados ni acciones que no estén en las políticas" |
| Latencia de 5–13 s, alta para atención en línea            | Streaming, limitar el razonamiento y acotar el largo de la respuesta                                              |
| Muestra pequeña y llamadas sin pausa (429)                 | Repetir con pausa entre llamadas y timeout de 60 s                                                                |
| Cambio de precios del proveedor                            | Precios parametrizados por modelo y revisión periódica en la página oficial de Gemini API                         |

## Alternativa descartada y por qué

Se descartó el modelo **gemini-3.6-flash** porque, con la misma calidad de respuesta que flash-lite en la regla de negocio, fue el más caro (≈ 18x por consulta) por su mayor consumo de tokens de razonamiento. Además, falló 3 de 4 ejecuciones (errores 429 y 503), lo que no cumple el requisito de disponibilidad para atención en línea.

También se descartó **gemini-3.8-flash** porque tuvo la mayor latencia (18,19 s en su única ejecución exitosa), dos ejecuciones superaron el tiempo de espera de 30 s y su costo es ≈ 12x el de flash-lite, sin una mejora de calidad que lo justifique.

**Alternativa a evaluar en una siguiente etapa:** un enrutamiento híbrido, con flash-lite por defecto y un modelo Flash solo para consultas complejas (varios casos cruzados o políticas ambiguas). Así se combina el bajo costo de flash-lite con la mayor completitud de los modelos Flash cuando realmente aporta valor.

---

# Decisiones de arquitectura del Gate 2 (servicio RAG)

## D-01. Cómo se llama al modelo: cliente del Gate 1 o cliente de LangChain

En mi ficha escribí que la miniaplicación del Gate 1 pasaría a ser una pieza del servicio. Al integrar el servicio, evalué dos caminos:

| Opción | A favor | En contra |
|---|---|---|
| A. Reutilizar mi cliente HTTP del Gate 1 (`cliente.py` + `consumir_gemini_refactor.py`) | Reutiliza código propio ya probado (reintentos, costo) | No se integra con la cadena de LangChain ni con LangGraph; habría que adaptar mensajes, `usage_metadata` y callbacks; envía la clave como parámetro de URL (`?key=`), que puede quedar en logs intermedios |
| **B. `ChatGoogleGenerativeAI` de LangChain (elegida)** | Compatible con retriever, callbacks y LangGraph; entrega `usage_metadata` estándar; la clave no viaja en la URL | No reutiliza el código del Gate 1, solo sus decisiones |

**Decisión:** opción B. Lo que se conserva del Gate 1 son sus decisiones de diseño, no el archivo: reintentos acotados (`max_retries=2`), `timeout=60` (aprendizaje de los 429/503 de la comparación de modelos), cálculo de costo por tokens con tarifas parametrizadas y el modelo `gemini-3.1-flash-lite`. El cliente del Gate 1 se mantiene para `consistencia.py` (evaluación del banco de prompts con salida estructurada).

## D-02. Reglas de montos en código, no en el modelo

Las políticas POL-15, POL-16, POL-20 y POL-21 definen montos, topes y elegibilidad. Se calculan en `evaluar_ajuste()` y llegan al modelo ya resueltas; el prompt le prohíbe recalcularlas. **Por qué:** un monto de dinero debe ser determinista, auditable y testeable (`test_reglas_de_ajuste_deterministas`). El modelo redacta; no decide cuánto se devuelve.

## D-03. CRM consultado, no indexado

El estado del caso cambia en cada interacción; indexarlo en Chroma dejaría datos viejos. Se consulta en cada pregunta y su tipo y política se usan para enriquecer la búsqueda en la base de conocimiento.

## D-04. Supervisión humana síncrona (alcance Gate 2)

Escalamientos (POL-12), ajustes económicos (POL-20) y cambios de prompt pasan por un grafo de LangGraph con `interrupt()`/`Command`. En esta etapa el checkpointer es en memoria: la aprobación ocurre en la misma ejecución. **Trade-off aceptado:** simple y demostrable ahora; en Gate 3 se reemplaza por un checkpointer persistente y un endpoint de aprobación (riesgos R-05, R-07 y R-11 de `docs/matriz_riesgos.md`).
