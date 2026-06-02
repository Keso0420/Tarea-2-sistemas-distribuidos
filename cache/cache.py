import os
import redis
import requests
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis-db')
cache = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

RESPUESTAS_URL = "http://generador-respuestas:5000/procesar"
METRICAS_URL = "http://almacenamiento-metricas:9000/registrar"

def generar_cache_key(data):
    """Genera la llave: tipo:zona:params [cite: 54, 102, 113]"""
    tipo = data.get('tipo')
    zona = data.get('zona_id')
    conf = data.get('params', {}).get('confidence_min', 0.0)
    return f"{tipo}:{zona}:conf={conf}"

@app.route('/consultar', methods=['POST'])
def consultar():
    # Inicia el cronómetro para medir la latencia [cite: 42, 181]
    start_time = time.time()
    
    data = request.json
    cache_key = generar_cache_key(data)
    
    # 1. Intentar obtener de la caché [cite: 37, 55]
    resultado_cache = cache.get(cache_key)
    
    if resultado_cache:
        # HIT 
        evento = "HIT"
        fuente = "cache"
        respuesta_final = resultado_cache
    else:
        # MISS 
        evento = "MISS"
        fuente = "generador_respuestas"
        try:
            # Delegar al Generador de Respuestas [cite: 39, 49, 64]
            response = requests.post(RESPUESTAS_URL, json=data, timeout=10)
            respuesta_final = response.json()
            
            cache.setex(cache_key, 300, str(respuesta_final)) # ttl de 5 min
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    latencia_ms = (time.time() - start_time) * 1000

    payload_metrica = {
        "evento": evento,
        "key": cache_key,
        "latencia_ms": latencia_ms,
        "fuente": fuente
    }
    
    try:
        # Registro paralelo del evento [cite: 65, 80]
        requests.post(METRICAS_URL, json=payload_metrica, timeout=1)
    except:
        print("Error registrando métricas")

    # Retornar respuesta al Generador de Tráfico [cite: 37, 57, 64]
    return jsonify({"fuente": fuente, "data": respuesta_final})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)