import random
from datetime import datetime, timedelta


class SimulacionRed:
    """Simula el estado de la red para el soporte técnico."""

    ESTADOS = {"verde", "naranja", "rojo"}

    def __init__(self):
        self.routers = {}
        self._listeners = []
        self._inicializar_routers()

    def on_state_change(self, callback):
        self._listeners.append(callback)

    def _notify(self, router_data, old_state, new_state, reason=""):
        for cb in self._listeners:
            try:
                cb(router_data, old_state, new_state, reason)
            except Exception as e:
                print(f"[EVENT ERROR] {e}")

    def _inicializar_routers(self):
        """Inicializa los routers con IPs asignadas."""
        nombres = [
            "Router-Alpha", "Router-Bravo", "Router-Charlie",
            "Router-Delta", "Router-Echo", "Router-Foxtrot",
            "Router-Golf", "Router-Hotel", "Router-India", "Router-Juliet"
        ]
        for i, nombre in enumerate(nombres, 1):
            self.routers[f"192.168.{i}.1"] = {
                "nombre": nombre,
                "ip": f"192.168.{i}.1",
                "estado": "verde",
                "ultimo_cambio": datetime.now().isoformat(),
                "fallos": 0,
                "ultima_falla": None,
                "tecnico_despachado": False
            }
        print(f"[OK] {len(self.routers)} routers inicializados: {list(self.routers.keys())}")

    def verificar_estado(self, ip):
        """Verifica el estado de un router por su IP."""
        if ip in self.routers:
            return self.routers[ip]
        return None

    def atender_cliente(self, ip):
        """
        Atiende al cliente según el estado de su router.
        """
        print(f"[DEBUG] atender_cliente called with ip='{ip}' (type={type(ip).__name__})")
        print(f"[DEBUG] Router keys available: {list(self.routers.keys())}")

        if ip not in self.routers:
            print(f"[WARN] Router NO encontrado para IP '{ip}'")
            return {
                "accion": "no_encontrado",
                "mensaje": f"No se encontró un router con IP {ip} en la red."
            }

        router = self.routers[ip]
        old_state = router["estado"]
        estado = old_state
        nombre = router["nombre"]

        if estado == "naranja":
            router["estado"] = "verde"
            router["ultimo_cambio"] = datetime.now().isoformat()
            router["ultima_falla"] = None
            router["tecnico_despachado"] = False
            self._notify(router, old_state, "verde", "Reinicio automático")
            return {
                "accion": "reiniciado",
                "estado_anterior": "naranja",
                "estado_actual": "verde",
                "router": nombre,
                "ip": ip,
                "mensaje": (
                    f"🔧 **Diagnóstico del router {nombre} (IP: {ip}):**\n\n"
                    f"Se detectó una falla menor (naranja). Se realizó un **reinicio automático** "
                    f"del router para restablecer el servicio.\n\n"
                    f"✅ **Servicio restablecido.** Tu conexión debería funcionar normalmente."
                )
            }

        elif estado == "rojo":
            fecha_tecnico = (datetime.now() + timedelta(days=3)).strftime("%d/%m/%Y")
            router["tecnico_despachado"] = True
            return {
                "accion": "tecnico_despachado",
                "estado": "rojo",
                "router": nombre,
                "ip": ip,
                "fecha_tecnico": fecha_tecnico,
                "mensaje": (
                    f"🚨 **Falla crítica detectada en {nombre} (IP: {ip}).**\n\n"
                    f"Tu router presenta una falla grave que no puede resolverse con un reinicio.\n\n"
                    f"📋 **Se ha despachado un técnico a tu ubicación.**\n"
                    f"📅 **Fecha estimada de atención:** {fecha_tecnico} (3 días hábiles).\n\n"
                    f"Si la falla es urgente, contacta directamente a soporte."
                )
            }

        else:
            router["ultimo_cambio"] = datetime.now().isoformat()
            return {
                "accion": "verificado",
                "estado": "verde",
                "router": nombre,
                "ip": ip,
                "mensaje": (
                    f"✅ **Router {nombre} (IP: {ip}) funcionando correctamente.**\n\n"
                    f"Tu servicio de internet está operativo. No se detectaron fallas."
                )
            }

    def cambiar_estado(self, ip, nuevo_estado, reason="Cambio manual"):
        """Cambia el estado de un router y notifica a los listeners."""
        if ip not in self.routers:
            return None
        router = self.routers[ip]
        old_state = router["estado"]
        if old_state == nuevo_estado:
            return router
        router["estado"] = nuevo_estado
        router["ultimo_cambio"] = datetime.now().isoformat()
        if nuevo_estado == "verde":
            router["ultima_falla"] = None
            router["tecnico_despachado"] = False
        if nuevo_estado != "verde":
            router["fallos"] += 1
            router["ultima_falla"] = datetime.now().isoformat()
        if nuevo_estado == "rojo":
            router["tecnico_despachado"] = True
        self._notify(router, old_state, nuevo_estado, reason)
        return router

    def simular_falla_aleatoria(self):
        """Simula una falla aleatoria en un router verde."""
        disponibles = [ip for ip, r in self.routers.items() if r["estado"] == "verde"]
        if not disponibles:
            return None

        ip = random.choice(disponibles)
        estado = random.choice(["naranja", "rojo"])
        old_state = self.routers[ip]["estado"]
        self.routers[ip]["estado"] = estado
        self.routers[ip]["ultimo_cambio"] = datetime.now().isoformat()
        self.routers[ip]["fallos"] += 1
        self.routers[ip]["ultima_falla"] = datetime.now().isoformat()
        if estado == "rojo":
            self.routers[ip]["tecnico_despachado"] = True

        self._notify(self.routers[ip], old_state, estado, "Falla automática simulada")
        return self.routers[ip]

    def reiniciar_router(self, ip):
        """Reinicia un router manualmente."""
        if ip not in self.routers:
            return None

        router = self.routers[ip]
        old_state = router["estado"]
        if router["estado"] in ("verde", "naranja"):
            router["estado"] = "verde"
            router["ultimo_cambio"] = datetime.now().isoformat()
            router["tecnico_despachado"] = False
            self._notify(router, old_state, "verde", "Reinicio manual")
            return {
                "success": True,
                "mensaje": f"Router {router['nombre']} reiniciado exitosamente.",
                "router": router
            }
        else:
            return {
                "success": False,
                "mensaje": f"Router {router['nombre']} requiere intervención técnica (rojo).",
                "router": router
            }

    def obtener_todos_routers(self):
        """Retorna el estado de todos los routers."""
        return list(self.routers.values())

    def obtener_resumen(self):
        """Retorna un resumen de la red."""
        verde = sum(1 for r in self.routers.values() if r["estado"] == "verde")
        naranja = sum(1 for r in self.routers.values() if r["estado"] == "naranja")
        rojo = sum(1 for r in self.routers.values() if r["estado"] == "rojo")
        total = len(self.routers)
        return {
            "total": total,
            "verde": verde,
            "naranja": naranja,
            "rojo": rojo,
            "disponibilidad": f"{(verde / total * 100):.0f}%"
        }


simulacion = SimulacionRed()
