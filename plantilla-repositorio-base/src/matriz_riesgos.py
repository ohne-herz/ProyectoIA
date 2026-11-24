"""Matriz de riesgos (Bloque 32): asistente para ejecutivos de Customer Service
conectado a Dynamics 365.

Usa la estructura de la actividad del Bloque 32:
  - cada fila tiene riesgo, probabilidad (1-5), impacto (1-5) y mitigacion;
  - puntaje = probabilidad x impacto; categoria segun categoria_riesgo();
  - esta_en_el_limite() marca las filas que conviene revisar con otra persona;
  - los puntos de supervision se documentan aparte (PUNTOS_DE_SUPERVISION).

Campos agregados para este proyecto:
  - id y alcance: "prototipo" (implementado en el Gate 2) o "d365" (diseño objetivo
    de la integracion con Dynamics 365, no implementado todavia);
  - justificacion: por que esa probabilidad y ese impacto.

Uso:
  python src/matriz_riesgos.py              # imprime la matriz y las validaciones
  python src/matriz_riesgos.py --markdown   # ademas regenera docs/matriz_riesgos.md
"""
import sys
from pathlib import Path


# ---------------------------------------------------------------- Funciones de la leccion
def puntaje_riesgo(probabilidad, impacto):
    return probabilidad * impacto


def categoria_riesgo(puntaje):
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


def esta_en_el_limite(probabilidad, impacto):
    categoria_actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto), (probabilidad - 1, impacto),
        (probabilidad, impacto + 1), (probabilidad, impacto - 1),
    ]
    for p2, i2 in vecinos:
        if not (1 <= p2 <= 5 and 1 <= i2 <= 5):
            continue
        if categoria_riesgo(puntaje_riesgo(p2, i2)) != categoria_actual:
            return True
    return False


