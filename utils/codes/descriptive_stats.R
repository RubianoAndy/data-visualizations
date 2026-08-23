#' Actividad 3 - Fase 3: verificacion cruzada en R del analisis estadistico.
#'
#' Lee el CSV generado por exploration.py y recalcula de forma INDEPENDIENTE
#' -sin reutilizar ningun valor de Python- la distribucion de frecuencias
#' (Sturges), las medidas de tendencia central (media, mediana, moda por clase
#' modal interpolada), las de dispersion (rango, varianza, desviacion estandar,
#' coeficiente de variacion) y las de forma (asimetria y curtosis). Si todo
#' coincide, los hallazgos no dependen de la libreria que los calculo.
#'
#' Genera ademas dos replicas graficas con la graficacion base de R, que es lo
#' que la actividad pide al exigir graficos en Python y en R: el histograma con
#' las tres medidas de tendencia central y el diagrama de caja por sector. La
#' cuadricula se traza en dos pasadas porque R base no tiene una nocion de
#' "dibujar detras de los datos" equivalente a axisbelow.
#'
#' Escribe las imagenes en public/assets/images/figures/r/statistics/.
#'
#' Las rutas se resuelven desde la ubicacion de este archivo, no desde el
#' directorio de trabajo, de modo que las salidas caen siempre dentro de este
#' proyecto aunque la sesion de RStudio apunte a otro.

#' 0. RESOLUCION DE RUTAS.
#'
#' R no expone un equivalente de __file__: con rutas relativas manda getwd(),
#' asi que una sesion abierta sobre otro proyecto escribe alli las figuras.
#' script_path() recupera la ruta real del archivo en los tres modos de
#' ejecucion: Rscript (argumento --file=), source() (variable ofile del marco
#' que hace la llamada) y el boton Source/Run de RStudio (rstudioapi).
script_path <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) > 0) {
    return(normalizePath(sub("^--file=", "", file_arg[1]), mustWork = FALSE))
  }
  for (i in seq_len(sys.nframe())) {
    ofile <- sys.frame(i)$ofile
    if (!is.null(ofile)) {
      return(normalizePath(ofile, mustWork = FALSE))
    }
  }
  if (requireNamespace("rstudioapi", quietly = TRUE) &&
      rstudioapi::isAvailable()) {
    contexto <- rstudioapi::getSourceEditorContext()
    if (!is.null(contexto) && nzchar(contexto$path)) {
      return(normalizePath(contexto$path, mustWork = FALSE))
    }
  }
  NULL
}

this_file <- script_path()
project_root <- if (is.null(this_file)) {
  normalizePath(getwd(), mustWork = FALSE)
} else {
  # utils/codes/descriptive_stats.R -> utils/codes -> utils -> raiz del proyecto
  dirname(dirname(dirname(this_file)))
}

data_path <- file.path(project_root, "data", "dataset", "consumo_energia.csv")
figures_dir <- file.path(project_root, "public", "assets", "images", "figures",
                         "r", "statistics")

#' Verificar el dataset antes de crear nada: si la raiz deducida fuera la
#' equivocada, el script se detiene en vez de sembrar carpetas y figuras en
#' otro proyecto.
if (!file.exists(data_path)) {
  stop(sprintf(paste0("No se encontro el dataset en '%s'. Ejecuta antes: ",
                      "python utils/codes/exploration.py"),
               data_path))
}
if (!dir.exists(figures_dir)) {
  dir.create(figures_dir, recursive = TRUE)
}

cat(sprintf("Raiz del proyecto: %s\n", project_root))

#' Carga de datos y vista rapida de su estructura.
df <- read.csv(data_path)
str(df)

sector_order <- c("Residencial", "Comercial", "Industrial")
df$sector <- factor(df$sector, levels = sector_order)
x <- df$consumo_kwh
n <- nrow(df)

#' 1. DISTRIBUCION DE FRECUENCIAS (regla de Sturges).
#'
#' Mismas k clases de igual amplitud que en Python; la tabla reporta fi, Fi,
#' hi (%) y Hi (%) para la verificacion cruzada.
k <- ceiling(1 + 3.322 * log10(n))
edges <- seq(min(x), max(x), length.out = k + 1)
fi <- hist(x, breaks = edges, plot = FALSE, include.lowest = TRUE)$counts
freq_table <- data.frame(
  lim_inferior = round(edges[-(k + 1)], 1),
  lim_superior = round(edges[-1], 1),
  marca_clase = round((edges[-(k + 1)] + edges[-1]) / 2, 1),
  fi = fi,
  Fi = cumsum(fi),
  hi_pct = round(fi / n * 100, 1),
  Hi_pct = round(cumsum(fi) / n * 100, 1)
)
cat("Distribucion de frecuencias recalculada en R\n")
print(freq_table, row.names = FALSE)

#' Moda interpolada dentro de la clase modal: Mo = L + d1 / (d1 + d2) * w.
interpolated_mode <- function(values, bin_edges) {
  counts <- hist(values, breaks = bin_edges, plot = FALSE,
                 include.lowest = TRUE)$counts
  m <- which.max(counts)
  width <- bin_edges[m + 1] - bin_edges[m]
  d1 <- counts[m] - ifelse(m > 1, counts[m - 1], 0)
  d2 <- counts[m] - ifelse(m < length(counts), counts[m + 1], 0)
  if (d1 + d2 == 0) {
    return(bin_edges[m] + width / 2)
  }
  bin_edges[m] + d1 / (d1 + d2) * width
}

