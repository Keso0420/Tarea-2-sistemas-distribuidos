import pandas as pd
from flask import Flask, request, jsonify
from datetime import datetime
import csv
import os

app = Flask(__name__)

# Ruta del archivo donde guardaremos los datos para el informe
LOG_FILE = "data/metricas_sistema.csv"

# Inicializar el archivo CSV con encabezados si no existe
if not os.path.exists(LOG_FILE):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "evento", "key", "latencia_ms", "fuente"])
else:
    with open(LOG_FILE, "w") as f:
        pass 

@app.route('/registrar', methods=['POST'])
def registrar():
    data = request.json
    evento = data.get('evento')  # "HIT" o "MISS" [cite: 42]
    key = data.get('key')
    latencia = data.get('latencia_ms')
    fuente = data.get('fuente') # "cache" o "respuestas"
    
    # Registro con marca de tiempo para calcular throughput y percentiles 
    nuevo_registro = [
        datetime.now().isoformat(),
        evento,
        key,
        latencia,
        fuente
    ]
    
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(nuevo_registro)
        f.flush() # Esto obliga a escribir al disco inmediatamente
    
    return jsonify({"status": "registrado"}), 201

if __name__ == "__main__":
    # El servicio de métricas corre de forma paralela [cite: 65]
    app.run(host='0.0.0.0', port=9000)