# ---------------------------------------------------------------- Mis riesgos
mis_riesgos = [
    # ===== Prototipo (alcance Gate 2: controles implementados) =====
    {"id": "R-01", "alcance": "prototipo",
     "riesgo": "El asistente sugiere al ejecutivo una respuesta sin respaldo en las politicas y el ejecutivo se la dice al cliente como oficial",
     "probabilidad": 3, "impacto": 4,
     "justificacion": "P3: en la corrida real el modelo afirmo un hecho que no estaba en el CRM (hallazgo H-1). I4: compromete a la empresa frente al cliente",
     "mitigacion": "Fuentes adjuntas desde los documentos usados + prompt restringido a <contexto>/<crm> + respuesta fija sin contexto (Bloque 27, servicio Gate 2)"},
    {"id": "R-02", "alcance": "prototipo",
     "riesgo": "Inyeccion de prompt via texto oculto en un documento de politicas indexado",
     "probabilidad": 2, "impacto": 4,
     "justificacion": "P2: la base de conocimiento es interna y curada, no la escriben usuarios. I4: podria cambiar las instrucciones del asistente",
     "mitigacion": "Filtro de patrones sobre Document.page_content + delimitacion de contexto (Bloque 31)"},
    {"id": "R-03", "alcance": "prototipo",
     "riesgo": "Inyeccion de prompt via texto del cliente que el ejecutivo copia desde el chat al asistente",
     "probabilidad": 3, "impacto": 3,
     "justificacion": "P3: el ejecutivo pega texto escrito por terceros. I3: el asistente no ejecuta acciones; el dano se limita a una sugerencia alterada",
     "mitigacion": "Bloqueo de la consulta antes de la recuperacion y del modelo (Bloque 31)"},
    {"id": "R-04", "alcance": "prototipo",
     "riesgo": "Datos personales del cliente (nombre, RUT, montos) quedan en los logs o se envian al modelo sin necesidad",
     "probabilidad": 3, "impacto": 4,
     "justificacion": "P3: los logs de depuracion tienden a guardar todo. I4: incumplimiento de proteccion de datos",
     "mitigacion": "Logs con largo y huella + guardia que rechaza texto largo + nombre del cliente excluido del prompt (Bloque 31)"},
    {"id": "R-05", "alcance": "prototipo",
     "riesgo": "El ejecutivo comunica un escalamiento o una nueva fecha por plazo vencido (POL-12) sin autorizacion de supervision",
     "probabilidad": 3, "impacto": 4,
     "justificacion": "P3: el caso vencido es comun (CAS-1043). I4: promesa al cliente que la operacion puede no cumplir",
     "mitigacion": "Plazo vencido calculado en codigo + grafo de aprobacion con interrupt()/Command (Bloque 32)"},
    {"id": "R-06", "alcance": "prototipo",
     "riesgo": "Se cambia el prompt de sistema sin control y no se puede saber que version genero cada sugerencia",
     "probabilidad": 3, "impacto": 4,
     "justificacion": "P3: el prompt ya cambio varias veces en el proyecto. I4: sin trazabilidad no se puede investigar un reclamo",
     "mitigacion": "RegistroDePrompts con huella + prompt_huella en cada respuesta + despliegue con aprobacion (Bloque 32)"},
    {"id": "R-07", "alcance": "prototipo",
     "riesgo": "Un ajuste economico (POL-15/16) se calcula mal, supera el monto reclamado o se confirma al cliente sin aprobacion (POL-20)",
     "probabilidad": 3, "impacto": 5,
     "justificacion": "P3: el modelo interpreto mal el estado del ajuste en la corrida real (H-1). I5: perdida de dinero y compromiso con el cliente",
     "mitigacion": "Monto calculado en codigo con tope (evaluar_ajuste) + CRM explicito 'solicitud NO ingresada' + aprobacion de supervisor (Bloque 32, servicio Gate 2)"},
    {"id": "R-08", "alcance": "prototipo",
     "riesgo": "Se genera un ajuste sobre un caso cerrado (POL-21) o un segundo ajuste en el mismo caso (POL-20)",
     "probabilidad": 2, "impacto": 4,
     "justificacion": "P2: la regla esta en codigo y testeada. I4: pago indebido",
     "mitigacion": "evaluar_ajuste bloquea estados cerrados y ajustes previos, con test por escenario (servicio Gate 2)"},
    {"id": "R-09", "alcance": "prototipo",
     "riesgo": "El asistente muestra un estado de caso desactualizado porque el dato del CRM quedo indexado",
     "probabilidad": 2, "impacto": 3,
     "justificacion": "P2: el CRM no se indexa por diseño. I3: respuesta incorrecta, corregible por el ejecutivo",
     "mitigacion": "CRM consultado en cada pregunta, no indexado (decision de personalizacion, Bloque 30)"},
    {"id": "R-10", "alcance": "prototipo",
     "riesgo": "Latencia de ~7,75 s o errores 429/503 del modelo mientras el cliente espera en linea",
     "probabilidad": 4, "impacto": 3,
     "justificacion": "P4: medido en la corrida real (86 % del tiempo en la generacion). I3: el ejecutivo abandona la herramienta, sin dano directo al cliente",
     "mitigacion": "timeout + reintentos acotados + latencia por etapa en consumo_llm.jsonl (Bloque 28)"},
    {"id": "R-11", "alcance": "prototipo",
     "riesgo": "Una solicitud de ajuste pendiente se pierde o vence porque la aprobacion vive en memoria",
     "probabilidad": 2, "impacto": 3,
     "justificacion": "P2: en el prototipo la aprobacion ocurre en la misma ejecucion. I3: el cliente queda sin respuesta, pero no se paga nada sin aprobar",
     "mitigacion": "Checkpointer persistente y cola de aprobaciones (planificado Gate 3)"},
    {"id": "R-21", "alcance": "prototipo",
     "riesgo": "El proveedor cambia las tarifas del modelo y el costo calculado queda desactualizado",
     "probabilidad": 2, "impacto": 1,
     "justificacion": "P2: los precios cambian pocas veces al año. I1: solo afecta el reporte de costo",
     "mitigacion": "Tarifas parametrizadas en .env y revision periodica (Bloque 28)"},

    # ===== Integracion Dynamics 365 (diseño objetivo, no implementado) =====
    {"id": "R-12", "alcance": "d365",
     "riesgo": "El servicio lee Dataverse con un usuario de aplicacion de permisos amplios y muestra al ejecutivo casos o columnas que su rol no permite",
     "probabilidad": 3, "impacto": 4,
     "justificacion": "P3: error frecuente en integraciones S2S. I4: acceso indebido a datos de clientes",
     "mitigacion": "Usuario de aplicacion con rol minimo + impersonacion del ejecutivo + seguridad por columna (diseño)"},
    {"id": "R-13", "alcance": "d365",
     "riesgo": "Se expone el secreto del app registration de Entra ID (en codigo, .env compartido o zip)",
     "probabilidad": 3, "impacto": 5,
     "justificacion": "P3: en este proyecto la clave de Gemini ya se expuso en un zip compartido. I5: acceso a Dataverse con los permisos del servicio",
     "mitigacion": ".env fuera de Git (Gate 1) + certificado o identidad administrada + Key Vault con rotacion (diseño)"},
    {"id": "R-14", "alcance": "d365",
     "riesgo": "Datos de clientes de Dynamics 365 salen del tenant de Microsoft hacia un modelo externo sin base contractual validada",
     "probabilidad": 3, "impacto": 5,
     "justificacion": "P3: el prototipo ya usa Gemini. I5: incumplimiento contractual o regulatorio",
     "mitigacion": "Minimizacion de datos enviados al modelo (Bloque 31) + evaluar un modelo dentro del tenant (diseño)"},
    {"id": "R-15", "alcance": "d365",
     "riesgo": "Un reintento o una doble aprobacion crea dos solicitudes de ajuste en Dataverse para el mismo caso",
     "probabilidad": 3, "impacto": 4,
     "justificacion": "P3: el servicio reintenta llamadas ante errores. I4: rompe POL-20 (un ajuste por caso) y puede duplicar el pago",
     "mitigacion": "Escritura idempotente (clave alternativa o upsert) + validacion server-side en Dataverse (diseño)"},
    {"id": "R-16", "alcance": "d365",
     "riesgo": "Se usan datos productivos de Dynamics 365 en DEV o UAT para probar el asistente",
     "probabilidad": 3, "impacto": 4,
     "justificacion": "P3: tentacion habitual para probar con casos reales. I4: datos de clientes en un ambiente sin controles de produccion",
     "mitigacion": "Datos simulados o anonimizados + configuracion por ambiente (diseño)"},
    {"id": "R-17", "alcance": "d365",
     "riesgo": "Los limites de proteccion de servicio de Dataverse (429) dejan al asistente sin estado del caso en hora punta",
     "probabilidad": 2, "impacto": 3,
     "justificacion": "P2: una lectura por consulta es un volumen bajo. I3: el ejecutivo consulta el caso directo en D365",
     "mitigacion": "Respetar Retry-After + leer solo las columnas necesarias + cache corta (diseño)"},
    {"id": "R-18", "alcance": "d365",
     "riesgo": "Los estados y campos del CRM simulado no coinciden con el estado y la razon del caso en D365 ni con sus columnas personalizadas",
     "probabilidad": 3, "impacto": 2,
     "justificacion": "P3: el prototipo uso estados simplificados. I2: se detecta en UAT antes de produccion",
     "mitigacion": "Mapeo documentado en el SDD + tests de contrato contra UAT (diseño)"},
    {"id": "R-19", "alcance": "d365",
     "riesgo": "La decision del supervisor queda solo en el log del servicio y no en el registro del caso en D365",
     "probabilidad": 2, "impacto": 3,
     "justificacion": "P2: el diseño ya contempla registrarla. I3: auditoria incompleta ante un reclamo",
     "mitigacion": "Registrar la solicitud y la decision con trace_id en Dataverse, con auditoria habilitada (diseño)"},
    {"id": "R-20", "alcance": "d365",
     "riesgo": "Se construye a medida una capacidad que Dynamics 365 Customer Service ya ofrece con Copilot para agentes",
     "probabilidad": 3, "impacto": 2,
     "justificacion": "P3: la oferta estandar evoluciona rapido. I2: sobrecosto de mantenimiento, no un incidente",
     "mitigacion": "Comparacion estandar vs. a medida en el Blueprint, verificando la oferta y el licenciamiento vigentes (diseño)"},
]

