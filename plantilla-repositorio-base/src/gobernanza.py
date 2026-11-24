"""Gobernanza del servicio RAG (Bloque 32).

1. RegistroDePrompts: historial persistido e inmutable de versiones de prompt.
   Cada respuesta del servicio registra la huella del prompt que la generó.
2. Puntos de supervisión humana con LangGraph (interrupt() + Command):
   - grafo_aprobacion: un supervisor aprueba, antes de comunicarlo al cliente,
     el escalamiento por plazo vencido (POL-12) o un ajuste económico (POL-20).
     Riesgos ALTO R-05 y R-07 en docs/matriz_riesgos.md.
   - grafo_despliegue_prompt: un responsable aprueba activar una nueva versión
     de prompt en producción (riesgo ALTO R-06).
"""
import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


def huella(texto: str) -> str:
    """SHA-256 truncado: identifica un texto sin guardarlo en los logs."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------- Registro de prompts
class RegistroDePrompts:
    """Historial de prompts persistido en JSON. Las versiones nunca se editan ni borran:
    solo se agregan, y una sola queda marcada como activa."""

    def __init__(self, ruta: Path):
        self.ruta = Path(ruta)
        self.datos = {"activa": {}, "versiones": []}
        if self.ruta.exists():
            self.datos = json.loads(self.ruta.read_text(encoding="utf-8"))

    def _guardar(self):
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.ruta.write_text(json.dumps(self.datos, ensure_ascii=False, indent=2), encoding="utf-8")

    def registrar(self, nombre: str, texto: str, autor: str, nota: str) -> dict:
        h = huella(texto)
        existente = self.buscar(nombre, h)
        if existente:
            return existente
        version = {
            "nombre": nombre,
            "huella": h,
            "texto": texto,
            "autor": autor,
            "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "nota": nota,
        }
        self.datos["versiones"].append(version)
        self._guardar()
        return version

    def buscar(self, nombre: str, h: str):
        return next((v for v in self.datos["versiones"]
                     if v["nombre"] == nombre and v["huella"] == h), None)

    def activar(self, nombre: str, h: str):
        if not self.buscar(nombre, h):
            raise ValueError(f"La version {h} de {nombre} no esta registrada")
        self.datos["activa"][nombre] = h
        self._guardar()

    def activa(self, nombre: str):
        h = self.datos["activa"].get(nombre)
        return self.buscar(nombre, h) if h else None


def diff_prompts(anterior: str, nuevo: str) -> list[str]:
    return list(difflib.unified_diff(anterior.split(), nuevo.split(),
                                     fromfile="version_activa", tofile="version_propuesta",
                                     lineterm=""))


# ---------------------------------------------------------------- HITL 1: aprobaciones de supervisor
class EstadoAprobacion(TypedDict, total=False):
    tipo: str          # "escalamiento" (POL-12) o "ajuste_economico" (POL-20)
    politica: str
    caso_id: str
    trace_id: str
    detalle: str
    monto: int
    aprobado: bool
    resultado: str


RESULTADOS = {
    ("escalamiento", True): "escalado a Supervision: ofrecer nueva fecha de contacto dentro de 48 horas",
    ("escalamiento", False): "escalamiento rechazado: el ejecutivo no compromete nueva fecha",
    ("ajuste_economico", True): "ajuste aprobado: el ejecutivo puede confirmarlo; el abono sigue POL-07",
    ("ajuste_economico", False): "ajuste rechazado: el ejecutivo NO confirma el ajuste al cliente",
}


def _preparar(estado: EstadoAprobacion):
    monto = f" por {estado['monto']}" if estado.get("monto") is not None else ""
    print(f"[hitl] caso {estado['caso_id']}: {estado['tipo']}{monto} ({estado['detalle']}) "
          f"-> requiere aprobacion de supervisor ({estado['politica']})")
    return {}


def _supervisar(estado: EstadoAprobacion):
    # interrupt() congela el grafo y guarda el estado en el checkpointer.
    # No continua hasta recibir Command(resume=<decision del supervisor>).
    decision = interrupt({
        "motivo": f"aprobar {estado['tipo']} segun {estado['politica']} antes de comunicarlo al cliente",
        "caso_id": estado["caso_id"],
        "monto": estado.get("monto"),
        "trace_id": estado["trace_id"],
    })
    return {"aprobado": bool(decision)}


def _registrar(estado: EstadoAprobacion):
    resultado = RESULTADOS[(estado["tipo"], estado["aprobado"])]
    print(f"[hitl] caso {estado['caso_id']}: {resultado}")
    return {"resultado": resultado}


def construir_grafo_aprobacion():
    g = StateGraph(EstadoAprobacion)
    g.add_node("preparar", _preparar)
    g.add_node("supervisar", _supervisar)
    g.add_node("registrar", _registrar)
    g.add_edge(START, "preparar")
    g.add_edge("preparar", "supervisar")
    g.add_edge("supervisar", "registrar")
    g.add_edge("registrar", END)
    # Sin checkpointer, Command(resume=...) falla: el estado pausado debe guardarse.
    return g.compile(checkpointer=InMemorySaver())


# ---------------------------------------------------------------- HITL 2: despliegue de prompt
class EstadoDespliegue(TypedDict, total=False):
    nombre: str
    huella_actual: str
    huella_nueva: str
    aprobado: bool


def construir_grafo_despliegue(registro: RegistroDePrompts):
    def proponer(estado: EstadoDespliegue):
        actual = registro.buscar(estado["nombre"], estado["huella_actual"])
        nueva = registro.buscar(estado["nombre"], estado["huella_nueva"])
        print(f"[hitl] propuesta de prompt {estado['huella_actual']} -> {estado['huella_nueva']}")
        for linea in diff_prompts(actual["texto"], nueva["texto"]):
            print("   ", linea)
        return {}

    def supervisar(estado: EstadoDespliegue):
        decision = interrupt({
            "motivo": "aprobar nueva version de prompt en produccion",
            "huella_propuesta": estado["huella_nueva"],
        })
        return {"aprobado": bool(decision)}

    def aplicar(estado: EstadoDespliegue):
        if estado["aprobado"]:
            registro.activar(estado["nombre"], estado["huella_nueva"])
            print(f"[hitl] version {estado['huella_nueva']} activada")
        else:
            print(f"[hitl] version rechazada, se mantiene {estado['huella_actual']}")
        return {}

    g = StateGraph(EstadoDespliegue)
    g.add_node("proponer", proponer)
    g.add_node("supervisar", supervisar)
    g.add_node("aplicar", aplicar)
    g.add_edge(START, "proponer")
    g.add_edge("proponer", "supervisar")
    g.add_edge("supervisar", "aplicar")
    g.add_edge("aplicar", END)
    return g.compile(checkpointer=InMemorySaver())
