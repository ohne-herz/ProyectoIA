"""Bloque 27 sobre el corpus propio: precisión, exhaustividad y F1 de la recuperación.

Los ids de los chunks son estables (politicas_atencion.md::POL-xx), así que los
ids_relevantes de cada caso no cambian al reindexar.

Uso:
  python src/evaluar_corpus.py --simulado     # embeddings léxicos simulados
  python src/evaluar_corpus.py                # embeddings reales de Gemini (gasta tokens)
Escribe docs/evaluacion_recuperacion.json y docs/evaluacion_recuperacion.md
"""
import argparse
import json
from datetime import date
from pathlib import Path

from evaluador_rag import evaluar_recuperacion
from servicio_rag import RAIZ, cargar_indice, detectar_modo

F = "politicas_atencion.md::"
CASOS = [
    {"pregunta": "¿En cuántos días hábiles se abona un reembolso aprobado?", "ids_relevantes": {F + "POL-07"}},
    {"pregunta": "El reembolso aprobado lleva más días que el plazo, ¿qué hago?", "ids_relevantes": {F + "POL-07", F + "POL-12"}},
    {"pregunta": "¿Cuándo debo escalar un caso a Supervisión?", "ids_relevantes": {F + "POL-12"}},
    {"pregunta": "Me cobraron el precio normal de un producto que estaba en oferta", "ids_relevantes": {F + "POL-15"}},
    {"pregunta": "¿Cómo se calcula el ajuste por un descuento promocional no aplicado?", "ids_relevantes": {F + "POL-15"}},
    {"pregunta": "Devolví el producto y quiero que me devuelvan el dinero", "ids_relevantes": {F + "POL-16"}},
    {"pregunta": "¿Puedo confirmarle al cliente el ajuste antes de que lo apruebe el supervisor?", "ids_relevantes": {F + "POL-20"}},
    {"pregunta": "¿Se puede generar un segundo ajuste económico en el mismo caso?", "ids_relevantes": {F + "POL-20"}},
    {"pregunta": "El cliente insiste en un ajuste sobre un caso que ya está cerrado", "ids_relevantes": {F + "POL-21"}},
    {"pregunta": "¿Qué horario tiene la sucursal de Concepción?", "ids_relevantes": set()},  # sin respuesta en el corpus
]


def promedio(valores):
    valores = [v for v in valores if v is not None]
    return round(sum(valores) / len(valores), 3) if valores else None


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--simulado", action="store_true")
    args = p.parse_args(argv)
    modo = detectar_modo(args.simulado)
    vectorstore, _, _ = cargar_indice(modo)

    resumen = {"fecha": str(date.today()), "modo": modo, "n_casos": len(CASOS), "por_k": {}}
    for k in (1, 3):
        resultados = evaluar_recuperacion(vectorstore.as_retriever(search_kwargs={"k": k}), CASOS, k)
        con_respuesta = [r for r, c in zip(resultados, CASOS) if c["ids_relevantes"]]
        resumen["por_k"][k] = {
            "precision": promedio(r["precision"] for r in con_respuesta),
            "recall": promedio(r["recall"] for r in con_respuesta),
            "f1": promedio(r["f1"] for r in con_respuesta),
            "detalle": [{"pregunta": r["pregunta"],
                         "recuperados": [i.split("::")[-1] for i in r["ids_recuperados"]],
                         "precision": round(r["precision"], 2),
                         "recall": None if r["recall"] is None else round(r["recall"], 2)}
                        for r in resultados],
        }
        print(f"k={k} | precision={resumen['por_k'][k]['precision']} "
              f"recall={resumen['por_k'][k]['recall']} f1={resumen['por_k'][k]['f1']}")

    docs = RAIZ / "docs"
    (docs / "evaluacion_recuperacion.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")

    filas = "\n".join(f"| {k} | {v['precision']} | {v['recall']} | {v['f1']} |" for k, v in resumen["por_k"].items())
    detalle = "\n".join(
        f"| {d['pregunta']} | {', '.join(d['recuperados'])} | {d['precision']} | {d['recall']} |"
        for d in resumen["por_k"][3]["detalle"])
    aviso = ("\n> **Corrida SIMULADA**: embeddings léxicos deterministas (sin API). Recuperan por "
             "coincidencia de términos, no por significado. Repetir con `python src/evaluar_corpus.py` "
             "(embeddings Gemini) y reemplazar esta tabla.\n" if modo == "simulado" else "")
    (docs / "evaluacion_recuperacion.md").write_text(f"""# Evaluación de recuperación sobre el corpus propio (Bloque 27)

Fecha: {resumen['fecha']} · Modo: **{modo}** · Corpus: `src/corpus/politicas_atencion.md` (6 políticas, 1 chunk por política) · Casos: {len(CASOS)} (9 con respuesta, 1 sin respuesta en el corpus)
{aviso}
## Promedios (solo casos con respuesta)

| k | Precisión | Exhaustividad | F1 |
|---|---|---|---|
{filas}

## Detalle con k=3

| Pregunta | Recuperados | Precisión | Exhaustividad |
|---|---|---|---|
{detalle}

## Lectura

- Con k=3 la precisión queda acotada por diseño: la mayoría de las preguntas tiene 1 política relevante, así que el máximo posible es 0,33. La métrica que importa para el ejecutivo es la **exhaustividad** (que la política correcta llegue al contexto).
- El caso sin respuesta (horario de sucursal) igual recupera 3 políticas: el retriever siempre devuelve k documentos. La protección es el prompt ("si falta un dato, dilo") y no comprometer información fuera del contexto.
- Los casos con exhaustividad menor a 1 se ven en el detalle. En el servicio, la búsqueda se enriquece con el tipo de caso y la política que entrega el CRM (por ejemplo, POL-12 cuando el plazo está vencido), lo que compensa parte de estas pérdidas; esta evaluación mide el retriever sin ese refuerzo.
- Decisión: mantener k=3 en el servicio, porque prioriza exhaustividad y el costo de tokens extra es bajo (ver `logs/consumo_llm.jsonl`).
""", encoding="utf-8")
    print("Resultados en docs/evaluacion_recuperacion.md")


if __name__ == "__main__":
    main()
