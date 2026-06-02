import numpy as np
import requests
import time
import random

# Definición de las Bounding Boxes (Zonas de Santiago) [cite: 95]
ZONAS_SANTIAGO = {
    "Z1": {"nombre": "Providencia", "lat": (-33.445, -33.420), "lon": (-70.640, -70.600)},
    "Z2": {"nombre": "Las Condes", "lat": (-33.420, -33.390), "lon": (-70.600, -70.550)},
    "Z3": {"nombre": "Maipú", "lat": (-33.530, -33.490), "lon": (-70.790, -70.740)},
    "Z4": {"nombre": "Santiago Centro", "lat": (-33.460, -33.430), "lon": (-70.670, -70.630)},
    "Z5": {"nombre": "Pudahuel", "lat": (-33.470, -33.430), "lon": (-70.810, -70.760)}
}

#cambiar zipf a uniforme y testear ambos escenarios para el informe
def enviar_consulta(distribucion):
    ids_zonas = list(ZONAS_SANTIAGO.keys())
    
    # 1. Selección de zona según distribución (Zipf o Uniforme) [cite: 34]
    if distribucion == "zipf":
        # Favorece la repetición de zonas para probar la eficiencia de la caché [cite: 94]
        s = 1.2  
        idx = (np.random.zipf(a=s) - 1) % len(ids_zonas)
    else:
        # Distribución uniforme: igual probabilidad para todas las zonas [cite: 34]
        idx = random.randint(0, len(ids_zonas) - 1)
        
    zona_id = ids_zonas[idx]
    
    # 2. Selección del tipo de operación (Q1-Q5) 
    tipo_q = random.choice(["Q1", "Q2", "Q3", "Q4", "Q5"])

    # 3. Construcción del Payload con todos los parámetros según el tipo 
    payload = {
        "tipo": tipo_q,
        "zona_id": zona_id,
        "params": {
            "confidence_min": round(random.uniform(0.0, 0.9), 2) # Parámetro opcional Q1-Q4 [cite: 101, 112, 125, 137]
        }
    }

    # Lógica específica por consulta para cumplir con el enunciado:
    if tipo_q == "Q4":
        # Requiere una segunda zona para comparar densidades [cite: 137]
        zona_b = random.choice([z for z in ids_zonas if z != zona_id])
        payload["zona_id_b"] = zona_b
    
    elif tipo_q == "Q5":
        # Requiere el número de intervalos (bins) para la distribución [cite: 149]
        payload["params"]["bins"] = random.randint(3, 10)

    try:
        # Enviar la consulta al Sistema de Caché [cite: 63]
        response = requests.post("http://sistema-cache:8000/consultar", json=payload, timeout=5)
        print(f"[{distribucion}] Enviada {tipo_q} para {zona_id}. Status: {response.status_code}")
    except Exception as e:
        print(f"Error enviando consulta: {e}")

if __name__ == "__main__":
    time.sleep(10) # Espera a que el sistema estabilice
    
    TOTAL_PETICIONES = 5000
    contador = 0
    
    print(f"Iniciando experimento: enviando {TOTAL_PETICIONES} consultas...")
    
    while contador < TOTAL_PETICIONES:
        # Elige la distribución según el experimento que estés corriendo
        enviar_consulta(distribucion="zipf") 
        #enviar_consulta(distribucion="zipf") 
        contador += 1
        time.sleep(0.1) # Controla el Throughput (consultas/segundo) 
        
    print("Experimento finalizado. Datos recolectados en el CSV de métricas.")