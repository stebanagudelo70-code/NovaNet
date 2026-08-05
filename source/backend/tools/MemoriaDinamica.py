import time
import threading
from collections import OrderedDict


class MemoriaDinamica:
    def __init__(self, ttl=300, max_historial=20):
        self.ttl = ttl
        self.max_historial = max_historial
        self._sesiones = OrderedDict()
        self._lock = threading.Lock()
        self._limpiador_activo = False

    def registrar_turno(self, session_id, rol, contenido):
        with self._lock:
            if session_id not in self._sesiones:
                self._sesiones[session_id] = {
                    "historial": [],
                    "ultimo_acceso": time.time(),
                    "datos": {}
                }

            sesion = self._sesiones[session_id]
            sesion["ultimo_acceso"] = time.time()
            sesion["historial"].append({
                "role": rol,
                "content": contenido
            })

            if len(sesion["historial"]) > self.max_historial:
                sesion["historial"] = sesion["historial"][-self.max_historial:]

            self._mover_al_final(session_id)

        self._iniciar_limpieza_si_necesario()

    def obtener_historial(self, session_id):
        with self._lock:
            sesion = self._sesiones.get(session_id)
            if not sesion:
                return []

            if time.time() - sesion["ultimo_acceso"] > self.ttl:
                self._sesiones.pop(session_id, None)
                print(f"[MEMORIA] Sesión {session_id} expirada (TTL {self.ttl}s)")
                return []

            sesion["ultimo_acceso"] = time.time()
            return list(sesion["historial"])

    def guardar_dato(self, session_id, clave, valor):
        with self._lock:
            if session_id not in self._sesiones:
                self._sesiones[session_id] = {
                    "historial": [],
                    "ultimo_acceso": time.time(),
                    "datos": {}
                }

            sesion = self._sesiones[session_id]
            sesion["ultimo_acceso"] = time.time()
            sesion["datos"][clave] = valor

    def obtener_dato(self, session_id, clave, defecto=None):
        with self._lock:
            sesion = self._sesiones.get(session_id)
            if not sesion:
                return defecto

            if time.time() - sesion["ultimo_acceso"] > self.ttl:
                self._sesiones.pop(session_id, None)
                return defecto

            return sesion["datos"].get(clave, defecto)

    def obtener_resumen_contexto(self, session_id):
        historial = self.obtener_historial(session_id)
        if not historial:
            return ""

        lineas = []
        for turno in historial:
            if turno["role"] == "user":
                lineas.append(f"Cliente: {turno['content']}")
            else:
                lineas.append(f"Agente: {turno['content']}")

        return "\n".join(lineas)

    def esta_vacia(self, session_id):
        with self._lock:
            sesion = self._sesiones.get(session_id)
            if not sesion:
                return True
            if time.time() - sesion["ultimo_acceso"] > self.ttl:
                self._sesiones.pop(session_id, None)
                return True
            return len(sesion["historial"]) == 0

    def limpiar_sesion(self, session_id):
        with self._lock:
            self._sesiones.pop(session_id, None)

    def total_sesiones_activas(self):
        ahora = time.time()
        with self._lock:
            activas = 0
            for sid, sesion in list(self._sesiones.items()):
                if ahora - sesion["ultimo_acceso"] <= self.ttl:
                    activas += 1
                else:
                    self._sesiones.pop(sid, None)
            return activas

    def _mover_al_final(self, session_id):
        if session_id in self._sesiones:
            self._sesiones.move_to_end(session_id)

    def _iniciar_limpieza_si_necesario(self):
        if self._limpiador_activo:
            return
        self._limpiador_activo = True
        threading.Thread(target=self._ciclo_limpieza, daemon=True).start()

    def _ciclo_limpieza(self):
        time.sleep(60)
        self._limpiar_expiradas()
        self._limpiador_activo = False

    def _limpiar_expiradas(self):
        ahora = time.time()
        with self._lock:
            expiradas = [
                sid for sid, sesion in self._sesiones.items()
                if ahora - sesion["ultimo_acceso"] > self.ttl
            ]
            for sid in expiradas:
                self._sesiones.pop(sid, None)
                print(f"[MEMORIA] Sesión {sid} limpiada (expirada)")

            if expiradas:
                print(f"[MEMORIA] {len(expiradas)} sesiones limpiadas. "
                      f"Activas: {len(self._sesiones)}")


memoria = MemoriaDinamica(ttl=300, max_historial=20)
