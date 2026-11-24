import hashlib
import time #Latencia
import json #Registrar en jsonl la info
from contextlib import contextmanager #administrador de contexto: ejecuta antes, durante y después de hacerse una acción
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI #Modelo para instanciar gemini

from rag_indexer import cargar_vectorstore, formatear_contexto 

load_dotenv()

# Rutas ancladas a src/: el script funciona igual si se ejecuta desde la raíz o desde src/
CARPETA_SRC = Path(__file__).parent
ARCHIVO_REGISTROS = CARPETA_SRC / "registros_latencia_costo.jsonl"  # nombre que pide la entrega
MODELO = "gemini-3.5-flash-lite"

#Plantilla que me obligue a usar SOLO el contexto recuperado y también a citar [1], [2]
PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no \
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:

""" #contexto = el resultado de la búsqueda de vs, formateado con formatear_contexto, pregunta = la consulta del usuario final

def aprox_tokens(texto: str) -> int:
    return len(texto) // 4

#Latencia
@contextmanager #Administrador de contexto
def medir(tiempos: dict, etapa: str):
    """
    Cronometrar bloques de código (sin "ensuciar" la lógica)
    Uso:
        with medir(tiempos, "nombre_etapa"): #ej: "embedding_y_consulta"
            #Codigo que quiero medir
            retriever = vs.as_retriever....
            chunks = ....
    """
    #1.- ANTES del bloque with
    inicio = time.perf_counter() #empiezo a contar el tiempo

    #2.- PAUSA (yield): le cede el control al código que puse en el bloque de código dentro del with
    yield

    #3.- DESPUÉS del bloque with: cuando el código termina, vuelvo aquí y detengo el tiempo
    tiempos[etapa] = time.perf_counter() - inicio #Tiempo total en el que se ejecutó esa etapa/tarea

#Calculo de costos (tokens_entrada, tokens_salida, tarifa_entrada, tarifa_salida)
def calcular_costo(tokens_entrada: int, tokens_salida: int, tarifa_entrada_x1M: float = .3, tarifa_salida_x1M: float = 2.5) -> float:
    """
    Calcula el costo monetario real de la consulta con contexto de mi RAG
    """
    costo_entrada = (tokens_entrada / 1000000) * tarifa_entrada_x1M
    costo_salida = (tokens_salida / 1000000) * tarifa_salida_x1M

    return round(costo_entrada + costo_salida, 6)

#Registrar consulta
def registrar_consulta(vectorstore, pregunta: str, k: int = 3) -> dict:
    """
    Ejecutar de punta a punta el proceso completo con RAG. (Recuperación + Prompt con contexto + Generación con Gemini),
    Medir la latencia de cada etapa y extraer los tokens consumidos (reales) y el costo de esto
    """
    tiempos = {} #Es donde voy a almacenar la latencia de cada etapa

    chat_model = ChatGoogleGenerativeAI(model=MODELO)
    
    #Etapa 1: Embed y la busqueda vectorial (Consulta a mi VS) - Acción Local
    with medir(tiempos, "embed_y_busqueda"):
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        chunks = retriever.invoke(pregunta) #busqueda vectorial con Chroma

    #Etapa 2: Armado del prompt (agregando el contexto/chunks formateados) - Acción Local
    with medir(tiempos, "armado_prompt"):
        contexto, citas = formatear_contexto(chunks)
        prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)

    #Etapa 3: Generación de la respuesta con Gemini
    with medir(tiempos, "generacion"):
        respuesta = chat_model.invoke(prompt)
    
    #respuesta tiene usage_metadata -> tokens se gastaron. 
    #respuesta["usage_metadata"]["input_tokens"], respuesta["usage_metadata"]["output_tokens"]
    contenido = respuesta.content
    texto_respuesta = contenido if isinstance(contenido, str) else "".join(
        p.get("text", "") if isinstance(p, dict) else str(p) for p in contenido)
    tokens_reales = dict(respuesta.usage_metadata) if respuesta.usage_metadata else None

    costo_usd = None

    if tokens_reales:
        costo_usd = calcular_costo(
            tokens_entrada = tokens_reales.get("input_tokens", 0),
            tokens_salida = tokens_reales.get("output_tokens", 0), #output_tokens YA INCLUYE tokens de razonamiento
            tarifa_entrada_x1M = .3,
            tarifa_salida_x1M = 2.5
        )
    
    #Factor crecimiento: comparación de cuánto creció el texto de entrada vs la pregunta solita
    factor_crecimiento = round(len(prompt) / len(pregunta), 1)

    #Construir el diccionario con toda la info que obtuvimos
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # Sin contenido crudo (criterio no compensable): solo largo y huella
        "pregunta_len": len(pregunta),
        "pregunta_huella": hashlib.sha256(pregunta.encode("utf-8")).hexdigest()[:12],
        "k": k,
        "modelo": MODELO,
        "respuesta_len": len(texto_respuesta),
        "respuesta_huella": hashlib.sha256(texto_respuesta.encode("utf-8")).hexdigest()[:12],
        "citas_disponibles": citas,
        "tiempos_ms": {etapa: round(seg * 1000, 2) for etapa, seg in tiempos.items()},
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "factor_crecimiento": f"{factor_crecimiento}x",
        "tokens": tokens_reales,
        "costo_estimado_usd": costo_usd  # float o None si la respuesta no trajo usage_metadata
    }

    return registro

def guardar_registro_jsonl(registro: dict, ruta_archivo: Path = ARCHIVO_REGISTROS):
    """
    Guarda cada corrida/registro generado y lo agrega a un json
    """
    with open(ruta_archivo, "a", encoding="utf-8") as f: #agrego al final del archivo
        f.write(json.dumps(registro, ensure_ascii=False)+"\n")
    
    print(f"Registro guardado en {ruta_archivo}")

if __name__ == "__main__":
    vs = cargar_vectorstore(str(CARPETA_SRC / "vectorstore_ejemplo"))

    # Preguntas del conjunto de evaluación (Bloque 27), de distinto largo,
    # todas con respuesta en manual_de_usuario.txt
    PREGUNTAS = [
        "¿Cuántos intentos hace el cliente ante un TimeoutError y cuánto espera entre cada uno?",
        "Cuáles son los errores de credenciales inválidas?",
        "¿Qué pasa si supero el límite de peticiones por minuto?",
        "¿Cuánto cuesta una escritura?",
    ]

    # Prueba 1: al menos 3 preguntas distintas con k=3 (una línea por consulta)
    corridas = [(p, 3) for p in PREGUNTAS]
    # Prueba 2: la misma pregunta con k=6, para comparar input_tokens contra k=3
    corridas.append((PREGUNTAS[0], 6))

    for pregunta, k in corridas:
        registro = registrar_consulta(vs, pregunta, k)
        guardar_registro_jsonl(registro)
        print(f"k={k} | {registro['tiempos_ms']} | tokens={registro['tokens']} | {pregunta[:40]}")
