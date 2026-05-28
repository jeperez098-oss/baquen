from flask import Flask, render_template, request, redirect, url_for, session, flash
from database.conexion import obtener_conexion
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta_rhsoft_cobalsa'

# 1. RUTA: Raíz - Login
@app.route('/')
def login():
    return render_template('login.html')

# 2. RUTA: Procesar e identificar usuario y rol
@app.route('/validar-login', methods=['POST'])
def validar_login():
    usuario_input = request.form['usuario']
    password_input = request.form['password']
    
    conexion = obtener_conexion()
    if not conexion:
        return "Error en el servidor de base de datos.", 500
        
    cursor = conexion.cursor(dictionary=True)
    # Buscamos en tu tabla original 'usuarios'
    query = "SELECT id_usuario, usuario, password, rol, id_empleado FROM usuarios WHERE usuario = %s AND password = %s"
    cursor.execute(query, (usuario_input, password_input))
    cuenta = cursor.fetchone()
    
    if cuenta:
        session['logueado'] = True
        session['id_usuario'] = cuenta['id_usuario']
        session['usuario'] = cuenta['usuario']
        session['rol'] = cuenta['rol']
        session['id_empleado'] = cuenta['id_empleado']
        
        # Si tiene un empleado asociado, extraemos su nombre real
        if cuenta['id_empleado']:
            cursor.execute("""
                SELECT p.Nombres, p.Apellidos FROM empleados e 
                JOIN personas p ON e.ID_Persona = p.ID_Persona 
                WHERE e.ID_Empleado = %s
            """, (cuenta['id_empleado'],))
            persona = cursor.fetchone()
            if persona:
                session['nombre_completo'] = f"{persona['Nombres']} {persona['Apellidos']}"
        else:
            session['nombre_completo'] = "Administrador General"
            
        cursor.close()
        conexion.close()
        
        # Redirección obligatoria a la pantalla intermedia de selección
        return redirect(url_for('seleccion'))
    else:
        cursor.close()
        conexion.close()
        return "<h3>Usuario o contraseña incorrectos.</h3> <a href='/'>Volver a intentar</a>"

# 3. RUTA: Selección de Módulo Intermedio
@app.route('/seleccion')
def seleccion():
    if 'logueado' not in session:
        return redirect(url_for('login'))
    return render_template('seleccion.html')

# 4. RUTA: Panel del Administrador (Muestra y Registra Empleados)
@app.route('/menu-admin', methods=['GET', 'POST'])
def menu_admin():
    if 'logueado' not in session or session['rol'] != 'Administrador':
        return redirect(url_for('login'))
        
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    
    # PROCESAR FORMULARIO DE NUEVO EMPLEADO
    if request.method == 'POST':
        doc = request.form['documento']
        nom = request.form['nombres']
        ape = request.form['apellidos']
        eml = request.form['email']
        tel = request.form['telefono']
        f_nac = request.form['fecha_nacimiento']
        id_cargo = request.form['cargo']
        f_ing = request.form['fecha_ingreso']
        
        try:
            # Insertar en tabla personas
            sql_p = "INSERT INTO personas (Numero_Documento, Nombres, Apellidos, Email, Telefono, Fecha_Nacimiento) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql_p, (doc, nom, ape, eml, tel, f_nac))
            id_persona_nuevo = cursor.lastrowid
            
            # Insertar en tabla empleados
            sql_e = "INSERT INTO empleados (ID_Persona, ID_Cargo, Fecha_Ingreso, Estado_Empleado) VALUES (%s, %s, %s, 'Activo')"
            cursor.execute(sql_e, (id_persona_nuevo, id_cargo, f_ing))
            
            conexion.commit()
            flash("Empleado registrado exitosamente.")
        except Exception as e:
            conexion.rollback()
            return f"Error en la transacción SQL: {e}"

    # LISTAR EMPLEADOS EN LA TABLA
    query_lista = """
        SELECT e.ID_Empleado, p.Nombres, p.Apellidos, c.Nombre_Cargo, d.Nombre_Departamento 
        FROM empleados e
        JOIN personas p ON e.ID_Persona = p.ID_Persona
        JOIN cargos c ON e.ID_Cargo = c.ID_Cargo
        JOIN departamentos d ON c.ID_Departamento = d.ID_Departamento
    """
    cursor.execute(query_lista)
    empleados_activos = cursor.fetchall()
    
    # Listar cargos para el menú dinámico <select>
    cursor.execute("SELECT ID_Cargo, Nombre_Cargo FROM cargos")
    cargos_disponibles = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    return render_template('menu_administrador.html', empleados=empleados_activos, cargos=cargos_disponibles)

