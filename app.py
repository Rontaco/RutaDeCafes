from flask import Flask, render_template, request, redirect, url_for, flash, session
import database

app = Flask(__name__)
app.secret_key = 'clave-secreta-desarrollo'

PASSWORD_ADMIN = '0001'
PASSWORD_REACTIVAR = '0002'

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
    return render_template('index.html', clientes=clientes, texto=texto, ver_inactivos=ver_inactivos)

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

    return render_template('cliente.html', cliente=cliente, historial=historial, progreso=progreso)

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
    