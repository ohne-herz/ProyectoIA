from pathlib import Path
from collections import Counter
from pipeline_limpieza import procesar_texto
from cliente import consultar_modelo
import json


def contar_coincidencias(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> int:
    """Cuenta las coincidencias entre referencia y respuesta."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta
    return sum(interseccion.values())

def calcular_precision_cobertura_f1(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 de dos listas de tokens."""
    coincidencias = contar_coincidencias(
        tokens_referencia, tokens_respuesta
    )

    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    precision = coincidencias / len(tokens_respuesta)
    cobertura = coincidencias / len(tokens_referencia)

    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    resultado = {
        "precision": precision,
        "cobertura": cobertura,
        "f1": f1,
    }

    return resultado

def calcular_metricas(texto_referencia, texto_respuesta):
    tokens_referencia = procesar_texto(texto_referencia)
    tokens_respuesta = procesar_texto(texto_respuesta)
    
    return calcular_precision_cobertura_f1(
        tokens_referencia, tokens_respuesta
    )

# Bloque 16 - Casos de evaluación de Contact Center

BASE = Path(__file__).resolve().parent.parent
with open(
    BASE / "casos_contact_center.json",
    "r",
    encoding="utf-8"
) as archivo:
    casos = json.load(archivo)

with open(
    BASE / "contexto_contact_center.txt",
    "r",
    encoding="utf-8"
) as archivo:
    contexto = archivo.read()

resultados = []

for caso in casos:
    consulta = caso["consulta"]
    referencia = caso["referencia"]

    respuesta = consultar_modelo(
        consulta,
        system_instruction=contexto
    )

    metricas = calcular_metricas(referencia, respuesta)

    resultados.append({
        "consulta": consulta,
        "referencia": referencia,
        "respuesta": respuesta,
        **metricas,
    })
    
resultados = sorted(resultados, key=lambda r: r["f1"])

with open(
    "resultados_metricas.json", "w", encoding="utf-8"
) as archivo:
    json.dump(resultados, archivo, indent=2, ensure_ascii=False)

def resumir_metricas(resultados):
    if not resultados:
        return {
            "precision_promedio": 0,
            "cobertura_promedio": 0,
            "f1_promedio": 0,
        }
    n = len(resultados)
    return {
        "precision_promedio": sum(
            r["precision"] for r in resultados
        ) / n,
        "cobertura_promedio": sum(
            r["cobertura"] for r in resultados
        ) / n,
        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }
    
print("Promedios")
print(resumir_metricas(resultados))
    
# Bloque 17 - Selección de muestra cualitativa

peores_casos = sorted(
    resultados,
    key=lambda r: r["f1"]
)

muestra_para_revisar = (
    peores_casos[:5] + peores_casos[-5:]
)

print("\nMuestra para revisión manual:")

for caso in muestra_para_revisar:
    print(
        caso["consulta"],
        "F1:",
        round(caso["f1"], 3)
    )
    
    
# referencia = procesar_texto(
#     "Python es un lenguaje de programación interpretado."
# )

# texto_respuesta = consultar_modelo("¿Qué es Python?",
#                                    system_instruction="Responde en español con una definición breve, en una sola oración de máximo 15 palabras. Sin listas, ejemplos ni introducciones.")

# respuesta = procesar_texto(texto_respuesta)
# resultado = calcular_precision_cobertura_f1(referencia, respuesta)

# print("Respuesta:", texto_respuesta)
# print("Tokens de referencia:", len(referencia))
# print("Tokens de respuesta:", len(respuesta))
# print(resultado)