# 5. RUTA: Menú Principal del Empleado (Asistencia y Accidentes)
@app.route('/menu-empleado', methods=['GET', 'POST'])
def menu_empleado():
    if 'logueado' not in session:
        return redirect(url_for('login'))
        
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    id_emp = session['id_empleado']
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        # SUB-PROCESO A: MARCAR ASISTENCIA
        if accion == 'asistencia':
            hora_actual = datetime.now().strftime('%H:%M:%S')
            tipo_marcado = request.form.get('tipo_marcado') # 'Entrada' o 'Salida'
            
            if tipo_marcado == 'Entrada':
                sql_asist = "INSERT INTO asistencia (ID_Empleado, Fecha, Hora_Entrada, Estado_Asistencia) VALUES (%s, %s, %s, 'A tiempo')"
                cursor.execute(sql_asist, (id_emp, fecha_hoy, hora_actual))
            else:
                sql_asist = "UPDATE asistencia SET Hora_Salida = %s WHERE ID_Empleado = %s AND Fecha = %s"
                cursor.execute(sql_asist, (hora_actual, id_emp, fecha_hoy))
            conexion.commit()
            
        # SUB-PROCESO B: REGISTRAR REPORTE SST
        elif accion == 'sst':
            t_acc = request.form['tipo_accidente']
            desc = request.form['descripcion']
            acc_inm = request.form['accion_inmediata']
            
            sql_sst = "INSERT INTO sst_accidentes (ID_Empleado, Fecha_Accidente, Tipo_Accidente, Descripcion, Accion_Inmediata, Fecha_Reporte) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql_sst, (id_emp, fecha_hoy, t_acc, desc, acc_inm, fecha_hoy))
            conexion.commit()
            
    # Traer historial de asistencia del empleado logueado
    cursor.execute("SELECT Fecha, Hora_Entrada, Hora_Salida, Estado_Asistencia FROM asistencia WHERE ID_Empleado = %s", (id_emp,))
    historial_asistencia = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    return render_template('menu_empleado.html', asistencia=historial_asistencia)

# 6. RUTA: Ver Ficha Detallada del Perfil
@app.route('/perfil')
def perfil():
    if 'logueado' not in session or not session['id_empleado']:
        return redirect(url_for('login'))
        
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    
    query_perfil = """
        SELECT p.Numero_Documento, p.Nombres, p.Apellidos, p.Email, p.Telefono, p.Fecha_Nacimiento,
               c.Nombre_Cargo, c.Salario_Base, c.Hora_Inicio_Jornada, c.Hora_Fin_Jornada, e.Fecha_Ingreso
        FROM empleados e
        JOIN personas p ON e.ID_Persona = p.ID_Persona
        JOIN cargos c ON e.ID_Cargo = c.ID_Cargo
        WHERE e.ID_Empleado = %s
    """
    cursor.execute(query_perfil, (session['id_empleado'],))
    datos_personales = cursor.fetchone()
    
    cursor.close()
    conexion.close()
    return render_template('perfil.html', perfil=datos_personales)

# 7. RUTA: Desconexión total del entorno
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)