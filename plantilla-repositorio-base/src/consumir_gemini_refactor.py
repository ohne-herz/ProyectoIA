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
    respuesta = requests.post(url, json=body)
    return respuesta.json()
        
#Retornar la informacion
def extraer_texto(datos):
    return datos["candidates"][0]["content"]["parts"][0]["text"]

def obtener_dato_de_prueba(pregunta):
    url, body = armar_peticion(pregunta) #Obtiene url y body
    datos = enviar_peticion(url, body) #Envia la peticion y obtiene la respuesta
    return extraer_texto(datos) #Extrae el texto de la respuesta


print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))
