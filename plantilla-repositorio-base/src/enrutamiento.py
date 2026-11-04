from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableBranch,
    RunnablePassthrough,
    RunnableLambda,
)


# PLANTILLA DE CLASIFICACIÓN

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de un cliente de contact center "
    "en una sola palabra: pregunta, queja o sugerencia. "
    "Responde solamente con esa palabra.\n\n"
    "{mensaje}"
)


# CONSTRUIR PASO DE CLASIFICACIÓN

def construir_paso_clasificacion(modelo):

    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )


# CONSTRUIR RUTA DE PREGUNTA

def construir_cadena_pregunta(modelo):

    return (
        PromptTemplate.from_template(
            "Responde la siguiente pregunta de un cliente de contact "
            "center de forma clara y precisa. "
            "No inventes información que no aparezca en el mensaje.\n\n"
            "{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )


# CONSTRUIR RUTA DE QUEJA

def construir_cadena_queja(modelo):

    return (
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


# CONSTRUIR RUTA DE SUGERENCIA

def construir_cadena_sugerencia(modelo):

    return (
        PromptTemplate.from_template(
            "Agradece la siguiente sugerencia de un cliente y explica "
            "que será evaluada por el equipo responsable. "
            "No prometas que será implementada.\n\n"
            "{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )


# RESPUESTA DE RESPALDO

respuesta_generica = RunnableLambda(
    lambda x: (
        "Gracias por tu mensaje. Un miembro de nuestro "
        "equipo revisará tu caso y te responderá pronto."
    )
)


# PROTEGER LA RUTA DE QUEJA

def construir_cadena_queja_segura(cadena_queja):

    return cadena_queja.with_fallbacks(
        [respuesta_generica]
    )


# CONSTRUIR LA CADENA CON ENRUTAMIENTO

def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_queja=None,
    cadena_sugerencia=None,
    cadena_pregunta=None,
):

    cadena_queja = (
        cadena_queja or RunnablePassthrough()
    )

    cadena_sugerencia = (
        cadena_sugerencia or RunnablePassthrough()
    )

    cadena_pregunta = (
        cadena_pregunta or RunnablePassthrough()
    )

    bifurcacion = RunnableBranch(

        (
            lambda x: x["categoria"] == "queja",
            cadena_queja,
        ),

        (
            lambda x: x["categoria"] == "sugerencia",
            cadena_sugerencia,
        ),

        # Ruta por defecto
        cadena_pregunta,
    )

    return (
        RunnablePassthrough.assign(
            categoria=paso_clasificacion
        )
        | bifurcacion
    )


# PROTECCIÓN GENERAL DE LA CADENA

def procesar_mensaje_seguro(cadena, mensaje):

    try:

        return cadena.invoke(
            {"mensaje": mensaje}
        )

    except Exception as error:

        print(
            f"Error procesando mensaje: {error}"
        )

        return (
            "No pudimos procesar tu mensaje en este "
            "momento. Intenta de nuevo más tarde."
        )


# EJECUCIÓN REAL

if __name__ == "__main__":

    load_dotenv()

    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite"
    )

    paso_clasificacion = (
        construir_paso_clasificacion(modelo)
    )

    cadena_pregunta = (
        construir_cadena_pregunta(modelo)
    )

    cadena_queja = (
        construir_cadena_queja(modelo)
    )

    cadena_sugerencia = (
        construir_cadena_sugerencia(modelo)
    )

    cadena_queja_segura = (
        construir_cadena_queja_segura(
            cadena_queja
        )
    )

    cadena_con_enrutamiento = (
        construir_cadena_con_enrutamiento(
            paso_clasificacion=paso_clasificacion,
            cadena_queja=cadena_queja_segura,
            cadena_sugerencia=cadena_sugerencia,
            cadena_pregunta=cadena_pregunta,
        )
    )

    mensaje_cliente = (
        "Hola, en mi última factura aparece dos veces "
        "el mismo cobro y todavía no tengo una respuesta."
    )

    resultado = procesar_mensaje_seguro(
        cadena_con_enrutamiento,
        mensaje_cliente,
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
