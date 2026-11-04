from unittest.mock import MagicMock

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from src.enrutamiento import (
    construir_paso_clasificacion,
    construir_cadena_con_enrutamiento,
    construir_cadena_queja_segura,
    procesar_mensaje_seguro,
)


# PRUEBA 1:
# Verifica la normalización con strip().lower()

def test_clasificacion_normaliza_antes_de_comparar():

    modelo_falso = MagicMock()

    modelo_falso.return_value = AIMessage(
        content=" Queja \n"
    )

    paso_clasificacion = (
        construir_paso_clasificacion(
            modelo_falso
        )
    )

    resultado = paso_clasificacion.invoke(
        {
            "mensaje":
            "Me cobraron dos veces la misma factura."
        }
    )

    assert resultado == "queja"


# PRUEBA 2:
# Verifica la ruta de queja

def test_enrutamiento_va_a_cadena_queja():

    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "queja"

    cadena_queja_falsa = MagicMock()
    cadena_queja_falsa.return_value = (
        "respuesta de queja"
    )

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_queja=cadena_queja_falsa,
    )

    resultado = cadena.invoke(
        {
            "mensaje":
            "Me cobraron dos veces la misma factura."
        }
    )

    assert cadena_queja_falsa.called
    assert resultado == "respuesta de queja"


# PRUEBA 3:
# Verifica la ruta de sugerencia

def test_enrutamiento_va_a_cadena_sugerencia():

    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "sugerencia"

    cadena_sugerencia_falsa = MagicMock()
    cadena_sugerencia_falsa.return_value = (
        "respuesta de sugerencia"
    )

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_sugerencia=cadena_sugerencia_falsa,
    )

    resultado = cadena.invoke(
        {
            "mensaje":
            "Deberían agregar atención por WhatsApp."
        }
    )

    assert cadena_sugerencia_falsa.called
    assert resultado == "respuesta de sugerencia"


# PRUEBA 4:
# Verifica la ruta de pregunta

def test_enrutamiento_va_a_cadena_pregunta():

    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "pregunta"

    cadena_pregunta_falsa = MagicMock()
    cadena_pregunta_falsa.return_value = (
        "respuesta de pregunta"
    )

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_pregunta=cadena_pregunta_falsa,
    )

    resultado = cadena.invoke(
        {
            "mensaje":
            "¿Cómo puedo consultar el estado de mi caso?"
        }
    )

    assert cadena_pregunta_falsa.called
    assert resultado == "respuesta de pregunta"


# PRUEBA 5:
# Verifica la ruta por defecto

def test_enrutamiento_usa_default_ante_categoria_desconocida():

    clasificacion_falsa = MagicMock()

    clasificacion_falsa.return_value = (
        "categoria_inventada"
    )

    cadena_pregunta_falsa = MagicMock()

    cadena_pregunta_falsa.return_value = (
        "respuesta por defecto"
    )

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_pregunta=cadena_pregunta_falsa,
    )

    resultado = cadena.invoke(
        {
            "mensaje":
            "Este es un mensaje ambiguo."
        }
    )

    assert cadena_pregunta_falsa.called
    assert resultado == "respuesta por defecto"


# PRUEBA 6:
# Verifica el fallback de la cadena de queja

def test_cadena_queja_usa_fallback_ante_fallo_del_modelo():

    def fallar_a_proposito(x):

        raise ConnectionError(
            "Error de conexión simulado"
        )

    cadena_queja_falsa = RunnableLambda(
        fallar_a_proposito
    )

    cadena_queja_segura = (
        construir_cadena_queja_segura(
            cadena_queja_falsa
        )
    )

    resultado = cadena_queja_segura.invoke(
        {
            "mensaje":
            "Esto no funciona."
        }
    )

    assert "equipo" in resultado.lower()


# PRUEBA 7:
# Verifica la protección general con try/except

def test_procesar_mensaje_seguro_no_propaga_excepciones():

    clasificacion_falsa = MagicMock()

    clasificacion_falsa.side_effect = (
        ConnectionError(
            "Error de clasificación simulado"
        )
    )

    cadena_falsa = (
        construir_cadena_con_enrutamiento(
            paso_clasificacion=(
                clasificacion_falsa
            ),
        )
    )

    resultado = procesar_mensaje_seguro(
        cadena_falsa,
        "Mensaje de prueba",
    )

    assert (
        "no pudimos procesar"
        in resultado.lower()
    )