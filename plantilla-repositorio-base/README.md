# Asistente RAG para ejecutivos de contact center (Alejandro Orrego)

Proyecto de la Especialización en Desarrollo con IA Generativa, para el contact center de una empresa de retail / e-commerce. Responde la pregunta del ejecutivo **"¿qué le respondo a este cliente y en qué estado está su caso?"** cruzando dos fuentes (todos los datos son simulados):

| Fuente | Cómo se usa | Por qué |
|---|---|---|
| Políticas de atención (`src/corpus/politicas_atencion.md`) | RAG: índice Chroma persistido, con citas | Cambian poco y deben citarse |
| Estado del caso (`src/corpus/crm_simulado.json`) | Consulta directa en cada pregunta (CRM simulado) | Cambia en cada interacción: indexarlo dejaría datos viejos |
| Reglas de montos y elegibilidad (POL-15, 16, 20, 21) | Calculadas en código (`evaluar_ajuste`) | Un monto de dinero no debe depender de la interpretación del modelo |

**Casos de prueba del CRM:** `CAS-1043` reembolso vencido (escalamiento POL-12) · `CAS-1060` descuento no aplicado con tope (ajuste POL-15 + aprobación POL-20) · `CAS-1072` devolución de dinero (POL-16) · `CAS-1080` caso cerrado (POL-21) · `CAS-1085` ajuste ya generado (POL-20) · `CAS-1090` reembolso dentro de plazo (POL-07).

## Instalación (de cero)

```bash
git clone <url-del-repositorio>
cd plantilla-repositorio-base
python -m venv venv
# Windows: venv\Scripts\activate     macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
# Edita .env y completa GEMINI_API_KEY (sin clave, el servicio corre en modo --simulado)
python verificar_entorno.py
```

## Indexar el corpus y correr una consulta de punta a punta

El índice se crea solo en la primera corrida y se **reutiliza** en las siguientes. Si editas `politicas_atencion.md`, solo se re-embeben las políticas nuevas o modificadas.

```bash
python src/servicio_rag.py                    # Gemini real (usa GEMINI_API_KEY) -> indice_gate2/
python src/servicio_rag.py --simulado         # sin API ni costo               -> indice_gate2_simulado/
python src/servicio_rag.py --pregunta "¿Que le respondo al cliente del caso CAS-1060?"
python src/servicio_rag.py --interactivo      # el supervisor aprueba o rechaza por teclado
python src/servicio_rag.py --proponer-prompt  # despliegue de una nueva versión de prompt con aprobación
```

Salida esperada (resumen): eventos JSON con el mismo `trace_id` (`consulta_recibida` → `crm_consultado` → `documentos_recuperados` → `consumo_llm` → `respuesta_generada`), la respuesta con `Fuentes: [1] politicas_atencion.md (POL-12)…`, la pausa del punto de supervisión humana y `Proceso terminado sin errores.` Hay un ejemplo completo en `docs/corrida_documentada.md`.

## Verificar el Gate 2

```bash
pytest tests/test_gate2.py -v            # 4 criterios no compensables (modo simulado, sin API)
python src/evaluar_corpus.py --simulado  # precisión / exhaustividad sobre el corpus propio
pytest                                   # suite completa (test_orquestacion requiere GEMINI_API_KEY en .env)
```

## Mapa de la entrega (Gate 2)

| Pieza | Dónde está |
|---|---|
| Indexación persistida + actualización incremental (B25) | `src/servicio_rag.py`: `cargar_corpus`, `sincronizar_indice`, `cargar_indice` |
| Recuperación con citación + métricas sobre el corpus propio (B27) | `responder()` (campo `fuentes`) · `src/evaluar_corpus.py` · `docs/evaluacion_recuperacion.md` |
| Costo y latencia (B28) | `logs/consumo_llm.jsonl` (se genera) · corridas reales previas: `src/registros_latencia_costo.jsonl` |
| Decisión de personalización (B30) | `docs/decision_personalizacion.md` |
| Logging estructurado con `trace_id` + registro de consumo (B31) | `evento()` en `src/servicio_rag.py` → `logs/servicio_rag.jsonl` |
| Filtro de inyección sobre `Document` (B31) | `filtrar_documentos_sospechosos()` + patrones de `src/prevencion_prompt_injection.py` |
| Versionado de prompt + supervisión humana con `interrupt()`/`Command` (B32) | `src/gobernanza.py`: aprobación de escalamiento (POL-12), de ajuste económico (POL-20) y de despliegue de prompt · `src/prompts/registro_prompts.json` |
| Banco de prompts con salida estructurada | `src/prompts/banco.py` · se evalúa con `python -m src.consistencia` |
| Matriz de riesgos (método del Bloque 32) | `src/matriz_riesgos.py` (fuente, valida las reglas de la actividad) → `docs/matriz_riesgos.md` (generado con `--markdown`) |
| Costo, latencia y checklist operativo | `docs/checklist_operativo.md` · resumen de costo/latencia/alertas: `python src/resumen_operativo.py` |
| Autoevaluación | `docs/autoevaluacion_gate2.md` |

## Estructura de carpetas

- `src/` : código fuente. `servicio_rag.py` es el punto de entrada del Gate 2; el resto son los ejercicios de cada bloque.
- `src/corpus/` : base de conocimiento y CRM simulado.
- `docs/` : decisiones de arquitectura, matriz de riesgos, evaluación y evidencia de corridas.
- `tests/` : pruebas (`test_gate2.py` cubre los criterios no compensables).
- `indice_gate2*/` y `logs/` : se generan al correr; están en `.gitignore`.

## Reglas que se mantienen durante todo el programa

- Ningún secreto va en el código ni en el repositorio: solo en `.env` (excluido en `.gitignore`).
- Los logs nunca guardan el texto de preguntas, documentos ni respuestas: solo largos, conteos, ids y huellas SHA-256.
- Cada proyecto tiene su propio entorno virtual.

## Registro del ensayo de instalación limpia

**Gate 1 (23/10/2026).** Encontrado: el README no tenía el link del repositorio. Corregido: se agregó el link. Resultado: el repositorio se clonó de forma satisfactoria.

**Gate 2.** Encontrado: el `requirements.txt` de la raíz estaba vacío (el freeze estaba en `src/`), `.env.example` usaba `API_KEY` en vez de `GEMINI_API_KEY` y el README apuntaba al script del Gate 1. Corregido: dependencias directas fijadas en la raíz, `.env.example` actualizado y README con indexación y consulta de punta a punta. Resultado: completar tras clonar en una carpeta nueva y ejecutar los pasos de arriba.
