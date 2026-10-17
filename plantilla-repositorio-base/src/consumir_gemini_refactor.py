# Para interactuar con el sistema operativo  porque necesitamos ir a obtener env.
import os
# Sirve para hacer las peticiones 
import requests
# Sirve para leer el archivo .env y obtener las variables de entorno
from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env
MODELO = "gemini-flash-latest"
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI-API-KEY")  # Obtiene la clave de la variable de entorno

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
    except requests.excepcions.ConnectionError:
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
    datos = enviar_peticion(url, body) #Envia la peticion y obtiene la respuesta
    return extraer_texto(datos) #Extrae el texto de la respuesta

try:
    print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))
except (ValueError, RuntimeError) as error:
    print(f"No se pudo completar la operación: {error}")