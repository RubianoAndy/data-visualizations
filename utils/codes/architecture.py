"""Actividad 3 - Fase 3: historia y arquitectura de Matplotlib.

Documenta, con figuras hechas por la propia librería, las tres capas en las
que está organizada Matplotlib y la anatomía de una figura:

1. ``linea_tiempo_matplotlib.png``  - hitos desde su creación en 2003.
2. ``arquitectura_capas.png``       - las capas backend / artista / scripting,
   dibujada usando únicamente objetos Artist (rectángulos, flechas y textos),
   de modo que la figura es a la vez el diagrama y la demostración.
3. ``anatomia_figura.png``          - los componentes de una figura anotados
   sobre un gráfico real (Figure, Axes, Axis, Line2D, spines, ticks, legend).
4. ``capas_scripting_vs_artist.png``- el mismo gráfico construido dos veces:
   con la capa de scripting (``pyplot``) y con la capa de artistas (API
   orientada a objetos), para evidenciar que producen el mismo resultado.

Además mide el costo de la capa de backend exportando una misma figura a
PNG (Agg), SVG y PDF, y escribe la comparación en
``data/processed/backends.csv``.

Rutas: el script se ubica en codes -> utils -> raíz del proyecto.
"""

from pathlib import Path
from time import perf_counter

import matplotlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.text import Text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "dataset"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = (
    PROJECT_ROOT / "public" / "assets" / "images" / "figures" / "python" / "architecture"
)
for d in (PROCESSED_DIR, FIGURES_DIR):
    d.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150, "font.size": 10, "axes.titlesize": 11,
    "axes.titleweight": "bold", "axes.grid": True, "grid.alpha": 0.3,
    "axes.axisbelow": True,
})

AZUL, AZUL_MEDIO, AZUL_CLARO, NARANJA = "#2b8cbe", "#74a9cf", "#a6bddb", "#d95f02"

dataset_path = DATA_DIR / "consumo_energia.csv"
if not dataset_path.exists():
    raise SystemExit(
        f"No se encontró {dataset_path}. Ejecuta antes la Fase 1: "
        "python utils/codes/exploration.py"
    )
df = pd.read_csv(dataset_path)
sector_order = ["Residencial", "Comercial", "Industrial"]
medias = [df.loc[df["sector"] == s, "consumo_kwh"].mean() for s in sector_order]

print(f"Matplotlib {matplotlib.__version__} | backend activo: {matplotlib.get_backend()}")

"""1. LÍNEA DE TIEMPO.

Matplotlib nació en 2003 de la mano de John D. Hunter, neurobiólogo que
necesitaba graficar señales de electrocorticografía en Python con una
sintaxis parecida a la de MATLAB. Los hitos se dibujan sobre un eje
temporal con anotaciones alternadas para evitar solapamientos.
"""
hitos = [
    (2003, "Creación por\nJohn D. Hunter\n(versión 0.1)"),
    (2007, "Artículo fundacional\nen Computing in\nScience & Engineering"),
    (2012, "Fallece Hunter;\nel desarrollo pasa\na la comunidad"),
    (2017, "Versión 2.0:\nnuevo estilo por\ndefecto (viridis)"),
    (2019, "Presente en la\nprimera imagen de\nun agujero negro\n(proyecto EHT)"),
    (2026, "Versión 3.11.1,\nla usada en este\nlaboratorio"),
]
fig, ax = plt.subplots(figsize=(9.4, 3.4))
años = [h[0] for h in hitos]
ax.plot([2001, 2028], [0, 0], color=AZUL_CLARO, lw=3, zorder=1)
ax.scatter(años, [0] * len(años), s=90, color=AZUL, zorder=3)
for i, (año, texto) in enumerate(hitos):
    arriba = i % 2 == 0
    ax.annotate(
        f"{año}\n{texto}", xy=(año, 0), xytext=(año, 0.32 if arriba else -0.32),
        ha="center", va="bottom" if arriba else "top", fontsize=7.5,
        arrowprops=dict(arrowstyle="-", color=AZUL_MEDIO, lw=1),
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=AZUL_CLARO),
    )
ax.set_title("Matplotlib: más de dos décadas como estándar de la visualización científica en Python")
ax.set_xlabel("Año")
ax.set_xlim(2000, 2029)
ax.set_ylim(-1.0, 1.0)
ax.set_yticks([])
ax.grid(axis="y", visible=False)
for lado in ("left", "right", "top"):
    ax.spines[lado].set_visible(False)
fig.tight_layout()
fig.savefig(FIGURES_DIR / "linea_tiempo_matplotlib.png")
plt.close(fig)

