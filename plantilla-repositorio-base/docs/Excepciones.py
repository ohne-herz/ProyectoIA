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
'''x=10
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
'''
def dividir():
    try:
        num1 = int(input("Ingrese el primer número: "))
        num2 = int(input("Ingrese el segundo número: "))
        resultado = num1 / num2
        print(f"El resultado de la división es: {resultado}")
    except ValueError:
            print("La calculadora solo permite numeros enteros")    
    except ZeroDivisionError:
        print("La calculadora no puede dividirte entre cero.")
    except Exception as error:
        print(f"Ocurrió un error inesperado: {error}")
    finally:
        print("Gracias por usar la calculadora.")
#dividir()


try:
     bebidas = ["coca cola", "agua saborizada", "chocolate caliente"]
     bebida_deseada = input("Ingrese la bebida que quieres: ")
     if(bebida_deseada not in bebidas):
         raise ValueError("La bebida que ingresaste no está disponible.")
     else:
         print(f"Tu bebida {bebida_deseada} está lista!")
except ValueError as error:
    print(f"Error: {error}")    