# Puntos de supervision: se documentan aparte, como pide la leccion.
# Obligatorios para ALTO y CRITICO; opcionales para el resto.
PUNTOS_DE_SUPERVISION = {
    "R-01": "Humano: el ejecutivo revisa las fuentes antes de hablar (agent assist). Automatico: evento respuesta_sin_citas_del_modelo",
    "R-03": "Automatico: evento consulta_bloqueada; el ejecutivo sigue sin el asistente y se revisan los bloqueos semanalmente",
    "R-04": "Automatico: test_logs_sin_contenido_crudo en cada cambio (criterio no compensable)",
    "R-05": "Humano: grafo_aprobacion tipo escalamiento; interrupt() hasta la decision del supervisor",
    "R-06": "Humano: grafo_despliegue_prompt; sin aprobacion la version no se activa",
    "R-07": "Humano: grafo_aprobacion tipo ajuste_economico; un rechazo deja la instruccion 'NO confirmar al cliente'",
    "R-10": "Automatico: revision de tiempos_ms por trace_id en consumo_llm.jsonl; el ejecutivo vuelve a la busqueda manual si no hay respuesta",
    "R-12": "Pruebas de acceso por rol en UAT + auditoria de Dataverse, aprobadas por el arquitecto antes de PROD",
    "R-13": "Revision de secretos antes de cada entrega/commit + alertas de inicio de sesion del service principal en Entra ID",
    "R-14": "Gate de aprobacion de seguridad y legal del cliente antes de conectar datos reales; sin aprobacion solo datos simulados",
    "R-15": "Humano: grafo de aprobacion existente + validacion server-side en Dataverse probada en UAT",
    "R-16": "Checklist de promocion DEV -> UAT -> PROD revisado por el lider tecnico",
}