"""2. LAS TRES CAPAS DE MATPLOTLIB.

El diagrama se construye únicamente con objetos Artist -FancyBboxPatch,
FancyArrowPatch y Text- añadidos a unos ejes sin decoración: la figura
demuestra en su propia construcción la capa que describe.
"""
capas = [
    (
        "Capa de scripting  ·  matplotlib.pyplot",
        "Interfaz de alto nivel con estado global: plt.hist(), plt.bar(), plt.plot().\n"
        "Crea figuras y ejes por ti. Es la puerta de entrada y la que usa el 90 % del código.",
        AZUL_CLARO,
    ),
    (
        "Capa de artistas  ·  matplotlib.artist",
        "Jerarquía de objetos que describe QUÉ se dibuja: Figure > Axes > Axis, y los\n"
        "artistas primitivos Line2D, Rectangle, Text. Es la API orientada a objetos.",
        AZUL_MEDIO,
    ),
    (
        "Capa de backend  ·  FigureCanvas + Renderer",
        "Traduce los artistas a píxeles o vectores: Agg (PNG), PDF, SVG, Cairo, o los\n"
        "interactivos Qt y Tk. Define DÓNDE y CÓMO se materializa la figura.",
        AZUL,
    ),
]
fig = plt.figure(figsize=(9.4, 4.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 10)
ax.set_ylim(1.1, 10)
ax.axis("off")
ax.add_artist(Text(
    5, 9.4, "Arquitectura en capas de Matplotlib", ha="center", va="center",
    fontsize=13, fontweight="bold",
))
ax.add_artist(Text(
    5, 8.8, "cada capa delega en la inferior; se puede entrar por cualquiera de ellas",
    ha="center", va="center", fontsize=9, style="italic", color="#555555",
))
for i, (titulo, detalle, color) in enumerate(capas):
    y = 6.4 - i * 2.2
    ax.add_artist(FancyBboxPatch(
        (0.6, y), 8.8, 1.7, boxstyle="round,pad=0.06", facecolor=color,
        edgecolor="white", lw=2,
    ))
    ax.add_artist(Text(1.05, y + 1.28, titulo, fontsize=10.5, fontweight="bold",
                       color="white" if i == 2 else "#0b3d5c"))
    ax.add_artist(Text(1.05, y + 0.55, detalle, fontsize=8.4, va="center",
                       color="white" if i == 2 else "#123f5a"))
    if i < len(capas) - 1:
        ax.add_artist(FancyArrowPatch(
            (5, y - 0.06), (5, y - 0.45), arrowstyle="-|>", mutation_scale=16,
            color="#555555", lw=1.4,
        ))
ax.add_artist(Text(
    5, 0.75,
    "Este diagrama está dibujado solo con artistas (FancyBboxPatch, FancyArrowPatch y Text):\n"
    "es, literalmente, una demostración de la capa intermedia.",
    ha="center", va="center", fontsize=8.2, style="italic", color="#555555",
))
fig.savefig(FIGURES_DIR / "arquitectura_capas.png")
plt.close(fig)

"""3. ANATOMÍA DE UNA FIGURA.

Sobre un gráfico real -el consumo medio por sector- se rotulan los
componentes que hay que nombrar correctamente para leer la documentación
de Matplotlib y para etiquetar bien cualquier figura.
"""
fig, ax = plt.subplots(figsize=(9.4, 5.2))
fig.subplots_adjust(left=0.28, right=0.72, top=0.79, bottom=0.16)
barras = ax.bar(sector_order, medias, color=[AZUL_CLARO, AZUL_MEDIO, AZUL],
                edgecolor="white", label="Consumo medio")
ax.bar_label(barras, fmt="%.0f", padding=3, fontsize=8)
ax.set_ylim(0, max(medias) * 1.25)
ax.set_title("Consumo medio por sector")
ax.set_xlabel("Sector")
ax.set_ylabel("Consumo (kWh/mes)")
ax.legend(fontsize=8, loc="upper left")

"""Las etiquetas viven en los márgenes y se anclan en coordenadas de figura,
de modo que ninguna flecha atraviesa los datos ni se sale del lienzo."""
anotaciones = [
    ("Figure\nel lienzo completo", (0.030, 0.970), (0.13, 0.94)),
    ("Legend", (0.318, 0.748), (0.12, 0.72)),
    ("Grid", (0.350, 0.590), (0.12, 0.57)),
    ("Axis Y\nescala, ticks\ny tick labels", (0.240, 0.430), (0.12, 0.40)),
    ("Axes\nla región de trazado", (0.330, 0.260), (0.12, 0.21)),
    ("Title", (0.625, 0.818), (0.88, 0.90)),
    ("Text\netiqueta de dato", (0.652, 0.700), (0.88, 0.70)),
    ("Rectangle\ncada barra es\nun artista", (0.680, 0.430), (0.88, 0.46)),
    ("Spine\nmarco de los ejes", (0.722, 0.260), (0.88, 0.22)),
    ("Axis X: categorías y tick labels", (0.400, 0.128), (0.500, 0.045)),
]
for texto, xy, xytext in anotaciones:
    ax.annotate(
        texto, xy=xy, xycoords="figure fraction",
        xytext=xytext, textcoords="figure fraction",
        fontsize=7.8, color="#b3411a", ha="center", va="center",
        arrowprops=dict(arrowstyle="->", color=NARANJA, lw=1.1,
                        connectionstyle="arc3,rad=0.12"),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff4ec", edgecolor=NARANJA,
                  lw=0.8),
    )
