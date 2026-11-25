"""Verifica el entorno antes de la corrida final del Gate 2. Nunca imprime la clave."""
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

PAQUETES = ["langchain-core", "langchain-chroma", "langgraph", "python-dotenv", "langchain-google-genai"]
VARIABLES = ["GEMINI_API_KEY"]
RAIZ = Path(__file__).resolve().parent
INDICES = [RAIZ / "indice_gate2", RAIZ / "indice_gate2_simulado"]

try:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
except ImportError:
    pass

problemas, avisos = [], []
print("Python:", sys.version.split()[0])
if sys.version_info < (3, 10):
    problemas.append("usar Python 3.10 o superior")

for paquete in PAQUETES:
    try:
        print(f"{paquete}: {version(paquete)}")
    except PackageNotFoundError:
        print(f"{paquete}: NO instalado")
        problemas.append(f"instalar {paquete} (pip install -r requirements.txt)")

for nombre in VARIABLES:
    definida = bool(os.getenv(nombre))
    print(f"{nombre}: {'definida' if definida else 'FALTA'}")
    if not definida:
        avisos.append(f"{nombre} no definida: el servicio correra solo en modo --simulado")

indices_ok = [d.name for d in INDICES if d.is_dir() and any(d.iterdir())]
print("indices persistidos:", ", ".join(indices_ok) or "ninguno")
if not indices_ok:
    avisos.append("no hay indice: se crea en la primera corrida de src/servicio_rag.py")

print()
for a in avisos:
    print("Aviso:", a)
if problemas:
    print("Pendiente: " + "; ".join(problemas))
    sys.exit(1)
print("Entorno listo para la corrida final")
