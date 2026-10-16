MONTO_MINIMO_DESCUENTO = 50000
DESCUENTO = 0.1
IVA = 0.19


def calcular_subtotal(productos):
    subtotal = 0
    for producto in productos:
        subtotal += producto["precio"] * producto["cantidad"]
    return subtotal