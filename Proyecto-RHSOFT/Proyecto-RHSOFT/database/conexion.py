import mysql.connector

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            port=3307,
            user="root",
            password="",
            database="rrhh_empresa"
        )
        return conexion
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None