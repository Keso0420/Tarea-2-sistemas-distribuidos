# Usa una imagen ligera de Python
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requisitos e instálalos
# (Crea un archivo requirements.txt en cada carpeta con: pandas, redis, requests)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la carpeta al contenedor
COPY . .

# Comando para ejecutar tu script
CMD ["python", "trafico.py"]