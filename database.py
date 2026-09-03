import sqlite3

DATABASE = 'ruta_cafes.db'

def get_connection():
    """Abre una conexión a la base de datos."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # nos permite acceder a las columnas por nombre
    return conn

def init_db():
    """Crea las tablas ejecutando el script schema.sql."""
    conn = get_connection()
    with open('schema.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")

if __name__ == '__main__':
    init_db()
def crear_cliente(dni, nombre, apellido, email, edad):
    """
    Inserta un nuevo cliente en la base de datos.
    Devuelve (True, None) si se creó correctamente,
    o (False, mensaje_error) si hubo un problema (ej: DNI duplicado).
    """
    conn = get_connection()
    try:
        conn.execute(
            '''INSERT INTO clientes (dni, nombre, apellido, email, edad)
               VALUES (?, ?, ?, ?, ?)''',
            (dni, nombre, apellido, email, edad)
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Ya existe un cliente registrado con ese DNI."
    finally:
        conn.close()    
def buscar_clientes(texto=''):
    """
    Busca clientes activos cuyo DNI, nombre o apellido contengan el texto dado.
    Si texto está vacío, devuelve todos los clientes activos.
    """
    conn = get_connection()
    patron = f'%{texto}%'
    filas = conn.execute(
        '''SELECT id, dni, nombre, apellido, email, edad
           FROM clientes
           WHERE activo = 1
             AND (dni LIKE ? OR nombre LIKE ? OR apellido LIKE ?)
           ORDER BY apellido, nombre''',
        (patron, patron, patron)
    ).fetchall()
    conn.close()
    return filas
def obtener_cliente(cliente_id):
    """Devuelve una fila con los datos del cliente, o None si no existe."""
    conn = get_connection()
    fila = conn.execute(
        'SELECT * FROM clientes WHERE id = ?', (cliente_id,)
    ).fetchone()
    conn.close()
    return fila

def obtener_historial_compras(cliente_id):
    """Devuelve todas las compras de un cliente, más recientes primero."""
    conn = get_connection()
    filas = conn.execute(
        '''SELECT id, fecha, es_cortesia FROM compras
           WHERE cliente_id = ? ORDER BY fecha DESC''',
        (cliente_id,)
    ).fetchall()
    conn.close()
    return filas

def calcular_progreso(cliente_id):
    """
    Calcula el progreso del cliente hacia la próxima cortesía,
    a partir del historial de compras (no de un contador guardado).
    """
    conn = get_connection()
    compras_pagas = conn.execute(
        'SELECT COUNT(*) FROM compras WHERE cliente_id = ? AND es_cortesia = 0',
        (cliente_id,)
    ).fetchone()[0]
    cortesias_entregadas = conn.execute(
        'SELECT COUNT(*) FROM compras WHERE cliente_id = ? AND es_cortesia = 1',
        (cliente_id,)
    ).fetchone()[0]
    conn.close()

    # Compras pagas acumuladas DESDE la última cortesía entregada
    progreso_actual = compras_pagas - (cortesias_entregadas * 5)
    corresponde_cortesia = progreso_actual > 0 and progreso_actual % 5 == 0

    display = 5 if corresponde_cortesia else progreso_actual

    return {
        'compras_pagas': compras_pagas,
        'progreso_actual': progreso_actual,
        'corresponde_cortesia': corresponde_cortesia,
        'display': display
    }

def registrar_compra(cliente_id):
    """
    Registra una nueva compra para el cliente.
    Decide automáticamente si es cortesía según el progreso actual.
    """
    progreso = calcular_progreso(cliente_id)
    es_cortesia = progreso['corresponde_cortesia']

    conn = get_connection()
    conn.execute(
        'INSERT INTO compras (cliente_id, es_cortesia) VALUES (?, ?)',
        (cliente_id, es_cortesia)
    )
    conn.commit()
    conn.close()

    return es_cortesia

def actualizar_cliente(cliente_id, dni, nombre, apellido, email, edad):
    """
    Actualiza los datos de un cliente existente.
    Devuelve (True, None) si se actualizó correctamente,
    o (False, mensaje_error) si hubo un problema (ej: DNI duplicado).
    """
    conn = get_connection()
    try:
        conn.execute(
            '''UPDATE clientes
               SET dni = ?, nombre = ?, apellido = ?, email = ?, edad = ?
               WHERE id = ?''',
            (dni, nombre, apellido, email, edad, cliente_id)
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Ya existe otro cliente registrado con ese DNI."
    finally:
        conn.close()

def dar_de_baja(cliente_id):
    """Realiza la baja lógica de un cliente (activo = 0)."""
    conn = get_connection()
    conn.execute('UPDATE clientes SET activo = 0 WHERE id = ?', (cliente_id,))
    conn.commit()
    conn.close()

def reactivar_cliente(cliente_id):
    """Reactiva a un cliente que estaba dado de baja (activo = 1)."""
    conn = get_connection()
    conn.execute('UPDATE clientes SET activo = 1 WHERE id = ?', (cliente_id,))
    conn.commit()
    conn.close()