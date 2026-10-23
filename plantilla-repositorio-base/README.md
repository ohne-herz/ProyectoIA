# Proyecto General de IA — Especialización en Desarrollo con IA Generativa (Alejandro Orrego)

Esta es la estructura base que vas a usar como punto de partida para tu proyecto en este programa. Es la misma estructura que vas a ir ampliando bloque a bloque, hasta llegar a la aplicación completa que entregas en el Gate 3.


## Cómo empezar

Estos pasos se completan de forma progresiva a lo largo de la Unidad U1.2, no todos el mismo día:

1. Clona este repositorio utilizando el comando "git clone <url-del-repositorio>"
2. Crea tu entorno virtual de Python usando el comando <python -m venv venv> en tu terminal y actívalo usando el comando <venv/Scripts/activate>.
3. Instala las dependencias del proyecto usando el comando <pip install -r requirements.txt> para poder usarlas en la aplicación.

4. Copia `.env.example` a un archivo nuevo llamado `.env`, y completa ahí tus credenciales reales (llaves de API, tokens). El archivo `.env` nunca se sube al repositorio: ya está excluido en `.gitignore`.

5. Para ejectuar la "aplicación", usa el comando <python src/consumir_gemini_refactor.py>.


## Estructura de carpetas

- `src/` : todo el código fuente de tu proyecto va aquí.
- `docs/` : documentación técnica del proyecto (diagramas, decisiones de arquitectura, notas).
- `tests/` : pruebas de tu código (las vas a usar más adelante en el programa, cuando el proyecto lo requiera).
- `requirements.txt` : dependencias de Python de tu proyecto, para que cualquier otra persona pueda reconstruir tu entorno con un solo comando.
- `.env.example` : plantilla de las variables de entorno que tu proyecto necesita, sin valores reales. Tu archivo `.env` real (con tus credenciales) nunca se commitea.
- `.gitignore` : le dice a Git qué archivos y carpetas ignorar (entre ellos, tu entorno virtual y tu archivo `.env`).

## Reglas que se mantienen durante todo el programa

- Ningún secreto (contraseña, llave de API, token) va escrito directamente en el código ni en ningún archivo que se suba al repositorio.
- Cada proyecto nuevo tiene su propio entorno virtual: no se comparten dependencias entre proyectos distintos.
- Todo el trabajo que se entrega en este programa vive en un repositorio de GitHub, sin excepción.

## Registro del ensayo de instalación limpia

Fecha: 23/10/2026
Encontrado: En el README.md, no aparece el link del repositorio.
Corregido: Se puso el link correcto del repositorio.
Resultado tras la corrección: El repositorio se clonó de forma satisfactoria.