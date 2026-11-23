# Decisión de personalización: asistente para ejecutivos de contact center

## 1. El problema

Mi asistente ayuda a un ejecutivo de contact center a responderle al cliente. Para eso necesita saber en qué estado está su caso y qué política aplica. El problema es que hoy esa información la escribí a mano dentro del prompt (`contexto_contact_center.txt`). Si cambia una política o el estado de un caso, tengo que editar el texto, porque el modelo no tiene otra forma de enterarse.

## 2. Resultado del método de decisión

Respondí las cinco preguntas con lo que tengo en mi proyecto:

- **informacion_cambia_seguido: True.** El estado de los casos cambia todo el tiempo. Por ejemplo, el caso CAS-1043 lleva 13 días hábiles aprobado y su situación cambia día a día.
- **problema_de_formato_o_tono: False.** En las 4 pruebas que hice al elegir el modelo, las 4 respuestas tuvieron las 3 partes del formato. Pero el criterio pide revisar 20 respuestas y yo solo revisé 4, así que esta respuesta es provisional.
- **dataset_grande_y_de_calidad: False.** Tengo 20 ejemplos en `casos_contact_center.json` y el criterio pide al menos 200.
- **presupuesto_limitado_o_iterar_rapido: True.** Es un proyecto del curso y no tengo presupuesto para pagar entrenamientos.
- **necesita_multiples_variantes: False.** Es un solo contact center, en un solo idioma.

Puntaje: **RAG: 5 puntos, PEFT: 1 punto, Fine-tuning completo: 0 puntos.** No hubo empate: ganó RAG.

## 3. Técnica elegida y por qué

Elegí **RAG**. Lo que le falta a mi asistente no es aprender a responder mejor, sino tener la información actualizada. Con RAG la busca en cada consulta, así que no tengo que reentrenar nada cuando algo cambia.

Como tenía dudas con la pregunta del formato, corrí el método otra vez cambiándola a True. PEFT subió de 1 a 3 puntos, porque esa pregunta le suma 2. Fine-tuning completo subió de 0 a 1, porque le suma 1. RAG se quedó en 5, porque esa pregunta no lo afecta. Igual ganó RAG. Además, con solo 20 ejemplos no me alcanzaría para entrenar un modelo.

## 4. Qué necesitaría para ejecutarla

- **Corpus a indexar:** me falta indexar 1 documento con mis 2 políticas de atención (POL-07 y POL-12). Hoy están escritas en el prompt. Lo que tengo indexado son 20 chunks del manual de la API, que no tienen relación con las políticas.
- **Estado del CRM:** no lo voy a indexar, porque cambia en cada interacción. Lo correcto es consultarlo por API en cada pregunta.
- **Para evaluar:** tengo 20 casos de prueba, pero a ninguno le marqué todavía los `ids_relevantes` que necesito para medir con `evaluador_rag.py`. A 5 minutos por caso, son unas 1,7 horas.
- **Pendiente:** revisar 20 respuestas reales para confirmar la pregunta del formato. Si 3 o más fallan, la cambio a True.
