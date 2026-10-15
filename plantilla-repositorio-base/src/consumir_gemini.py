# Para interactuar con el sistema operativo  porque necesitamos ir a obtener env.
import os
# Sirve para hacer las peticiones 
import requests
# Sirve para leer el archivo .env y obtener las variables de entorno
from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env
def obtener_dato_de_prueba(pregunta):
    api_key = os.getenv("GEMINI-API-KEY")  # Obtiene la clave de la variable de entorno

    modelo = "gemini-flash-latest"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    
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
    try:
        respuesta = requests.post(url, json=body)
        #print(respuesta)
        datos = respuesta.json()
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        #print(f"Error: {e}")
        return f"Error al obtener el dato {e} : {respuesta}"

print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))
