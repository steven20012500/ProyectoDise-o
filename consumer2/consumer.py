from kafka import KafkaConsumer
import mysql.connector
import json
import time

# Función para inicializar el consumidor Kafka con reintentos
def create_kafka_consumer(topic):
    while True:
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers='kafka:9092',
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            print(f"Conexión exitosa al broker Kafka desde el consumidor para el topic {topic}")
            return consumer
        except Exception as e:
            print(f"No se pudo conectar a Kafka desde el consumidor para el topic {topic}: {e}. Reintentando en 5 segundos...")
            time.sleep(5)

# Función para conectar a la base de datos MySQL con reintentos
def connect_to_mysql():
    while True:
        try:
            db = mysql.connector.connect(
                host='mysql',
                user='user',
                password='password',
                database='viveres_blanquita'
            )
            print("Conexión exitosa a MySQL desde el consumidor")
            return db
        except mysql.connector.Error as e:
            print(f"No se pudo conectar a MySQL desde el consumidor: {e}. Reintentando en 5 segundos...")
            time.sleep(5)

# Inicializa las conexiones con reintentos
consumer_inventario = create_kafka_consumer('inventarios')
db = connect_to_mysql()
cursor = db.cursor()

# Procesa los mensajes de los topics 'ventas' e 'inventario'
while True:
    # Procesar mensajes del topic 'inventario'
    for message in consumer_inventario:
        try:
            data = message.value
            print(f"Mensaje recibido en 'inventario': {data}")

            # Verificar el tipo de acción en el mensaje
            if data.get('accion') == 'eliminar':
                # Procesar eliminación de un producto del inventario
                id = data.get('id')
                cursor.execute("DELETE FROM inventario WHERE id = %s", (id,))
                db.commit()
                print(f"Producto eliminado: {id}")
            else:
                # Procesar las actualizaciones o inserciones de inventarios enviados
                for inventario in data['inventarios']:
                    # Verificar si el producto ya existe en la base de datos
                    cursor.execute("SELECT id FROM inventario WHERE nombre = %s", (inventario['nombre'],))
                    resultado = cursor.fetchone()

                    if resultado:
                        # Si el producto ya existe, actualiza la cantidad y el precio
                        cursor.execute("""
                            UPDATE inventario 
                            SET cantidad = %s, precio = %s 
                            WHERE nombre = %s
                        """, (inventario['cantidad'], inventario['precio'], inventario['nombre']))
                        print(f"Producto actualizado: {inventario['nombre']}")
                    else:
                        # Si el producto no existe, insértalo como un nuevo registro
                        cursor.execute("""
                            INSERT INTO inventario (nombre, cantidad, precio) 
                            VALUES (%s, %s, %s)
                        """, (inventario['nombre'], inventario['cantidad'], inventario['precio']))
                        print(f"Producto insertado: {inventario['nombre']}")

                # Confirmar los cambios
                db.commit()
                print("Cambios confirmados en la base de datos.")
        except Exception as e:
            print(f"Error al procesar el mensaje en 'inventario': {e}")
            db.rollback()  # Deshace cualquier cambio si hay un error