# ---------------------------------------------------------------- Calculo
for r in mis_riesgos:
    r["puntaje"] = puntaje_riesgo(r["probabilidad"], r["impacto"])
    r["categoria"] = categoria_riesgo(r["puntaje"])
    r["al_limite"] = esta_en_el_limite(r["probabilidad"], r["impacto"])
    r["supervision"] = PUNTOS_DE_SUPERVISION.get(r["id"], "")


def validar(riesgos) -> list[str]:
    """Las tres condiciones que la actividad dice que siempre deben cumplirse."""
    errores = []
    if len(riesgos) < 5:
        errores.append("hay menos de cinco riesgos")
    sin_supervision = [r["id"] for r in riesgos
                       if r["categoria"] in ("ALTO", "CRITICO") and not r["supervision"]]
    if sin_supervision:
        errores.append(f"ALTO/CRITICO sin punto de supervision: {sin_supervision}")
    con_bloque = [r["id"] for r in riesgos if "Bloque" in r["mitigacion"]]
    if len(con_bloque) < 2:
        errores.append("menos de dos mitigaciones apuntan a algo construido con numero de bloque")
    if not any(r["categoria"] in ("ALTO", "CRITICO") for r in riesgos):
        errores.append("no hay ningun ALTO o CRITICO: revisar si se subestima")
    return errores


