# Decisión de arquitectura: elección de modelo
  Nombre: Alejandro Orrego
  Fecha comparación: 2026-10-20
  Nombre de la miniaplicacion: "Modelo atencion casos"
 ## Modelo elegido
  **gemini-3.1-flash-lite**

Elegí el modelo porque fue el único que completó las 4 ejecuciones sin errores, aplicó correctamente las políticas de atención en todas ellas y tiene un costo por consulta entre 12 y 18 veces menor que los otros candidatos, con una latencia promedio igual o mejor.  
  
# Utilidad de la aplicación

La aplicación sirve para ayudar a ejecutivos de un contact center a responder, mientras el cliente espera en línea, la pregunta "¿qué le respondo a este cliente y en qué estado está su caso?". Para ello cruza una base de conocimiento con procedimientos y políticas de atención (RAG) con el estado de los casos del cliente en un CRM simulado expuesto por API.


Los requisitos que necesito cumplir son:

* **Requisito 1 – Precisión en la aplicación de políticas:** la respuesta debe identificar correctamente el estado del caso, aplicar la política que corresponde y no comprometer plazos ni resultados que las políticas no respaldan.
* **Requisito 2 – Latencia y disponibilidad para atención en línea:** el ejecutivo tiene al cliente esperando, por lo que el modelo debe responder rápido y de forma estable, sin fallas de servicio.
* **Requisito 3 – Costo sostenible a escala:** el costo por consulta debe ser bajo, porque la aplicación se usa en cada interacción de cada ejecutivo.

 ## Diagrama de arquitectura
  [Diagrama de Arquitectura] - (docs/secuencia gemini.drawio)

 ## Comparación de candidatos

Se compararon los modelos **gemini-3.1-flash-lite**, **gemini-3.8-flash** y **gemini-3.6-flash**, ejecutando 4 veces la misma petición con cada uno. El prompt simula el caso real del proyecto: políticas de reembolso y escalamiento (RAG) más el estado del cliente en el CRM, con un caso de reembolso que supera el plazo comprometido.

### Resultados de la medición

| Criterio | gemini-3.1-flash-lite | gemini-3.8-flash | gemini-3.6-flash |
|---|---|---|---|
| Ejecuciones exitosas | **4 de 4** | 1 de 4 | 1 de 4 |
| Latencia promedio | **9,35 s** | 18,19 s (1 muestra) | 9,58 s (1 muestra) |
| Latencia mínima – máxima | 5,65 s – 13,25 s | No medible | No medible |
| Costo por consulta (USD) | **$0,000305** | $0,003704 | $0,005444 |
| Costo relativo vs flash-lite | **1x** | ≈ 12x | ≈ 18x |
| Proyección 10.000 consultas/mes | **≈ $3** | ≈ $37 | ≈ $54 |
| Errores observados | Ninguno | 503 (servicio sobrecargado) y 2 timeouts (más de 30 s) | 2 × 429 (límite de peticiones) y 503 |
| Precio por 1M tokens (entrada / salida) | $0,25 / $1,50 | $0,75 / $3,75 | $0,75 / $3,75 |

### Evaluación de calidad de respuesta

| Criterio | gemini-3.1-flash-lite | gemini-3.8-flash | gemini-3.6-flash |
|---|---|---|---|
| Detecta que el caso superó el plazo (13 vs 10 días hábiles) |  4 de 4 |  1 de 1 |  1 de 1 |
| Aplica escalamiento según POL-12 |  4 de 4 |  1 de 1 |  1 de 1 |
| Cita ambas políticas (POL-07 y POL-12) | Parcial (2 de 4) |  |  |
| Respuesta consistente entre ejecuciones |  Misma conclusión en las 4 | No evaluable | No evaluable |
| Compromisos no respaldados por la política |  En 3 de 4 ("agilizar su pago", "una resolución", "He escalado" antes de hacerlo) | No observados | No observados |

### Cumplimiento de requisitos

| Requisito | gemini-3.1-flash-lite | gemini-3.8-flash | gemini-3.6-flash |
|---|---|---|---|
| R1 – Precisión en políticas |  Cumple, con ajuste de prompt |  Cumple |  Cumple |
| R2 – Latencia y disponibilidad |  Disponible 4 de 4, pero la latencia es alta para atención en línea |  3 de 4 fallidas, la más lenta |  3 de 4 fallidas |
| R3 – Costo sostenible |  El más bajo |  ≈ 12x |  ≈ 18x, el más alto |

## Justificación

Se definió usar el modelo **gemini-3.1-flash-lite** por las siguientes razones:

1. **Calidad suficiente para el caso de uso:** en las 4 ejecuciones identificó correctamente el incumplimiento de plazo y aplicó el escalamiento según POL-12. Los modelos Flash no mostraron una conclusión distinta ni mejor, solo respuestas algo más completas en la forma.
2. **Único modelo con disponibilidad comprobada:** fue el único que completó las 4 ejecuciones. En un contact center, una herramienta que falla mientras el cliente espera obliga al ejecutivo a volver a la búsqueda manual en varios sistemas.
3. **Costo significativamente menor:** cuesta entre 12 y 18 veces menos por consulta. Los modelos Flash usan más tokens de razonamiento (que se cobran como salida) para llegar a la misma conclusión.
4. **Latencia igual o mejor:** su promedio (9,35 s) es igual o menor que el de los modelos Flash en su única ejecución exitosa.

**Riesgos identificados y mitigaciones:**

| Riesgo | Mitigación |
|---|---|
| Flash-lite compromete acciones o resultados no respaldados por la política | Agregar al prompt una instrucción explícita: "No comprometas plazos, resultados ni acciones que no estén en las políticas entregadas". |
| Latencia de 5–13 s, alta para atención en línea | Usar streaming para que el ejecutivo empiece a leer en menos de 1 s, limitar el razonamiento y acotar el largo de la respuesta. |
| Muestra de 4 ejecuciones y prueba sin pausa entre llamadas | Repetir la medición con pausa entre llamadas y timeout de 60 s para validar los modelos Flash con 4 de 4 muestras. |
| Cambio de precios del proveedor | Mantener los precios parametrizados por modelo y revisarlos periódicamente en la página oficial de precios de Gemini API. |

## Alternativa descartada y por qué

Se descartó el modelo **gemini-3.6-flash** porque, con la misma calidad de respuesta que flash-lite en la regla de negocio, fue el más caro (≈ 18x por consulta) por su mayor consumo de tokens de razonamiento. Además, falló 3 de 4 ejecuciones (errores 429 y 503), lo que no cumple el requisito de disponibilidad para atención en línea.

También se descartó **gemini-3.8-flash** porque tuvo la mayor latencia (18,19 s en su única ejecución exitosa), dos ejecuciones superaron el tiempo de espera de 30 s y su costo es ≈ 12x el de flash-lite, sin una mejora de calidad que lo justifique.

**Alternativa a evaluar en una siguiente etapa:** un enrutamiento híbrido, con flash-lite por defecto y un modelo Flash solo para consultas complejas (varios casos cruzados o políticas ambiguas). Así se combina el bajo costo de flash-lite con la mayor completitud de los modelos Flash cuando realmente aporta valor.
