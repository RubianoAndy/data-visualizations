"""Actividad 3 - Fase 6: comparación de herramientas de visualización.

Construye EL MISMO gráfico -consumo medio por sector, con título, ejes
rotulados y etiquetas de dato- en cuatro herramientas del ecosistema
Python, y mide sobre esa base común tres indicadores objetivos:

* líneas de código efectivas necesarias para producirlo,
* tiempo mediano de renderizado (5 repeticiones tras un calentamiento),
* peso del archivo PNG resultante.

Mantener fija la especificación gráfica es lo que permite atribuir las
diferencias a la herramienta y no al gráfico. El resultado se escribe en
``data/processed/comparativa_herramientas.csv`` y se resume en la figura
``comparativa_herramientas.png``.

Rutas: el script se ubica en codes -> utils -> raíz del proyecto.
"""

import inspect
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
from matplotlib.ticker import MaxNLocator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "dataset"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = (
    PROJECT_ROOT / "public" / "assets" / "images" / "figures" / "python" / "tools"
)
for d in (PROCESSED_DIR, FIGURES_DIR):
    d.mkdir(parents=True, exist_ok=True)

matplotlib.use("Agg")   # backend no interactivo: mide el render, no la ventana
plt.rcParams.update({
    "figure.dpi": 150, "font.size": 10, "axes.titlesize": 11,
    "axes.titleweight": "bold", "axes.grid": True, "grid.alpha": 0.3,
    "axes.axisbelow": True,
})

PALETA = ["#a6bddb", "#74a9cf", "#2b8cbe"]
ORDEN = ["Residencial", "Comercial", "Industrial"]
TITULO = "Consumo medio por sector"
EJE_X, EJE_Y = "Sector", "Consumo (kWh/mes)"
ANCHO_PX, ALTO_PX = 975, 555

dataset_path = DATA_DIR / "consumo_energia.csv"
if not dataset_path.exists():
    raise SystemExit(
        f"No se encontró {dataset_path}. Ejecuta antes la Fase 1: "
        "python utils/codes/exploration.py"
    )
df = pd.read_csv(dataset_path)
df["sector"] = pd.Categorical(df["sector"], categories=ORDEN, ordered=True)
medias = df.groupby("sector", observed=True)["consumo_kwh"].mean().round(1)

"""1. LA MISMA FIGURA EN CUATRO HERRAMIENTAS.

Cada función recibe la ruta de salida y escribe el PNG. Se escriben con el
estilo idiomático de su librería: reescribirlas todas al estilo de
Matplotlib falsearía la comparación de líneas de código.
"""


def con_matplotlib(salida: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 3.7))
    barras = ax.bar(medias.index, medias.values, color=PALETA, edgecolor="white")
    ax.bar_label(barras, fmt="%.0f", padding=3, fontsize=8)
    ax.set_ylim(0, medias.max() * 1.18)
    ax.set_title(f"{TITULO} (Matplotlib)")
    ax.set_xlabel(EJE_X)
    ax.set_ylabel(EJE_Y)
    fig.tight_layout()
    fig.savefig(salida)
    plt.close(fig)


def con_pandas(salida: Path) -> None:
    ax = medias.plot.bar(color=PALETA, edgecolor="white", figsize=(6.5, 3.7),
                         rot=0, title=f"{TITULO} (pandas.plot)", legend=False,
                         ylim=(0, medias.max() * 1.18))
    ax.bar_label(ax.containers[0], fmt="%.0f", padding=3, fontsize=8)
    ax.set_xlabel(EJE_X)
    ax.set_ylabel(EJE_Y)
    ax.figure.tight_layout()
    ax.figure.savefig(salida)
    plt.close(ax.figure)


