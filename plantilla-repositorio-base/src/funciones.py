def suma(a,b): #a=5, b=6
    resultado = a + b
    return resultado #return: devueve valor de retorno



print (suma(5,6))


#JSON Javascript oject notation

estudiante = {
    "nombre": "Ana",
    "edad": 24,
    "curso": {
        "nombre": "Python",
        "calificacion": 92
    },
    "tareas": [
        {
            "titulo": "Variables",
            "completada": True
        },
        {
            "titulo": "Consumo de APIs",
            "completada": False
        }
    ]
}
#El nombre de la estudiante
print(estudiante["nombre"])
#La calificación del curso
print(estudiante["curso"]["calificacion"])
#El titulo de la segunda tarea
print(estudiante["tareas"][1]["titulo"])
#Si la primera tarea está completada
if estudiante["tareas"][0]["completada"]:
    print("La primera tarea está completada")
    if estudiante["tareas"][0]["completada"] == True:
        print("La primera tarea está completada")