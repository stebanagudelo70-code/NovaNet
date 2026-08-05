import os
import importlib

DB_DISPONIBLE = False
clientes_mock = {}
pagos_mock = []
reportes_mock = []
contador_id = 1

_db_module = None
_RealDictCursor = None

for mod_name in ['psycopg2', 'pg8000']:
    try:
        mod = importlib.import_module(mod_name)
        _db_module = mod
        if mod_name == 'psycopg2':
            from psycopg2.extras import RealDictCursor as _RDF
            _RealDictCursor = _RDF
        break
    except ImportError:
        continue


def get_db_connection():
    if not _db_module:
        return None
    try:
        host = os.getenv('DB_HOST', 'localhost')
        dbname = os.getenv('DB_NAME', 'clientes_internet')
        user = os.getenv('DB_USER', 'postgres')
        # La contraseña se lee del archivo config/.env (DB_PASSWORD).
        # No se incluye ningún valor real en el código.
        password = os.getenv('DB_PASSWORD', '')
        port = int(os.getenv('DB_PORT', '5432'))

        if _db_module.__name__ == 'psycopg2':
            conn = _db_module.connect(
                host=host, dbname=dbname, user=user,
                password=password, port=port,
                cursor_factory=_RealDictCursor,
                options='-c client_encoding=latin1'
            )
        else:
            conn = _db_module.connect(
                host=host, database=dbname, user=user,
                password=password, port=port
            )
        return conn
    except Exception as e:
        print(f"[!] PostgreSQL no disponible: {e}")
        return None


COLUMN_ALIASES = {
    "ip_cliente": "ip",
    "ip_address": "ip",
    "ip_del_router": "ip",
    "direccion_ip": "ip",
    "ip_asignada": "ip",
    "router_asignado": "router",
    "router_name": "router",
    "nombre_router": "router",
    "tipo_plan": "plan",
    "plan_nombre": "plan",
    "estado_servicio": "estado",
    "servicio_estado": "estado",
}


def _normalizar_cliente(row_dict):
    normalized = {}
    for key, value in row_dict.items():
        normalized_key = COLUMN_ALIASES.get(key, key)
        if hasattr(value, '__str__') and type(value).__name__ == 'IPv4Address':
            value = str(value)
        normalized[normalized_key] = value
    return normalized


def _cargar_datos_mock():
    global clientes_mock
    clientes_mock = {
        "10101010": {
            "id": 1, "cedula": "10101010", "nombre": "Carlos Rodriguez",
            "email": "carlos@email.com", "telefono": "3101234567",
            "direccion": "Calle 10 #5-20", "plan": "Premium",
            "ip": "192.168.1.1", "router": "Router-Alpha",
            "estado": "activo"
        },
        "20202020": {
            "id": 2, "cedula": "20202020", "nombre": "Maria Garcia",
            "email": "maria@email.com", "telefono": "3209876543",
            "direccion": "Av 15 #30-10", "plan": "Basico",
            "ip": "192.168.2.1", "router": "Router-Bravo",
            "estado": "activo"
        },
        "30303030": {
            "id": 3, "cedula": "30303030", "nombre": "Pedro Lopez",
            "email": "pedro@email.com", "telefono": "3155551234",
            "direccion": "Cra 7 #45-60", "plan": "Business",
            "ip": "192.168.3.1", "router": "Router-Charlie",
            "estado": "activo"
        }
    }


def init_db():
    global DB_DISPONIBLE

    _cargar_datos_mock()
    print("[OK] Datos mock cargados como fallback")

    conn = get_db_connection()
    if not conn:
        print("⚠️ Modo sin PostgreSQL - Usando datos de prueba")
        DB_DISPONIBLE = False
        return True

    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM clientes")
        row = cur.fetchone()
        count = row[0] if _db_module.__name__ == 'pg8000' else row['count']
        DB_DISPONIBLE = True
        print(f"[OK] PostgreSQL conectada - {count} clientes en la base de datos")
        return True
    except Exception as e:
        print(f"[!] Error al verificar base de datos: {e}")
        DB_DISPONIBLE = False
        return False
    finally:
        conn.close()


def buscar_cliente_por_cedula(cedula):
    global clientes_mock
    if DB_DISPONIBLE:
        conn = get_db_connection()
        if not conn:
            return clientes_mock.get(cedula)
        try:
            cur = conn.cursor()
            if _db_module.__name__ == 'pg8000':
                cur.execute("SELECT * FROM clientes WHERE cedula = $1", (cedula,))
            else:
                cur.execute("SELECT * FROM clientes WHERE cedula = %s", (cedula,))
            row = cur.fetchone()
            if not row:
                return None
            if _db_module.__name__ == 'pg8000':
                cols = [d[0] for d in cur.description]
                raw = dict(zip(cols, row))
            else:
                raw = dict(row)
            normalized = _normalizar_cliente(raw)
            print(f"[DEBUG] Cliente DB raw keys: {list(raw.keys())} -> normalized: {list(normalized.keys())}")
            return normalized
        except Exception as e:
            print(f"Error: {e}")
            return clientes_mock.get(cedula)
        finally:
            conn.close()
    else:
        return clientes_mock.get(cedula)


def registrar_pago(cliente_id, monto, metodo_pago, referencia=None):
    global pagos_mock, contador_id
    if DB_DISPONIBLE:
        conn = get_db_connection()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            if _db_module.__name__ == 'pg8000':
                cur.execute("""
                    INSERT INTO pagos (cliente_id, monto, metodo_pago, referencia, estado)
                    VALUES ($1, $2, $3, $4, 'completado')
                    RETURNING id
                """, (cliente_id, monto, metodo_pago, referencia))
            else:
                cur.execute("""
                    INSERT INTO pagos (cliente_id, monto, metodo_pago, referencia, estado)
                    VALUES (%s, %s, %s, %s, 'completado')
                    RETURNING id
                """, (cliente_id, monto, metodo_pago, referencia))
            row = cur.fetchone()
            pago_id = row[0] if _db_module.__name__ == 'pg8000' else row['id']
            conn.commit()
            return pago_id
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    else:
        contador_id += 1
        pagos_mock.append({
            "id": contador_id, "cliente_id": cliente_id,
            "monto": monto, "metodo_pago": metodo_pago,
            "referencia": referencia, "estado": "completado"
        })
        return contador_id


def registrar_reporte_falla(cliente_id, descripcion):
    global reportes_mock, contador_id
    if DB_DISPONIBLE:
        conn = get_db_connection()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            if _db_module.__name__ == 'pg8000':
                cur.execute("""
                    INSERT INTO reportes_falla (cliente_id, descripcion)
                    VALUES ($1, $2)
                    RETURNING id
                """, (cliente_id, descripcion))
            else:
                cur.execute("""
                    INSERT INTO reportes_falla (cliente_id, descripcion)
                    VALUES (%s, %s)
                    RETURNING id
                """, (cliente_id, descripcion))
            row = cur.fetchone()
            reporte_id = row[0] if _db_module.__name__ == 'pg8000' else row['id']
            conn.commit()
            return reporte_id
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    else:
        contador_id += 1
        reportes_mock.append({
            "id": contador_id, "cliente_id": cliente_id,
            "descripcion": descripcion, "estado": "abierto"
        })
        return contador_id
