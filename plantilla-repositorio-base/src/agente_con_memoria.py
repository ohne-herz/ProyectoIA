#Herramientas Personalizadas
#Intro a Memoria

# ---------------------------------------------------------------------------
# Agente de logística con LangChain + Gemini, con memoria por sesión.
# Conceptos que cubre:
#   1) Herramientas con esquema de argumentos explícito .
#   2) Agente con tool calling (consulta de envíos y cálculo de costos).
#   3) Memoria conversacional: un historial independiente por session_id,
#      inyectado en el prompt en cada turno.
# ---------------------------------------------------------------------------

# Carga las variables del archivo .env (API key de Google) al entorno del proceso
from dotenv import load_dotenv
# Decorador que convierte una función Python en una herramienta invocable por el LLM
from langchain_core.tools import tool
# Plantilla de prompt y espacio dinámico para insertar mensajes en tiempo de ejecución
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# Permite envolver una función Python como paso de una cadena (se usa para limpiar la salida)
from langchain_core.runnables import RunnableLambda
# Wrapper de LangChain para modelos Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
# Constructor del agente con tool calling y orquestador del ciclo razonar-actuar-observar
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
# BaseModel/Field: definen el esquema de argumentos de una tool.
# ValidationError: importado pero no utilizado en este script.
from pydantic import BaseModel, Field, ValidationError
from langchain_core.chat_history import InMemoryChatMessageHistory #Crear el historial en base a la sesión
from langchain_core.runnables.history import RunnableWithMessageHistory #Encapsular mi agente para que implemente la memoria
import queue
import threading
import sys
from datetime import datetime, timezone
import json
from pathlib import Path


#Configuraciones e Inicializaciones
# La carga del .env debe ocurrir antes de instanciar el modelo
load_dotenv()
modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

# Rutas ancladas a la carpeta del script: la traza queda siempre en src/,
# sin importar desde qué carpeta se ejecute el agente.
RUTA_TRAZAS = Path(__file__).parent / "trazas_agente.json"
RUTA_APROBACIONES = Path(__file__).parent / "aprobaciones_agente.jsonl"

#================ Persistencia y análisis de trazabilidad.
def registrar_traza(session_id: str, entrada: str, resultado: dict) ->None:
    
    """resultado = {"intermediate_steps": [
        {
        "action": {
                "tool": x,
                "tool_input": argumentos   
            },
        "observation": respuesta de la herramienta
        }
    ]}
    """
    
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion

            }
            for accion, observacion in resultado.get("intermediate_steps",[])
        ],
        "respuesta_final": resultado.get("output","")
    }

    with open(RUTA_TRAZAS,"a",encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False)+"\n") 



    
#=== Auditoria / Human in the loop
registro_aprobaciones = []

def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int=20) -> bool:
    cola_respuesta = queue.Queue()

    def pedir_entrada():
        try:
            texto = input(mensaje)
            cola_respuesta.put(texto.strip().lower())
        except(EOFError, KeyboardInterrupt):
            cola_respuesta.put("")

    hilo = threading.Thread(target=pedir_entrada, daemon=True)
    hilo.start()


    try:
        respuesta = cola_respuesta.get(timeout=tiempo_limite_segundos)
        return respuesta == "s"
    except queue.Empty:
        print("Tiempo de espera agotado. Solicitud denegada por timeout")
        return False
    # Nota: se usa threading + queue en vez de select.select() (Bloque 23)
    # porque select sobre stdin no funciona en Windows. Mismo propósito:
    # espera con límite de tiempo y deniega por defecto (fail-closed).

def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool) -> None:
    registro = {
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "fecha_hora": datetime.now(timezone.utc).isoformat()
    }
    registro_aprobaciones.append(registro)
    # Persistencia: la lista en memoria se pierde al cerrar el proceso;
    # el archivo deja evidencia auditable de cada decisión humana.
    with open(RUTA_APROBACIONES, "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")

#=== Esquemas de validación
class ArgumentosConsultaEnvio(BaseModel): #class ClaseHija(ClasePadre):
    """
    Esquema para documentar y validar argumentos campo por campo ante el LLM.
    """
    # Cada Field aporta una descripción en lenguaje natural que el modelo lee para
    # saber qué valor debe enviar en cada argumento (con ejemplo incluido)
    numero_seguimiento: str = Field(
        description="Número de seguimiento del envío, por ejemplo 'AR129012'."
    )
    # Argumento opcional: si el modelo no lo informa, toma el valor por defecto False
    incluir_historial: bool = Field(
        default= False,
        description="Si es True, incluye en historial completo de los estados, no solo el actual."
    )

#Base de Datos
# Base de datos simulada en memoria: número de seguimiento -> estado actual + historial.
# En un caso real sería una consulta a una API o base de datos de logística.
ESTADOS = {
    "AR12345": {
        "actual": "En tránsito, entrega estimada de 2 días",
        "historial": [
            "Recibido en depósito",
            "En tránsito"
        ]
    },
    "AR12346": {
        "actual": "Entregado",
        "historial": [
            "Recibido en depósito",
            "En tránsito"
        ]
    }
}

