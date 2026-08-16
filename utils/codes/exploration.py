"""Actividad 3 - Fase 1: exploración y manipulación de datos con pandas.

Reconstruye el dataset de consumo energético con la semilla fija de la
Actividad 1 (continuidad analítica sobre las mismas 120 observaciones) y
recorre el flujo de trabajo habitual de pandas: inspección de la
estructura, perfilado de calidad (tipos, nulos, duplicados, cardinalidad),
creación de variables derivadas, agregación con ``groupby`` y resumen
bidimensional con ``pivot_table`` sobre una variable discretizada con
``pd.cut``.

Es el primer eslabón del pipeline: escribe ``data/dataset/consumo_energia.csv``,
que consumen todas las fases posteriores (Python y R).

Rutas: el script se ubica en codes -> utils -> raíz del proyecto.
"""

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "dataset"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
for d in (DATA_DIR, PROCESSED_DIR):
    d.mkdir(parents=True, exist_ok=True)

pd.set_option("display.width", 100)
pd.set_option("display.max_columns", 20)

"""1. GENERACIÓN DEL DATASET.

Idéntico al de las Actividades 1 y 2 (semilla fija 42): 120 clientes de una
empresa distribuidora, con su sector, consumo mensual y costo facturado.
"""
rng = np.random.default_rng(42)
n = 120
sectors = rng.choice(
    ["Residencial", "Comercial", "Industrial"], size=n, p=[0.5, 0.3, 0.2]
)
base = {"Residencial": 250, "Comercial": 900, "Industrial": 2500}
spread = {"Residencial": 60, "Comercial": 220, "Industrial": 600}
consumption = np.array([rng.normal(base[s], spread[s]) for s in sectors]).clip(50)
tariff = {"Residencial": 820, "Comercial": 710, "Industrial": 640}
cost = consumption * np.array([tariff[s] for s in sectors]) * rng.normal(1, 0.04, n) / 1000

df = pd.DataFrame({
    "cliente_id": [f"CL-{i:03d}" for i in range(1, n + 1)],
    "sector": sectors,
    "consumo_kwh": consumption.round(1),
    "costo_miles_cop": cost.round(1),
})
df.to_csv(DATA_DIR / "consumo_energia.csv", index=False)

"""2. EXPLORACIÓN: ¿qué contiene el archivo?

Primer contacto con los datos antes de calcular nada: forma, primeras
filas, tipos y estadísticos de posición. `describe()` ya anticipa la
asimetría del consumo (media muy por encima de la mediana).
"""
print("=" * 78)
print("EXPLORACIÓN DEL DATASET")
print("=" * 78)
print(f"\nForma (filas, columnas): {df.shape}")
print("\nPrimeras filas -- df.head()")
print(df.head().to_string(index=False))
print("\nEstructura -- df.info()")
df.info()
print("\nResumen estadístico -- df.describe()")
print(df.describe().round(1).to_string())

"""3. PERFILADO DE CALIDAD.

Tabla que documenta, columna a columna, el tipo de dato, los valores
nulos, los duplicados y la cardinalidad. Es la evidencia de que el dataset
está limpio antes de analizarlo: sin nulos y sin clientes repetidos.
"""
profile = pd.DataFrame({
    "columna": df.columns,
    "tipo": [str(t) for t in df.dtypes],
    "no_nulos": df.notna().sum().values,
    "nulos": df.isna().sum().values,
    "valores_unicos": df.nunique().values,
})
profile.to_csv(PROCESSED_DIR / "perfil_datos.csv", index=False)
print("\nPerfil de calidad de los datos")
print(profile.to_string(index=False))
print(f"\nFilas duplicadas: {df.duplicated().sum()}")
print(f"Clientes duplicados: {df['cliente_id'].duplicated().sum()}")

"""4. MANIPULACIÓN: variables derivadas.

`tarifa_cop_kwh` recupera el precio implícito de cada factura y
`rango_consumo` discretiza una variable continua en categorías ordenadas
con `pd.cut`, el mismo mecanismo que la Fase 2 usará para construir la
distribución de frecuencias.
"""
df["tarifa_cop_kwh"] = (df["costo_miles_cop"] * 1000 / df["consumo_kwh"]).round(1)
df["rango_consumo"] = pd.cut(
    df["consumo_kwh"],
    bins=[0, 500, 1000, 2000, np.inf],
    labels=["Bajo (<500)", "Medio (500-1000)", "Alto (1000-2000)", "Muy alto (>2000)"],
)
print("\nVariables derivadas -- df.head()")
print(df.head().to_string(index=False))

"""5. AGREGACIÓN CON GROUPBY.

Una sola expresión encadenada resume los tres sectores: cuántos clientes
hay, cuánto consumen y facturan en promedio, y a qué tarifa implícita.
`observed=True` evita las combinaciones vacías de las variables
categóricas, comportamiento por defecto desde pandas 3.0.
"""
summary = (
    df.groupby("sector", observed=True)
    .agg(
        clientes=("cliente_id", "count"),
        consumo_medio=("consumo_kwh", "mean"),
        consumo_mediana=("consumo_kwh", "median"),
        consumo_total=("consumo_kwh", "sum"),
        costo_medio=("costo_miles_cop", "mean"),
        tarifa_media=("tarifa_cop_kwh", "mean"),
    )
    .round(1)
    .sort_values("consumo_medio")
)
summary["pct_clientes"] = (summary["clientes"] / n * 100).round(1)
summary["pct_consumo"] = (summary["consumo_total"] / df["consumo_kwh"].sum() * 100).round(1)
summary.to_csv(PROCESSED_DIR / "resumen_por_sector.csv")
print("\nResumen por sector -- groupby().agg()")
print(summary.to_string())

"""6. TABLA DINÁMICA.

Cruce de las dos variables categóricas (sector x rango de consumo) para
ver cómo se reparten los 120 clientes. Confirma que los rangos no se
solapan entre sectores: cada uno ocupa su propia franja de consumo.
"""
pivot = pd.pivot_table(
    df, values="cliente_id", index="rango_consumo", columns="sector",
    aggfunc="count", fill_value=0, observed=True,
)[["Residencial", "Comercial", "Industrial"]]
pivot["Total"] = pivot.sum(axis=1)
pivot.to_csv(PROCESSED_DIR / "tabla_dinamica_sector_rango.csv")
print("\nClientes por sector y rango de consumo -- pivot_table()")
print(pivot.to_string())

"""7. FILTRADO Y ORDENAMIENTO.

Consulta de negocio típica: los diez clientes que más consumen. `nlargest`
resuelve en una línea lo que exigiría ordenar y recortar por separado.
"""
top10 = df.nlargest(10, "consumo_kwh")[
    ["cliente_id", "sector", "consumo_kwh", "costo_miles_cop", "tarifa_cop_kwh"]
]
top10.to_csv(PROCESSED_DIR / "top10_consumo.csv", index=False)
print("\nDiez mayores consumidores -- nlargest()")
print(top10.to_string(index=False))
share = top10["consumo_kwh"].sum() / df["consumo_kwh"].sum() * 100
print(f"\nEstos 10 clientes (8,3 % del total) concentran el {share:.1f} % del consumo.")

print("\nOK - dataset generado y exploración con pandas completada")
