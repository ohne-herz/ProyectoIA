import json
import time
import sys
from prompts.banco import BANCO_DE_PROMPTS
from consumir_gemini_refactor import armar_peticion, enviar_peticion,extraer_texto,parsear_respuesta_json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

registro = {}

try:

    for prompt in BANCO_DE_PROMPTS:
        exitos = 0
        intentos = 3
        for intento in range(intentos):
            url,body = armar_peticion("gemini-3.5-flash-lite",
                                      prompt["ejemplo_usuario"],
                                      prompt["system_instruction"],
                                      prompt["response_schema"]
                                      )
            respuesta = enviar_peticion(url,body)
            texto = extraer_texto(respuesta)
            try:
                datos = parsear_respuesta_json (texto,prompt["claves_esperadas"])
                exitos +=1
            except ValueError as error:
                print(f"Intento {intento +1} falló {error}")
            time.sleep(1)
        print(f"{prompt["nombre"]}: {exitos}/{intentos} respuesta válidas")
        registro[prompt["nombre"]] = {"exitos":exitos, "intentos":intentos} 
    #cuando termine de recorrer los prompts quiero guardar esa info en el registro_resultados.json
    with open(f"{RAIZ}/src/prompts/registro_resultados.json", "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, indent=2, ensure_ascii=False)

except(ValueError,RuntimeError) as error:
    print("No se pudo completar la operación",error)