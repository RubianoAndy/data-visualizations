#' Actividad 3 - Fase 4: comparacion de herramientas de visualizacion en R.
#'
#' Replica el mismo grafico que la comparacion en Python -consumo medio por
#' sector, con titulo, ejes rotulados, cuadricula sutil en el eje de magnitudes
#' y etiquetas de dato- con las dos herramientas dominantes en R: la
#' graficacion base y ggplot2. Se miden los mismos tres
#' indicadores (lineas de codigo efectivas, tiempo mediano de renderizado y
#' peso del PNG) y ambas escriben con el MISMO dispositivo png(type="cairo")
#' y el mismo tamano, para que la diferencia sea atribuible a la libreria.
#'
#' Escribe data/processed/comparativa_herramientas_r.csv y las figuras en
#' public/assets/images/figures/r/tools/.
#'
#' Las rutas se resuelven desde la ubicacion de este archivo, no desde el
#' directorio de trabajo, de modo que las salidas caen siempre dentro de este
#' proyecto aunque la sesion de RStudio apunte a otro.

#' keep.source permite contar las lineas reales de cada funcion, igual que
#' inspect.getsource() en la version de Python.
options(keep.source = TRUE)

if (!requireNamespace("ggplot2", quietly = TRUE)) {
  stop("Falta ggplot2. Instalalo con install.packages('ggplot2')")
}
library(ggplot2)

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
  # utils/codes/benchmark.R -> utils/codes -> utils -> raiz del proyecto
  dirname(dirname(dirname(this_file)))
}

data_path <- file.path(project_root, "data", "dataset", "consumo_energia.csv")
processed_dir <- file.path(project_root, "data", "processed")
figures_dir <- file.path(project_root, "public", "assets", "images", "figures",
                         "r", "tools")

#' Verificar el dataset antes de crear nada: si la raiz deducida fuera la
#' equivocada, el script se detiene en vez de sembrar carpetas y figuras en
#' otro proyecto.
if (!file.exists(data_path)) {
  stop(sprintf(paste0("No se encontro el dataset en '%s'. Ejecuta antes: ",
                      "python utils/codes/exploration.py"),
               data_path))
}
for (d in c(processed_dir, figures_dir)) {
  if (!dir.exists(d)) dir.create(d, recursive = TRUE)
}

cat(sprintf("Raiz del proyecto: %s\n", project_root))

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
#'
#' La cuadricula forma parte de la especificacion comun. En R base cuesta una
#' pasada extra -dibujar el marco sin relleno, insertar la cuadricula y repetir
#' las barras encima- porque no existe una nocion de "dibujar detras"; ggplot2
#' la trae en su tema y solo hay que restringirla al eje de magnitudes.

render_base <- function(salida) {
  png(salida, width = 975, height = 555, res = 150, type = "cairo")
  par(mar = c(4, 4.5, 3, 1))
  pos <- barplot(medias, col = NA, border = NA, ylim = c(0, max(medias) * 1.18),
                 main = paste(titulo, "(R base)"), xlab = eje_x, ylab = eje_y)
  grid(nx = NA, ny = NULL, col = "#cccccc", lty = 1)
  barplot(medias, col = paleta, border = "white", add = TRUE, axes = FALSE)
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
    theme(legend.position = "none", plot.title = element_text(face = "bold"),
          panel.grid.major.x = element_blank(), panel.grid.minor = element_blank())
  print(p)
  dev.off()
}

#' Cuenta las lineas de codigo del cuerpo, sin la firma, la llave de cierre,
#' los comentarios ni las lineas en blanco.
#'
#' Depende de que la funcion conserve su srcref. El options(keep.source) del
#' encabezado basta con Rscript y en RStudio, que evaluan expresion por
#' expresion, pero no con source() en una sesion no interactiva: ahi el archivo
#' se parsea entero antes de ejecutar nada, con keep.source = FALSE, y los
#' srcref se pierden. Sin esta comprobacion la medicion devolveria 0 en
#' silencio, que es peor que detenerse.
lineas_efectivas <- function(f) {
  refs <- attr(f, "srcref")
  if (is.null(refs)) {
    stop(paste("No hay srcref: no se pueden contar las lineas de codigo.",
               "Ejecuta 'Rscript utils/codes/benchmark.R' o, si usas source(),",
               "pasa source(..., keep.source = TRUE)."))
  }
  src <- trimws(as.character(refs))
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
