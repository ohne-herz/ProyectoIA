# Matriz de riesgos: asistente para ejecutivos de Customer Service conectado a Dynamics 365

> Archivo generado por `python src/matriz_riesgos.py --markdown`. La fuente es `src/matriz_riesgos.py`: 

## Contexto

El asistente **apoya al ejecutivo** (agent assist): le sugiere qué responder y qué acción tomar mientras atiende a un cliente. No conversa con el cliente final. Combina la base de conocimiento de políticas (RAG) con el estado del caso en el CRM: un JSON simulado en el prototipo y Dynamics 365 Customer Service sobre Dataverse en la arquitectura objetivo.

**Método (Bloque 32):** probabilidad e impacto de 1 a 5; puntaje = P × I; CRÍTICO ≥ 15 · ALTO ≥ 9 · MEDIO ≥ 4 · BAJO < 4. "Al límite" = un punto más o menos en P o I cambia la categoría: conviene que otra persona revise la estimación.

## Parte A: prototipo (alcance Gate 2, controles implementados)

CRITICO: 1 · ALTO: 6 · MEDIO: 4 · BAJO: 1

| ID | Riesgo | P | I | Puntaje | Categoría | Al límite | Mitigación | Punto de supervisión |
|---|---|---|---|---|---|---|---|---|
| R-07 | Un ajuste economico (POL-15/16) se calcula mal, supera el monto reclamado o se confirma al cliente sin aprobacion (POL-20) | 3 | 5 | 15 | **CRITICO** | Sí | Monto calculado en codigo con tope (evaluar_ajuste) + CRM explicito 'solicitud NO ingresada' + aprobacion de supervisor (Bloque 32, servicio Gate 2) | Humano: grafo_aprobacion tipo ajuste_economico; un rechazo deja la instruccion 'NO confirmar al cliente' |
| R-01 | El asistente sugiere al ejecutivo una respuesta sin respaldo en las politicas y el ejecutivo se la dice al cliente como oficial | 3 | 4 | 12 | **ALTO** | Sí | Fuentes adjuntas desde los documentos usados + prompt restringido a <contexto>/<crm> + respuesta fija sin contexto (Bloque 27, servicio Gate 2) | Humano: el ejecutivo revisa las fuentes antes de hablar (agent assist). Automatico: evento respuesta_sin_citas_del_modelo |
| R-04 | Datos personales del cliente (nombre, RUT, montos) quedan en los logs o se envian al modelo sin necesidad | 3 | 4 | 12 | **ALTO** | Sí | Logs con largo y huella + guardia que rechaza texto largo + nombre del cliente excluido del prompt (Bloque 31) | Automatico: test_logs_sin_contenido_crudo en cada cambio (criterio no compensable) |
| R-05 | El ejecutivo comunica un escalamiento o una nueva fecha por plazo vencido (POL-12) sin autorizacion de supervision | 3 | 4 | 12 | **ALTO** | Sí | Plazo vencido calculado en codigo + grafo de aprobacion con interrupt()/Command (Bloque 32) | Humano: grafo_aprobacion tipo escalamiento; interrupt() hasta la decision del supervisor |
| R-06 | Se cambia el prompt de sistema sin control y no se puede saber que version genero cada sugerencia | 3 | 4 | 12 | **ALTO** | Sí | RegistroDePrompts con huella + prompt_huella en cada respuesta + despliegue con aprobacion (Bloque 32) | Humano: grafo_despliegue_prompt; sin aprobacion la version no se activa |
| R-10 | Latencia de ~7,75 s o errores 429/503 del modelo mientras el cliente espera en linea | 4 | 3 | 12 | **ALTO** | Sí | timeout + reintentos acotados + latencia por etapa en consumo_llm.jsonl (Bloque 28) | Automatico: revision de tiempos_ms por trace_id en consumo_llm.jsonl; el ejecutivo vuelve a la busqueda manual si no hay respuesta |
| R-03 | Inyeccion de prompt via texto del cliente que el ejecutivo copia desde el chat al asistente | 3 | 3 | 9 | **ALTO** | Sí | Bloqueo de la consulta antes de la recuperacion y del modelo (Bloque 31) | Automatico: evento consulta_bloqueada; el ejecutivo sigue sin el asistente y se revisan los bloqueos semanalmente |
| R-02 | Inyeccion de prompt via texto oculto en un documento de politicas indexado | 2 | 4 | 8 | MEDIO | Sí | Filtro de patrones sobre Document.page_content + delimitacion de contexto (Bloque 31) | — |
| R-08 | Se genera un ajuste sobre un caso cerrado (POL-21) o un segundo ajuste en el mismo caso (POL-20) | 2 | 4 | 8 | MEDIO | Sí | evaluar_ajuste bloquea estados cerrados y ajustes previos, con test por escenario (servicio Gate 2) | — |
| R-09 | El asistente muestra un estado de caso desactualizado porque el dato del CRM quedo indexado | 2 | 3 | 6 | MEDIO | Sí | CRM consultado en cada pregunta, no indexado (decision de personalizacion, Bloque 30) | — |
| R-11 | Una solicitud de ajuste pendiente se pierde o vence porque la aprobacion vive en memoria | 2 | 3 | 6 | MEDIO | Sí | Checkpointer persistente y cola de aprobaciones (planificado Gate 3) | — |
| R-21 | El proveedor cambia las tarifas del modelo y el costo calculado queda desactualizado | 2 | 1 | 2 | BAJO | Sí | Tarifas parametrizadas en .env y revision periodica (Bloque 28) | — |

