from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate


def cadena_tres_pasos(modelo):

    # PASO 1

    plantilla_analisis = PromptTemplate.from_template(
        "Analiza el mensaje de un cliente de un contact center "
        "y devuelve 3 puntos: la categoría del caso, lo que necesita el "
        "cliente y los datos importantes mencionados. "
        "No inventes información.\n\n"
        "{consulta}"
    )


    # PASO 2

    plantilla_recomendacion = PromptTemplate.from_template(
        "A partir del siguiente análisis de la consulta de un cliente, "
        "indica qué debería revisar un ejecutivo de atención antes de "
        "responder. Detecta si el sentimiento del cliente es positivo, "
        "neutral o negativo. "
        "No inventes información que no aparezca en el análisis.\n\n"
        "{analisis}"
    )


    # PASO 3

    plantilla_respuesta = PromptTemplate.from_template(
        "Utiliza las siguientes recomendaciones para redactar una "
        "respuesta para el cliente. Usa un tono claro, cordial y "
        "profesional. No inventes información y no agregues una "
        "introducción adicional.\n\n"
        "{recomendacion}"
    )


    # CHAIN COMPLETA

    cadena = (
        plantilla_analisis
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
        | (lambda analisis: {"analisis": analisis})
        | plantilla_recomendacion
        | modelo
        | StrOutputParser()
        | (lambda recomendacion: {"recomendacion": recomendacion})
        | plantilla_respuesta
        | modelo
        | StrOutputParser()
    )

    return cadena


if __name__ == "__main__":

    load_dotenv()

    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite"
    )

    consulta_cliente = (
        "Hola, en mi última factura aparece dos veces el mismo cobro. "
        "Ayer llamé y me indicaron que habían creado un caso para revisar "
        "el problema, pero todavía no sé en qué estado está. "
        "Necesito saber qué está pasando con mi solicitud y cuándo "
        "tendré una respuesta."
    )

    cadena = cadena_tres_pasos(modelo)

    respuesta = cadena.invoke(
        {"consulta": consulta_cliente}
    )

    print(respuesta)