"""
Banco de prompts - Proyecto IA Atención al Cliente (aseguradora de salud).
Convención para datos no disponibles 
  - Campos de texto: "no_informado"
  - Campos numéricos: 0, y el nombre del campo se agrega a "datos_faltantes"
"""

NO_INFORMADO = "no_informado"

BANCO_DE_PROMPTS = [
    # ---------- 1. Supervisor_Reembolsos ----------
    {
        "nombre": "Supervisor_Reembolsos",
        "system_instruction": (
            "Eres un supervisor del área de reembolsos de una aseguradora de salud. "
            "Tu misión es responder al cliente de forma amable y eficaz, y extraer los datos del reembolso. "
            "Usa solo la información que el cliente entrega o que viene en el contexto; nunca la inventes. "
            "Si un dato de texto no está disponible, usa 'no_informado'. "
            "Si el monto no está disponible, usa 0. "
            "Lista en 'datos_faltantes' cada campo que no pudiste obtener. "
            "Si faltan datos, pídeselos al cliente en 'respuesta_cliente'. "
            "La fecha de pago usualmente es 5 dias despues del requerimiento."
        ),
        "ejemplo_usuario": "Necesito que me devuelvan los $45.000 del examen, ojalá por transferencia.",
        "claves_esperadas": [
            "respuesta_cliente", "monto_reembolso", "fecha_pago", "forma_pago", "datos_faltantes",
        ],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "respuesta_cliente": {"type": "STRING"},
                "monto_reembolso": {
                    "type": "NUMBER",
                    "description": "Monto en pesos chilenos, sin puntos ni símbolo. 0 si no se informó.",
                },
                "fecha_pago": {
                    "type": "STRING",
                    "description": "Formato YYYY-MM-DD, o 'no_informado'.",
                },
                "forma_pago": {
                    "type": "STRING",
                    "enum": ["transferencia", "cheque", "abono_tarjeta", "otro", NO_INFORMADO],
                },
                "datos_faltantes": {
                    "type": "ARRAY",
                    "items": {
                        "type": "STRING",
                        "enum": ["monto_reembolso", "fecha_pago", "forma_pago"],
                    },
                },
            },
            "required": [
                "respuesta_cliente", "monto_reembolso", "fecha_pago", "forma_pago", "datos_faltantes",
            ],
        },
    },
    # ---------- 2. Clasificador_Intencion ----------
    {
        "nombre": "Clasificador_Intencion",
        "system_instruction": (
            "Eres un clasificador de mensajes de clientes de una aseguradora de salud. "
            "Asigna una sola categoría entre: reembolso, cobertura, facturacion, reclamo, "
            "actualizacion_datos u otro. "
            "Usa 'facturacion' para cobros, cuotas y pagos del plan; "
            "usa 'reclamo' para quejas sobre la atención o el servicio. "
            "Si el mensaje no encaja en ninguna categoría, usa 'otro'. "
            "Entrega un nivel de confianza entre 0 y 1 y el motivo en una frase. "
            "No respondas al cliente; solo clasifica."
        ),
        "ejemplo_usuario": "Me cobraron dos veces la cuota de este mes, ¿qué pasó?",
        "claves_esperadas": ["categoria", "confianza", "motivo"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "categoria": {
                    "type": "STRING",
                    "enum": [
                        "reembolso", "cobertura", "facturacion",
                        "reclamo", "actualizacion_datos", "otro",
                    ],
                },
                "confianza": {"type": "NUMBER", "description": "Valor entre 0 y 1."},
                "motivo": {"type": "STRING", "description": "Justificación en una frase."},
            },
            "required": ["categoria", "confianza", "motivo"],
        },
    },
    # ---------- 3. Detector_Escalamiento ----------
    {
        "nombre": "Detector_Escalamiento",
        "system_instruction": (
            "Eres un analista de calidad de atención. Evalúa el sentimiento y la urgencia del "
            "mensaje del cliente y decide si debe derivarse a un ejecutivo humano. "
            "Debes escalar siempre si hay amenaza de reclamo formal o acción legal, "
            "riesgo para la salud del paciente, o enojo explícito tras varios intentos. "
            "Si escalas, explica el motivo en 'razon_escalamiento'; si no escalas, usa 'no_aplica'. "
            "No respondas al cliente; solo evalúa."
        ),
        "ejemplo_usuario": (
            "Es la tercera vez que escribo y nadie me responde. Voy a reclamar a la Superintendencia."
        ),
        "claves_esperadas": ["sentimiento", "urgencia", "escalar", "razon_escalamiento"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "sentimiento": {"type": "STRING", "enum": ["positivo", "neutro", "negativo"]},
                "urgencia": {"type": "STRING", "enum": ["baja", "media", "alta"]},
                "escalar": {"type": "BOOLEAN"},
                "razon_escalamiento": {
                    "type": "STRING",
                    "description": "Motivo si escalar es true; 'no_aplica' si es false.",
                },
            },
            "required": ["sentimiento", "urgencia", "escalar", "razon_escalamiento"],
        },
    },
    # ---------- 4. Resumidor_Caso ----------
    {
        "nombre": "Resumidor_Caso",
        "system_instruction": (
            "Eres un asistente que prepara el traspaso de una conversación entre un bot y un cliente "
            "hacia un ejecutivo humano. "
            "Resume la conversación de forma objetiva, sin opiniones, para que el ejecutivo "
            "entienda el caso sin leer todo el historial. "
            "Incluye solo datos mencionados explícitamente; si algo no se mencionó, usa 'no_informado'. "
            "Si no hay acciones pendientes, entrega una lista vacía. "
            "No incluyas datos sensibles como RUT completo, números de tarjeta o diagnósticos."
        ),
        "ejemplo_usuario": (
            "Cliente: Hola, pedí un reembolso hace 15 días y no me llega. "
            "Bot: ¿Me indica el número de solicitud? "
            "Cliente: Es la 88213. Ya me estoy molestando."
        ),
        "claves_esperadas": [
            "resumen", "solicitud_relacionada", "acciones_pendientes", "estado_animo",
        ],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "resumen": {"type": "STRING", "description": "Máximo 3 frases."},
                "solicitud_relacionada": {
                    "type": "STRING",
                    "description": "Número de solicitud mencionado, o 'no_informado'.",
                },
                "acciones_pendientes": {"type": "ARRAY", "items": {"type": "STRING"}},
                "estado_animo": {
                    "type": "STRING",
                    "enum": ["tranquilo", "molesto", "muy_molesto"],
                },
            },
            "required": [
                "resumen", "solicitud_relacionada", "acciones_pendientes", "estado_animo",
            ],
        },
    },
]