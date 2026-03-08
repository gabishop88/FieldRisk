## ----setup, echo=FALSE, results='hide', warning=FALSE---------------------------------------------
knitr::opts_chunk$set(
  message = FALSE,
  warning = FALSE,
  background = '#F7F7F7',
  fig.align = 'center',
  dev = 'png',
  dpi = 96,
  optipng = knitr::hook_optipng,
  comment = "#>"
)

# keep examples from using more than 2 cores
data.table::setDTthreads(Sys.getenv("OMP_THREAD_LIMIT", unset = 2))

options(width = 100, stringsAsFactors = FALSE, timeout = 600)

suppressMessages(library(aqp, quietly = TRUE))

## ----echo = FALSE, fig.width=8, fig.height=4------------------------------------------------------
.m <- '10YR 6/6'

data("munsell.spectra.wide")
w <- munsell.spectra.wide[, 1]
s <- munsell.spectra.wide[, .m]

par(mar = c(4.5, 4.5, 2, 1), cex.axis = 0.75, lend = 2)
plot(w, s, xlab = 'Wavelength (nm)', ylab = 'Reflectance', type = 'b', main = .m, cex = 0.8, pch = 16, axes = FALSE)
rect(xleft = 400, ybottom = 0.35, xright = 450, ytop = 0.4, col = parseMunsell(.m), border = 1, lwd = 1)
axis(side = 1, at = seq(380, 730, by = 20))
axis(side = 2, las = 1)

## -------------------------------------------------------------------------------------------------
# Munsell -> hex color
parseMunsell('5PB 4/6')

# Munsell -> sRGB
parseMunsell('5PB 4/6',  return_triplets = TRUE)

# Munsell -> CIELAB
parseMunsell('5PB 4/6',  returnLAB = TRUE)

# hex color -> Munsell
col2Munsell('#476189FF')

# neutral color
parseMunsell('N 5/')

# non-standard notation
getClosestMunsellChip('3.3YR 4.4/6.1', convertColors = FALSE)

