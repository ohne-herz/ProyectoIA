from dotenv import load_dotenv
import os
from langchain_core.output_parsers import StrOutputParser #Parsea respuesta y transforma en solo texto
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate #Prompt Dinamico
from langchain_core.prompts import ChatPromptTemplate #Plantilla que incluye rol del sistema e instrucción

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
#respuesta = modelo.invoke("¿Que es un token?")
#print(respuesta.content)

#f-strings
plantilla = PromptTemplate.from_template(
    "Explica el concepto de {tema} en un parrafo, para alguien que recien comienza en {area}")

#prompt = plantilla.invoke({"tema": "tokenización", "area": "procesamiento de texto"})
#print(prompt.text)

cadena_simple= plantilla | modelo | StrOutputParser()
respuesta = cadena_simple.invoke({"tema": "embeddings", "area": "búsqueda semántica"})
print(respuesta)

plantilla_conrol = ChatPromptTemplate.from_messages([
    ("system", "Eres un experto en el área correspondiente, vas a responder siempre con texto simple para el usuario."),
    ("human", "Explica el concepto de {tema} en un parrafo, para alguien que recien comienza en {area}")
])