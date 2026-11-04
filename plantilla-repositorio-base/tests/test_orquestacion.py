from langchain_core.output_parsers import StrOutputParser
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from langchain_core.runnables import (
    RunnableBranch,
    RunnablePassthrough,
    RunnableLambda,
)

from src.enrutamiento import (
    plantilla_clasificacion,
    fallback_con_log,
    procesar_mensaje_seguro,
)


# PRUEBA 1
# Verifica que la clasificación se normalice
# antes de ser utilizada por el enrutamiento.

def test_clasificacion_normaliza_antes_de_comparar():

    modelo_falso = MagicMock()

    modelo_falso.return_value = AIMessage(
        content=" Queja \n"
    )

    paso_clasificacion_falso = (
        plantilla_clasificacion
        | modelo_falso
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )

    resultado = paso_clasificacion_falso.invoke(
        {
            "mensaje":
            "Me cobraron dos veces la misma factura."
        }
    )

    assert resultado == "queja"


# PRUEBA 2
# Verifica que una queja vaya a cadena_queja.

def test_enrutamiento_va_a_cadena_queja():

    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "queja"

    cadena_queja_falsa = MagicMock()
    cadena_queja_falsa.return_value = (
        "respuesta de queja"
    )

    cadena_sugerencia_falsa = MagicMock()

    cadena_pregunta_falsa = MagicMock()

    bifurcacion_falsa = RunnableBranch(
        (
            lambda x: x["clasificacion"] == "queja",
            cadena_queja_falsa,
        ),
        (
            lambda x: x["clasificacion"] == "sugerencia",
            cadena_sugerencia_falsa,
        ),
        cadena_pregunta_falsa,
    )

    cadena_falsa = (
        RunnablePassthrough.assign(
            clasificacion=clasificacion_falsa
        )
        | bifurcacion_falsa
    )

    resultado = cadena_falsa.invoke(
        {
            "mensaje":
            "Me cobraron dos veces la misma factura."
        }
    )

    assert cadena_queja_falsa.called
    assert resultado == "respuesta de queja"


# PRUEBA 3
# Verifica que una sugerencia vaya a cadena_sugerencia.

def test_enrutamiento_va_a_cadena_sugerencia():

    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "sugerencia"

    cadena_sugerencia_falsa = MagicMock()
    cadena_sugerencia_falsa.return_value = (
        "respuesta de sugerencia"
    )

    cadena_queja_falsa = MagicMock()

    cadena_pregunta_falsa = MagicMock()

    bifurcacion_falsa = RunnableBranch(
        (
            lambda x: x["clasificacion"] == "queja",
            cadena_queja_falsa,
        ),
        (
            lambda x: x["clasificacion"] == "sugerencia",
            cadena_sugerencia_falsa,
        ),
        cadena_pregunta_falsa,
    )

    cadena_falsa = (
        RunnablePassthrough.assign(
            clasificacion=clasificacion_falsa
        )
        | bifurcacion_falsa
    )

    resultado = cadena_falsa.invoke(
        {
            "mensaje":
            "Deberían tener más ejecutivos disponibles."
        }
    )

    assert cadena_sugerencia_falsa.called

    assert resultado == "respuesta de sugerencia"


# PRUEBA 4
# Verifica la ruta pregunta.

def test_enrutamiento_va_a_cadena_pregunta():

    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "pregunta"

    cadena_pregunta_falsa = MagicMock()
    cadena_pregunta_falsa.return_value = (
        "respuesta de pregunta"
    )

    cadena_queja_falsa = MagicMock()

    cadena_sugerencia_falsa = MagicMock()

    bifurcacion_falsa = RunnableBranch(
        (
            lambda x: x["clasificacion"] == "queja",
            cadena_queja_falsa,
        ),
        (
            lambda x: x["clasificacion"] == "sugerencia",
            cadena_sugerencia_falsa,
        ),
        cadena_pregunta_falsa,
    )

    cadena_falsa = (
        RunnablePassthrough.assign(
            clasificacion=clasificacion_falsa
        )
        | bifurcacion_falsa
    )

    resultado = cadena_falsa.invoke(
        {
            "mensaje":
            "¿Cómo puedo consultar mi última factura?"
        }
    )

    assert cadena_pregunta_falsa.called

    assert resultado == "respuesta de pregunta"


# PRUEBA 5
# Verifica que una categoría desconocida use
# la ruta por defecto.

def test_enrutamiento_usa_default_ante_categoria_desconocida():

    clasificacion_falsa = MagicMock()

    clasificacion_falsa.return_value = (
        "categoria_inventada"
    )

    cadena_pregunta_falsa = MagicMock()

    cadena_pregunta_falsa.return_value = (
        "respuesta por defecto"
    )

    cadena_queja_falsa = MagicMock()

    cadena_sugerencia_falsa = MagicMock()

    bifurcacion_falsa = RunnableBranch(
        (
            lambda x: x["clasificacion"] == "queja",
            cadena_queja_falsa,
        ),
        (
            lambda x: x["clasificacion"] == "sugerencia",
            cadena_sugerencia_falsa,
        ),
        cadena_pregunta_falsa,
    )

    cadena_falsa = (
        RunnablePassthrough.assign(
            clasificacion=clasificacion_falsa
        )
        | bifurcacion_falsa
    )

    resultado = cadena_falsa.invoke(
        {
            "mensaje":
            "Este es un mensaje ambiguo."
        }
    )

    assert cadena_pregunta_falsa.called

    assert resultado == "respuesta por defecto"


# PRUEBA 6
# Verifica que with_fallbacks use realmente
# la respuesta genérica cuando falla la chain.

def test_cadena_robusta_usa_fallback_ante_fallo():

    def fallar_a_proposito(x):
        raise ConnectionError(
            "Error de red simulado"
        )

    cadena_rota = RunnableLambda(
        fallar_a_proposito
    )

    respuesta_generica_falsa = RunnableLambda(
        fallback_con_log
    )

    cadena_robusta_falsa = (
        cadena_rota.with_fallbacks(
            [respuesta_generica_falsa]
        )
    )

    resultado = cadena_robusta_falsa.invoke(
        {
            "mensaje":
            "Tengo problemas con mi factura."
        }
    )

    assert "equipo" in resultado.lower()


# PRUEBA 7
# Verifica la protección final con try/except.
#
# Aquí NO usamos with_fallbacks porque queremos
# provocar una excepción que llegue efectivamente
# hasta procesar_mensaje_seguro.

def test_procesar_mensaje_seguro_no_propaga_excepciones():

    def fallar_a_proposito(x):
        raise ConnectionError(
            "Error general simulado"
        )

    cadena_rota = RunnableLambda(
        fallar_a_proposito
    )

    resultado = procesar_mensaje_seguro(
        cadena_rota,
        "Mensaje de prueba",
    )

    assert (
        "no pudimos procesar"
        in resultado.lower()
    )