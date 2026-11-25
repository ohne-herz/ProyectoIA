"""La matriz cumple las reglas de la actividad del Bloque 32."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matriz_riesgos as m  # noqa: E402


def test_matriz_cumple_reglas_de_la_actividad():
    assert m.validar(m.mis_riesgos) == []


def test_funciones_de_la_leccion():
    assert m.categoria_riesgo(m.puntaje_riesgo(4, 4)) == "CRITICO"  # fila modelo: 16
    assert m.esta_en_el_limite(4, 4) is True
    assert m.categoria_riesgo(3) == "BAJO" and m.categoria_riesgo(9) == "ALTO"
