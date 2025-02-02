# Usa una imagen base de Python
FROM python:3.9-slim

# Crea un directorio de trabajo
WORKDIR /app

# Copia los archivos necesarios
COPY app.py requirements.txt ./

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto 5000
EXPOSE 5000

# Comando para ejecutar la API
CMD ["python", "app.py"]
