from flask import Flask, render_template, request, redirect, url_for, session
import pyodbc
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Conexión a la base de datos
def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=tu_servidor;'
        'DATABASE=DeanValdivia;'
        'UID=tu_usuario;'
        'PWD=tu_contraseña'
    )
    return conn

@app.route('/dashboard')
def dashboard():
    return "<h1>Bienvenido al Panel de Control</h1><a href='/alumnos'>Ir a Gestión de Alumnos</a>"

@app.route('/alumnos')
def alumnos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            u.id, 
            u.nombre_completo, 
            r.horario, 
            r.horas, 
            r.total_pagar, 
            r.pago_id, 
            r.monto_abonado, 
            r.fecha_pago, 
            r.abonado_acumulado, 
            r.falta_actual
        FROM Usuarios u
        JOIN RegistrosAlumnos r ON u.id = r.alumno_id
        ORDER BY u.nombre_completo
    """)

    alumnos = []
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        alumnos.append(dict(zip(columns, row)))

    conn.close()

    return render_template('alumnos.html', alumnos=alumnos)

@app.route('/alumno/nueva', methods=['GET', 'POST'])
def nueva():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        horario = request.form.get('horario', '').strip()
        horas = request.form.get('horas', '0').strip()

        if not nombre or not horario or not horas.isdigit():
            return render_template('nueva.html', error="Datos inválidos")

        horas = int(horas)

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO Usuarios (nombre_completo, usuario, contraseña) VALUES (?, ?, ?)",
                (nombre, nombre.lower().replace(' ', ''), 'temp123')
            )

            alumno_id = cursor.execute("SELECT SCOPE_IDENTITY()").fetchone()[0]
            total_pagar = horas * 50
            pago_id = f"PAG-{datetime.now().strftime('%Y%m%d')}-{alumno_id:04d}"

            cursor.execute("""
                INSERT INTO RegistrosAlumnos (
                    alumno_id, horario, horas, total_pagar, pago_id,
                    monto_abonado, fecha_pago, abonado_acumulado, falta_actual
                ) VALUES (?, ?, ?, ?, ?, 0, GETDATE(), 0, ?)
            """, (alumno_id, horario, horas, total_pagar, pago_id, total_pagar))

            conn.commit()
            return redirect(url_for('alumnos'))
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error: {str(e)}")
            return render_template('nueva.html', error="Error al registrar alumno")
        finally:
            if conn:
                conn.close()

    return render_template('nueva.html')

@app.route('/alumno/<int:alumno_id>')
def ver(alumno_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                u.id,
                u.nombre_completo, 
                r.horario, 
                r.horas, 
                r.total_pagar, 
                r.pago_id, 
                r.monto_abonado, 
                r.fecha_pago, 
                r.abonado_acumulado, 
                r.falta_actual
            FROM Usuarios u
            JOIN RegistrosAlumnos r ON u.id = r.alumno_id
            WHERE u.id = ?
        """, (alumno_id,))

        alumno = cursor.fetchone()

        if not alumno:
            return redirect(url_for('alumnos'))

        columnas = ['id', 'nombre_completo', 'horario', 'horas', 'total_pagar', 'pago_id', 
                    'monto_abonado', 'fecha_pago', 'abonado_acumulado', 'falta_actual']

        return render_template('ver.html', alumno=dict(zip(columnas, alumno)))
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect(url_for('alumnos'))
    finally:
        if conn:
            conn.close()

@app.route('/alumno/editar/<int:alumno_id>', methods=['GET', 'POST'])
def editar(alumno_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        campo = request.form.get('campo', '').strip()
        nuevo_valor = request.form.get('nuevo_valor', '').strip()

        if not campo or not nuevo_valor:
            return redirect(url_for('ver', alumno_id=alumno_id))

        campos_permitidos = ['nombre_completo', 'horario', 'horas']
        if campo not in campos_permitidos:
            return redirect(url_for('ver', alumno_id=alumno_id))

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            if campo == 'horas':
                if not nuevo_valor.isdigit():
                    return redirect(url_for('ver', alumno_id=alumno_id))

                horas = int(nuevo_valor)
                cursor.execute("""
                    UPDATE RegistrosAlumnos 
                    SET horas = ?, total_pagar = ?, falta_actual = total_pagar - abonado_acumulado 
                    WHERE alumno_id = ?
                """, (horas, horas * 50, alumno_id))
            elif campo == 'horario':
                cursor.execute("""
                    UPDATE RegistrosAlumnos 
                    SET horario = ? 
                    WHERE alumno_id = ?
                """, (nuevo_valor, alumno_id))
            elif campo == 'nombre_completo':
                cursor.execute("""
                    UPDATE Usuarios 
                    SET nombre_completo = ? 
                    WHERE id = ?
                """, (nuevo_valor, alumno_id))

            conn.commit()
            return redirect(url_for('ver', alumno_id=alumno_id))
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error: {str(e)}")
            return redirect(url_for('ver', alumno_id=alumno_id))
        finally:
            if conn:
                conn.close()

    # GET
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                u.id, 
                u.nombre_completo, 
                r.horario, 
                r.horas
            FROM Usuarios u
            JOIN RegistrosAlumnos r ON u.id = r.alumno_id
            WHERE u.id = ?
        """, (alumno_id,))

        alumno = cursor.fetchone()

        if not alumno:
            return redirect(url_for('alumnos'))

        columnas = ['id', 'nombre_completo', 'horario', 'horas']
        return render_template('editar.html', alumno=dict(zip(columnas, alumno)))
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect(url_for('alumnos'))
    finally:
        if conn:
            conn.close()

@app.route('/ver', methods=['GET'])
def ver():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    alumno_id = request.args.get('alumno_id', type=int)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener lista de alumnos para el desplegable
    cursor.execute("SELECT id, nombre_completo FROM Usuarios ORDER BY nombre_completo")
    lista_alumnos = [dict(id=row[0], nombre_completo=row[1]) for row in cursor.fetchall()]

    alumno = None
    if alumno_id:
        cursor.execute("""
            SELECT 
                u.id, u.nombre_completo, r.horario, r.horas, r.total_pagar,
                r.pago_id, r.monto_abonado, r.fecha_pago, r.abonado_acumulado, r.falta_actual
            FROM Usuarios u
            JOIN RegistrosAlumnos r ON u.id = r.alumno_id
            WHERE u.id = ?
        """, (alumno_id,))
        row = cursor.fetchone()
        if row:
            columnas = ['id', 'nombre_completo', 'horario', 'horas', 'total_pagar',
                        'pago_id', 'monto_abonado', 'fecha_pago', 'abonado_acumulado', 'falta_actual']
            alumno = dict(zip(columnas, row))

    conn.close()
    return render_template('ver.html', lista_alumnos=lista_alumnos, alumno=alumno)

if __name__ == '_main_':
    app.run(debug=True)