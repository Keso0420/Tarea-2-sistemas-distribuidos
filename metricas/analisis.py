import pandas as pd
import numpy as np
import redis
import os

ARCHIVO_METRICAS = "/home/keso/Escritorio/T1_SD/data/metricas_sistema.csv"

def obtener_evictions():
    try:
        # Intentamos conectar a Redis para sacar el Eviction Rate real
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        info = r.info('stats')
        return int(info.get('evicted_keys', 0))
    except:
        return 0

def analizar_experimento():
    if not os.path.exists(ARCHIVO_METRICAS):
        print(f"Error: No existe {ARCHIVO_METRICAS}")
        return

    # Leemos el CSV asegurándonos de limpiar espacios en los nombres de columnas
    df = pd.read_csv(ARCHIVO_METRICAS, names=["timestamp", "evento", "key", "latencia_ms", "fuente"])
    df.columns = df.columns.str.strip()

    if 'evento' not in df.columns:
        print(f"Error: No se encuentra la columna 'evento'. Columnas detectadas: {list(df.columns)}")
        return

    # --- CÁLCULO DE MÉTRICAS SEGÚN LA GUÍA ---
    
    total = len(df)
    hits = len(df[df['evento'] == 'HIT'])
    misses = len(df[df['evento'] == 'MISS'])
    
    # 1. Hit Rate
    hit_rate = hits / total if total > 0 else 0
    
    # 2. Throughput (Consultas exitosas / segundo)
    # Calculamos el tiempo total del experimento usando el primer y último timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    tiempo_total_seg = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
    throughput = total / tiempo_total_seg if tiempo_total_seg > 0 else 0
    
    # 3. Latencia p50/p95
    p50 = df['latencia_ms'].median()
    p95 = df['latencia_ms'].quantile(0.95)
    
    # 4. Eviction Rate (Evictions / minuto)
    evictions_totales = obtener_evictions()
    tiempo_total_min = tiempo_total_seg / 60
    eviction_rate = evictions_totales / tiempo_total_min if tiempo_total_min > 0 else 0
    
    # 5. Cache Efficiency
    # Fórmula: (hits * t_cache - misses * t_db) / total
    # Asumiremos t_cache como la latencia media de los HITS y t_db como la de los MISSES
    t_cache = df[df['evento'] == 'HIT']['latencia_ms'].mean() if hits > 0 else 0
    t_db = df[df['evento'] == 'MISS']['latencia_ms'].mean() if misses > 0 else 0
    cache_efficiency = ((hits * t_cache) - (misses * t_db)) / total if total > 0 else 0

    # --- SALIDA PARA EL INFORME ---
    print("\n" + "="*45)
    print("      METRICAS PARA ANÁLISIS")
    print("="*45)
    print(f"{'Métrica':<20} | {'Valor':<20}")
    print("-" * 45)
    print(f"{'Hit Rate':<20} | {hit_rate:.4f} ({hit_rate*100:.2f}%)")
    print(f"{'Throughput':<20} | {throughput:.2f} req/seg")
    print(f"{'Latencia p50':<20} | {p50:.2f} ms")
    print(f"{'Latencia p95':<20} | {p95:.2f} ms")
    print(f"{'Eviction Rate':<20} | {eviction_rate:.2f} evic/min")
    print(f"{'Cache Efficiency':<20} | {cache_efficiency:.4f}")
    print("="*45)

if __name__ == "__main__":
    analizar_experimento()