#Herramientas
#@tool("nuevo_nombre")
# Con args_schema, el esquema de entrada se toma de la clase Pydantic definida arriba
# (descripciones y defaults incluidos) y no de la firma de la función.
# Alternativa comentada: @tool("nuevo_nombre") permite cambiar el nombre visible de la tool.
@tool(args_schema=ArgumentosConsultaEnvio) #LangChain transforma esta clase en un esquema JSON que se envía al LLM. El modelo lo lee textualmente
def consultar_estado_envio_detallado(numero_seguimiento: str, incluir_historial: bool = False):
    # El docstring también se envía al modelo como descripción de la herramienta
    """
    Consulta el estado de un envío, con la opción de incluir el historial completo.
    """
    # .get() devuelve None si el número no existe (en vez de lanzar KeyError)
    envio = ESTADOS.get(numero_seguimiento) #AR12346
    #envio = {
    #     "actual": "Entregado",
    #     "historial": [
    #         "Recibido en depósito",
    #         "En tránsito"
    #     ]
    # }
    # Envío inexistente: se informa al modelo para que lo comunique al usuario
    if envio is None:
        return f"No se encontró un envío con el número {numero_seguimiento}."
    
    #Si no se solicita el historial, retornamos solo el estado actual
    if not incluir_historial:
        return envio["actual"]

    #Si sí se solicita el historial, formatear y retornar la info
    # Convierte la lista de estados en un único texto separado por comas
    historial = ", ".join(envio["historial"]) # "Recibido en depósito, En tránsito"
    return f"{envio['actual']} (historial: {historial})" #"Entregado" (historial: Recibido en depósito, En tránsito)

# Esta tool no usa args_schema: LangChain infiere el esquema desde los tipos de la
# firma (peso_kg, distancia_km) y la descripción desde el docstring
@tool
def calcular_costo_envio(peso_kg: float, distancia_km: float) -> str:
    """Calcula el costo estimado de un envío según su peso y la distancia a recorrer.
    Usar cuando el usuario pregunta cuánto va a costar enviar algo."""
    # Fórmula de tarifa: base fija 500 + 120 por kg + 3 por km
    costo = 500 + (peso_kg * 120) + (distancia_km * 3)
    # Formatea con 2 decimales
    return f"El costo estimado es de ${costo:.2f}"

@tool
def generar_reembolso(numero_pedido: str, monto: float) -> str:
    """
    Generar un reembolso económico par aun pedido. Acción irreversible: requiere aprobación humana antes de ejecutarse
    """
    mensaje = f"[SUPERVISION HUMANA REQUERIDA] El usuario solicita reembolsar ${monto} para el pedido {numero_pedido}. ¿Desea aprobar? (s/n) : "

    #condelar el proceso, hasta que el supervisor de el visto bueno
    aprobado = esperar_aprobacion(mensaje, tiempo_limite_segundos=15)

    #Registrar en la lista si se aprobó o rechazó el reembolso
    registrar_aprobacion(
        herramienta="generar_reembolso",
        argumentos={"numero_pedido": numero_pedido, "monto": monto},
        aprobado=aprobado
    )

    if not aprobado:
        # La marca [APROBACION: ...] deja la decisión humana visible en la traza
        # (observacion), para que revisar_trazas.py pueda verificarla.
        return "[APROBACION: rechazado] Reembolso no aprobado por el supervisor o cancelado por timeout"

    #Acciones para regresar el dinero (Ej: Una llamada a la pasarela de pagos)
    return f"[APROBACION: aprobado] Reembolso de {monto} fue generado con éxito para el pedido número {numero_pedido}"

#Listado de herramientas
# Catálogo registrado tanto en el agente (para que el modelo las conozca)
# como en el ejecutor (para poder ejecutarlas)
herramientas = [consultar_estado_envio_detallado, calcular_costo_envio,generar_reembolso]

#Gestión de historial en memoria
# Diccionario session_id -> historial de mensajes de esa sesión.
# Al vivir en memoria del proceso, se pierde al reiniciar la aplicación
# (para producción se usaría un almacén persistente: Redis, Cosmos DB, Dataverse, etc.).
historiales = {}
"""
historiales = {
    'cliente_123': {MENSAJES},
    'cliente_345': {MENSAJES},
    'cliente_567': {"Cuánto me cuesta x y y?"}
}
"""
# Función "fábrica" de historiales: RunnableWithMessageHistory la llama en cada invoke()
# con el session_id recibido en la config. Si la sesión no existe, la crea; si existe,
# devuelve el historial acumulado. Así cada cliente tiene su conversación aislada.
def obtener_historial(session_id: str): #cliente_567
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]


#Construcción del agente
prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system", "Eres un asistente de logística que responde preguntas usando las herramientas disponibles."
    ),
    # Aquí se inyectan los mensajes previos de la sesión. El nombre "chat_history"
    # debe coincidir con history_messages_key en RunnableWithMessageHistory (más abajo).
    MessagesPlaceholder("chat_history"),
    # Mensaje actual del usuario. "entrada" debe coincidir con input_messages_key.
    ("human", "{entrada}"),
    # Espacio donde LangChain registra las llamadas a tools y sus resultados en cada ciclo
    MessagesPlaceholder("agent_scratchpad")
])

