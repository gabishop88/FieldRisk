## ----setup, include=FALSE-----------------------------------------------------
knitr::opts_chunk$set(echo = TRUE)
library(apsimx)
library(ggplot2)
apsimx_options(warn.versions = FALSE)
tmp.dir <- tempdir()

## ----sens0, eval = FALSE------------------------------------------------------
# ## Create a temporary directory and copy the Wheat.apsimx file
# tmp.dir <- tempdir()
# extd.dir <- system.file("extdata", package = "apsimx")
# file.copy(file.path(extd.dir, "Wheat.apsimx"), tmp.dir)
# ## Identify a parameter of interest
# ## In this case we want to know the impact of varying the fertilizer amount
# pp <- inspect_apsimx("Wheat.apsimx", src.dir = tmp.dir,
#                       node = "Manager", parm = list("SowingFertiliser", 1))
# ## For simplicity, we create a vector of fertilizer amounts (instead of sampling)
# ferts <- seq(5, 200, length.out = 7)
# col.res <- NULL
# for(i in seq_along(ferts)){
# 
#   edit_apsimx("Wheat.apsimx", src.dir = tmp.dir,
#               node = "Other",
#               parm.path = pp, parm = "Amount",
#               value = ferts[i])
# 
#   sim <- apsimx("Wheat.apsimx", src.dir = tmp.dir)
#   col.res <- rbind(col.res, data.frame(fertilizer.amount = ferts[i],
#                                        wheat.aboveground.wt = mean(sim$Wheat.AboveGround.Wt, na.rm = TRUE)))
# }

## ----sens_apsimx, eval = FALSE------------------------------------------------
# tmp.dir <- tempdir()
# extd.dir <- system.file("extdata", package = "apsimx")
# file.copy(file.path(extd.dir, "Wheat.apsimx"), tmp.dir)
# ## Identify a parameter of interest
# ## In this case we want to know the impact of varying the fertilizer amount
# ## and the plant population
# pp1 <- inspect_apsimx("Wheat.apsimx", src.dir = tmp.dir,
#                       node = "Manager", parm = list("SowingFertiliser", 1))
# pp1 <- paste0(pp1, ".Amount")
# 
# pp2 <- inspect_apsimx("Wheat.apsimx", src.dir = tmp.dir,
#                       node = "Manager", parm = list("SowingRule1", 9))
# pp2 <- paste0(pp2, ".Population")
# 
# ## The names in the grid should (partially) match the parameter path names
# grd <- expand.grid(Fertiliser = c(50, 100, 150), Population = c(100, 200, 300))
# 
# ## This takes 2-3 minutes
# sns <- sens_apsimx("Wheat.apsimx", src.dir = tmp.dir,
#                     parm.paths = c(pp1, pp2),
#                     grid = grd)

## ----sensitivity-parameterSets------------------------------------------------
library(sensitivity)
## Simple example: see documentation for other options
X.grid <- parameterSets(par.ranges = list(Fertiliser = c(1, 300), 
                                          Population = c(1, 300)),
                        samples = c(3,3), method = "grid")
X.grid

## ----sensitivity-morris-------------------------------------------------------
X.mrrs <- morris(factors = c("Fertiliser", "Population"),
                   r = 3, design = list(type = "oat", levels = 3, grid.jump = 1),
                   binf = c(0, 5), bsup = c(200, 300))
X.mrrs$X

## ----sensitivity-decoupling, eval = FALSE-------------------------------------
# ## This takes 2-3 minutes
# sns2 <- sens_apsimx("Wheat.apsimx", src.dir = tmp.dir,
#                      parm.paths = c(pp1, pp2),
#                      grid = X.mrrs$X)
# ## These are the sensitivity results for AboveGround.Wt only
# sns.res.ag <- tell(X.mrrs, sns2$grid.sims$Wheat.AboveGround.Wt)
# sns.res.ag
# ## Call: morris(factors = c("Fertiliser", "Population"),
# ## r = 3, design = list(type = "oat", levels = 3, grid.jump = 1),
# ## binf = c(0, 5), bsup = c(200, 300))
# ##
# ## Model runs: 9
# ##                 mu  mu.star    sigma
# ## Fertiliser 916.6674 916.6674 662.8798
# ## Population 448.4530 448.4530 640.6807
# plot(sns.res.ag)