def con_seaborn(salida: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 3.7))
    sns.barplot(data=df, x="sector", y="consumo_kwh", hue="sector", order=ORDEN,
                palette=PALETA, estimator="mean", errorbar=None, legend=False, ax=ax)
    ax.bar_label(ax.containers[0], fmt="%.0f", padding=3, fontsize=8)
    ax.set(title=f"{TITULO} (seaborn)", xlabel=EJE_X, ylabel=EJE_Y,
           ylim=(0, medias.max() * 1.18))
    fig.tight_layout()
    fig.savefig(salida)
    plt.close(fig)


def con_plotly(salida: Path) -> None:
    fig = px.bar(x=medias.index, y=medias.values, text_auto=".0f",
                 color=medias.index, color_discrete_sequence=PALETA,
                 title=f"{TITULO} (Plotly)",
                 labels={"x": EJE_X, "y": EJE_Y, "color": EJE_X})
    fig.update_layout(showlegend=False, template="simple_white")
    fig.write_image(salida, width=ANCHO_PX, height=ALTO_PX)


HERRAMIENTAS = [
    (con_matplotlib, "Matplotlib", version("matplotlib"),
     "Imperativa (orientada a objetos)", "Agg / propio",
     "No (imagen estática)",
     "Control absoluto de cada artista; es el motor sobre el que corren las demás"),
    (con_pandas, "pandas.plot", version("pandas"),
     "Imperativa (método del DataFrame)", "Matplotlib",
     "No (imagen estática)",
     "Atajo para explorar: grafica directo desde el DataFrame, hereda sus límites"),
    (con_seaborn, "seaborn", version("seaborn"),
     "Declarativa (gramática estadística)", "Matplotlib",
     "No (imagen estática)",
     "Agrega y estiliza por ti; ideal para gráficos estadísticos frecuentes"),
    (con_plotly, "Plotly", version("plotly"),
     "Declarativa (Plotly Express)", "JavaScript (D3) / Kaleido",
     "Sí (zoom, tooltip, HTML)",
     "Pensado para la web; exportar a imagen exige un motor externo (Kaleido)"),
]


def lineas_efectivas(funcion) -> int:
    """Cuenta las líneas de código de la función, sin firma, comentarios ni blancos."""
    cuerpo = inspect.getsource(funcion).splitlines()[1:]
    return sum(1 for l in cuerpo if l.strip() and not l.strip().startswith("#"))


filas = []
for funcion, nombre, ver, paradigma, motor, interactivo, nota in HERRAMIENTAS:
    salida = FIGURES_DIR / f"{funcion.__name__.replace('con_', 'bar_')}.png"
    funcion(salida)                      # calentamiento: descarta la primera pasada
    tiempos = []
    for _ in range(5):
        inicio = perf_counter()
        funcion(salida)
        tiempos.append((perf_counter() - inicio) * 1000)
    filas.append({
        "herramienta": nombre,
        "version": ver,
        "paradigma": paradigma,
        "motor_render": motor,
        "interactivo": interactivo,
        "loc": lineas_efectivas(funcion),
        "tiempo_ms": round(float(np.median(tiempos)), 1),
        "peso_kb": round(salida.stat().st_size / 1024, 1),
        "observacion": nota,
    })

comparativa = pd.DataFrame(filas)
comparativa.to_csv(PROCESSED_DIR / "comparativa_herramientas.csv", index=False)
print("Comparación de herramientas de visualización (Python)")
print(comparativa.drop(columns=["observacion"]).to_string(index=False))

"""2. LA VENTAJA QUE NO SE MIDE EN SEGUNDOS: la interactividad.

Plotly es el único de los cuatro que produce un gráfico navegable. Se
exporta también en HTML para dejar constancia de esa capacidad, que es su
argumento real frente a Matplotlib.
"""
fig_html = px.bar(x=medias.index, y=medias.values, text_auto=".0f",
                  color=medias.index, color_discrete_sequence=PALETA,
                  title=f"{TITULO} (Plotly, versión interactiva)",
                  labels={"x": EJE_X, "y": EJE_Y, "color": EJE_X})
