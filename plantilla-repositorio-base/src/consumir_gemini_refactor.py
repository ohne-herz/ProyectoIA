# Para interactuar con el sistema operativo  porque necesitamos ir a obtener env.
import os
#sirve para medir el tiempo de ejecución de la función
import time
# Sirve para hacer las peticiones 
import requests
# Sirve para leer el archivo .env y obtener las variables de entorno
from dotenv import load_dotenv
import json 
import re

load_dotenv()  # Carga las variables de entorno desde el archivo .env
MODELO = "gemini-3.6-flash"
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI-API-KEY")  # Obtiene la clave de la variable de entorno

#Funcion para crear la solicitud
def armar_peticion(modelo,pregunta,system_instruction,response_schema=None):
    if pregunta == "": # if not pregunta --- if pregunta empty
        raise ValueError("La pregunta no puede estar vacía")
    
    url = f"{URL_BASE}{modelo}:generateContent?key={API_KEY}"
    body = {
        "systemInstruction":{
                "parts":[{"text":system_instruction}]
            },
     	"contents": [
         	{"parts": [{"text": pregunta}]}
     	]
    }
    if response_schema is not None:
        body["generationConfig"] = {
        	"responseMimeType": "application/json",
        	"responseSchema": response_schema
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

    if respuesta.status_code in(401,403):
        raise ValueError("Credenciales inválidas o sin permisos. Revisa tu GEMINI-API-KEY")

    if respuesta.status_code>=500:
        raise TimeoutError("El proveedor no pudo procesar la petición. Hay que esperar y reintentar")

    if respuesta.status_code == 429:
        segundos = respuesta.headers.get("Retry-After")
        mensaje = f"Limite excedido. Reintentar en {segundos}" if segundos else "Límite excedido."
        raise TimeoutError(mensaje)
        
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
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "categoria": {"type": "STRING"},
            "prioridad": {"type": "NUMBER"}
        },
        "required": ["categoria","prioridad"]
    }
    system_instruction = "Eres un asistente amigable y respondes en máximo 2 palabras."
    url, body = armar_peticion("gemini-3.6-flash",pregunta,system_instruction,response_schema) #Obtiene url y body
    #Contador de latencia
    inicio = time.perf_counter() #Inicia el contador de tiempo

    datos = enviar_peticion(url, body) #Envia la peticion y obtiene la respuesta
    #Contador de latencia
    fin = time.perf_counter() #Finaliza el contador de tiempo
    latencia = fin - inicio #Calcula la latencia
    print(f"Latencia: {latencia:.2f} segundos") #Imprime la latencia

    costo = calcular_costo(datos, 0.00000075,0.00000375) #Calcula el costo de la peticion
    print(f"Costo de la petición: ${costo:.6f} USD") #Imprime el costo de la peticion
    texto = extraer_texto(datos) #Extrae el texto de la respuesta
    datos_formateados = parsear_respuesta_json(texto,["categoria","prioridad"])
    return datos_formateados

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
    tokens_razonamiento = uso["thoughtsTokenCount"]
    costo = (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida)
    return costo

def parsear_respuesta_json(texto, claves_requeridas=None):
    """
    Limpia y parsea una respuesta JSON de un modelo.

    claves_requeridas: lista opcional, ej. ["categoria", "prioridad"]
    """
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)

    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError as e:
        raise ValueError("La respuesta del modelo no es JSON válido.") from e

    if claves_requeridas:
        faltantes = [clave for clave in claves_requeridas if clave not in datos]
        if faltantes:
            raise ValueError(f"Faltan claves en la respuesta: {faltantes}")

    return datos
'''
try:
   
    print(obtener_dato_de_prueba("""Eres un asistente para ejecutivos de un contact center. El ejecutivo tiene al cliente en línea.
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
3. Acción que debe hacer el ejecutivo, citando la política aplicada."""))

except (ValueError, RuntimeError) as error:
    print(f"No se pudo completar la operación: {error}")
    '''

