import mysql.connector

conexion = mysql.connector.connect(
    host="localhost",
    port=3307,
    user="root",       # <-- Asegúrate de que termine en 't' y NO en 'n'
    password="",       # <-- Vacío, justo como me dijiste
    database="rrhh_empresa"
)

print("Conexion exitosa")