fig_html.update_layout(showlegend=False, template="simple_white")
fig_html.write_html(FIGURES_DIR / "bar_plotly_interactivo.html", include_plotlyjs="cdn")

"""3. RESUMEN VISUAL DE LA COMPARACIÓN.

Dos paneles con la misma lectura: menos es mejor. Se grafica con
Matplotlib -la herramienta que el laboratorio justifica como elección- de
modo que la figura que resume la comparación es también un argumento a su
favor.
"""
orden_loc = comparativa.sort_values("loc")
orden_t = comparativa.sort_values("tiempo_ms")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.6))
b1 = ax1.barh(orden_loc["herramienta"], orden_loc["loc"], color=PALETA[1])
ax1.bar_label(b1, padding=3, fontsize=8)
ax1.set_xlim(0, orden_loc["loc"].max() * 1.25)
ax1.set_title("Líneas de código para el mismo gráfico")
ax1.set_xlabel("Líneas efectivas (menos es mejor)")
b2 = ax2.barh(orden_t["herramienta"], orden_t["tiempo_ms"], color=PALETA[2])
ax2.bar_label(b2, fmt="%.0f ms", padding=3, fontsize=8)
ax2.set_xlim(0, orden_t["tiempo_ms"].max() * 1.35)
ax2.set_title("Tiempo de renderizado del PNG")
ax2.set_xlabel("Milisegundos por figura (menos es mejor)")
fig.suptitle("Mismo gráfico, cuatro herramientas: costo de escribirlo y de dibujarlo",
             fontsize=11, fontweight="bold")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "comparativa_herramientas.png")
plt.close(fig)

"""4. CONSOLIDADO PYTHON + R.

Si la Fase 5 (benchmark.R) ya corrió, sus dos filas se unen a las cuatro de
Python para cerrar el cuadro completo de seis herramientas. Los tiempos
entre lenguajes son indicativos: cada uno mide su propio entorno de
ejecución, no un mismo motor.
"""
csv_r = PROCESSED_DIR / "comparativa_herramientas_r.csv"
if not csv_r.exists():
    print(f"\nAviso: no se encontró {csv_r.name}; ejecuta 'Rscript utils/codes/"
          "benchmark.R' y vuelve a correr esta fase para el consolidado.")
else:
    comp_r = pd.read_csv(csv_r)
    todas = pd.concat([comparativa.assign(ecosistema="Python"),
                       comp_r.assign(ecosistema="R")], ignore_index=True)
    todas.to_csv(PROCESSED_DIR / "comparativa_consolidada.csv", index=False)

    colores = {"Python": PALETA[2], "R": "#d95f02"}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    for eje, columna, titulo, formato in [
        (ax1, "loc", "Líneas de código para el mismo gráfico", "%.0f"),
        (ax2, "tiempo_ms", "Tiempo de renderizado por figura", "%.0f ms"),
    ]:
        datos = todas.sort_values(columna)
        barras = eje.barh(datos["herramienta"], datos[columna],
                          color=[colores[e] for e in datos["ecosistema"]])
        eje.bar_label(barras, fmt=formato, padding=3, fontsize=8)
        eje.set_xlim(0, datos[columna].max() * 1.32)
        eje.set_title(titulo)
    ax1.set_xlabel("Líneas efectivas (menos es mejor)")
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax2.set_xlabel("Milisegundos (menos es mejor)")
    manijas = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colores.values()]
    ax1.legend(manijas, colores.keys(), title="Ecosistema", fontsize=8,
               title_fontsize=8, loc="lower right")
    fig.suptitle("Seis herramientas, un mismo gráfico: brevedad frente a velocidad",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "comparativa_consolidada.png")
    plt.close(fig)
    print("\nComparativa consolidada (Python + R)")
    print(todas[["ecosistema", "herramienta", "loc", "tiempo_ms", "peso_kb"]]
          .to_string(index=False))

print("\nOK - comparación de herramientas de Python completada")
