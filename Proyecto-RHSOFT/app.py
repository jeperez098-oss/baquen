from flask import Flask, request, render_template, redirect, url_for
# Importamos la variable 'conexion' desde la carpeta 'database'
from database.conexion import conexion 

app = Flask(__name__)

@app.route('/validar-login', methods=['POST'])
def validar_login():
    usuario = request.form['usuario']
    password = request.form['password']
    
    cursor = conexion.cursor()
    
    sql = """
    SELECT * FROM usuarios
    WHERE usuario = %s
    AND password = %s
    """
    
    valores = (usuario, password)
    
    cursor.execute(sql, valores)
    
    resultado = cursor.fetchone()
    
    if resultado:
        return "LOGIN CORRECTO"
    else:
        return "USUARIO INCORRECTO"

# EJECUTAR SERVIDOR FLASK (Asegúrate de los dobles __)

    app.run(debug=True)