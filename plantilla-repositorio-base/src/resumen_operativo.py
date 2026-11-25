"""Resumen operativo del servicio RAG: costo, latencia y alertas por consulta.

Lee los logs que ya genera servicio_rag.py (solo biblioteca estandar, sin dependencias):
  - logs/consumo_llm.jsonl  -> tokens, costo y tiempos por etapa de cada consulta
  - logs/servicio_rag.jsonl -> eventos de seguridad y calidad

Uso:
  python src/resumen_operativo.py            # todas las consultas (reales y simuladas)
  python src/resumen_operativo.py --reales   # solo consultas con Gemini real

Termina con codigo 1 si algun umbral de docs/checklist_operativo.md se supera.
"""
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LOGS = RAIZ / "logs"

# Umbrales (ver docs/checklist_operativo.md). Ajustar con datos reales de operacion.
UMBRAL_LATENCIA_P95_MS = 10_000      # el cliente esta en linea; Gate 1 midio 5-13 s
UMBRAL_COSTO_CONSULTA_USD = 0.001    # ~2x el costo real medido (USD 0,00042)
UMBRAL_TASA_SIN_CITAS = 0.10         # mas del 10 % de respuestas sin citas del modelo

EVENTOS_A_VIGILAR = ["consulta_bloqueada", "documentos_descartados",
                     "sin_contexto_confiable", "respuesta_sin_citas_del_modelo"]


def leer_jsonl(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    registros = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            try:
                registros.append(json.loads(linea))
            except json.JSONDecodeError:
                pass  # una linea corrupta no debe impedir el resumen
    return registros


def percentil(valores: list[float], p: float) -> float:
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    indice = min(len(ordenados) - 1, round(p / 100 * (len(ordenados) - 1)))
    return ordenados[indice]


def resumir(consumos: list[dict], eventos: list[dict]) -> dict:
    latencias = [c["tiempo_total_ms"] for c in consumos]
    costos = [c.get("costo_usd") or 0 for c in consumos]
    etapas = Counter()
    for c in consumos:
        for etapa, ms in c.get("tiempos_ms", {}).items():
            etapas[etapa] += ms
    trazas = {c["trace_id"] for c in consumos}
    conteo_eventos = Counter(e["evento"] for e in eventos
                             if e.get("trace_id") in trazas or e["evento"] == "consulta_bloqueada")
    n = len(consumos)
    return {
        "consultas": n,
        "reales": sum(1 for c in consumos if not c.get("simulado")),
        "simuladas": sum(1 for c in consumos if c.get("simulado")),
        "latencia_p50_ms": round(percentil(latencias, 50), 1),
        "latencia_p95_ms": round(percentil(latencias, 95), 1),
        "latencia_max_ms": round(max(latencias, default=0), 1),
        "tiempo_por_etapa_pct": {e: round(100 * ms / sum(etapas.values()), 1)
                                 for e, ms in etapas.most_common()} if etapas else {},
        "costo_total_usd": round(sum(costos), 6),
        "costo_promedio_usd": round(sum(costos) / n, 7) if n else 0,
        "costo_max_usd": round(max(costos, default=0), 7),
        "tokens_entrada_promedio": round(sum(c["tokens"].get("input_tokens", 0) for c in consumos) / n) if n else 0,
        "versiones_de_prompt": dict(Counter(c.get("prompt_huella") for c in consumos)),
        "eventos": {e: conteo_eventos.get(e, 0) for e in EVENTOS_A_VIGILAR},
    }


def alertas(r: dict) -> list[str]:
    salida = []
    if r["latencia_p95_ms"] > UMBRAL_LATENCIA_P95_MS:
        salida.append(f"latencia p95 {r['latencia_p95_ms']} ms > {UMBRAL_LATENCIA_P95_MS} ms")
    if r["costo_max_usd"] > UMBRAL_COSTO_CONSULTA_USD:
        salida.append(f"costo maximo por consulta {r['costo_max_usd']} USD > {UMBRAL_COSTO_CONSULTA_USD}")
    if r["consultas"] and r["eventos"]["respuesta_sin_citas_del_modelo"] / r["consultas"] > UMBRAL_TASA_SIN_CITAS:
        salida.append("mas del 10 % de las respuestas llegaron sin citas del modelo: revisar el prompt (R-01)")
    if r["eventos"]["documentos_descartados"]:
        salida.append("hubo documentos descartados por inyeccion: revisar la base de conocimiento (R-02)")
    return salida


if __name__ == "__main__":
    consumos = leer_jsonl(LOGS / "consumo_llm.jsonl")
    if "--reales" in sys.argv:
        consumos = [c for c in consumos if not c.get("simulado")]
    if not consumos:
        tipo = "reales (con Gemini) " if "--reales" in sys.argv else ""
        sys.exit(f"No hay consultas {tipo}en logs/consumo_llm.jsonl. Corre primero: python src/servicio_rag.py")

    r = resumir(consumos, leer_jsonl(LOGS / "servicio_rag.jsonl"))
    print("=== Resumen operativo ===")
    print(f"Consultas: {r['consultas']} (reales: {r['reales']}, simuladas: {r['simuladas']})")
    print(f"Latencia: p50 {r['latencia_p50_ms']} ms | p95 {r['latencia_p95_ms']} ms | max {r['latencia_max_ms']} ms")
    print("Tiempo por etapa:", ", ".join(f"{e} {p} %" for e, p in r["tiempo_por_etapa_pct"].items()))
    print(f"Costo: total USD {r['costo_total_usd']} | promedio USD {r['costo_promedio_usd']} | max USD {r['costo_max_usd']}")
    print(f"Tokens de entrada promedio: {r['tokens_entrada_promedio']}")
    print("Versiones de prompt usadas:", r["versiones_de_prompt"])
    print("Eventos a vigilar:", r["eventos"])

    print("\n=== Alertas ===")
    lista = alertas(r)
    for a in lista:
        print("ALERTA:", a)
    if lista:
        sys.exit(1)
    print("Sin alertas: dentro de los umbrales de docs/checklist_operativo.md")
