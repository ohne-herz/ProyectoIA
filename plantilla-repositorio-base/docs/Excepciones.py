'''
numero = int("hola")
print (numero)


try: #intentar
except:  #si sucede ese error, haz lo que está en except
raise:  #lanza explicitamente una excepcion
finally: #siempre se ejecuta, haya o no excepcion
else: #si no hay excepcion

Sintaxis:
try:
    # Bloque de codigo que quiero tratar de realizar
except Error:
    # Bloque de codigo que quiero que se ejecute si ocurre la excepcion
else:
    # Código que se ejecuta si no hay excepción
finally:
    # Código que se ejecuta siempre, haya o no excepción
'''
x=10
y=0
try: 
    resultado = x/y
except ZeroDivisionError:
    print("Error: No se puede dividir por cero.")
finally:
    print("Ejecución finalizada")

try:
    numero = int("hola")
    print(numero)
except ValueError: # error de casteo de str a num
    print("Error: Favor de dar un numeral")

    texto = "Hola Clase !"
    num = 22
    try:
        frase = texto + num #esto da excepcion
    except TypeError: # error de tipo de dato
        print("Tipos de datos distintos, debe castear a string")


frutas = ["manzana", "platano", "sandia"]
try:
    print (frutas[6])
except IndexError: # error de indice fuera de rango
    print("Fruta inexistente")

#Este error sirve para candidates.
estudiante = {
    "nombre": "Pedro",
    "apellido": "Páramo"
}
try:
    print (estudiante["email"])
except KeyError: # error de clave inexistente
    print("Email no encontrado")