#' Asimetria y curtosis de Fisher con la correccion muestral que usa pandas,
#' de modo que ambos lenguajes reporten exactamente el mismo numero.
skewness <- function(v) {
  m <- length(v)
  z <- (v - mean(v)) / sd(v)
  m / ((m - 1) * (m - 2)) * sum(z^3)
}

kurtosis <- function(v) {
  m <- length(v)
  z <- (v - mean(v)) / sd(v)
  m * (m + 1) / ((m - 1) * (m - 2) * (m - 3)) * sum(z^4) -
    3 * (m - 1)^2 / ((m - 2) * (m - 3))
}

#' 2. TENDENCIA CENTRAL, DISPERSION Y FORMA por sector y a nivel global.
#'
#' var() y sd() de R son muestrales (denominador n - 1), igual que en pandas,
#' por lo que los valores deben coincidir digito a digito con
#' central_tendency.csv y dispersion.csv.
summary_stats <- function(values) {
  k_g <- ceiling(1 + 3.322 * log10(length(values)))
  edges_g <- seq(min(values), max(values), length.out = k_g + 1)
  cuartiles <- quantile(values, c(0.25, 0.75), type = 7)
  c(
    n = length(values),
    media = round(mean(values), 1),
    mediana = round(median(values), 1),
    moda_interpolada = round(interpolated_mode(values, edges_g), 1),
    rango = round(max(values) - min(values), 1),
    varianza = round(var(values), 1),
    desv_std = round(sd(values), 1),
    cv_pct = round(sd(values) / mean(values) * 100, 1),
    iqr = round(unname(diff(cuartiles)), 1),
    asimetria = round(skewness(values), 2),
    curtosis = round(kurtosis(values), 2)
  )
}

stats_by_group <- t(sapply(sector_order,
                           function(s) summary_stats(x[df$sector == s])))
cat("\nMedidas descriptivas recalculadas en R (kWh)\n")
print(rbind(stats_by_group, Global = summary_stats(x)))
cat("Moda del sector (variable nominal):",
    names(which.max(table(df$sector))), "\n")

#' 3. REPLICAS GRAFICAS EN R.
#'
#' Principios aplicados, los mismos que en Python: titulo informativo, ejes con
#' unidades, eje de frecuencias desde cero, cuadricula sutil detras de los datos
#' y color funcional.

#' Histograma con clases de Sturges y las tres medidas de tendencia central.
#'
#' La primera pasada traza un histograma sin relleno para fijar ejes y escala,
#' la cuadricula se inserta detras y la segunda pasada dibuja las barras encima.
png(file.path(figures_dir, "hist_sturges_central_tendency.png"),
    width = 1950, height = 1140, res = 300, type = "cairo")
par(mar = c(4, 4.5, 3, 1), las = 1)
hist(x, breaks = edges, border = NA, col = NA, include.lowest = TRUE,
     main = sprintf("Distribución de frecuencias del consumo (R, %d clases)", k),
     xlab = "Consumo (kWh/mes)", ylab = "Frecuencia absoluta (clientes)")
grid(nx = NA, ny = NULL, col = "#cccccc", lty = 1)
hist(x, breaks = edges, col = "#2c7fb8", border = "white",
     include.lowest = TRUE, add = TRUE)
global_mode <- interpolated_mode(x, edges)
abline(v = c(global_mode, median(x), mean(x)),
       col = "#d95f02", lty = c(3, 2, 1), lwd = 1.4)
legend("topright", cex = 0.75, col = "#d95f02", lty = c(3, 2, 1), lwd = 1.4,
       legend = c(sprintf("Moda = %.0f", global_mode),
                  sprintf("Mediana = %.0f", median(x)),
                  sprintf("Media = %.0f", mean(x))))
dev.off()

#' Diagrama de caja por sector con la media y la desviacion estandar
#' superpuestas, tambien en dos pasadas.
png(file.path(figures_dir, "boxplot_dispersion_by_sector.png"),
    width = 1950, height = 1140, res = 300, type = "cairo")
par(mar = c(4, 4.5, 3, 1), las = 1)
boxplot(consumo_kwh ~ sector, data = df, border = NA, ylim = c(0, max(x) * 1.15),
        main = "Dispersión del consumo por sector (R)",
        xlab = "Sector", ylab = "Consumo (kWh/mes)")
grid(nx = NA, ny = NULL, col = "#cccccc", lty = 1)
boxplot(consumo_kwh ~ sector, data = df,
        col = c("#a6bddb", "#74a9cf", "#2b8cbe"), add = TRUE, axes = FALSE)
group_means <- tapply(x, df$sector, mean)
group_sd <- tapply(x, df$sector, sd)
points(seq_along(sector_order), group_means, col = "#d95f02", pch = 19)
text(seq_along(sector_order), tapply(x, df$sector, max) + max(x) * 0.05,
     labels = sprintf("sigma = %.0f", group_sd), cex = 0.75)
legend("topleft", cex = 0.75, bty = "n", col = "#d95f02", pch = 19,
       legend = "Media")
dev.off()

cat("\nOK - verificacion cruzada y figuras de R generadas\n")
