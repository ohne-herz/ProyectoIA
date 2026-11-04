from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI #Modelo
from langchain_core.prompts import PromptTemplate #Plantilla -> Prompt dinámico
from langchain_core.output_parsers import StrOutputParser #Parsea la respuesta y la transforma en solo textos
from langchain_core.runnables import (RunnableBranch, RunnablePassthrough) #Bifurcaciones/Branches/Ramificaciones

load_dotenv()
modelo = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de soporte en una sola palabra: " \
    "pregunta, queja o sugerencia. Responde solo con esa palabra. \n {mensaje}")

paso_clasificacion = plantilla_clasificacion | modelo | StrOutputParser()

# mensaje_prueba ="Mi teléfono no está funcionando"

# clasificacion = paso_clasificacion.invoke({"mensaje": mensaje_prueba})

# print(clasificacion)

cadena_pregunta = (
    PromptTemplate.from_template("Responde esta pregunta técnica, con presición: \n\n{mensaje}")
    | modelo
    | StrOutputParser()
)

cadena_queja = (
    PromptTemplate.from_template("Responde esta queja con empatía, reconociendo el problema antes de ofrecer una solución: \n\n{mensaje}")
    | modelo
    | StrOutputParser()
)

cadena_sugerencia = (PromptTemplate.from_template("Agradece esta sugerencia en un solo parrafo \n\n{mensaje}")
    | modelo
    | StrOutputParser()
)   

# caminos = RunnableBranch(
#     (condicion_1, rama_1), #if
#     (condicion_2, rama_2), #elif
#     (condicion_3, rama_3), #elif
#     rama_por_defecto
#)
#Cada condicion debe ser una función; suele ser un lambda

bifurcacion = RunnableBranch(
    (lambda x: x["clasificacion"]== "queja", cadena_queja),
    (lambda x: x["clasificacion"]== "sugerencia", cadena_sugerencia),
    cadena_pregunta
)

cadena_con_enrutamiento = (
    #Ejecutar el paso de clasificación, obtener la respuesta como clasificación y tambien conservar el mensaje original
    #RunnablePassthrough(lambda x: {"mensaje": x, "clasificacion": paso_clasificacion.invoke({"mensaje": x})})
    RunnablePassthrough.assign(clasificacion=paso_clasificacion) # {"mensaje": "Deberian de tener mas agentes disponibles", "clasificacion": resultado de paso_clasificacion}
    | bifurcacion
)

resultado = cadena_con_enrutamiento.invoke(
    {"mensaje": "Deberian de tener mas agentes disponibles"}
)
print(resultado)

#Entrada inicial: {"mensaje": "Deberian de tener mas agentes disponibles"}
#RunnablePassthrough -> {"mensaje": "Deberian de tener mas agentes disponibles", "clasificacion": "sugerencia"}
#   1: Pasa elmensaje a paso_clasificacion --> return una palabra (queja, pregunta, sugerencia)
#   2: Fusiona ambos datos
#   3: Return {"mensaje": "Deberian de tener mas agentes disponibles", "clasificacion": "sugerencia"}}
# Pasa el resultado a bifurcacion (runnableBranch)
#       IF¿Clasificación ?== queja? No, pasa a siguiente condición
#       ELIF ¿Clasificación ?== sugerencia? 
#           Si, entra a cadena_sugerencia
#           cadena_sugerencia.invoke({"mensaje": "Deberian de tener mas agentes disponibles", "clasificacion": "sugerencia"})
#           return respuesta final generada.
