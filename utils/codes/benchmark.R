#' Actividad 3 - Fase 5: comparacion de herramientas de visualizacion en R.
#'
#' Replica el mismo grafico que la comparacion en Python -consumo medio por sector, con
#' titulo, ejes rotulados y etiquetas de dato- con las dos herramientas
#' dominantes en R: la graficacion base y ggplot2. Se miden los mismos tres
#' indicadores (lineas de codigo efectivas, tiempo mediano de renderizado y
#' peso del PNG) y ambas escriben con el MISMO dispositivo png(type="cairo")
#' y el mismo tamano, para que la diferencia sea atribuible a la libreria.
#'
#' Escribe data/processed/comparativa_herramientas_r.csv y las figuras en
#' public/assets/images/figures/r/tools/. Ejecutar desde la raiz del proyecto.

#' keep.source permite contar las lineas reales de cada funcion, igual que
#' inspect.getsource() en la version de Python.
options(keep.source = TRUE)

if (!requireNamespace("ggplot2", quietly = TRUE)) {
  stop("Falta ggplot2. Instalalo con install.packages('ggplot2')")
}
library(ggplot2)

data_path <- "data/dataset/consumo_energia.csv"
processed_dir <- file.path("data", "processed")
figures_dir <- file.path("public", "assets", "images", "figures", "r", "tools")
for (d in c(processed_dir, figures_dir)) {
  if (!dir.exists(d)) dir.create(d, recursive = TRUE)
}
if (!file.exists(data_path)) {
  stop("No se encontro el dataset. Ejecuta antes: python utils/codes/exploration.py")
}

df <- read.csv(data_path)
orden <- c("Residencial", "Comercial", "Industrial")
df$sector <- factor(df$sector, levels = orden)
medias <- tapply(df$consumo_kwh, df$sector, mean)
paleta <- c("#a6bddb", "#74a9cf", "#2b8cbe")
titulo <- "Consumo medio por sector"
eje_x <- "Sector"
eje_y <- "Consumo (kWh/mes)"

#' 1. EL MISMO GRAFICO CON LAS DOS HERRAMIENTAS.
#'
#' Cada funcion se escribe con el estilo idiomatico de su libreria: base
#' dibuja por pasos sobre un dispositivo abierto, ggplot2 declara el grafico
#' como una suma de capas y lo imprime al final.

render_base <- function(salida) {
  png(salida, width = 975, height = 555, res = 150, type = "cairo")
  par(mar = c(4, 4.5, 3, 1))
  pos <- barplot(medias, col = paleta, border = "white",
                 ylim = c(0, max(medias) * 1.18),
                 main = paste(titulo, "(R base)"), xlab = eje_x, ylab = eje_y)
  text(pos, medias + max(medias) * 0.04, labels = sprintf("%.0f", medias), cex = 0.8)
  dev.off()
}

render_ggplot <- function(salida) {
  png(salida, width = 975, height = 555, res = 150, type = "cairo")
  datos <- data.frame(sector = factor(orden, levels = orden), media = as.numeric(medias))
  p <- ggplot(datos, aes(x = sector, y = media, fill = sector)) +
    geom_col(color = "white") +
    geom_text(aes(label = sprintf("%.0f", media)), vjust = -0.5, size = 3) +
    scale_fill_manual(values = paleta) +
    expand_limits(y = max(medias) * 1.18) +
    labs(title = paste(titulo, "(ggplot2)"), x = eje_x, y = eje_y) +
    theme_minimal(base_size = 10) +
    theme(legend.position = "none", plot.title = element_text(face = "bold"))
  print(p)
  dev.off()
}

#' Cuenta las lineas de codigo del cuerpo, sin la firma, la llave de cierre,
#' los comentarios ni las lineas en blanco.
lineas_efectivas <- function(f) {
  src <- trimws(as.character(attr(f, "srcref")))
  src <- src[-c(1, length(src))]
  sum(nchar(src) > 0 & !startsWith(src, "#"))
}

#' 2. MEDICION.
#'
#' Una pasada de calentamiento y cinco cronometradas; se reporta la mediana
#' para que una pausa puntual del sistema no distorsione el resultado.
herramientas <- list(
  list(f = render_base, nombre = "R base (graphics)", archivo = "bar_r_base.png",
       version = paste(R.version$major, R.version$minor, sep = "."),
       paradigma = "Imperativa (dibujo por pasos)",
       motor = "grDevices / Cairo", interactivo = "No (imagen estatica)",
       nota = "Viene con R; sintaxis breve pero cada detalle se ajusta a mano"),
  list(f = render_ggplot, nombre = "ggplot2", archivo = "bar_r_ggplot2.png",
       version = as.character(packageVersion("ggplot2")),
       paradigma = "Declarativa (gramatica de graficos)",
       motor = "grid / Cairo", interactivo = "No (imagen estatica)",
       nota = "Capas componibles y estilo consistente; es el estandar en R")
)

filas <- lapply(herramientas, function(h) {
  salida <- file.path(figures_dir, h$archivo)
  h$f(salida)
  tiempos <- replicate(5, {
    inicio <- Sys.time()
    h$f(salida)
    as.numeric(difftime(Sys.time(), inicio, units = "secs")) * 1000
  })
  data.frame(
    herramienta = h$nombre,
    version = h$version,
    paradigma = h$paradigma,
    motor_render = h$motor,
    interactivo = h$interactivo,
    loc = lineas_efectivas(h$f),
    tiempo_ms = round(median(tiempos), 1),
    peso_kb = round(file.size(salida) / 1024, 1),
    observacion = h$nota
  )
})

comparativa <- do.call(rbind, filas)
write.csv(comparativa, file.path(processed_dir, "comparativa_herramientas_r.csv"),
          row.names = FALSE)
cat("Comparacion de herramientas de visualizacion (R)\n")
print(comparativa[, c("herramienta", "version", "loc", "tiempo_ms", "peso_kb")],
      row.names = FALSE)

cat("\nOK - comparacion de herramientas de R completada\n")
