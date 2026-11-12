# ---------------------------------------------------------------------------
# Primera pasada automatizada sobre la traza del agente (Bloque 23).
# Marca CANDIDATAS a revisión humana; no decide si algo está mal.
# Cubre 2 de los 3 patrones del Bloque 23:
#   1) Misma herramienta invocada varias veces seguidas.
#   2) Herramienta de riesgo alto sin registro de aprobación en la traza.
# El patrón 3 (respuesta final que no coincide con ninguna observación)
# se revisa a mano: compararlo por texto genera demasiados falsos positivos.
# ---------------------------------------------------------------------------
import json
import sys
from pathlib import Path

ARCHIVO_TRAZAS = Path(__file__).parent / "trazas_agente.json"

# Debe coincidir con lo declarado en docs/limites_autonomia_agente.md
HERRAMIENTAS_RIESGO_ALTO = {"generar_reembolso"}
MARCA_APROBACION = "[APROBACION:"


def cargar_trazas(archivo: Path = ARCHIVO_TRAZAS) -> list[dict]:
    """Lee el archivo línea por línea. Una línea corrupta se informa y se
    salta, en vez de interrumpir la revisión completa."""
    try:
        with open(archivo, encoding="utf-8") as f:
            lineas = f.readlines()
    except FileNotFoundError:
        print(f"No se encontró '{archivo}'. Corre el agente (registrar_traza) "
              "al menos una vez antes de revisar.")
        return []

    registros = []
    for numero, linea in enumerate(lineas, start=1):
        if not linea.strip():
            continue
        try:
            registros.append(json.loads(linea))
        except json.JSONDecodeError as e:
            print(f"Línea {numero} corrupta, se omite: {e}")
    return registros


def marcar_repeticiones_sospechosas(registros: list[dict]) -> int:
    """Patrón 1: la misma herramienta invocada dos veces seguidas dentro de
    una interacción. Compara solo el nombre (no los argumentos)."""
    marcados = 0
    for registro in registros:
        herramientas = [a.get("herramienta") for a in registro.get("acciones", [])]
        for i in range(1, len(herramientas)):
            if herramientas[i] == herramientas[i - 1]:
                print(f"Revisar [repetición]: {registro.get('session_id')} "
                      f"({registro.get('timestamp')}) usó '{herramientas[i]}' "
                      "dos veces seguidas")
                marcados += 1
                break
    return marcados


def marcar_alto_riesgo_sin_aprobacion(registros: list[dict]) -> int:
    """Patrón 2: herramienta de riesgo alto cuya observación no refleja una
    decisión humana (ni aprobación ni rechazo)."""
    marcados = 0
    for registro in registros:
        for accion in registro.get("acciones", []):
            if accion.get("herramienta") not in HERRAMIENTAS_RIESGO_ALTO:
                continue
            if MARCA_APROBACION not in str(accion.get("observacion", "")):
                print(f"Revisar [sin aprobación]: {registro.get('session_id')} "
                      f"({registro.get('timestamp')}) invocó "
                      f"'{accion['herramienta']}' sin registro de aprobación")
                marcados += 1
    return marcados


def resumen(registros: list[dict]) -> None:
    """Conteo por herramienta: confirma que hay al menos una traza por nivel."""
    conteo: dict[str, int] = {}
    for registro in registros:
        for accion in registro.get("acciones", []):
            nombre = accion.get("herramienta", "?")
            conteo[nombre] = conteo.get(nombre, 0) + 1
    sin_herramienta = sum(1 for r in registros if not r.get("acciones"))
    print(f"Interacciones: {len(registros)} | sin herramienta: {sin_herramienta}")
    for nombre, total in sorted(conteo.items()):
        print(f"  {nombre}: {total}")


if __name__ == "__main__":
    archivo = Path(sys.argv[1]) if len(sys.argv) > 1 else ARCHIVO_TRAZAS
    registros = cargar_trazas(archivo)
    if registros:
        resumen(registros)
        total = (marcar_repeticiones_sospechosas(registros)
                 + marcar_alto_riesgo_sin_aprobacion(registros))
        print(f"Candidatas a revisión humana: {total}")
