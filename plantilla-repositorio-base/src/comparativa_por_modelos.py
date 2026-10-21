# Para interactuar con el sistema operativo  porque necesitamos ir a obtener env.
import os
#sirve para medir el tiempo de ejecución de la función
import time
# Sirve para hacer las peticiones
import requests
# Sirve para leer el archivo .env y obtener las variables de entorno
from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env
MODELO = "gemini-3.6-flash"  # Modelo actual (la comparación lo va cambiando)
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI-API-KEY")  # Obtiene la clave de la variable de entorno

# [NUEVO] Modelos a comparar con su precio en USD por token (precio por 1M / 1.000.000)
# Fuente: https://ai.google.dev/gemini-api/docs/pricing (tier pagado, consultado oct-2026)
# OJO: 3.6-flash y 3.8-flash duplican su precio desde el 1-ene-2027
PRECIOS = {
    "gemini-3.1-flash-lite": {"entrada": 0.25 / 1_000_000, "salida": 1.50 / 1_000_000},
    "gemini-3.6-flash":      {"entrada": 0.75 / 1_000_000, "salida": 3.75 / 1_000_000},
    "gemini-3.8-flash":      {"entrada": 0.75 / 1_000_000, "salida": 3.75 / 1_000_000},
}

#Funcion para crear la solicitud
def armar_peticion(pregunta):
    if pregunta == "": # if not pregunta --- if pregunta empty
        raise ValueError("La pregunta no puede estar vacía")

    url = f"{URL_BASE}{MODELO}:generateContent?key={API_KEY}"
    body = {
     	"contents": [
         	{
                 "parts": [
                     {
                         "text": pregunta
                     }
                     ]
            }
     	]
     }
    return url, body

#Funcion para enviar la peticion
def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body, timeout=30)  # Se establece un tiempo de espera de 30 segundos
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No se pudo conectar con el servicio")
    except requests.exceptions.Timeout:
        raise RuntimeError("La solicitud ha excedido el tiempo de espera")

    if respuesta.status_code != 200:
        raise RuntimeError(f"Error en la petición. Status Code: {respuesta.status_code}")

    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta no llegó en el formato esperado")

#Retornar la informacion
def extraer_texto(datos):
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La estructura de la respuesta no es la esperada")

def obtener_dato_de_prueba(pregunta):

    url, body = armar_peticion(pregunta) #Obtiene url y body
    #Contador de latencia
    inicio = time.perf_counter() #Inicia el contador de tiempo

    datos = enviar_peticion(url, body) #Envia la peticion y obtiene la respuesta
    #Contador de latencia
    fin = time.perf_counter() #Finaliza el contador de tiempo
    latencia = fin - inicio #Calcula la latencia
    print(f"Latencia: {latencia:.2f} segundos") #Imprime la latencia

    # [CAMBIO] El precio ahora depende del modelo que se está probando
    costo = calcular_costo(datos, PRECIOS[MODELO]["entrada"], PRECIOS[MODELO]["salida"]) #Calcula el costo de la peticion
    print(f"Costo de la petición: ${costo:.6f} USD") #Imprime el costo de la peticion
    return extraer_texto(datos) #Extrae el texto de la respuesta

#def calcular_costo(datos: dict,precio_entrada: float,precio_salida: float) -> float:
def calcular_costo(datos,precio_entrada,precio_salida):
    #Datos porque tiene todo lo que se necesita para calcular el costo (tokens, modelo, etc)
    #datos = {dict..... "usageMetadata"}
    uso = datos["usageMetadata"]
    '''
    uso = {
        "promptTokenCount": 8,
        "candidatesTokenCount": 14,
        "totalTokenCount": 355,
        "promptTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 8
            }
        ],
        "thoughtsTokenCount": 333,
        "serviceTier": "standard"
    }
    '''
    tokens_entrada = uso["promptTokenCount"]
    tokens_salida = uso["candidatesTokenCount"]
    # [CAMBIO] Si el modelo no razona (ej. flash-lite), este campo no viene: se asume 0
    tokens_razonamiento = uso.get("thoughtsTokenCount", 0)
    try:
        costo = (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida)
        return costo
    except KeyError:
        raise RuntimeError("La estructura de la respuesta no es la esperada")


# Ejecuta N veces la MISMA petición e imprime latencia, costo y respuesta
def calcular_latencia(pregunta, repeticiones=4):
    for i in range(1, repeticiones + 1):
        print("=" * 60)
        print(f"Ejecución {i} de {repeticiones} - Modelo: {MODELO}")
        print("=" * 60)
        try:
            respuesta = obtener_dato_de_prueba(pregunta)  # Imprime latencia y costo
            print(f"Respuesta:\n{respuesta}\n")
        except (ValueError, RuntimeError, KeyError) as error:
            # Si una ejecución falla, se informa y se continúa con la siguiente
            print(f"La ejecución {i} falló: {error}\n")


# Repite la rutina de 4 ejecuciones para cada modelo de la lista
def comparar_modelos(pregunta, modelos, repeticiones=4):
    global MODELO  # Permite cambiar el modelo que usa armar_peticion
    for modelo in modelos:
        MODELO = modelo
        print("\n" + "#" * 60)
        print(f"#  MODELO: {MODELO}")
        print("#" * 60 + "\n")
        calcular_latencia(pregunta, repeticiones)


prompt = """Eres un asistente para ejecutivos de un contact center. El ejecutivo tiene al cliente en línea.
Responde SOLO con la información entregada. Si falta un dato, dilo explícitamente.

[POLÍTICAS DE ATENCIÓN - Base de conocimiento]
- POL-07 Reembolsos: un reembolso aprobado se abona en un plazo máximo de 10 días hábiles.
- POL-12 Escalamiento: si un caso supera el plazo comprometido, el ejecutivo debe escalarlo a Supervisión y ofrecer al cliente una nueva fecha de contacto dentro de 48 horas.

[ESTADO DEL CLIENTE - CRM]
Cliente: María González (RUT 12.345.678-9)
- Caso CAS-1043 | Tipo: Reembolso | Estado: Aprobado | Fecha aprobación: hace 13 días hábiles
- Caso CAS-1051 | Tipo: Cambio de dirección | Estado: Cerrado

[PREGUNTA DEL CLIENTE]
"Me aprobaron un reembolso hace casi tres semanas y todavía no me llega la plata. ¿Qué pasa?"

Entrega:
1. Estado del caso relevante (1 línea).
2. Qué le respondo al cliente (texto listo para decir, máximo 3 frases).
3. Acción que debe hacer el ejecutivo, citando la política aplicada."""

# Modelos
comparar_modelos(prompt, ["gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3.6-flash"])