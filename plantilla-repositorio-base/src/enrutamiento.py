from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableBranch,
    RunnablePassthrough,
    RunnableLambda,
)

import logging


# CONFIGURACIÓN DE LOGGING

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", #2026-11-04 16:40 [WARNING] main: No se pudo procesar x
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="error.log",
    filemode="a", # agrega al final del archivo la nueva linea
    encoding="utf-8",
    force=True
)

logger = logging.getLogger(__name__)


load_dotenv()

modelo = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite"
)


# PLANTILLA DE CLASIFICACIÓN

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de un cliente de contact center "
    "en una sola palabra: pregunta, queja o sugerencia. "
    "Responde solamente con esa palabra.\n\n"
    "{mensaje}"
)


# PASO DE CLASIFICACIÓN

paso_clasificacion = (
    plantilla_clasificacion
    | modelo
    | StrOutputParser()
    | (lambda texto: texto.strip().lower())
)


# RUTA PREGUNTA

cadena_pregunta = (
    PromptTemplate.from_template(
        "Responde la siguiente pregunta de un cliente de contact "
        "center de forma clara y precisa. "
        "No inventes información que no aparezca en el mensaje.\n\n"
        "{mensaje}"
    )
    | modelo
    | StrOutputParser()
)


# RUTA QUEJA

cadena_queja = (
    PromptTemplate.from_template(
        "Responde a la siguiente queja con empatía. "
        "Primero reconoce el problema del cliente y luego explica "
        "qué debería hacerse para revisar su caso. "
        "No inventes información.\n\n"
        "{mensaje}"
    )
    | modelo
    | StrOutputParser()
)


# RUTA SUGERENCIA

cadena_sugerencia = (
    PromptTemplate.from_template(
        "Agradece la siguiente sugerencia de un cliente y explica "
        "que será evaluada por el equipo responsable. "
        "No prometas que será implementada.\n\n"
        "{mensaje}"
    )
    | modelo
    | StrOutputParser()
)


# BIFURCACIÓN

bifurcacion = RunnableBranch(

    (
        lambda x: x["clasificacion"] == "queja",
        cadena_queja
    ),

    (
        lambda x: x["clasificacion"] == "sugerencia",
        cadena_sugerencia
    ),

    # Ruta por defecto
    cadena_pregunta
)


# CADENA CON ENRUTAMIENTO

cadena_con_enrutamiento = (

    RunnablePassthrough.assign(
        clasificacion=paso_clasificacion
    )

    | bifurcacion
)


# RESPUESTA GENÉRICA
# Se utiliza como fallback si falla cadena_con_enrutamiento
def fallback_con_log(x):
    logger.warning("Cadena principal falló. Activando respuesta genericas")
    return "Gracias por tu mensaje. Un miembro de nuestro equipo revisará tu caso y te responderá pronto."

respuesta_generica = RunnableLambda(
    fallback_con_log
)


# CADENA ROBUSTA
# Si falla cualquier parte de cadena_con_enrutamiento,
# ejecuta respuesta_generica.

cadena_robusta = cadena_con_enrutamiento.with_fallbacks(
    [respuesta_generica]
)


# PROTECCIÓN GENERAL

def procesar_mensaje_seguro(cadena, mensaje):

    try:

        return cadena.invoke(
            {"mensaje": mensaje}
        )

    except Exception as error:

        # Registra el error que no pudo resolver el fallback
        logger.error("Error procesando mensaje %s", error)

        return (
            "No pudimos procesar tu mensaje en este "
            "momento. Intenta de nuevo más tarde."
        )


# EJECUCIÓN DIRECTA

if __name__ == "__main__":

    mensaje = (
        "Hola, en mi última factura aparece dos veces "
        "el mismo cobro y todavía no tengo una respuesta."
    )

    print(
        procesar_mensaje_seguro(
            cadena_robusta,
            mensaje
        )
    )


# Entrada inicial:
#
# {
#     "mensaje": "Deberian de tener mas agentes disponibles"
# }
#
#                   |
#                   v
#
# RunnablePassthrough.assign
#
# 1. Pasa el mensaje a paso_clasificacion
#       -> retorna "sugerencia"
#
# 2. Fusiona clasificación y mensaje
#
# 3. Retorna:
#
# {
#     "mensaje": "Deberian de tener mas agentes disponibles",
#     "clasificacion": "sugerencia"
# }
#
#                   |
#                   v
#
# bifurcacion (RunnableBranch)
#
# IF clasificacion == "queja"
#       No
#
# ELIF clasificacion == "sugerencia"
#       Si
#
#       Entra a cadena_sugerencia
#
#       cadena_sugerencia.invoke(
#           {
#               "mensaje":
#               "Deberian de tener mas agentes disponibles",
#
#               "clasificacion":
#               "sugerencia"
#           }
#       )
#
#       Retorna respuesta final generada.
#
#
# MANEJO DE ERRORES:
#
# cadena_con_enrutamiento
#       |
#       | falla
#       v
#
# with_fallbacks
#       |
#       v
#
# respuesta_generica
#       |
#       v
#
# "Gracias por tu mensaje..."
#
#
# Si incluso cadena_robusta no puede entregar
# una respuesta:
#
# procesar_mensaje_seguro
#       |
#       v
#
# except Exception
#       |
#       +----> logger.error(...)
#       |
#       +----> "No pudimos procesar tu mensaje..."