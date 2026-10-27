from unittest.mock import patch, Mock
import pytest
from src.consumir_gemini_refactor import enviar_peticion
from cliente import con_reintento
from cliente import consultar_modelo
import cliente

def test_enviar_peticion_credencial_invalida():
    """Verifica que una respuesta 401 (credencial inválida) lance ValueError."""
    respuesta_falsa = Mock(status_code=401)
    #with patch hace la sustitucion de request.post
    with patch("src.consumir_gemini_refactor.requests.post",return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion("https://ejemplo.invalid",{"pregunta":"test"})

def test_enviar_peticion_limite_de_uso():
    """Verifica que una respuesta 429 (límite de uso) lance TimeoutError."""
    respuesta_falsa = Mock(status_code=429)
    with patch("src.consumir_gemini_refactor.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion("https://ejemplo.invalid",{"pregunta": "test"})


def test_enviar_peticion_exito():
    """Verifica que una respuesta 200 devuelva el JSON del cuerpo de la respuesta."""
    respuesta_falsa = Mock(status_code=200)
    respuesta_falsa.json.return_value = {"texto": "respuesta simulada"}

    with patch("src.consumir_gemini_refactor.requests.post", return_value=respuesta_falsa):
        resultado = enviar_peticion("https://ejemplo.invalid",{"pregunta": "test"})

    assert resultado == {"texto":"respuesta simulada"}



def test_con_reintento_agota_intentos():
    """Verifica que, al agotar los intentos, con_reintento propague el TimeoutError."""
    def siempre_falla():
        """Función simulada que siempre lanza TimeoutError."""
        raise TimeoutError("simulado")

    with patch("cliente.time.sleep"):
        with pytest.raises(TimeoutError):
            con_reintento(siempre_falla, intentos=3)

def test_con_reintento_no_reintenta_value_error():
    """Verifica que ante un ValueError con_reintento no reintente ni espere."""
    funcion_falla = Mock(side_effect=ValueError("simulado"))

    with patch("cliente.time.sleep") as mock_sleep:
        with pytest.raises(ValueError):
            con_reintento(funcion_falla, intentos=3)

    assert funcion_falla.call_count == 1
    mock_sleep.assert_not_called()

def test_consultar_modelo_convierte_error():
    """Verifica que consultar_modelo convierta un TimeoutError en RuntimeError."""
    error_simulado = TimeoutError("simulado")

    with patch("cliente.con_reintento", side_effect=error_simulado):
        with pytest.raises(RuntimeError):
            consultar_modelo("pregunta de prueba")


def test_registrar_costo_acumula():
    """Verifica que registrar_costo calcule el costo y lo sume al total de la sesión."""
    cliente.costo_total_sesion = 0
    respuesta_falsa = {"usageMetadata": {"totalTokenCount": 1000}}
    costo = cliente.registrar_costo(respuesta_falsa)

    assert costo == cliente.COSTO_POR_1000_TOKENS
    assert cliente.costo_total_sesion == cliente.COSTO_POR_1000_TOKENS


@pytest.fixture(autouse=True)
def reiniciar_costo_total():
    """Reinicia el costo total de la sesión antes de cada test."""
    cliente.costo_total_sesion = 0
    yield