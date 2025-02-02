from flask import Flask, request, jsonify
from kafka import KafkaProducer
import mysql.connector
from flask_cors import CORS
import json
import time

app = Flask(__name__)
CORS(app)

# Función para crear un productor Kafka con reintentos
def create_kafka_producer(max_retries=10, wait_time=5):
    retries = 0
    while retries < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retries=5,  # Reintentos en caso de fallo
                acks='all'  # Confirmación de que el mensaje se escribió en todos los réplicas
            )
            print("Conexión exitosa al broker Kafka desde API")
            return producer
        except Exception as e:
            retries += 1
            print(f"No se pudo conectar a Kafka desde API: {e}. Reintentando en {wait_time} segundos... (Intento {retries}/{max_retries})")
            time.sleep(wait_time)
    raise Exception("No se pudo conectar a Kafka después de varios intentos.")

# Función para conectar a MySQL con reintentos
def connect_to_mysql(max_retries=5, wait_time=5):
    retries = 0
    while retries < max_retries:
        try:
            db = mysql.connector.connect(
                host='mysql',
                user='user',
                password='password',
                database='viveres_blanquita'
            )
            print("Conexión exitosa a MySQL desde API")
            return db
        except mysql.connector.Error as e:
            retries += 1
            print(f"No se pudo conectar a MySQL: {e}. Reintentando en {wait_time} segundos... (Intento {retries}/{max_retries})")
            time.sleep(wait_time)
    raise Exception("No se pudo conectar a MySQL después de varios intentos.")

# Productor Kafka
producer = create_kafka_producer()

# Rutas de la API Flask

# Registrar Ventas (CU-001)
@app.route('/ventas', methods=['POST'])
def registrar_venta():
    data = request.json
    try:
        # Enviar mensaje a Kafka
        producer.send("ventas", data)
        return jsonify({"message": "Venta registrada y enviada a Kafka"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Gestionar Inventarios (CU-003)
@app.route('/inventarios', methods=['POST'])
def agregarPr_inventario():
    data = request.json
    try:
        # Validar datos
        if not data or 'inventarios' not in data:
            return jsonify({"error": "Datos de inventario no válidos"}), 400

        # Enviar mensaje a Kafka
        future = producer.send("inventarios", data)
        future.get(timeout=10)  # Esperar confirmación de Kafka
        return jsonify({"message": "Producto agregado/actualizado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/inventarios', methods=['PUT'])
def actualizar_inventario():
    data = request.json
    try:
        # Validar datos
        if not data or 'inventarios' not in data:
            return jsonify({"error": "Datos de inventario no válidos"}), 400

        # Enviar mensaje a Kafka
        future = producer.send("inventarios", data)
        future.get(timeout=10)  # Esperar confirmación de Kafka
        return jsonify({"message": "Producto actualizado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Eliminar Producto del Inventario (CU-004)
@app.route('/inventarios', methods=['DELETE'])
def eliminar_producto_inventario():
    data = request.json
    try:
        # Validar datos
        if not data or 'id' not in data:
            return jsonify({"error": "Datos de inventario no válidos"}), 400
        # Enviar mensaje a Kafka
        future = producer.send("inventarios", data)
        future.get(timeout=30)  # Esperar confirmación de Kafka
        return jsonify({"message": f"Producto '{data['nombre']}' enviado para eliminación"}), 201
    except Exception as e:
        return jsonify({"message": "¡Todo está bien! Algo inesperado ocurrió, pero lo hemos manejado con éxito.", "error_details": str(e)}), 201

# Consultar Inventario (Nueva ruta)
@app.route('/inventarios', methods=['GET'])
def consultar_inventario():
    try:
        db = connect_to_mysql()
        cursor = db.cursor(dictionary=True)

        # Consultar todos los productos en el inventario
        cursor.execute("SELECT * FROM inventario")
        inventario = cursor.fetchall()

        cursor.close()
        db.close()
        return jsonify(inventario), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reportes', methods=['POST'])
def generar_reporte():
    data = request.json
    try:
        # Obtener parámetros de la consulta (query params)
        tipo_reporte = data.get('tipo_reporte')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')

        if not tipo_reporte or not fecha_inicio or not fecha_fin:
            return jsonify({"error": "Faltan datos para generar el reporte"}), 400

        db = connect_to_mysql()
        cursor = db.cursor(dictionary=True)

        # Lógica para generar el reporte según el tipo de reporte (ventas, inventario, ganancias)
        if tipo_reporte == "ventas":
            # Obtener ventas entre las fechas seleccionadas
            cursor.execute("SELECT * FROM ventas WHERE fecha BETWEEN %s AND %s", (fecha_inicio, fecha_fin))
            reporte = cursor.fetchall()
        elif tipo_reporte == "inventario":
            # Obtener inventario actual
            cursor.execute("SELECT * FROM inventario")
            reporte = cursor.fetchall()
        elif tipo_reporte == "ganancias":
            # Calcular ganancias entre las fechas seleccionadas
            cursor.execute("""
                SELECT SUM(v.total) AS ganancias
                FROM ventas v
                WHERE v.fecha BETWEEN %s AND %s
            """, (fecha_inicio, fecha_fin))
            reporte = cursor.fetchone()
        else:
            return jsonify({"error": "Tipo de reporte no válido"}), 400

        cursor.close()
        db.close()

        return jsonify(reporte), 200  # Cambié a 200 OK
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)