# Une modelo + herramientas + prompt. Solo decide qué tool llamar; no la ejecuta
agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

# Orquestador del ciclo: llama al agente, ejecuta la tool, devuelve la observación al
# modelo y repite hasta obtener la respuesta final. verbose=True imprime los pasos.
ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    verbose=True,
    return_intermediate_steps=True
)

# Paso de post-procesamiento: el modelo puede devolver "output" como lista de bloques
# de contenido ({"text": ...}) o como str. Esta función normaliza ambos casos a texto:
# si es lista, toma el texto del primer bloque; si no, lo deja como está.
# {**d, ...} copia el diccionario original y solo reemplaza la clave "output".
# Es necesario para que el historial guarde la respuesta como texto plano.
limpiar_salida = RunnableLambda(
    lambda d: {**d, "output": d["output"][0]["text"] if isinstance(d.get("output"), list) else d.get("output")}
)

# Encadena con el operador | (LCEL): la salida del ejecutor pasa a limpiar_salida
cadena_agente = ejecutor_agente | limpiar_salida

#agente con memoria
# Envuelve la cadena para que, en cada invoke():
#   1) obtenga el historial de la sesión (obtener_historial),
#   2) lo inyecte en el prompt vía "chat_history",
#   3) tras responder, guarde en el historial el mensaje del usuario ("entrada")
#      y la respuesta ("output").
# Solo se persisten la pregunta y la respuesta final; los pasos intermedios de las
# tools (agent_scratchpad) no se guardan en el historial.
agente_con_memoria = RunnableWithMessageHistory(
    cadena_agente,
    obtener_historial,
    input_messages_key="entrada",
    history_messages_key="chat_history",
    output_messages_key="output"
)

# Punto de entrada: el bloque solo corre al ejecutar el archivo directamente,
# no cuando se importa como módulo
if __name__ == "__main__":
    # # Prueba anterior sin memoria (desactivada)
    # # resultado = ejecutor_agente.invoke(
    # #     {"entrada": "¿Cuál es el estado del envío AR12345, con su historial?"}
    # # )

    # #print("Respuesta: ", resultado["output"][0]["text"])
    
    # # Sesión 1 (cliente_456): el session_id viaja en config["configurable"]
    # # y es lo que recibe obtener_historial
    # config1 = {"configurable": {"session_id": "cliente_456"}}
    # # Turno 1: debería invocar consultar_estado_envio_detallado con
    # # numero_seguimiento="AR12345" e incluir_historial=True
    # resultado1 = agente_con_memoria.invoke(
    #     {"entrada": "¿Cuál es el estado del envío AR12345, con su historial?"},
    #     config1
    # )

    # # Gracias a limpiar_salida, "output" ya es texto y no requiere [0]["text"]
    # print("Turno 1: ", resultado1["output"])

    # # Turno 2 (misma sesión): "ese mismo envío" no trae número de seguimiento.
    # # El modelo lo resuelve leyendo el historial del turno 1, lo que demuestra la memoria.
    # resultado2 = agente_con_memoria.invoke(
    #     {"entrada": "¿Y ese mismo envío ya fue entregado?"},
    #     config1
    # )

    # print("Turno 2: ", resultado2["output"])

    # # Sesión 2 (cliente_567): historial independiente del de cliente_456
    # config2 = {"configurable": {"session_id": "cliente_567"}}
    # # Turno 3: debería invocar calcular_costo_envio con peso_kg=3 y distancia_km=300
    # resultado3 = agente_con_memoria.invoke(
    #     {"entrada": "¿Cuánto cuesta enviar un paquete de 3kg a 300km"},
    #     config2
    # )

    # print("Turno 3:", resultado3['output'])

    # # Turno 4 (misma sesión): "el doble de peso" solo se entiende recordando el turno 3
    # # (6 kg a 300 km). Sin memoria, el modelo no tendría los datos para calcular.
    # resultado4 = agente_con_memoria.invoke(
    #     {"entrada": "¿Y cuánto costaría con el doble de peso?"},
    #     config2
    # )

    # print("Turno 4:", resultado4['output'])

    # Una entrada por herramienta (cubre riesgo bajo y alto); TODAS se registran
    # en la traza, incluida la de reembolso (antes no se trazaba).
    casos = [
        ("cliente_246", "¿Cuánto me cuesta enviar un paquete de 2.5 kg a 50 km?"),
        ("cliente_456", "¿Cuál es el estado del envío AR12345, con su historial?"),
        ("cliente_123", "Mi pedido PED123 llegó roto. Exijo un reembolso de mis 25000 pesos"),
    ]
    for session_id, entrada in casos:
        config = {"configurable": {"session_id": session_id}}
        resultado = agente_con_memoria.invoke({"entrada": entrada}, config)
        registrar_traza(session_id=session_id, entrada=entrada, resultado=resultado)
        print(f"[{session_id}] {resultado['output']}")

    print("Registros de aprobación de esta ejecución:")
    for registro in registro_aprobaciones:
        print(registro)