## Parte B: integración con Dynamics 365 (diseño objetivo, no implementado)

CRITICO: 2 · ALTO: 3 · MEDIO: 4 · BAJO: 0

| ID | Riesgo | P | I | Puntaje | Categoría | Al límite | Mitigación | Punto de supervisión |
|---|---|---|---|---|---|---|---|---|
| R-13 | Se expone el secreto del app registration de Entra ID (en codigo, .env compartido o zip) | 3 | 5 | 15 | **CRITICO** | Sí | .env fuera de Git (Gate 1) + certificado o identidad administrada + Key Vault con rotacion (diseño) | Revision de secretos antes de cada entrega/commit + alertas de inicio de sesion del service principal en Entra ID |
| R-14 | Datos de clientes de Dynamics 365 salen del tenant de Microsoft hacia un modelo externo sin base contractual validada | 3 | 5 | 15 | **CRITICO** | Sí | Minimizacion de datos enviados al modelo (Bloque 31) + evaluar un modelo dentro del tenant (diseño) | Gate de aprobacion de seguridad y legal del cliente antes de conectar datos reales; sin aprobacion solo datos simulados |
| R-12 | El servicio lee Dataverse con un usuario de aplicacion de permisos amplios y muestra al ejecutivo casos o columnas que su rol no permite | 3 | 4 | 12 | **ALTO** | Sí | Usuario de aplicacion con rol minimo + impersonacion del ejecutivo + seguridad por columna (diseño) | Pruebas de acceso por rol en UAT + auditoria de Dataverse, aprobadas por el arquitecto antes de PROD |
| R-15 | Un reintento o una doble aprobacion crea dos solicitudes de ajuste en Dataverse para el mismo caso | 3 | 4 | 12 | **ALTO** | Sí | Escritura idempotente (clave alternativa o upsert) + validacion server-side en Dataverse (diseño) | Humano: grafo de aprobacion existente + validacion server-side en Dataverse probada en UAT |
| R-16 | Se usan datos productivos de Dynamics 365 en DEV o UAT para probar el asistente | 3 | 4 | 12 | **ALTO** | Sí | Datos simulados o anonimizados + configuracion por ambiente (diseño) | Checklist de promocion DEV -> UAT -> PROD revisado por el lider tecnico |
| R-17 | Los limites de proteccion de servicio de Dataverse (429) dejan al asistente sin estado del caso en hora punta | 2 | 3 | 6 | MEDIO | Sí | Respetar Retry-After + leer solo las columnas necesarias + cache corta (diseño) | — |
| R-18 | Los estados y campos del CRM simulado no coinciden con el estado y la razon del caso en D365 ni con sus columnas personalizadas | 3 | 2 | 6 | MEDIO | Sí | Mapeo documentado en el SDD + tests de contrato contra UAT (diseño) | — |
| R-19 | La decision del supervisor queda solo en el log del servicio y no en el registro del caso en D365 | 2 | 3 | 6 | MEDIO | Sí | Registrar la solicitud y la decision con trace_id en Dataverse, con auditoria habilitada (diseño) | — |
| R-20 | Se construye a medida una capacidad que Dynamics 365 Customer Service ya ofrece con Copilot para agentes | 3 | 2 | 6 | MEDIO | Sí | Comparacion estandar vs. a medida en el Blueprint, verificando la oferta y el licenciamiento vigentes (diseño) | — |

