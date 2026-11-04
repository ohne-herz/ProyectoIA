from dotenv import load_dotenv
import os
from langchain_core.output_parsers import StrOutputParser #Parsea respuesta y transforma en solo texto
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate #Prompt Dinamico
from langchain_core.prompts import ChatPromptTemplate #Plantilla que incluye rol del sistema e instrucción

load_dotenv()
modelo = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

plantilla_extraccion = PromptTemplate.from_template("Lee el siguiente texto y devuelve solo sus 3 puntos clave, uno por línea, sin desarrollarlos: \n\n {texto}")

paso_extraccion = plantilla_extraccion | modelo | StrOutputParser()

texto_prueba = (
    "Los modelos de lenguaje grandes generan texto "

    "prediciendo un token a la vez, basándose en el "

    "texto que ya generaron antes. Cada token puede "
    
    "ser una palabra completa, parte de una palabra, "

    "o un signo de puntuación. Antes de que el modelo "

    "genere una respuesta, el texto de entrada se "

    "divide en tokens, un proceso llamado tokenización."
)

#puntos = paso_extraccion.invoke(
#    {"texto": texto_prueba}
#)

#print(puntos)

plantilla_simplificacion = PromptTemplate.from_template("Reescribe estos puntos en lenguaje natural, sin jerga técnica para alguien sin conocimientos previos \n\n{puntos}")

paso_simplificacion = plantilla_simplificacion | modelo | StrOutputParser()

#simple = paso_simplificacion.invoke(
#    {"puntos": puntos}
#)
#print(simple)   

plantilla_formato = PromptTemplate.from_template("Convierte este texto en una lista de viñetas markdown de máximo 3 lineas, sin instroducción \n\n{texto_simple}")

paso_formato = plantilla_formato | modelo | StrOutputParser()

# formato = paso_formato.invoke(
#    {"texto_simple": simple}
# )
# print(formato)   


#Sintaxis lambda -> lambda argumentos: expresión
cadena_tres_pasos = (
    plantilla_extraccion 
    | modelo
    | StrOutputParser()
    |(lambda puntos: {"puntos": puntos})
    | plantilla_simplificacion
    | modelo
    | StrOutputParser()
    |(lambda texto_simple: {"texto_simple": texto_simple})
    | plantilla_formato
    | modelo
    | StrOutputParser()
)

respuesta = cadena_tres_pasos.invoke({"texto": texto_prueba})
print(respuesta)