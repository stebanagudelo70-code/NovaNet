import uuid
from datetime import datetime


def simular_pago_mercadopago(monto, descripcion="Servicio de internet"):
    """Simula un pago con Mercado Pago."""
    referencia = f"MP-{uuid.uuid4().hex[:8].upper()}"
    return {
        "metodo": "Mercado Pago",
        "monto": monto,
        "estado": "aprobado",
        "referencia": referencia,
        "descripcion": descripcion,
        "fecha": datetime.now().isoformat(),
        "mensaje": f"Pago de ${monto:.2f} procesado exitosamente vía Mercado Pago. Referencia: {referencia}"
    }


def simular_pago_visa(numero_tarjeta, monto, descripcion="Servicio de internet"):
    """Simula un pago con tarjeta Visa."""
    ultimos_digitos = numero_tarjeta[-4:] if len(numero_tarjeta) >= 4 else "****"
    referencia = f"VISA-{uuid.uuid4().hex[:8].upper()}"
    return {
        "metodo": "Visa",
        "monto": monto,
        "estado": "aprobado",
        "referencia": referencia,
        "descripcion": descripcion,
        "fecha": datetime.now().isoformat(),
        "tarjeta_final": ultimos_digitos,
        "mensaje": f"Pago de ${monto:.2f} procesado exitosamente con Visa terminación {ultimos_digitos}. Referencia: {referencia}"
    }


def procesar_pago(metodo_pago, monto, datos_adicionales=None):
    """Procesa un pago según el método seleccionado."""
    if metodo_pago.lower() == "mercadopago":
        return simular_pago_mercadopago(monto)
    elif metodo_pago.lower() == "visa":
        datos = datos_adicionales or {}
        numero_tarjeta = datos.get("numero_tarjeta", "4111111111111111")
        return simular_pago_visa(numero_tarjeta, monto)
    else:
        return {
            "metodo": metodo_pago,
            "estado": "rechazado",
            "mensaje": f"Método de pago '{metodo_pago}' no disponible. Use Mercado Pago o Visa."
        }