fig.suptitle("Anatomía de una figura de Matplotlib", fontsize=12, fontweight="bold",
             y=0.975)
fig.savefig(FIGURES_DIR / "anatomia_figura.png")
plt.close(fig)

"""4. CAPA DE SCRIPTING FRENTE A CAPA DE ARTISTAS.

Izquierda: pyplot mantiene el estado y decide sobre qué ejes actúa.
Derecha: el mismo gráfico armado colocando rectángulos y textos uno a uno.
Ambos paneles son idénticos porque el primero termina haciendo lo del
segundo por debajo.
"""
fig = plt.figure(figsize=(9.4, 4.0))

# Capa de scripting: ninguna variable guarda la figura ni los ejes.
plt.subplot(1, 2, 1)
plt.bar(sector_order, medias, color=[AZUL_CLARO, AZUL_MEDIO, AZUL], edgecolor="white")
plt.title("Capa de scripting (pyplot)")
plt.xlabel("Sector")
plt.ylabel("Consumo (kWh/mes)")
plt.ylim(0, max(medias) * 1.25)
for i, v in enumerate(medias):
    plt.text(i, v + max(medias) * 0.03, f"{v:,.0f}", ha="center", fontsize=8)

# Capa de artistas: cada barra es un Rectangle y cada rótulo un Text.
ax2 = fig.add_subplot(1, 2, 2)
for i, (sector, valor) in enumerate(zip(sector_order, medias)):
    ax2.add_artist(Rectangle((i - 0.4, 0), 0.8, valor,
                             facecolor=[AZUL_CLARO, AZUL_MEDIO, AZUL][i],
                             edgecolor="white"))
    ax2.add_artist(Text(i, valor + max(medias) * 0.03, f"{valor:,.0f}",
                        ha="center", fontsize=8))
ax2.set_xlim(-0.6, 2.6)
ax2.set_ylim(0, max(medias) * 1.25)
ax2.set_xticks(range(3), sector_order)
ax2.set_title("Capa de artistas (API orientada a objetos)")
ax2.set_xlabel("Sector")
ax2.set_ylabel("Consumo (kWh/mes)")

fig.suptitle("El mismo gráfico por dos caminos: pyplot delega en los artistas",
             fontsize=11, fontweight="bold")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "capas_scripting_vs_artist.png")
plt.close(fig)

"""5. LA CAPA DE BACKEND, MEDIDA.

La misma figura se exporta con tres backends distintos. Agg rasteriza a
píxeles (PNG); PDF y SVG conservan vectores, por lo que escalan sin pérdida
pero pesan distinto. La medición justifica por qué el laboratorio entrega
PNG a 150 ppp y no vectores.
"""
fig, ax = plt.subplots(figsize=(6.5, 3.6))
ax.bar(sector_order, medias, color=[AZUL_CLARO, AZUL_MEDIO, AZUL], edgecolor="white")
ax.set_title("Figura de prueba para la comparación de backends")
ax.set_xlabel("Sector")
ax.set_ylabel("Consumo (kWh/mes)")

backend_rows = []
for formato, backend, descripcion in [
    ("png", "Agg (Anti-Grain Geometry)", "Rasterizado a 150 ppp"),
    ("svg", "SVG", "Vectorial, texto editable"),
    ("pdf", "PDF", "Vectorial, listo para imprimir"),
]:
    salida = FIGURES_DIR / f"backend_demo.{formato}"
    fig.savefig(salida)                       # descarta la primera pasada (calentamiento)
    tiempos = []
    for _ in range(5):
        inicio = perf_counter()
        fig.savefig(salida)
        tiempos.append((perf_counter() - inicio) * 1000)
    backend_rows.append({
        "formato": formato.upper(),
        "backend": backend,
        "tipo": descripcion,
        "tiempo_ms": round(float(np.median(tiempos)), 1),
        "peso_kb": round(salida.stat().st_size / 1024, 1),
    })
plt.close(fig)

backends = pd.DataFrame(backend_rows)
backends.to_csv(PROCESSED_DIR / "backends.csv", index=False)
print("\nCapa de backend: misma figura, tres salidas")
print(backends.to_string(index=False))

print("\nOK - figuras de arquitectura generadas")
