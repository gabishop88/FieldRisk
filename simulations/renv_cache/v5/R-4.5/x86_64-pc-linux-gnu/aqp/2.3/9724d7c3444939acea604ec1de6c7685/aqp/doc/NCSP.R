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

## -------------------------------------------------------------------------------------------------
library(aqp)
library(cluster)

# load data and make a copy
data("osd")
x <- osd

## -------------------------------------------------------------------------------------------------
# assume a standard deviation of 10cm for horizon boundary depths
# far too large for most horizons, but helps to make a point
x$hzd <- 10

# generate 4 realizations of each soil profile in `x`
# limit the minimum horizon thickness to 5cm
set.seed(10101)
s <- perturb(x, id = sprintf("sim-%02d", 1:4), boundary.attr = 'hzd', min.thickness = 5)

# combine source + simulated data into a single SoilProfileCollection
z <- combine(x, s)

## ----fig.width=8.5, fig.height=5------------------------------------------------------------------
# set plotSPC argument defaults
options(.aqp.plotSPC.args = list(name.style = 'center-center', depth.axis = list(style = 'compact', line = -2.5), width = 0.33, cex.names = 0.75, cex.id = 0.66, max.depth = 185))

par(mar = c(0, 0, 0, 1))
plotSPC(z)

## ----fig.width=8.5, fig.height=5.25---------------------------------------------------------------
# encode as a factor for distance calculation
z$subgroup <- factor(z$subgroup)

par(mar = c(0, 0, 1, 1))
groupedProfilePlot(z, groups = 'subgroup', group.name.offset = -10, break.style = 'arrow', group.line.lty = 1, group.line.lwd = 1)

## ----fig.width=8.5, fig.height=5.25---------------------------------------------------------------
# assign GHL
z$genhz <- generalize.hz(
  z$hzname, new = c('A', 'E', 'Bt', 'C'), 
  pattern = c('A', 'E', 'Bt', 'C|Bt4')
)

# check GHL
par(mar = c(0, 0, 3, 1))
groupedProfilePlot(z, groups = 'subgroup', group.name.offset = -10, break.style = 'arrow', group.line.lty = 1, group.line.lwd = 1, color = 'genhz')

## -------------------------------------------------------------------------------------------------
# horizon-level distance matrix weight
w1 <- 1
# perform NCSP using only the GHL (ordered factors) to a depth of 185cm
d1 <- NCSP(z, vars = c('genhz'), maxDepth = 185, k = 0, rescaleResult = TRUE)

# site-level distance matrix weight
w2 <- 2
# Gower's distance metric applied to subgroup classification (nominal factor)
d2 <- compareSites(z, 'subgroup')

# perform weighted average of distance matrices
D <- Reduce(
  `+`, 
  list(d1 * w1, d2 * w2)
) / sum(c(w1, w2))

## ----fig.width=8.5, fig.height=6------------------------------------------------------------------
library(ape)

# divisive hierarchical clustering
h <- as.hclust(diana(D))

# hang soil profile sketches from resulting dendrogram
par(mar = c(1, 0, 0, 1))
plotProfileDendrogram(z, clust = h, scaling.factor = 0.0075, y.offset = 0.1, width = 0.33, color = 'genhz', name = NA)

# annotate dendrogram with subgroup classification
# this handy function provided by the ape package
tiplabels(pch = 15, col = c(2, 3)[z$subgroup], cex = 1.5, offset = 0.05)

# helpful legend
legend('topleft', legend = levels(z$subgroup), pch = 15, col = c(2, 3), bty = 'n')

