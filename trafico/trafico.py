import numpy as np
import requests
import time
import random
import json
import os
from kafka import KafkaProducer

ZONAS_SANTIAGO = {
    "Z1": {"nombre": "Providencia",     "lat": (-33.445, -33.420), "lon": (-70.640, -70.600)},
    "Z2": {"nombre": "Las Condes",      "lat": (-33.420, -33.390), "lon": (-70.600, -70.550)},
    "Z3": {"nombre": "Maipú",           "lat": (-33.530, -33.490), "lon": (-70.790, -70.740)},
    "Z4": {"nombre": "Santiago Centro", "lat": (-33.460, -33.430), "lon": (-70.670, -70.630)},
    "Z5": {"nombre": "Pudahuel",        "lat": (-33.470, -33.430), "lon": (-70.810, -70.760)}
}

KAFKA_BROKER     = os.getenv("KAFKA_BROKER", "kafka:9092")
MODO             = os.getenv("MODO", "sincrono")
DISTRIBUCION     = os.getenv("DISTRIBUCION", "zipf")
TOTAL_PETICIONES = int(os.getenv("TOTAL_PETICIONES", "200"))
INTERVALO_SEG    = float(os.getenv("INTERVALO_SEG", "0.1"))

def generar_consulta(distribucion):
    ids_zonas = list(ZONAS_SANTIAGO.keys())
    if distribucion == "zipf":
        s = 1.2
        idx = (np.random.zipf(a=s) - 1) % len(ids_zonas)
    else:
        idx = random.randint(0, len(ids_zonas) - 1)
    zona_id  = ids_zonas[idx]
    tipo_q   = random.choice(["Q1", "Q2", "Q3", "Q4", "Q5"])
    conf_min = round(random.uniform(0.0, 0.9), 2)
    payload = {
        "id":          f"{tipo_q}-{zona_id}-{int(time.time()*1000)}-{random.randint(0,9999)}",
        "tipo":        tipo_q,
        "zona_id":     zona_id,
        "timestamp":   time.time(),
        "retry_count": 0,
        "params": {"confidence_min": conf_min}
    }
    if tipo_q == "Q4":
        payload["zona_id_b"] = random.choice([z for z in ids_zonas if z != zona_id])
    elif tipo_q == "Q5":
        payload["params"]["bins"] = random.randint(3, 10)
    return payload

def enviar_sincrono(distribucion):
    payload = generar_consulta(distribucion)
    try:
        response = requests.post("http://sistema-cache:8000/consultar", json=payload, timeout=5)
        print(f"[sincrono] {payload['tipo']} zona={payload['zona_id']} → {response.status_code}")
    except Exception as e:
        print(f"[sincrono] Error: {e}")

def crear_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=5,
                linger_ms=10
            )
            print(f"[producer] Conectado a Kafka en {KAFKA_BROKER}")
            return producer
        except Exception as e:
            print(f"[producer] Kafka no disponible, reintentando en 3s... ({e})")
            time.sleep(3)

def enviar_kafka(producer, distribucion):
    payload = generar_consulta(distribucion)
    try:
        future = producer.send("consultas", value=payload)
        future.get(timeout=10)
        print(f"[kafka] Publicada {payload['tipo']} zona={payload['zona_id']} id={payload['id']}")
    except Exception as e:
        print(f"[kafka] Error publicando: {e}")

if __name__ == "__main__":
    print(f"[trafico] Modo={MODO} | Dist={DISTRIBUCION} | Total={TOTAL_PETICIONES}")
    time.sleep(10)
    if MODO == "kafka":
        producer = crear_producer()
    contador = 0
    while contador < TOTAL_PETICIONES:
        if MODO == "kafka":
            enviar_kafka(producer, DISTRIBUCION)
        else:
            enviar_sincrono(DISTRIBUCION)
        contador += 1
        time.sleep(INTERVALO_SEG)
    if MODO == "kafka":
        producer.flush()
        producer.close()
    print(f"[trafico] Finalizado. {contador} consultas enviadas.")
