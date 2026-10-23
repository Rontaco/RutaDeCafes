from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import database

app = Flask(__name__)
app.secret_key = 'clave-secreta-desarrollo'

PASSWORD_ADMIN = '0001'
PASSWORD_REACTIVAR = '0002'

def formato_gmt3(valor):
    """Convierte una fecha guardada en UTC (como la guarda SQLite) a GMT-3 para mostrar en pantalla."""
    try:
        fecha_utc = datetime.strptime(valor, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return valor
    fecha_local = fecha_utc - timedelta(hours=3)
    return fecha_local.strftime('%d/%m/%Y %H:%M')

app.jinja_env.filters['gmt3'] = formato_gmt3

@app.route('/verificar-clave', methods=['GET', 'POST'])
def verificar_clave():
    destino = request.values.get('next') or url_for('index')

    if request.method == 'POST':
        clave = request.form.get('clave', '')
        if clave == PASSWORD_ADMIN:
            session['autenticado'] = True
            return redirect(destino)
        else:
            flash('Contraseña incorrecta.')

    return render_template('verificar_clave.html', destino=destino)

@app.route('/')
def index():
    texto = request.args.get('q', '').strip()
    ver_inactivos = request.args.get('estado') == 'inactivos'
    clientes = database.buscar_clientes(texto, activo=not ver_inactivos)
    proximas = database.obtener_proximos_a_cortesia(10)
    top_cortesias = database.obtener_top_cortesias(10)
    return render_template('index.html', clientes=clientes, texto=texto, ver_inactivos=ver_inactivos, proximas=proximas, top_cortesias=top_cortesias)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
def nuevo_cliente():
    if request.method == 'POST':
        dni = request.form.get('dni', '').strip()
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        email = request.form.get('email', '').strip() or None
        fecha_nacimiento = request.form.get('fecha_nacimiento', '').strip() or None

        if not dni or not nombre or not apellido:
            flash('DNI, nombre y apellido son obligatorios.')
            return render_template('nuevo_cliente.html')

        ok, error = database.crear_cliente(dni, nombre, apellido, email, fecha_nacimiento)

        if ok:
            flash(f'Cliente {nombre} {apellido} registrado correctamente.')
            return redirect(url_for('index'))
        else:
            flash(error)
            return render_template('nuevo_cliente.html')

    return render_template('nuevo_cliente.html')

@app.route('/clientes/<int:cliente_id>')
def ver_cliente(cliente_id):
    cliente = database.obtener_cliente(cliente_id)
    if cliente is None:
        flash('Cliente no encontrado.')
        return redirect(url_for('index'))

    historial = database.obtener_historial_compras(cliente_id)
    progreso = database.calcular_progreso(cliente_id)
    eliminadas = database.obtener_progreso_eliminado(cliente_id)

    return render_template('cliente.html', cliente=cliente, historial=historial, progreso=progreso, eliminadas=eliminadas)

@app.route('/clientes/<int:cliente_id>/editar', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    cliente = database.obtener_cliente(cliente_id)
    if cliente is None:
        flash('Cliente no encontrado.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        clave = request.form.get('clave', '')
        if clave != PASSWORD_ADMIN:
            flash('Contraseña incorrecta.')
            return render_template('editar_cliente.html', cliente=cliente)

        dni = request.form.get('dni', '').strip()
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        email = request.form.get('email', '').strip() or None
        fecha_nacimiento = request.form.get('fecha_nacimiento', '').strip() or None

        if not dni or not nombre or not apellido:
            flash('DNI, nombre y apellido son obligatorios.')
            return render_template('editar_cliente.html', cliente=cliente)

        ok, error = database.actualizar_cliente(cliente_id, dni, nombre, apellido, email, fecha_nacimiento)

        if ok:
            flash('Datos actualizados correctamente.')
            return redirect(url_for('ver_cliente', cliente_id=cliente_id))
        else:
            flash(error)
            return render_template('editar_cliente.html', cliente=cliente)

    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/clientes/<int:cliente_id>/dar-de-baja', methods=['GET', 'POST'])
def dar_de_baja(cliente_id):
    cliente = database.obtener_cliente(cliente_id)
    if cliente is None:
        flash('Cliente no encontrado.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        clave = request.form.get('clave', '')
        if clave != PASSWORD_ADMIN:
            flash('Contraseña incorrecta.')
            return render_template('confirmar_baja.html', cliente=cliente)

        database.dar_de_baja(cliente_id)
        flash(f"Cliente {cliente['nombre']} {cliente['apellido']} dado de baja.")
        return redirect(url_for('ver_cliente', cliente_id=cliente_id))

    return render_template('confirmar_baja.html', cliente=cliente)

@app.route('/clientes/<int:cliente_id>/reactivar', methods=['GET', 'POST'])
def reactivar_cliente(cliente_id):
    cliente = database.obtener_cliente(cliente_id)
    if cliente is None:
        flash('Cliente no encontrado.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        clave = request.form.get('clave', '')
        if clave != PASSWORD_REACTIVAR:
            flash('Contraseña incorrecta.')
            return render_template('confirmar_reactivar.html', cliente=cliente)

        database.reactivar_cliente(cliente_id)
        flash(f"Cliente {cliente['nombre']} {cliente['apellido']} reactivado.")
        return redirect(url_for('ver_cliente', cliente_id=cliente_id))

    return render_template('confirmar_reactivar.html', cliente=cliente)

@app.route('/clientes/<int:cliente_id>/comprar', methods=['POST'])
def registrar_compra(cliente_id):
    cliente = database.obtener_cliente(cliente_id)
    if cliente is None:
        flash('Cliente no encontrado.')
        return redirect(url_for('index'))

    es_cortesia = database.registrar_compra(cliente_id)

    if es_cortesia:
        flash('¡Café de cortesía entregado! El ciclo se reinicia.')
    else:
        flash('Compra registrada correctamente.')

    return redirect(url_for('ver_cliente', cliente_id=cliente_id))

@app.route('/clientes/<int:cliente_id>/compras/<int:compra_id>/eliminar', methods=['GET', 'POST'])
def eliminar_compra(cliente_id, compra_id):
    cliente = database.obtener_cliente(cliente_id)
    if cliente is None:
        flash('Cliente no encontrado.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        motivo = request.form.get('motivo', '').strip()
        if not motivo:
            flash('Tenés que indicar un motivo para eliminar este punto del progreso.')
            return render_template('eliminar_compra.html', cliente=cliente, compra_id=compra_id)

        ok = database.eliminar_compra_progreso(compra_id, cliente_id, motivo)
        if ok:
            flash('El punto se eliminó del progreso correctamente.')
        else:
            flash('No se pudo eliminar: la compra no existe, ya fue eliminada, o es una cortesía (las cortesías no se pueden eliminar desde acá).')
        return redirect(url_for('ver_cliente', cliente_id=cliente_id))

    return render_template('eliminar_compra.html', cliente=cliente, compra_id=compra_id)

if __name__ == '__main__':
    app.run(debug=True, port=5001)