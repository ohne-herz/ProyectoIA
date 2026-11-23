import json
from pathlib import Path

ARCHIVO = Path(__file__).parent / "registros_latencia_costo.jsonl"

with open(ARCHIVO, encoding="utf-8") as f:
    for linea in f:
        r = json.loads(linea)
        tokens_entrada = r["tokens"]["input_tokens"] if r["tokens"] else None
        etapa_mas_lenta = max(r["tiempos_ms"], key=r["tiempos_ms"].get)
        print(f"k={r['k']}  input_tokens={tokens_entrada}  total={r['tiempo_total_ms']} ms  "
              f"mas_lenta={etapa_mas_lenta}  {r['pregunta'][:35]}")
