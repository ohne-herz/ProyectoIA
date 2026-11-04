from src.cadena_tres_pasos_contact_center import cadena_tres_pasos
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage


def test_cadena_conecta_los_tres_pasos():

    modelo_falso = MagicMock()

    modelo_falso.side_effect = [
        AIMessage(
            content=(
                "Categoría: facturación\n"
                "Necesidad: conocer el estado del caso\n"
                "Datos: cobro duplicado"
            )
        ),
        AIMessage(
            content=(
                "Revisar el estado del caso. "
                "Sentimiento negativo."
            )
        ),
        AIMessage(
            content=(
                "Lamentamos el inconveniente con su factura. "
                "Revisaremos el estado de su caso."
            )
        ),
    ]

    cadena = cadena_tres_pasos(modelo_falso)

    resultado = cadena.invoke(
        {
            "consulta": (
                "Hola, en mi última factura aparece "
                "dos veces el mismo cobro."
            )
        }
    )

    assert modelo_falso.call_count == 3
    assert "Lamentamos" in resultado