def a_markdown(riesgos) -> str:
    def tabla(alcance):
        filas = sorted((r for r in riesgos if r["alcance"] == alcance), key=lambda x: -x["puntaje"])
        lineas = ["| ID | Riesgo | P | I | Puntaje | Categoría | Al límite | Mitigación | Punto de supervisión |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for r in filas:
            cat = f"**{r['categoria']}**" if r["categoria"] in ("ALTO", "CRITICO") else r["categoria"]
            lineas.append(f"| {r['id']} | {r['riesgo']} | {r['probabilidad']} | {r['impacto']} | "
                          f"{r['puntaje']} | {cat} | {'Sí' if r['al_limite'] else ''} | "
                          f"{r['mitigacion']} | {r['supervision'] or '—'} |")
        return "\n".join(lineas)

    def conteo(alcance):
        return " · ".join(f"{c}: {sum(1 for r in riesgos if r['alcance'] == alcance and r['categoria'] == c)}"
                          for c in ("CRITICO", "ALTO", "MEDIO", "BAJO"))

    justificaciones = "\n".join(f"- **{r['id']}** (P{r['probabilidad']} × I{r['impacto']}): {r['justificacion']}"
                                for r in riesgos)
    al_limite = ", ".join(r["id"] for r in riesgos if r["al_limite"])
    return f"""# Matriz de riesgos: asistente para ejecutivos de Customer Service conectado a Dynamics 365

> Archivo generado por `python src/matriz_riesgos.py --markdown`. La fuente es `src/matriz_riesgos.py`: edita ahí, no aquí.

## Contexto

El asistente **apoya al ejecutivo** (agent assist): le sugiere qué responder y qué acción tomar mientras atiende a un cliente. No conversa con el cliente final. Combina la base de conocimiento de políticas (RAG) con el estado del caso en el CRM: un JSON simulado en el prototipo y Dynamics 365 Customer Service sobre Dataverse en la arquitectura objetivo.

**Método (Bloque 32):** probabilidad e impacto de 1 a 5; puntaje = P × I; CRÍTICO ≥ 15 · ALTO ≥ 9 · MEDIO ≥ 4 · BAJO < 4. "Al límite" = un punto más o menos en P o I cambia la categoría: conviene que otra persona revise la estimación.

## Parte A: prototipo (alcance Gate 2, controles implementados)

{conteo("prototipo")}

{tabla("prototipo")}

## Parte B: integración con Dynamics 365 (diseño objetivo, no implementado)

{conteo("d365")}

{tabla("d365")}

## Justificación de cada estimación

{justificaciones}

## Filas al límite (revisar con otra persona)

{al_limite}

**Lectura:** con la escala de 1 a 5 y los umbrales 4 / 9 / 15, casi cualquier estimación queda a un punto de cambiar de categoría, así que el indicador es muy sensible. Para priorizar la revisión, empezar por los CRÍTICO en 15 (R-07, R-13 y R-14): bajan a ALTO con un solo punto menos, y esa diferencia decide si se exige un gate de aprobación antes de producción.

## Supuestos

- La tabla de solicitudes de ajuste en Dataverse es una **propuesta de diseño** (tabla personalizada), no un objeto estándar de D365.
- En R-20, la oferta y el licenciamiento vigentes de Copilot en Customer Service se deben **verificar con Microsoft**.
- En R-07, para devoluciones (POL-16) se solicita el monto reclamado completo, porque la política solo define el tope. **Validar con el negocio.**

## Referencias (Microsoft Learn)

- [Service protection API limits (Dataverse)](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/api-limits): R-17
- [Server-to-server (S2S) authentication](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/build-web-applications-server-server-s2s-authentication): R-12, R-13
- [Impersonate another user (Dataverse)](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/impersonate-another-user): R-12
- [Column-level security](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/column-level-security): R-12
- [Manage Dataverse auditing](https://learn.microsoft.com/en-us/power-platform/admin/manage-dataverse-auditing): R-12, R-19
"""


if __name__ == "__main__":
    print("=== Matriz de riesgos (ordenada por puntaje) ===")
    for r in sorted(mis_riesgos, key=lambda x: -x["puntaje"]):
        print(f"{r['categoria']:8} ({r['puntaje']:2}) - {r['id']} [{r['alcance']}] {r['riesgo']}")

    print("\n=== Filas al limite ===")
    for r in mis_riesgos:
        if r["al_limite"]:
            print("revisar con otra persona:", r["id"], "-", r["riesgo"])

    print("\n=== Validaciones de la actividad ===")
    errores = validar(mis_riesgos)
    if errores:
        for e in errores:
            print("FALTA:", e)
        sys.exit(1)
    print(f"OK: {len(mis_riesgos)} riesgos; todo ALTO/CRITICO tiene punto de supervision; "
          f"{sum('Bloque' in r['mitigacion'] for r in mis_riesgos)} mitigaciones apuntan a un bloque construido")

    if "--markdown" in sys.argv:
        destino = Path(__file__).resolve().parents[1] / "docs" / "matriz_riesgos.md"
        destino.write_text(a_markdown(mis_riesgos), encoding="utf-8")
        print(f"Markdown regenerado en {destino.relative_to(destino.parents[1])}")