## Justificación de cada estimación

- **R-01** (P3 × I4): P3: en la corrida real el modelo afirmo un hecho que no estaba en el CRM (hallazgo H-1). I4: compromete a la empresa frente al cliente
- **R-02** (P2 × I4): P2: la base de conocimiento es interna y curada, no la escriben usuarios. I4: podria cambiar las instrucciones del asistente
- **R-03** (P3 × I3): P3: el ejecutivo pega texto escrito por terceros. I3: el asistente no ejecuta acciones; el dano se limita a una sugerencia alterada
- **R-04** (P3 × I4): P3: los logs de depuracion tienden a guardar todo. I4: incumplimiento de proteccion de datos
- **R-05** (P3 × I4): P3: el caso vencido es comun (CAS-1043). I4: promesa al cliente que la operacion puede no cumplir
- **R-06** (P3 × I4): P3: el prompt ya cambio varias veces en el proyecto. I4: sin trazabilidad no se puede investigar un reclamo
- **R-07** (P3 × I5): P3: el modelo interpreto mal el estado del ajuste en la corrida real (H-1). I5: perdida de dinero y compromiso con el cliente
- **R-08** (P2 × I4): P2: la regla esta en codigo y testeada. I4: pago indebido
- **R-09** (P2 × I3): P2: el CRM no se indexa por diseño. I3: respuesta incorrecta, corregible por el ejecutivo
- **R-10** (P4 × I3): P4: medido en la corrida real (86 % del tiempo en la generacion). I3: el ejecutivo abandona la herramienta, sin dano directo al cliente
- **R-11** (P2 × I3): P2: en el prototipo la aprobacion ocurre en la misma ejecucion. I3: el cliente queda sin respuesta, pero no se paga nada sin aprobar
- **R-21** (P2 × I1): P2: los precios cambian pocas veces al año. I1: solo afecta el reporte de costo
- **R-12** (P3 × I4): P3: error frecuente en integraciones S2S. I4: acceso indebido a datos de clientes
- **R-13** (P3 × I5): P3: en este proyecto la clave de Gemini ya se expuso en un zip compartido. I5: acceso a Dataverse con los permisos del servicio
- **R-14** (P3 × I5): P3: el prototipo ya usa Gemini. I5: incumplimiento contractual o regulatorio
- **R-15** (P3 × I4): P3: el servicio reintenta llamadas ante errores. I4: rompe POL-20 (un ajuste por caso) y puede duplicar el pago
- **R-16** (P3 × I4): P3: tentacion habitual para probar con casos reales. I4: datos de clientes en un ambiente sin controles de produccion
- **R-17** (P2 × I3): P2: una lectura por consulta es un volumen bajo. I3: el ejecutivo consulta el caso directo en D365
- **R-18** (P3 × I2): P3: el prototipo uso estados simplificados. I2: se detecta en UAT antes de produccion
- **R-19** (P2 × I3): P2: el diseño ya contempla registrarla. I3: auditoria incompleta ante un reclamo
- **R-20** (P3 × I2): P3: la oferta estandar evoluciona rapido. I2: sobrecosto de mantenimiento, no un incidente

## Filas al límite (revisar con otra persona)

R-01, R-02, R-03, R-04, R-05, R-06, R-07, R-08, R-09, R-10, R-11, R-21, R-12, R-13, R-14, R-15, R-16, R-17, R-18, R-19, R-20

**Lectura:** con la escala de 1 a 5 y los umbrales 4 / 9 / 15, casi cualquier estimación queda a un punto de cambiar de categoría, así que el indicador es muy sensible. Para priorizar la revisión, empezar por los CRÍTICO en 15 (R-07, R-13 y R-14): bajan a ALTO con un solo punto menos, y esa diferencia decide si se exige un gate de aprobación antes de producción.

## Supuestos

- La tabla de solicitudes de ajuste en Dataverse es una **propuesta de diseño** (tabla personalizada), no un objeto estándar de D365.
- En R-07, para devoluciones (POL-16) se solicita el monto reclamado completo, porque la política solo define el tope. **Validar con el negocio.**
